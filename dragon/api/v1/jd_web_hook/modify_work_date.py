import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from api.v1.jd_web_hook.models import WebHookItem
from conf import Settings, Micro
from dragon_micro_client import AsyJDAPI, JDSerialize

doc = '''

    触发表单 修改正式上班日期申请
    修改 条件流程完成
    人员档案
        - 无忧在职历史记录
        - 无忧在职历史记录.入职时间
        - 无忧在职历史记录.离职时间
        - 椰泰在职历史记录
        - 椰泰在职历史记录.入职时间
        - 椰泰在职历史记录.离职时间
        注 修改最后一条日期
    考勤记录（终端）
        更新
            - 工号
            - 工号(会计)
'''


def register(router: APIRouter):
    @router.post('/modify-work-date', tags=['修改正式上班日期申请'], description=doc)
    async def modify_work_date(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
        # 人事管理
        jd = AsyJDAPI.auto_init(
            app_id_list=[
                Settings.JD_APP_ID_MINISTRY_OF_PERSONNEL,
                Settings.JD_APP_ID_BUSINESS
            ],
            entry_id_list=[
                '5df7a704c75c0e00061de8f6',
                '5df89b4289cd790006316ea3'
            ],
            api_key=Settings.JD_API_KEY,
            mcc=Micro.mcc
        )

        if whi.data['change_type']:
            if whi.data['change_type'] == '修改离职时间':
                # 人员档案
                jd_personnel_files_form = jd[0]
                res = await jd_personnel_files_form.get_form_data(
                    data_filter={
                        "cond": [
                            {
                                "field": 'no',
                                "type": 'text',
                                "method": "eq",
                                "value": whi.data['no']  # 工号
                            }
                        ]
                    })

                if res:
                    # 是否为无忧类型
                    if whi.data['is_free'] == '':
                        return
                    elif whi.data['is_free'] == '否':
                        # 椰泰类型
                        if not res[0]['yetai_quit_sub_table']:
                            return
                        yetai_quit_sub_table = res[0]['yetai_quit_sub_table']
                        yetai_quit_sub_json = yetai_quit_sub_table[-1]
                        # 离职时间
                        yetai_quit_sub_json['yetai_quit_time'] = whi.data['quit_time']
                        yetai_quit_sub_table[-1] = yetai_quit_sub_json
                        data = {
                            'yetai_quit_sub_table':
                                JDSerialize.subform(subform_field='yetai_quit_sub_table', data=yetai_quit_sub_table)[
                                    'yetai_quit_sub_table']
                        }
                    else:
                        # 无忧类型
                        if not res[0]['free_quit_sub_table']:
                            return
                        free_quit_sub_table = res[0]['free_quit_sub_table']
                        free_quit_sub_json = free_quit_sub_table[-1]
                        # 离职时间
                        free_quit_sub_json['free_quit_time'] = whi.data['quit_time']
                        free_quit_sub_table[-1] = free_quit_sub_json
                        data = {
                            'free_quit_sub_table':
                                JDSerialize.subform(subform_field='free_quit_sub_table', data=free_quit_sub_table)[
                                    'free_quit_sub_table']
                        }
                    await jd_personnel_files_form.update_data(dataId=res[0]['_id'], data=data)
                # 考勤记录表
                jd_attendance_record_form = jd[1]
                start_time = whi.data['entry_date']
                end_time = whi.data['quit_time']

                res2 = await jd_attendance_record_form.get_all_data(
                    data_filter={
                        "cond": [
                            {
                                "field": 'managername',
                                "type": 'text',
                                "method": "eq",
                                "value": whi.data['managername']  # 工号
                            },
                            {
                                "field": 'commuterdate',
                                "method": "range",
                                'type': 'datetime',
                                "value": [start_time, end_time]
                            },
                        ]
                    })
                for value in res2:
                    print(value['_id'])
                    await jd_attendance_record_form.update_data(
                        dataId=value['_id'],
                        data={
                            'worknumber': {"value": whi.data['no']},
                            'worknumberkj': {"value": whi.data['no']},
                        }
                    )

        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 更新完成')
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
