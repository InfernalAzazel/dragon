import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from api.v1.jd_web_hook.models import WebHookItem
from utils import JdAPI, JdType

doc = '''
    无忧合批量修改表

'''

# 人员档案
personnel_files_form = JdAPI(JdAPI.APP_ID_MINISTRY_OF_PERSONNEL, '5df7a704c75c0e00061de8f6')


def register(router: APIRouter):
    @router.post('/free-contract-batch-modify', tags=['无忧合批量修改表'], description=doc)
    async def free_contract_batch_modify(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != JdAPI.get_signature(
                nonce=req.query_params['nonce'],
                timestamp=req.query_params['timestamp'],
                payload=bytes(await req.body()).decode('utf-8')):
            return 'fail',

        # 添加任务
        background_tasks.add_task(business, whi)

        return '2xx'


# 处理业务
async def business(whi):
    # 启动时间
    start = time.perf_counter()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':

        res = await personnel_files_form.get_form_data(
            data_filter={
                "cond": [
                    {
                        "field": 'no',
                        "type": 'text',
                        "method": "eq",
                        "value": whi.data['no']
                    }
                ]

            }
        )

        if res:
            subform = JdType.subform(subform_field='signing_status', data=whi.data['signing_status'])
            data = {
                # 合同编号
                'contract_number': {
                    'value': whi.data['contract_number']
                },
                # 无忧合同类型
                'free_contract_type': {
                    'value': whi.data['free_contract_type']
                },
                # 无忧合同到期日
                'free_contract_expire': {
                    'value': whi.data['free_contract_expire']
                },
                # 无忧人员资料是否齐全
                'free_personnel_is_it_complete': {
                    'value': whi.data['free_personnel_is_it_complete']
                },
                # 无忧纸质资料回收情况
                'free_data_recycling': {
                    'value': whi.data['free_data_recycling']
                },
                # 无忧合同签订情况
                'signing_status': {
                    'value': subform['signing_status']['value']
                },
            }
            await personnel_files_form.update_data(
                dataId=res[0]['_id'],
                data=data
            )

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
