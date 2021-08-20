import time

from dragon_micro_client import AsyJDAPI
from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from api.v1.jd_web_hook.models import WebHookItem
from conf import Settings, Micro

doc = '''
    账号管理-人员维护

'''


def register(router: APIRouter):
    @router.post('/personnel-maintain', tags=['账号管理-人员维护'], description=doc)
    async def personnel_maintain(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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

    jd = AsyJDAPI(
        app_id=Settings.JD_APP_ID_MINISTRY_OF_PERSONNEL,
        entry_id="5df87216281aa4000604af2e",
        api_key=Settings.JD_API_KEY,
        mcc=Micro.mcc
    )

    # 人员维护表单
    personnel_maintain_form = jd

    await personnel_maintain_form.query_update_data_one(
        data_filter={
            "rel": "and",
            "cond": [
                {
                    "field": 'name',
                    "type": 'text',
                    "method": whi.data['_widget_1571113838984'],
                },
            ]
        },
        data={
            'name': {
                'value': whi.data['_widget_1571113838984']
            },
            'name_member': {
                'value': whi.data['_widget_1571113838969']
            },
        },
        non_existent_create=True
    )
    # # 流程完成
    # if whi.data['flowState'] == 1 and whi.op == 'data_update':

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 入职申请表-人员维护 处理耗时 {elapsed}s')
