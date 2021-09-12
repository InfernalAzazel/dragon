import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from conf import Settings
from func.jd_web_hook import WebHookItem
from lunar_you_ying import JDSDK, JDSerialize

doc = '''
    修改工资缴纳工资扣款日期 -> 流程完成 -> 触发

    目标表单：工资扣款（主表） 工资缴纳支出审批

'''


def register(router: APIRouter):
    @router.post('/m-p-payment-deduction-date', tags=['修改工资缴纳工资扣款日期-修改2个表单'], description=doc)
    async def m_p_payment_deduction_date(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != JDSDK.get_signature(
                nonce=req.query_params['nonce'],
                secret=Settings.JD_SECRET,
                timestamp=req.query_params['timestamp'],
                payload=bytes(await req.body()).decode('utf-8')):
            return 'fail', 401
        # 添加任务
        background_tasks.add_task(business, whi)
        return '2xx'


# 处理业务
async def business(whi):
    async def errFn(e):
        if e is not None:
            print(e)

    # 启动时间
    start = time.perf_counter()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':

        modifySubForm = whi.data['modify_details']

        jd = JDSDK.auto_init(
            app_id_list=[
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
            ],
            entry_id_list=[
                '6107694c948a220008d383ad',
                '61078f39c7d3ad00089ed5d3'
            ],
            api_key=Settings.JD_API_KEY,
        )

        jd_payroll_deduction_form = jd[0]  # 工资扣款（主表）
        jd_salary_payment_expenditure_approval_form = jd[1]  # 工资缴纳支出审批

        for modify in modifySubForm:
            res, err = await jd_payroll_deduction_form.query_update_data_one(
                data_filter={
                    "cond": [
                        {
                            "field": 'wyz',
                            "type": 'text',
                            "method": "eq",
                            "value": modify['wyz']
                        }
                    ]
                },
                data={
                    'modify_number': {'value': whi.data['modify_number']},
                    'kkrq': {'value': modify['kkrq']},
                    'kkny': {'value': modify['kkny']},
                    'nygh': {'value': modify['nygh']},
                }
            )
            await errFn(err)

            res, err = await jd_salary_payment_expenditure_approval_form.get_form_data(
                data_filter={
                    "cond": [
                        {
                            "field": 'jzdh',
                            "type": 'text',
                            "method": "eq",
                            "value": modify['source_number']
                        }
                    ]
                }
            )
            await errFn(err)
            if res:
                deductionSubForm = res[0]['deduction']
                for i in range(len(deductionSubForm)):
                    if modify['wyz'] == deductionSubForm[i]['wyz']:
                        deductionSubForm[i]['kkrq'] = modify['kkrq']
                        deductionSubForm[i]['kkny'] = modify['kkny']
                        deductionSubForm[i]['nygh'] = modify['nygh']
                _, err = await jd_salary_payment_expenditure_approval_form.update_data(
                    dataId=res[0]['_id'],
                    data=JDSerialize.subform('deduction', deductionSubForm))
                await errFn(err)
        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
