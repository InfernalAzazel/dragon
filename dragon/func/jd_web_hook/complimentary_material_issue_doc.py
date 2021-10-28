import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger
from func.jd_web_hook.models import WebHookItem
from conf import Settings
from robak import Jdy, JdySerialize

doc = '''

    搭赠物料出库单 -> 提交 -> 触发

    创建数据
    
    物料出库单_总表

'''


def register(router: APIRouter):
    @router.post('/complimentary-material-issue-doc', tags=['搭赠物料出库单-创建数据到->物料出库单_总表'], description=doc)
    async def complimentary_material_issue_doc(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
                data=whi.dict()
            )
            return

    # 启动时间
    start = time.perf_counter()

    if whi.op == 'data_create':

        # 营销_产品出库总表
        jd = Jdy(
            app_id=Settings.JD_APP_ID_WAREHOUSE_M_SYSTEM,
            entry_id='5eeb0c30494c830006f80d46',
            api_key=Settings.JD_API_KEY,
        )
        if whi.data['total_issue_quantity'] != 0:
            _, err = await jd.query_update_data_one(
                data_filter={
                    "rel": "and",  # 或者"or"
                    "cond": [
                        {
                            "field": 'only_code',
                            "type": 'text',
                            "method": "eq",
                            "value": whi.data['only_code']  # 唯一值
                        },
                    ],
                },
                data={
                    'document_type': {'value': whi.data["document_type"]},  # 单据类型
                    'a_sales_order_no': {'value': whi.data["a_sales_order_no"]},  # 关联销售单编号
                    'only_code': {'value': whi.data["document_type"] + whi.data["a_sales_order_no"]},  # 唯一编号
                    'delivery_date': {'value': whi.data['delivery_date']},  # 出库日期
                    'customer_name': {'value': whi.data['customer_name']},  # 客户名称
                    'customer_code': {'value': whi.data['customer_code']},  # 客户代码
                    'total_issue_quantity': {'value': whi.data['total_issue_quantity']},  # 出库数量合计
                    'warehouse': {'value': whi.data['warehouse']},  # 仓库
                    'delivery_details':
                        JdySerialize.subform(subform_field="delivery_details", data=whi.data['delivery_details'])[
                            "delivery_details"],
                    # 出库明细 子表单
                    'remarks': {'value': whi.data['remarks']},  # 备注

                },
                non_existent_create=True
            )
            await errFn(err)

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
