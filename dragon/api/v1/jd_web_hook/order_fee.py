import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from api.v1.jd_web_hook.models import WebHookItem
from utils.jd_api import JdAPI

doc = '''

    触发表单 订单费用剩余数量过渡表  
    修改  活动-订单过渡表

'''


def register(router: APIRouter):
    @router.post('/order-fee', tags=['订单费用剩余数量过渡表'], description=doc)
    async def order_fee(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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

    if whi.data['flowState'] == 1 and whi.op == 'data_update':
        if whi.data['surplus_count'] == 0 or whi.data['actual_count'] == 0:
            # 业务管理 -> 活动-订单过渡表
            jd = JdAPI(app_id=JdAPI.APP_ID_BUSINESS, entry_id='5de241b77d6271000609bb76')
            value = await jd.get_form_data(data_filter={
                "cond": [
                    {
                        "field": 'activity_code',
                        "type": 'text',
                        "method": "eq",
                        "value": whi.data['activity_code']  # 活动识别码
                    }
                ]
            })

            if value:
                await jd.update_data(value[0]['_id'], data={'use_state': {"value": "已使用"}})

        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 更新完成')
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
