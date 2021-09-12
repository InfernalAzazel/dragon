import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger
from func.jd_web_hook.models import WebHookItem
from conf import Settings
from lunar_you_ying import JDSDK

doc = '''
    新增或修改物流备忘录

'''


def register(router: APIRouter):
    @router.post('/r-r-application-for-violations', tags=['审核违规情况奖励申请'], description=doc)
    async def r_r_application_for_violations(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
    jd = JDSDK(
        app_id=Settings.JD_APP_ID_BUSINESS,
        entry_id="61128c29bf70cb00077c8703",
        api_key=Settings.JD_API_KEY,
    )

    # 提交时候触发并且创建数据
    if whi.data['flowState'] == 0 and whi.op == 'data_create':
        _, err = await jd.create_data(
            data={
                'name': {'value': whi.data['violation_name']},
                'no': {'value': whi.data['violation_no']}
            }
        )
        await errFn(err)
    # 流程完成后
    elif whi.data['flowState'] == 1 and whi.op == 'data_update':
        if whi.data['processing_type'] == "在职罚款":
            _, err = await jd.query_delete_one(
                data_filter={"cond": [
                    {
                        "field": 'no',
                        "type": 'text',
                        "method": "eq",
                        "value": whi.data['violation_no']
                    }
                ]}
            )
            await errFn(err)
    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
