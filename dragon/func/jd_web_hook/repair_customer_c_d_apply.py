import datetime
import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from func.jd_web_hook.models import WebHookItem
from conf import Settings
from yetai import JDSDK, JDSerialize

doc = '''
    补客户业代提成差额申请 -> 流程完成 -> 触发

    目标表单：
    
        U8应收单过渡表

'''


def register(router: APIRouter):
    @router.post('/repair_customer_c_d_apply', tags=['补客户业代提成差额申请-U8应收单过渡表'], description=doc)
    async def repair_customer_c_d_apply(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != JDSDK.get_signature(
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
        jdy = JDSDK(
            app_id=Settings.JD_APP_ID_BUSINESS,
            entry_id='5facec6b40e1cb00079e03cb',
            api_key=Settings.JD_API_KEY,
        )
        hs_time = datetime.datetime.strptime(whi.data['hs_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        source_no = whi.data['source_no']
        filling_time = whi.data['filling_time']
        customer_name = whi.data['customer_name']
        customer_code = whi.data['customer_code']
        money = whi.data['money']  # 本月补差金额合计
        qujili_u8_code = whi.data['qujili_u8_code']
        zhuguan_no = whi.data['zhuguan_no']
        abstract = f'{whi.data["source_no"]} [{whi.data["is_paymentis_for_goods"]}] 补{hs_time.month}月客户业代提成差额'

        if money is None:
            pass
        else:
            if money > 0:
                res, err = await jdy.get_form_data(
                    data_filter={
                        "cond": [
                            {
                                "field": 'source_no',
                                "type": 'text',
                                "method": "eq",
                                "value": whi.data['source_no']  # 申请批号
                            }
                        ]
                    })
                await errFn(err)
                subform = [
                    {
                        '_id': '60bf5e91ff26fc00077e2f9d',
                        'r_fx': '借',
                        'r_km_code': '236',
                        'r_money': money,
                        'r_bm_code': qujili_u8_code,
                        'r_zhuguan_no': zhuguan_no,
                        'r_abstract': abstract,
                    }
                ]
                if res:
                    _, err = await jdy.update_data(
                        dataId=res[0]['_id'],
                        data={
                            'source_no': {'value': source_no},
                            'is_handle': {'value': '是'},
                            'source_form': {'value': '补客户业代提成差额申请'},
                            'filling_time': {'value': filling_time},
                            'customer_name': {'value': customer_name},
                            'customer_code': {'value': customer_code},
                            'km_code': {'value': '122'},
                            'money': {'value': money},
                            'qujili_u8_code': {'value': qujili_u8_code},
                            'zhuguan_no': {'value': zhuguan_no},
                            'abstract': {'value': abstract},
                            'receivable': JDSerialize.subform('receivable', subform)['receivable'],
                        })
                    await errFn(err)
                else:
                    _, err = await jdy.create_data(
                        data={
                            'source_no': {'value': source_no},
                            'is_handle': {'value': '否'},
                            'source_form': {'value': '补客户业代提成差额申请'},
                            'filling_time': {'value': filling_time},
                            'customer_name': {'value': customer_name},
                            'customer_code': {'value': customer_code},
                            'km_code': {'value': '122'},
                            'money': {'value': money},
                            'qujili_u8_code': {'value': qujili_u8_code},
                            'zhuguan_no': {'value': zhuguan_no},
                            'abstract': {'value': abstract},
                            'receivable': JDSerialize.subform('receivable', subform)['receivable'],
                        },
                        is_start_workflow=True
                    )
                    await errFn(err)
        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
