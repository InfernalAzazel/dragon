import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from func.jd_web_hook.models import WebHookItem
from conf import Settings
from lunar_you_ying import JDSDK

doc = '''
    结案离职工资申请-修改多个表单 -> 流程完成 -> 触发

    修改表单: 
    修改以下
    
    活动申请  字段：流水号、结案日期 结案年月

'''


def register(router: APIRouter):
    @router.post('/c-r-salary-application', tags=['结案离职工资申请-修改多个表单'], description=doc)
    async def c_r_salary_application(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
async def business(whi: WebHookItem):

    async def errFn(e):
        if e is not None:
            print(e)

    # 启动时间
    start = time.perf_counter()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':

        jd = JDSDK.auto_init(
            app_id_list=[
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
            ],
            entry_id_list=[
                '5e620f208b64ef000672d4d6',  # 实销量/发货量工资单
                '5e78cdf902ab2600065863e1',  # 品牌总监工资单
                '5e5fa2dad1691000066b927d',  # 省外直营业代工资
                '5f1e3278ad6bed00063798ad',  # 省外直营业代工资（新版）
                '5e5f6521d45f4b00069a70a7',  # 省内直营业代工资
                '5e8840e252d3630006430dbe'  # 不足月离职工资（丽嘉）
            ],
            api_key=Settings.JD_API_KEY,
        )

        sub_form = whi.data['sublist_1']

        for value in sub_form:

            if value['source_form'] == '实销量/发货量工资单':
                field = 'nianyuegh'
                whi_field = 'years_job'
                jds = jd[0]
            elif value['source_form'] == '品牌总监工资单':
                field = 'nianyuegh'
                whi_field = 'years_job'
                jds = jd[1]
            elif value['source_form'] == '省外直营业代工资':
                field = 'nianyuegh'
                whi_field = 'years_job'
                jds = jd[2]
            elif value['source_form'] == '省外直营业代工资（新版）':
                field = 'nianyuegh'
                whi_field = 'years_job'
                jds = jd[3]
            elif value['source_form'] == '省内直营业代工资':
                field = 'nianyuegh'
                whi_field = 'years_job'
                jds = jd[4]
            else:
                field = 'gz_no'
                whi_field = 's_no'
                jds = jd[5]

            _, err = await jds.query_update_data_one(
                data_filter={
                    "cond": [
                        {
                            "field": field,
                            "type": 'text',
                            "method": "eq",
                            "value": value[whi_field]
                        }
                    ]},
                data={
                    # 流水号
                    'closing_application_no': {
                        'value': whi.data['source_no']
                    },
                    # 结案日期
                    'u8_date': {
                        'value': whi.data['close_date']
                    },
                    # 结案年月
                    'u8_years': {
                        'value': whi.data['close_yearm']
                    },
                }
            )
            await errFn(err)

        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
