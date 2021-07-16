import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from api.v1.jd_web_hook.models import WebHookItem
from utils.jd_api import JdAPI

doc = '''
    活动延期申请 -> 流程完成 -> 触发

    触发表单：活动延期申请  字段：活动延期日期、申请日期
    修改以下
    目标表单：活动申请  字段：活动截止日期、申请日期

'''
# 活动申请表单
activity_apply_form = JdAPI(JdAPI.APP_ID_BUSINESS, '5ddc897f830d6a000683341a')


def register(router: APIRouter):
    @router.post('/activity-delay-apply', tags=['活动延期申请-修改日期'], description=doc)
    async def activity_delay_apply(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
        pass

        res = await activity_apply_form.get_form_data(
            data_filter={
                "cond": [
                    {
                        "field": 'activitycode',
                        "type": 'text',
                        "method": "eq",
                        "value": whi.data['activitycode']  # 申请批号
                    }
                ]
            })

        if res:
            await activity_apply_form.update_data(dataId=res[0]['_id'], data={
                # 活动截止日期
                'enddate': {
                    'value': whi.data['activity_delay_date']
                },
                # 申请日期
                'id': {
                    'value': whi.data['id']
                },
            })
        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
