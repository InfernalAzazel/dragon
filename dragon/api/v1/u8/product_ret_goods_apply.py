from fastapi import APIRouter, Request, BackgroundTasks
from api.v1.jd_web_hook.models import WebHookItem
from utils.jd_api import JdAPI

doc = '''

   产品退货申请单
   
   u8 数据同步

'''


def register(router: APIRouter):
    @router.post('/product-ret-goods-apply', tags=['产品退货申请单-u8'], description=doc)
    async def product_ret_goods_apply(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
async def business(whi: WebHookItem):
    pass
    print(whi.data)
    # # 启动时间
    # start = time.perf_counter()
    #
    # if whi.data['flowState'] == 1 and whi.op == 'data_update':
    #     if whi.data['surplus_count'] == 0 or whi.data['actual_count'] == 0:
    #
    #
    #     # 结束时间
    #     elapsed = (time.perf_counter() - start)
    #     logger.info(f'[+] 更新完成')
    #     logger.info(f'[+] 程序处理耗时 {elapsed}s')
