import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

import models
from api.v1.jd_web_hook.models import WebHookItem
from conf import Settings, Micro
from dragon_micro_client import AsyJDAPI, JDSerialize

doc = '''

    采购退货出库单 -> 提交 -> 触发

    创建数据
    
    物料出库单_总表

'''


def register(router: APIRouter):
    @router.post('/purchase-return-issue-doc', tags=['采购退货出库单-创建数据到->物料出库单_总表'], description=doc)
    async def purchase_return_issue_doc(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
async def business(whi: WebHookItem):
    # 启动时间
    start = time.perf_counter()

    if whi.op == 'data_create':

        # 营销_产品出库总表
        jd = AsyJDAPI(
            app_id=models.JDApp.warehouse_m_system,
            entry_id=models.JDWarehouseMSystem.material_issue_doc_summary_form,
            api_key=Settings.JD_API_KEY,
            mcc=Micro.mcc
        )
        if whi.data['total_issue_quantity'] != 0:
            await jd.query_update_data_one(
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
                    'warehouse': {'value': whi.data['warehouse']},  # 仓库
                    'delivery_details': JDSerialize.subform(subform_field="delivery_details", data=whi.data['delivery_details'])["delivery_details"],  # 出库明细 子表单
                    'remarks': {'value': whi.data['remarks']},  # 备注

                },
                non_existent_create=True
            )

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
