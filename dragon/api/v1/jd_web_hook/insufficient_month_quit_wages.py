import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from api.v1.jd_web_hook.models import WebHookItem
from conf import Settings, Micro
from dragon_micro_client import AsyJDAPI

doc = '''
    
    不足月离职工资（丽嘉） -> 流程完成 -> 触发
    
    创建数据

'''


def register(router: APIRouter):
    @router.post('/insufficient-month-quit-wages', tags=['不足月离职工资（丽嘉）-创建数据到->工资扣款（主表）'], description=doc)
    async def insufficient_month_quit_wages(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != AsyJDAPI.get_signature(
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
    # 启动时间
    start = time.perf_counter()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':

        form_name = whi.data['formName']  # 来源表单
        jzdh = whi.data['form_no']  # 来源单号
        deduction = whi.data['jz_content']  # 扣款子表

        # 工资扣款（主表）
        jd = AsyJDAPI(
            app_id=Settings.JD_APP_ID_BUSINESS,
            entry_id='6107694c948a220008d383ad',
            api_key=Settings.JD_API_KEY,
            mcc=Micro.mcc
        )
        for value in deduction:
            money = value['jz_money'] - value['jz_money']*2
            await jd.query_update_data_one(
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
                },
                data={
                    'source_form': {'value': form_name},  # 来源表单
                    'jzdh': {'value': jzdh},  # 来源单号
                    'jzje': {'value': money},  # 金额
                    'jzzy': {'value': value['jz_zhaiyao']},  # 摘要
                    'jzr': {'value': whi.data['person']['username']},  # 姓名
                    'jzr_wb': {'value': whi.data['jzr_wb']},  # 姓名（文本）
                    'jzrgh': {'value': value['jz_person_code']},  # 工号
                    # 'gsbm': {'value': [value['gsbm'][0]['dept_no']]},  # 归属部门
                    # 'kkrq': {'value': value['kkrq']},  # 对应工资扣款日期
                    # 'kkny': {'value': value['kkny']},  # 对应工资扣款年月
                    'nygh': {'value': value['nygh']},  # 年月+工号
                    'kmdm': {'value': value['jz_code']},  # 科目代码
                    'kmmc': {'value': value['kmmc']},  # 科目名称
                    'kklb': {'value': value['kklb']},  # 扣款类别
                    'wyz': {'value': value['wyz']},  # 唯一值
                },
                non_existent_create=True
            )

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
