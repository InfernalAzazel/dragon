import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from func.jd_web_hook.models import WebHookItem
from conf import Settings
from robak import Jdy

doc = '''
    新增或修改物流备忘录 流程完成 -> 触发
    
    没有特殊条件

'''


def register(router: APIRouter):
    @router.post('/add-or-modify-logistics-note', tags=['新增或修改物流备忘录'], description=doc)
    async def add_or_modify_logistics_note(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != Jdy.get_signature(
                nonce=req.query_params['nonce'],
                secret=Settings.JD_SECRET,
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
                data=whi.dict(),
                is_start_workflow=True
            )
            return
    # 启动时间
    start = Settings.log.start_time()
    # 流程完成
    if whi.data['flowState'] == 1 and whi.op == 'data_update':

        # 流备忘录
        logistics_note_form = Jdy(
            app_id=Settings.JD_APP_ID_BUSINESS,
            entry_id='5f969ac016a8df0006f8b1e2',
            api_key=Settings.JD_API_KEY,
        )

        res, err = await logistics_note_form.get_form_data(
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
        await errFn(err)
        if res:
            await logistics_note_form.update_data(dataId=res[0]['_id'], data={
                # 注意事项
                'note': {'value': whi.data['note']},
            })
        else:
            _, err = await logistics_note_form.create_data(data={
                # 填单日期
                'time_date': {'value': whi.data['time_date']},
                # 客户代码
                'customer_code': {'value': whi.data['customer_code']},
                # 注意事项
                'note': {'value': whi.data['note']},
            })
            await errFn(err)
        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
