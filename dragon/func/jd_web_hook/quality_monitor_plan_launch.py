from datetime import datetime
import time

from robak import Jdy, JdySerialize
from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from conf import Settings
from func.jd_web_hook.models import WebHookItem

doc = '''

   质量监控计划基础信息 (非流程表单)

   流程进行中:

   按照 线别+项目 查询 质量监控计划检查 

   修改

   上次操作时间 + 周期 -> 上次操作日期
   当前操作日期 + 周期 -> 准备操作日期
   下次操作时间 + 周期 -> 下次操作日期

'''


def register(router: APIRouter):
    @router.post('/quality-monitor-plan-launch', tags=['质量监控计划基础信息'], description=doc)
    async def quality_monitor_plan_launch(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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

    if whi.op == 'data_create' or whi.op == 'data_update':

        try:
            cycle = whi.data['cycle'] * 86400
        except:
            cycle = 0
        try:
            e_w_lead_time = whi.data['e_w_lead_time'] * 86400
        except:
            e_w_lead_time = 0

        jdy = Jdy(
            app_id=Settings.JD_APP_ID_QUALITY,
            entry_id='60f373bc498d2c000890f574',  # 质量监控计划检查
            api_key=Settings.JD_API_KEY,
        )

        res, err = await jdy.get_form_data(
            data_filter={
                "rel": "and",  # 或者"or"
                "cond": [
                    {
                        "field": 'linear_project',
                        "type": 'text',
                        "method": "eq",
                        "value": whi.data['linear_project']
                    },
                    {
                        "field": 'flowState',
                        "method": "eq",
                        "value": [0]
                    }
                ]
            }
        )

        await errFn(err)

        for value in res:
            # print(value)
            try:
                last_data_temp = time.strptime(value['last_data'], '%Y-%m-%dT%H:%M:%S.%fZ')

                current_date = datetime.strptime(
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.mktime(last_data_temp) + cycle)),
                    '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                current_date_temp = time.strptime(current_date, '%Y-%m-%dT%H:%M:%S.%fZ')

                next_date = datetime.strptime(
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.mktime(current_date_temp) + cycle)),
                    '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                next_date_temp = time.strptime(next_date, '%Y-%m-%dT%H:%M:%S.%fZ')

                lowest_data = datetime.strptime(
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.mktime(next_date_temp) + cycle)),
                    '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                next_e_w_date = datetime.strptime(
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.mktime(next_date_temp) - e_w_lead_time)),
                    '%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                _, err = await jdy.update_data(
                    dataId=value['_id'],
                    data={
                        'cycle': {'value': whi.data['cycle']},
                        'e_w_lead_time': {'value': whi.data['e_w_lead_time']},
                        'dispatch': {'value': JdySerialize.member_array_err_to_none(whi.data, 'dispatch')},
                        'supervisor': {'value': JdySerialize.member_array_err_to_none(whi.data, 'supervisor')},
                        'o_is_qualified': {'value': ''},
                        'current_date': {'value': current_date},
                        'next_date': {'value': next_date},
                        'lowest_data': {'value': lowest_data},
                        'next_e_w_date': {'value': next_e_w_date},
                    }
                )
                await errFn(err)
            except Exception as e:
                await errFn(e)

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 更新完成')
    logger.info(f'[+] 程序处理耗时 {elapsed}s')
