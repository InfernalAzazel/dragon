import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from api.v1.jd_web_hook.models import WebHookItem
from conf import Settings, Micro
from dragon_micro_client import AsyJDAPI, JDSerialize

doc = '''
    专项申请 -> 流程完成 -> 触发
    修改以下
    
    目标表单：活动申请  字段：产品系列 对应活动项目 考核渠道

'''


def register(router: APIRouter):
    @router.post('/special-application', tags=['专项申请-情况无关项'], description=doc)
    async def special_application(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
async def business(whi):
    # 启动时间
    start = time.perf_counter()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':
        # 活动申请表单
        jd_special_application_from = AsyJDAPI(
            app_id=Settings.JD_APP_ID_BUSINESS,
            entry_id='6122f601434d980008a21e9e',
            api_key=Settings.JD_API_KEY,
            mcc=Micro.mcc
        )
        subform = whi.data['jixiao_zb2']
        for i in range(len(subform)):
            # 考核项目
            if subform[i]['khxm2'] == '专项活动执行家数':
                subform[i]['qudao'] = ''  # 清空 考核渠道 3
            elif subform[i]['khxm2'] == '专项产品维护家数':
                subform[i]['c_activities'] = ''  # 清空 对应活动项目 2
                subform[i]['qudao'] = ''  # 清空 考核渠道 3
            elif subform[i]['khxm2'] == '专项渠道维护家数':
                subform[i]['khbz2'] = ''  # 清空 产品系列 1
                subform[i]['c_activities'] = ''  # 清空 对应活动项目 2
            elif subform[i]['khxm2'] == '指定特渠开发奖励':
                subform[i]['khbz2'] = ''  # 清空 产品系列 1
                subform[i]['c_activities'] = ''  # 清空 对应活动项目 2

        await jd_special_application_from.update_data(
            dataId=whi.data['_id'],
            data=JDSerialize.subform(subform_field='jixiao_zb2', data=subform))

        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
