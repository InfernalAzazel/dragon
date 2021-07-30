from dragon_micro_client import AsyJDAPI
from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger
from sqlobject import *

from api.v1.jd_web_hook.models import WebHookItem
from conf import Settings, Micro

doc = '''

   客户产品预提修改申请

'''


class CustomerProduct(SQLObject):
    cid = StringCol()
    cname = StringCol()
    code = StringCol()
    pname = StringCol()
    withholding = StringCol()


def register(router: APIRouter):
    @router.post('/cpw-modify-apply', tags=['客户产品预提修改申请'], description=doc)
    async def cpw_modify_apply(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
async def business(whi: WebHookItem):
    # 启动时间
    start = time.perf_counter()
    sqlhub.processConnection = connectionForURI('sqlite:///:memory:')
    # 配置腾龙微服务

    # 异步模式-使用简道云接口 单表单
    asy_jd = AsyJDAPI(
        app_id=Settings.JD_APP_ID_BUSINESS,
        entry_id='5de228733b001e000659af62',
        api_key=Settings.JD_API_KEY,
        mcc=Micro.mcc
    )

    res = await asy_jd.get_all_data(
        data_filter={
            "rel": "and",  # 或者 "or"
            "cond": [
                {
                    "field": 'k_h_code',
                    "type": 'text',
                    "method": "eq",
                    "value": whi.data['k_h_code']
                },
                {
                    "field": 'pstatus',
                    "type": 'text',
                    "method": "eq",
                    "value": '启用'
                }
            ]
        }
    )
    if res['data']:
        print(len(res['data']))
    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 更新完成')
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
