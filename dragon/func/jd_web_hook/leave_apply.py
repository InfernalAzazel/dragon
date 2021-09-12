import time

from lunar_you_ying import JDSDK, JDSerialize
from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from func.jd_web_hook.models import WebHookItem
from conf import Settings

doc = '''

   客户产品预提修改申请

'''


def register(router: APIRouter):
    @router.post('/leave-apply', tags=['请假申请-创建历史记录'], description=doc)
    async def leave_apply(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != JDSDK.get_signature(
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

    async def errFn(e):
        if e is not None:
            print(e)
    # 启动时间
    start = time.perf_counter()
    # print(whi.data)
    if whi.data['flowState'] == 1 and whi.op == 'data_update':

        # 异步模式-使用简道云接口 单表单
        asy_jd = JDSDK(
            app_id=Settings.JD_APP_ID_MINISTRY_OF_PERSONNEL,
            entry_id='6100b2ab3ed49200083475a9',
            api_key=Settings.JD_API_KEY,
        )
        data = {
            'apply_name': {'value': whi.data['apply_name']},
            'apply_date': {'value': whi.data['apply_date']},
            'cause_statement': {'value': whi.data['cause_statement']},
            'leave_date_subform': JDSerialize.subform(subform_field='leave_date_subform',
                                                      data=whi.data['leave_date_subform'])['leave_date_subform'],
            'total_days': {'value': whi.data['total_days']},
        }
        _, err = await asy_jd.create_data(
            data=data
        )
        await errFn(err)
    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 更新完成')
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
