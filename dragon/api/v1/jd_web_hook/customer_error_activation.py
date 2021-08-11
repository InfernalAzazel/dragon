import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from api.v1.jd_web_hook.models import WebHookItem
from dragon_micro_client import AsyJDAPI
from conf import Settings, Micro

doc = '''
    异常客户激活申请处理 -> 流程完成 -> 触发
    
    客户档案客户合作状态被修改

'''


def register(router: APIRouter):
    @router.post('/customer-error-activation', tags=['异常客户激活申请处理'], description=doc)
    async def customer_error_activation(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
        # 业务管理 ID 和 客户档案 ID
        jd = AsyJDAPI(
            app_id=Settings.JD_APP_ID_BUSINESS,
            entry_id='5dd102e307747e0006801bee',
            api_key=Settings.JD_API_KEY,
            mcc=Micro.mcc
        )

        value = await jd.get_form_data(data_filter={
            "cond": [
                {
                    "field": 'customer_code',
                    "type": 'text',
                    "method": "eq",
                    "value": whi.data['customer_code']  # 客户代码
                }
            ]
        })

        if value:
            for val in value:
                # 更新
                await jd.update_data(val['_id'], data={'khhzzt': {"value": "合作"}})
        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 更新完成')
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
