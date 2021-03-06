from fastapi import APIRouter, Request, BackgroundTasks
from robak import Jdy, JdySerialize

from conf import Settings
from func.jd_web_hook.models import WebHookItem

doc = '''
    
    工资缴纳支出审批 -> 流程完成 -> 触发
    
    创建数据
    
    工资扣款（主表）
'''


def register(router: APIRouter):
    @router.post('/salary-deduction-approval', tags=['工资缴纳支出审批-创建数据到->工资扣款（主表）'], description=doc)
    async def salary_deduction_approval(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != Jdy.get_signature(
                nonce=req.query_params['nonce'],
                secret=Settings.JD_SECRET,
                timestamp=req.query_params['timestamp'],
                payload=bytes(await req.body()).decode('utf-8')):
            return 'fail', 401
        # 添加任务
        background_tasks.add_task(business, whi, str(req.url))
        return '2xx'


# 处理业务
async def business(whi: WebHookItem, url):
    async def errFn(e):
        if e is not None:
            await Settings.log.send(
                level=Settings.log.ERROR,
                url=url,
                secret=Settings.JD_SECRET,
                err=e,
                data=whi.dict(),
                is_start_workflow=True
            )
            return

    # 启动时间
    start = Settings.log.start_time()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':

        form_name = whi.data['formName']  # 来源表单
        jzdh = whi.data['jzdh']  # 来源单号
        deduction = whi.data['deduction']  # 扣款子表

        # 工资扣款（主表）
        jdy = Jdy(
            app_id=Settings.JD_APP_ID_BUSINESS,
            entry_id='6107694c948a220008d383ad',
            api_key=Settings.JD_API_KEY,
        )
        for value in deduction:
            try:
                gsbm = [value['gsbm'][0]['dept_no']]
            except:
                gsbm = []
            await jdy.query_update_data_one(
                data_filter={
                    "rel": "and",  # 或者"or"
                    "cond": [
                        {
                            "field": 'jzdh',
                            "type": 'text',
                            "method": "eq",
                            "value": whi.data['jzdh']  # 来源单号
                        },
                        {
                            "field": 'wyz',
                            "type": 'text',
                            "method": "eq",
                            "value": value['wyz']
                        },
                    ],
                },
                data={
                    'debit_no': {'value': value['jz_no']},  # 工资单的借支单号
                    'back_write': {'value': '是'},  # 回写
                    'source_form': {'value': form_name},  # 来源表单
                    'jzdh': {'value': jzdh},  # 来源单号
                    'jzje': {'value': value['jzje']},  # 金额
                    'jzzy': {'value': value['jzzy']},  # 摘要
                    'jzr': {'value': JdySerialize.member_err_to_none(value, 'jzr')},  # 姓名
                    'jzr_wb': {'value': value['jzr_wb']},  # 姓名（文本）
                    'jzrgh': {'value': value['jzrgh']},  # 工号
                    'gsbm': {'value': gsbm},  # 归属部门
                    'kkrq': {'value': value['kkrq']},  # 对应工资扣款日期
                    'kkny': {'value': value['kkny']},  # 对应工资扣款年月
                    'nygh': {'value': value['nygh']},  # 年月+工号
                    # 'kmdm': {'value': value['kmdm']},  # 科目代码
                    # 'kmmc': {'value': value['kmmc']},  # 科目名称
                    'kklb': {'value': value['kklb']},  # 扣款类别
                    'wyz': {'value': value['wyz']},  # 唯一值
                }
            )

    elif whi.data['flowState'] == 1 and whi.op == 'data_remove':
        deduction = whi.data['jz_content']  # 扣款子表

        # 工资扣款（主表）
        jdy = Jdy(
            app_id=Settings.JD_APP_ID_BUSINESS,
            entry_id='6107694c948a220008d383ad',
            api_key=Settings.JD_API_KEY,
        )
        for value in deduction:
            _, err = await jdy.query_delete_one(
                data_filter={
                    "rel": "and",  # 或者"or"
                    "cond": [
                        {
                            "field": 'jzdh',
                            "type": 'text',
                            "method": "eq",
                            "value": whi.data['gz_no']  # 来源单号
                        },
                        {
                            "field": 'wyz',
                            "type": 'text',
                            "method": "eq",
                            "value": value['wyz']  # 唯一值
                        },
                    ],
                }
            )
            await errFn(err)

    # 结束时间
    Settings.log.print(name=url, info=f'程序处理耗时 {Settings.log.elapsed(start)}s')
