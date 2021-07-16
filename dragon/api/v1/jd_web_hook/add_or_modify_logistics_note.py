import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from api.v1.jd_web_hook.models import WebHookItem
from utils.jd_api import JdAPI

doc = '''
    新增或修改物流备忘录

'''
# 流备忘录
logistics_note_form = JdAPI(JdAPI.APP_ID_BUSINESS, '5f969ac016a8df0006f8b1e2')


def register(router: APIRouter):
    @router.post('/add-or-modify-logistics-note', tags=['新增或修改物流备忘录'], description=doc)
    async def add_or_modify_logistics_note(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
    # 流程完成
    if whi.data['flowState'] == 1 and whi.op == 'data_update':
        pass

        res = await logistics_note_form.get_form_data(
            data_filter={
                "cond": [
                    {
                        "field": 'customer_code',
                        "type": 'combo',  # 下拉框
                        "method": "eq",
                        "value": whi.data['customer_code']  # 客户代码
                    }
                ]
            })

        if res:
            await logistics_note_form.update_data(dataId=res[0]['_id'], data={
                # 注意事项
                'note': {
                    'value': whi.data['note']
                },
            })
        else:
            await logistics_note_form.create_data(data={
                # 填单日期
                'time_date': {
                    'value': whi.data['time_date']
                },
                # 客户代码
                'customer_code': {
                    'value': whi.data['customer_code']
                },
                # 注意事项
                'note': {
                    'value': whi.data['note']
                },
            })
        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
