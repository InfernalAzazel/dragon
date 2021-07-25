import time

from dragon_micro_client import MicroClientConfig, AsyJDAPI
from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

import settings
from api.v1.jd_web_hook.models import WebHookItem

doc = '''

   质量监控计划

'''


def register(router: APIRouter):
    @router.post('/quality-monitor-plan-launch2', tags=['质量监控计划'], description=doc)
    async def quality_monitor_plan_launch2(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != AsyJDAPI.get_signature(
                secret=settings.Default.JD_SECRET,
                nonce=req.query_params['nonce'],
                timestamp=req.query_params['timestamp'],
                payload=bytes(await req.body()).decode('utf-8')):
            return 'fail', 401
        # 添加任务
        background_tasks.add_task(business, whi)

        return '2xx'


# 处理业务
async def business(whi: WebHookItem):
    # 启动时间
    start = time.perf_counter()
    # print(whi.data)
    # 配置腾龙微服务
    mcc = MicroClientConfig(
        mcc_url=settings.Default.MCC_BASIC_URL,
        token=settings.Default.MCC_BASIC_TOKEN
    )
    # 异步模式-使用简道云接口 单表单
    asy_jd = AsyJDAPI(
        app_id=settings.Default.JD_APP_ID_QUALITY,
        entry_id='60f28718598cae0008105cae',
        api_key=settings.Default.JD_API_KEY,
        mcc=mcc
    )
    await asy_jd.query_update_data_one(
        data_filter={
            "cond": [
                {
                    "field": 'linear_project',
                    "type": 'text',
                    "method": "eq",
                    "value": whi.data['linear_project']
                }
            ]
        },
        data={
            'current_date': {'value': whi.data['current_date']},
            'next_date': {'value': whi.data['next_date']},
        }
    )

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 更新完成')
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
