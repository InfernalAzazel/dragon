import time
from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from api.v1.jd_web_hook.models import WebHookItem
from utils import Mgo
from utils.dragon_logger import DragonLogger
from conf import Settings, Micro
from dragon_micro_client import AsyJDAPI

doc = '''
    入职申请表-人员维护

'''

project_name = '入职申请表-人员维护'
program_type = 'web-hook'
business_name = 'personnel-maintain'

db_name = 'blue-jd'  # 简道云数据库
coll_name = 'query-cache'  # 查询缓存


def register(router: APIRouter):
    @router.post('/personnel-maintain', tags=['入职申请表-人员维护'], description=doc)
    async def personnel_maintain(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != AsyJDAPI.get_signature(
                secret=Settings.JD_SECRET,
                nonce=req.query_params['nonce'],
                timestamp=req.query_params['timestamp'],
                payload=bytes(await req.body()).decode('utf-8')):
            return 'fail', 401

        # 添加任务
        background_tasks.add_task(business, whi)

        return '2xx'


# 处理业务
async def business(whi):
    # 启动时间
    start = time.perf_counter()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':

        count = await Mgo(db_name=db_name, coll_name=coll_name).count({'data_id': whi.data['_id']})

        if count > 0:
            await DragonLogger.warn(
                project_name=project_name, program_type=program_type, business_name=business_name,
                error_msg=f'{whi.data["name"]} 反复触发已忽略下面代码运行'
            )
            return

        await Mgo(db_name=db_name, coll_name=coll_name).insert_one({'data_id': whi.data['_id']})

        # 人员维护表单
        personnel_maintain_form = AsyJDAPI(
            app_id=Settings.JD_APP_ID_MINISTRY_OF_PERSONNEL,
            entry_id='5df87216281aa4000604af2e',
            api_key=Settings.JD_API_KEY,
            mcc=Micro.mcc
        )

        # 入职申请表单
        entry_apply_form = AsyJDAPI(
            app_id=Settings.JD_APP_ID_MINISTRY_OF_PERSONNEL,
            entry_id='5df73f5ca667c000067cd60c',
            api_key=Settings.JD_API_KEY,
            mcc=Micro.mcc
        )

        # 创建数据
        await personnel_maintain_form.create_data(data={
            'name': {
                'value': whi.data['name']
            },
            'name_member': {
                'value': whi.data['no']
            },
        })
        # 查询人员维护表
        res = await personnel_maintain_form.get_form_data(
            limit=100,
            data_filter={
                "rel": "and",
                "cond": [
                    {
                        "field": 'name',
                        "type": 'text',
                        "method": "not_empty",
                    },
                    {
                        "field": 'name_member',
                        "type": 'number',
                        "method": "empty",  # 成员
                    },
                ]
            }
        )
        if res:
            for value in res:
                # # 查询入职申请表
                res2 = await entry_apply_form.get_form_data(
                    data_filter={
                        "cond": [
                            {
                                "field": 'name',
                                "type": 'text',
                                "method": "eq",
                                "value": value['name']  # 姓名
                            },
                        ]
                    }
                )
                if res2:
                    # 更新人员维护表
                    await personnel_maintain_form.update_data(
                        dataId=value['_id'],
                        data={
                            'name_member': {
                                'value': res2[0]['no']
                            },
                        })

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 入职申请表-人员维护 处理耗时 {elapsed}s')
