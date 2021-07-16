import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from api.v1.jd_web_hook.models import WebHookItem
from utils.jd_api import JdAPI

doc = '''

    校验:

        字段

    流程:

        手动结束 -> 清空 
        
        姓名
        手机号码
        身份证号码 
        
'''
# 入职申请表单
entry_application_form = JdAPI(app_id=JdAPI.APP_ID_MINISTRY_OF_PERSONNEL, entry_id='5df73f5ca667c000067cd60c')  # 上线


def register(router: APIRouter):
    @router.post('/entry_application/verify-field', tags=['入职申请表单-校验字段重复'], description=doc)
    async def entry_application_verify_field(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != JdAPI.get_signature(
                nonce=req.query_params['nonce'],
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

    widgets = await entry_application_form.get_form_widgets()

    for wid in widgets:
        if str(wid['label']) == '姓名':
            name_field = str(wid['name'])
            name_types = str(wid['type'])
        elif str(wid['label']) == '身份证号码':
            id_card_field = str(wid['name'])
        elif str(wid['label']) == '手机号码':
            mobile_phone_field = str(wid['name'])

    value = await entry_application_form.get_form_data(
        data_filter={
            "cond": [
                {
                    "field": name_field,
                    "type": name_types,
                    "method": "eq",
                    "value": whi.data[name_field]
                }
            ]
        })

    if value:
        for val in value:
            if val['flowState'] == 2:
                await entry_application_form.update_data(
                    dataId=whi.data['_id'],
                    data={
                        name_field: {'value': ''},
                        mobile_phone_field: {'value': ''},
                        id_card_field: {'value': ''}
                    })

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
