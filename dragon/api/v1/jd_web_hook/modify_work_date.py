import calendar
from datetime import datetime, timedelta
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

                # 当原离职年月工号与修改原离职年月工号不等时说明是超出一个月
                # 超出的需要用离职工号填充如 7.2 ~ 8.2, 8月的字段用修改原离职年月工号填充
                if whi.data['original_resignation_y_n'] != whi.data['modify_resignation_y_n']:
                    # 原离职时间 -> 开始时间
                    start_time_o_r_y_n = whi.data['entry_date']
                    o_r_y_n = datetime.strptime(start_time_o_r_y_n, '%Y-%m-%dT%H:%M:%S.000Z') + timedelta(hours=8)
                    last_day = calendar.monthrange(o_r_y_n.year, o_r_y_n.month)[1]  # 最后一天

                    # 原离职时间 -> 结束时间
                    end_time_o_r_y_n = datetime.strftime(
                        datetime(o_r_y_n.year, o_r_y_n.month, last_day, 0, 0, 0) - timedelta(
                            hours=8),
                        '%Y-%m-%dT%H:%M:%S.000Z')

                    # 修改原离职时间 -> 开始时间
                    end_time_m_r_y_n = whi.data['quit_time']
                    m_r_y_n = datetime.strptime(end_time_m_r_y_n, '%Y-%m-%dT%H:%M:%S.000Z')

                    # 修改原离职时间 -> 结束时间
                    start_time_m_r_y_n = datetime.strftime(
                        datetime(m_r_y_n.year, m_r_y_n.month, 1, 16, 0, 0) - timedelta(
                            hours=24),
                        '%Y-%m-%dT%H:%M:%S.000Z')

                    res_o_r_y_n = await jd_attendance_record_form.get_all_data(
                        data_filter={
                            "cond": [
                                {
                                    "field": 'worknumberzd',  # 终端工号
                                    "type": 'text',
                                    "method": "eq",
                                    "value": whi.data['no_zd']  # 终端工号
                                },
                                {
                                    "field": 'commuterdate',
                                    "method": "range",
                                    'type': 'datetime',
                                    "value": [start_time_o_r_y_n, end_time_o_r_y_n]
                                },
                            ]
                        })

                    for value_res_o_r_y_n in res_o_r_y_n:
                        await jd_attendance_record_form.update_data(
                            dataId=value_res_o_r_y_n['_id'],
                            data={
                                'worknumber': {"value": whi.data['no']},
                                'worknumberkj': {"value": whi.data['no']},
                                'year_wn': {"value": whi.data['original_resignation_y_n']},
                                'year_wnkj': {"value": whi.data['original_resignation_y_n']},

                            }
                        )

                    res_m_r_y_n = await jd_attendance_record_form.get_all_data(
                        data_filter={
                            "cond": [
                                {
                                    "field": 'worknumberzd',  # 终端工号
                                    "type": 'text',
                                    "method": "eq",
                                    "value": whi.data['no_zd']  # 终端工号
                                },
                                {
                                    "field": 'commuterdate',
                                    "method": "range",
                                    'type': 'datetime',
                                    "value": [start_time_m_r_y_n, end_time_m_r_y_n]
                                },
                            ]
                        })
                    for value_res_m_r_y_n in res_m_r_y_n:
                        await jd_attendance_record_form.update_data(
                            dataId=value_res_m_r_y_n['_id'],
                            data={
                                'worknumber': {"value": whi.data['no']},
                                'worknumberkj': {"value": whi.data['no']},
                                'year_wn': {"value": whi.data['modify_resignation_y_n']},
                                'year_wnkj': {"value": whi.data['modify_resignation_y_n']},

                            }
                        )

                else:
                    # 一个月内
                    res2 = await jd_attendance_record_form.get_all_data(
                        data_filter={
                            "cond": [
                                {
                                    "field": 'worknumberzd',  # 终端工号
                                    "type": 'text',
                                    "method": "eq",
                                    "value": whi.data['no_zd']  # 终端工号
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
                        await jd_attendance_record_form.update_data(
                            dataId=value['_id'],
                            data={
                                'worknumber': {"value": whi.data['no']},
                                'worknumberkj': {"value": whi.data['no']},
                                'year_wn': {"value": whi.data['original_resignation_y_n']},
                                'year_wnkj': {"value": whi.data['original_resignation_y_n']},

                            }
                        )

        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 更新完成')
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
