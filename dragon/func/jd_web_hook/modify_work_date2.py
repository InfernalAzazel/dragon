import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from func.jd_web_hook.models import WebHookItem
from conf import Settings
from robak import Jdy

doc = '''
   修改正式上班日期申请 -> 流程完成 -> 触发

    查询:
    
        终端工号 = 通过终端工号
    
    目前表单: 
        
        10月1-10号拜访订单审核（终端）
        10月11-20号拜访订单审核（终端）
        10月21-31号拜访订单审核（终端）

'''


def register(router: APIRouter):
    @router.post('/modify_work_date2', tags=['修改正式上班日期申请-修改日期'], description=doc)
    async def modify_work_date2(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
        jdy_list = Jdy.auto_init(
            app_id_list=[
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
            ],
            entry_id_list=[
                '61558698c27b610008e714fa',
                '615586a10ca0490008d39273',
                '615586a9ce27bf00075707d7'
            ],
            api_key=Settings.JD_API_KEY,
        )
        jdy1 = jdy_list[0]
        jdy2 = jdy_list[1]
        jdy3 = jdy_list[2]

        if whi.data['change_type'] == '修改正式上班时间':
            data_filter = {
                "rel": "and",
                "cond": [
                    {
                        "field": 'account',
                        "method": "eq",
                        "value": whi.data['no_zd']  # 终端工号
                    },
                    {
                        "field": 'visitdate',  # 拜访时间
                        "method": "range",
                        "value": ['', whi.data['modify_rz_time']]  # 小于入职时间
                    }
                ]
            }

            result1, err = await jdy1.get_form_data(
                limit=100,
                data_filter=data_filter
            )

            await errFn(err)
            for value1 in result1:
                print(value1)
                _, err = await jdy1.update_data(
                    dataId=value1['_id'],
                    data={
                        'is_learning_period': {'value': '是'}
                    }
                )
                await errFn(err)

            result2, err = await jdy2.get_form_data(
                limit=100,
                data_filter=data_filter
            )
            await errFn(err)

            for value2 in result2:
                _, err = await jdy2.update_data(
                    dataId=value2['_id'],
                    data={
                        'is_learning_period': {'value': '是'}
                    }
                )
                await errFn(err)

            result3, err = await jdy3.get_form_data(
                limit=100,
                data_filter=data_filter
            )
            await errFn(err)
            for value3 in result3:
                _, err = await jdy3.update_data(
                    dataId=value3['_id'],
                    data={
                        'is_learning_period': {'value': '是'}
                    }
                )
                await errFn(err)

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
