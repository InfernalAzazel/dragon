from datetime import datetime
import time

from robak import Jdy
from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from func.jd_web_hook.models import WebHookItem
from conf import Settings

doc = '''
    营业所借支费用申请
    
    流程完成 
    
    修改自身: 
        
        费用归属月份 -> 更新时间
        
        费用归属年月 -> 更新时间

'''


def register(router: APIRouter):
    @router.post('/b_o_borrowing_expenses_apply', tags=['营业所借支费用申请-修改自身'], description=doc)
    async def b_o_borrowing_expenses_apply(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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

    borrow_time = datetime.strptime(whi.data['updateTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
    borrow_years = f'{borrow_time.year}{borrow_time.month}'
    borrow_month = borrow_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # print(borrow_years)
    # print(borrow_month)

    jdy = Jdy(
        app_id=Settings.JD_APP_ID_BUSINESS,
        entry_id="606c33e06c6c3200073e451a",
        api_key=Settings.JD_API_KEY,
    )

    _, err = await jdy.update_data(
        dataId=whi.data['_id'],
        data={
            'borrow_years': {'value': borrow_years},
            'borrow_month': {'value': borrow_month},
        },
    )
    await errFn(err)

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 营业所借支费用申请-修改自身 处理耗时 {elapsed}s')
