import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from api.v1.jd_web_hook.models import WebHookItem
from conf import Settings, Micro
from dragon_micro_client import AsyJDAPI

doc = '''

    校验:

        字段

    流程:

        手动结束 -> 清空 
        
        姓名
        手机号码
        身份证号码 
        
'''


def register(router: APIRouter):
    @router.post('/entry_application/verify-field', tags=['入职申请表单-校验字段重复'], description=doc)
    async def entry_application_verify_field(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != AsyJDAPI.get_signature(
                secret=Settings.JD_SECRET,
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
    # 入职申请表单
    entry_application_form = AsyJDAPI(
        app_id=Settings.JD_APP_ID_MINISTRY_OF_PERSONNEL,
        entry_id='5df73f5ca667c000067cd60c',
        api_key=Settings.JD_API_KEY,
        mcc=Micro.mcc
    )  # 上线

    res = await entry_application_form.get_form_data(
        data_filter={
            "cond": [
                {
                    "field": 'name',
                    "type": 'text',
                    "method": "eq",
                    "value": whi.data['name']
                }
            ]
        })

    if res:
        for val in res:
            # 手动结束
            if val['flowState'] == 2:
                await entry_application_form.update_data(
                    dataId=val['_id'],
                    data={
                        'name': {'value': ''},
                        'phone': {'value': ''},
                        'id_card': {'value': ''}
                    })

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
