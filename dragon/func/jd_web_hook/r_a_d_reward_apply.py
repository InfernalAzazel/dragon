import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from func.jd_web_hook.models import WebHookItem
from conf import Settings
from robak import Jdy

doc = '''
    
    补指定开发奖励申请 -> 流程完成 -> 触发
    
    创建数据

'''


def register(router: APIRouter):
    @router.post('/r_a_d_reward_apply', tags=['补指定开发奖励申请-创建数据到指定开发奖励申请'], description=doc)
    async def r_a_d_reward_apply(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
                data=whi.dict(),
                is_start_workflow=True
            )
            return

    # 启动时间
    start = Settings.log.start_time()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':

        # 指定开发奖励申请过渡表
        jd = Jdy(
            app_id=Settings.JD_APP_ID_BUSINESS,
            entry_id='61052e6eb23ee70007657cc5',
            api_key=Settings.JD_API_KEY,
        )
        _, err = await jd.create_data(data={
            'serial_number': {'value': whi.data['serial_number']},  # 流水号
            'managername': {'value': whi.data['managername']},  # 建档人
            'workuser': {'value': whi.data['workuser']['username']},  # 建档人员
            'id': {'value': whi.data['id']},  # 工号
            'account': {'value': whi.data['account']},  # 终端工号
            'createddate': {'value': whi.data['createddate']},  # 建档日期
            'opendate': {'value': whi.data['opendate']},  # 合作日期
            'code': {'value': whi.data['code']},  # 门店编码
            'name': {'value': whi.data['name']},  # 门店名称
            'typename': {'value': whi.data['typename']},  # 门店类型
            'position': {'value': whi.data['position']},  # 职位
            'dealername': {'value': whi.data['dealername']},  # 经销商
            'dealercode': {'value': whi.data['dealercode']},  # 经销商代码
            'contactertel': {'value': whi.data['contactertel']},  # 联系电话
            'address': {'value': whi.data['address']},  # 终端建档位置
            'daqubumen': {'value': whi.data['daqubumen']['dept_no']},  # 归属主管
        },
            is_start_workflow=True
        )
        await errFn(err)
    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
