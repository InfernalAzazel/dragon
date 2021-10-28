import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from func.jd_web_hook.models import WebHookItem
from conf import Settings
from robak import Jdy

doc = '''

    触发表单 订单费用剩余数量过渡表  
    修改  活动-订单过渡表

'''


def register(router: APIRouter):
    @router.post('/order-fee', tags=['订单费用剩余数量过渡表'], description=doc)
    async def order_fee(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != Jdy.get_signature(
                secret=Settings.JD_SECRET,
                nonce=req.query_params['nonce'],
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
                data=whi.dict()
            )
            return

    # 启动时间
    start = Settings.log.start_time()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':
        if whi.data['surplus_count'] == 0 or whi.data['actual_count'] == 0:
            # 业务管理 -> 活动-订单过渡表
            jd = Jdy(
                app_id=Settings.JD_APP_ID_BUSINESS,
                entry_id='5de241b77d6271000609bb76',
                api_key=Settings.JD_API_KEY,
            )
            value, err = await jd.get_form_data(data_filter={
                "cond": [
                    {
                        "field": 'activity_code',
                        "type": 'text',
                        "method": "eq",
                        "value": whi.data['activity_code']  # 活动识别码
                    }
                ]
            })
            await errFn(err)
            if value:
                _, err = await jd.update_data(value[0]['_id'], data={'use_state': {"value": "已使用"}})
                await errFn(err)

        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 更新完成')
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
