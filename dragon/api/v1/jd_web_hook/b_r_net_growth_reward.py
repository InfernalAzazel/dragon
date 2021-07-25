import time
from dragon_micro_client import MicroClientConfig, AsyJDAPI
from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

import settings
from api.v1.jd_web_hook.models import WebHookItem

doc = '''

   业代净增加人员奖励

'''


def register(router: APIRouter):
    @router.post('/b-r-net-growth-reward', tags=['业代净增加人员奖励'], description=doc)
    async def b_r_net_growth_reward(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != AsyJDAPI.get_signature(
                secret=settings.Default.JD_SECRET,
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

        # 配置腾龙微服务
        mcc = MicroClientConfig(
            mcc_url=settings.Default.MCC_BASIC_URL,
            token=settings.Default.MCC_BASIC_TOKEN
        )
        # 异步模式-使用简道云接口 单表单
        asy_jd = AsyJDAPI(
            app_id=settings.Default.JD_APP_ID_BUSINESS,
            entry_id='5e3a7d0ac3668d00063776fe',
            api_key=settings.Default.JD_API_KEY,
            mcc=mcc
        )
        data_filter = {
            "cond": [
                {
                    "field": 'source_no',
                    "type": 'text',
                    "method": "eq",
                    "value": whi.data['source_no']  # 流水号
                }
            ]
        }
        if whi.data['reward_type'] == '拨款营业所工资':
            data = {
                'person': {"value": whi.data['person']['username']},  # 提交人
                'write_date': {"value": whi.data['updateTime']},  # 更新时间
                'out_type': {"value": '从总经办预提调出'},
                'marketing_dept': {"value": whi.data['marketing_dept']['dept_no']},  # 归属营销总监
                'marketing_dept_t': {"value": '营销总监'},  # 归属营销总监（名称）
                'marketing_dept_u8': {"value": '109'},
                'money_7': {"value": whi.data['money_7']},
                'in_type': {"value": '调入营业所工资'},
                'business_office_dept': {"value": whi.data['business_office_dept']['dept_no']},
                'to_b_o_u8_dept': {"value": whi.data['to_b_o_u8_dept']},
                'fuzong_bumen': {"value": whi.data['fuzong_bumen']['dept_no']},
                'fuzongjian_bumen': {"value": whi.data['fuzongjian_bumen']['dept_no']},
                'transfer_in_salary': {"value": whi.data['money_7']},
                'reason': {"value": '业代净增加人员奖励' + whi.data['source_no']},
                'all_money_4': {"value": whi.data['money_7']},
                'all_money_3': {"value": whi.data['money_7']},
                'source_form': {"value": whi.data['formName']},
                'source_no': {"value": whi.data['source_no']},
            }
        else:
            data = {
                'person': {"value": whi.data['person']['username']},  # 提交人
                'write_date': {"value": whi.data['updateTime']},  # 更新时间
                'out_type': {"value": '从总经办预提调出'},
                'marketing_dept': {"value": whi.data['marketing_dept']['dept_no']},  # 归属营销总监
                'marketing_dept_t': {"value": '营销总监'},  # 归属营销总监（名称）
                'money_7': {"value": whi.data['personal_money']},
                'marketing_dept_u8': {"value": '109'},
                'in_type': {"value": '调入个人'},
                'reason': {"value": '业代净增加人员奖励' + whi.data['source_no']},
                'all_money_4': {"value": whi.data['personal_money']},
                'all_money_3': {"value": whi.data['personal_money']},
                'source_form': {"value": whi.data['formName']},
                'source_no': {"value": whi.data['source_no']},

            }

        # 业务管理 -> 费用调拨申请单 如果存在则删除
        await asy_jd.query_delete_one(data_filter=data_filter)
        # 业务管理 -> 费用调拨申请单 如果存在则跟更新，不存在则创建
        await asy_jd.query_update_data_one(
            data_filter=data_filter,
            data=data,
            is_start_workflow=True,
            non_existent_create=True
        )

        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 更新完成')
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
