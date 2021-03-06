import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from conf import Settings
from func.jd_web_hook.models import WebHookItem
from robak import Jdy

doc = '''

   省外直营业代工资
   
   条件
   
   是否已提供银行账号 == 否/修改

'''


def register(router: APIRouter):
    @router.post('/outside-b-r-wages', tags=['省外直营业代工资'], description=doc)
    async def outside_b_r_wages(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != Jdy.get_signature(
                secret=Settings.JD_SECRET,
                nonce=req.query_params['nonce'],
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
        if whi.data['view'] == '否/修改':
            # 异步模式-使用简道云接口 表单
            asy_jd = Jdy(
                app_id=Settings.JD_APP_ID_MINISTRY_OF_PERSONNEL,
                entry_id='608bf52d1ed68a0007501a54',
                api_key=Settings.JD_API_KEY,
            )
            # 人事管理 -> 修改人员档案银行卡信息申请
            _, err = await asy_jd.query_update_data_one(
                data_filter={
                    "cond": [
                        {
                            "field": 'gz_no',
                            "type": 'text',
                            "method": "eq",
                            "value": whi.data['gz_no']  # 工资单编号
                        }
                    ]
                },
                data={
                    'write_person': {"value": whi.data['person']['username']},
                    'submit_time': {"value": whi.data['updateTime']},
                    'person_no': {"value": whi.data['person_no']},
                    'person_name': {"value": whi.data['person_name']},
                    'person': {"value": whi.data['person']['username']},
                    'turn_no_worries': {"value": whi.data['turn_no_worries']},
                    'bank_card_number': {"value": whi.data['bank_card_number']},
                    'subbranch_number': {"value": whi.data['subbranch_number']},
                    'open_an_account_name': {"value": whi.data['open_an_account_name']},
                    'bank_card_number_new': {"value": whi.data['bank_card_number_new']},
                    'subbranch_number_new': {"value": whi.data['subbranch_number_new']},
                    'open_an_account_name_new': {"value": whi.data['open_an_account_name_new']},
                    'source_form': {"value": whi.data['formName']},
                    'gz_no': {"value": whi.data['gz_no']},
                },
                is_start_workflow=True,
                non_existent_create=True

            )
            await errFn(err)

        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 更新完成')
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
