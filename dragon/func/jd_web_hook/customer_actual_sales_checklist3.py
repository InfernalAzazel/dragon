import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from func.jd_web_hook.models import WebHookItem
from conf import Settings
from robak import Jdy, JdySerialize

doc = '''
    客户自销量奖励核算申请 -> 流程完成 -> 触发

    目标表单：
        
        客户实销量核对过渡表
    
    新增或修改: 
        
        (新增 触发流程 修改不触发)

'''


def register(router: APIRouter):
    @router.post('/customer_actual_sales_checklist3', tags=['客户实销量核对单-客户实销量核对过渡表'], description=doc)
    async def customer_actual_sales_checklist3(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != Jdy.get_signature(
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
    async def errFn(e):
        if e is not None:
            print(e)
            return

    # 启动时间
    start = time.perf_counter()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':

        jdy = Jdy(
            app_id=Settings.JD_APP_ID_BUSINESS,
            entry_id='616133814c7bca0007b23eb6',
            api_key=Settings.JD_API_KEY
        )

        gz_date = whi.data['gz_date']
        gz_nianyue = whi.data['gz_nianyue']
        sx_years_code = whi.data['sx_years_code']
        customer_code = whi.data['customer_code']
        customer_name = whi.data['customer_name']
        total_sales = whi.data['total_sales']
        b_subform = whi.data['business']

        # 生成主表 客户实销量核对过渡表
        for v in b_subform:
            data = {
                'b_wyz': {'value': v['b_wyz']},
                'gz_date': {'value': gz_date},
                'gz_nianyue': {'value': gz_nianyue},
                'sx_years_code': {'value': sx_years_code},
                'customer_code': {'value': customer_code},
                'customer_name': {'value': customer_name},
                'subtotal': {'value': v['b_15']},
                'total_sales': {'value': total_sales},
                'b_person': {'value': JdySerialize.member_err_to_none(v, 'b_person')},
                'b_person_name': {'value': v['b_person_name']},
                'b_person_no': {'value': v['b_person_no']},
                'b_nianyuegh': {'value': v['b_nianyuegh']},
                'b_gzjb': {'value': v['b_gzjb']},
                'b_1': {'value': v['b_1']},
                'b_2': {'value': v['b_2']},
                'b_3': {'value': v['b_3']},
                'b_4': {'value': v['b_4']},
                'b_5': {'value': v['b_5']},
                'b_6': {'value': v['b_6']},
                'b_7': {'value': v['b_7']},
                'b_8': {'value': v['b_8']},
                'b_9': {'value': v['b_9']},
                'b_10': {'value': v['b_10']},
                'b_11': {'value': v['b_11']},
                'b_12': {'value': v['b_12']},
                'b_13': {'value': v['b_13']},
                'b_14': {'value': v['b_14']},
            }

            res, err = await jdy.query_update_data_one(
                data_filter={
                    "cond": [
                        {
                            "field": 'b_wyz',
                            "type": 'text',
                            "method": "eq",
                            "value": v['b_wyz']  # 唯一值
                        },
                    ],
                },
                data=data,
                non_existent_create=True,
            )
            await errFn(err)

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
