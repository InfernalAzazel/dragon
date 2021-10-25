import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from func.jd_web_hook.models import WebHookItem
from conf import Settings
from robak import Jdy, JdySerialize

doc = '''
    客户实销量核对单 -> 流程完成 -> 触发

    目标表单：
        
        省外直营业代工资（新版）
        实销量/发货量工资单
        底薪业代工资
        自由业代奖励核对
        新客户实销量奖励核算申请
        客户实销量核对过渡表
    
    新增或修改: 
        
        (新增 触发流程 修改不触发)

'''


def register(router: APIRouter):
    @router.post('/customer_actual_sales_checklist', tags=['客户实销量核对单-多个表单'], description=doc)
    async def customer_actual_sales_checklist(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != Jdy.get_signature(
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
    async def errFn(e):
        if e is not None:
            print(e)
            return

    # 启动时间
    start = time.perf_counter()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':

        jdy_list = Jdy.auto_init(
            app_id_list=[
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
            ],
            entry_id_list=[
                '5f1e3278ad6bed00063798ad',  # 省外直营业代工资（新版）
                '5e620f208b64ef000672d4d6',  # 实销量/发货量工资单
                '5e5dcdca18708d0006e198ef',  # 底薪业代工资
                '615abc52dcb0cc0007ea2d06',  # 自由业代奖励核对
                '60adbb1f46804c000841dad9',  # 新客户实销量奖励核算申请
                '616133814c7bca0007b23eb6',  # 客户实销量核对过渡表
            ],
            api_key=Settings.JD_API_KEY
        )

        gz_date = whi.data['gz_date']
        gz_nianyue = whi.data['gz_nianyue']
        sx_years_code = whi.data['sx_years_code']
        customer_code = whi.data['customer_code']
        customer_name = whi.data['customer_name']
        total_sales = whi.data['total_sales']
        b_subform = whi.data['business']

        s_list = []
        c_list = []

        for v in b_subform:
            if v['b_form'] == '省外直营业代工资（新版）' and v['b_is_bzy'] != '是':
                b = [{
                    '_id': v['_id'],
                    'b_1': v['b_1'],
                    'b_2': v['b_2'],
                    'b_3': v['b_3'],
                    'b_4': v['b_4'],
                    'b_5': v['b_5'],
                    'b_6': v['b_6'],
                    'b_7': v['b_7'],
                    'b_8': v['b_8'],
                    'b_9': v['b_9'],
                    'b_10': v['b_10'],
                    'b_11': v['b_11'],
                    'b_12': v['b_12'],
                    'b_13': v['b_13'],
                    'b_14': v['b_14'],
                }]

                data = {
                    'b_wyz': {'value': v['b_wyz']},
                    'gz_date': {'value': gz_date},
                    'gz_nianyue': {'value': gz_nianyue},
                    'sx_years_code': {'value': sx_years_code},
                    'customer_code': {'value': customer_code},
                    'customer_name': {'value': customer_name},
                    'total': {'value': v['b_15']},
                    'total_sales': {'value': total_sales},
                    'person': {'value': JdySerialize.member_err_to_none(v, 'b_person')},
                    'person_name': {'value': v['b_person_name']},
                    'person_no': {'value': v['b_person_no']},
                    'nianyuegh': {'value': v['b_nianyuegh']},
                    'gzjb': {'value': v['b_gzjb']},
                    'business': JdySerialize.subform('business', b)['business'],
                }

                jdy = jdy_list[0]
                res, err = await jdy.get_form_data(
                    data_filter={
                        "cond": [
                            {
                                "field": 'b_wyz',
                                "type": 'text',
                                "method": "eq",
                                "value": v['b_wyz']  # 唯一值
                            },
                        ],
                    },
                )
                await errFn(err)
                if res:
                    _, err = await jdy.update_data(
                        dataId=res[0]['_id'],
                        data=data
                    )
                    await errFn(err)
                else:
                    _, err = await jdy.create_data(
                        data=data,
                        is_start_workflow=True,
                    )
                    await errFn(err)
            elif v['b_form'] == '实销量/发货量工资单' and v['b_is_bzy'] != '是':
                b = [{
                    '_id': v['_id'],
                    'b_1': v['b_1'],
                    'b_2': v['b_2'],
                    'b_3': v['b_3'],
                    'b_4': v['b_4'],
                    'b_5': v['b_5'],
                    'b_6': v['b_6'],
                    'b_7': v['b_7'],
                    'b_8': v['b_8'],
                    'b_9': v['b_9'],
                    'b_10': v['b_10'],
                    'b_11': v['b_11'],
                    'b_12': v['b_12'],
                    'b_13': v['b_13'],
                    'b_14': v['b_14'],
                }]

                data = {
                    'b_wyz': {'value': v['b_wyz']},
                    'gz_date': {'value': gz_date},
                    'gz_nianyue': {'value': gz_nianyue},
                    'customer_code': {'value': customer_code},
                    'customer_name': {'value': customer_name},
                    'person': {'value': JdySerialize.member_err_to_none(v, 'b_person')},
                    'person_name': {'value': v['b_person_name']},
                    'person_no': {'value': v['b_person_no']},
                    'nianyuegh': {'value': v['b_nianyuegh']},
                    'gzjb': {'value': v['b_gzjb']},
                    # 'subtotal': {'value': v['b_15']},
                    'business': JdySerialize.subform('business', b)['business'],
                }
                jdy1 = jdy_list[1]
                res, err = await jdy1.get_form_data(
                    data_filter={
                        "cond": [
                            {
                                "field": 'b_wyz',
                                "type": 'text',
                                "method": "eq",
                                "value": v['b_wyz']  # 唯一值
                            },
                        ],
                    },
                )
                await errFn(err)
                if res:
                    _, err = await jdy1.update_data(
                        dataId=res[0]['_id'],
                        data=data
                    )
                    await errFn(err)
                else:
                    _, err = await jdy1.create_data(
                        data=data,
                        is_start_workflow=True,
                    )
                    await errFn(err)
            elif v['b_form'] == '自由业代奖励核对' and v['b_is_bzy'] != '是':
                b = [{
                    '_id': v['_id'],
                    'b_1': v['b_1'],
                    'b_2': v['b_2'],
                    'b_3': v['b_3'],
                    'b_4': v['b_4'],
                    'b_5': v['b_5'],
                    'b_6': v['b_6'],
                    'b_7': v['b_7'],
                    'b_8': v['b_8'],
                    'b_9': v['b_9'],
                    'b_10': v['b_10'],
                    'b_11': v['b_11'],
                    'b_12': v['b_12'],
                    'b_13': v['b_13'],
                    'b_14': v['b_14'],
                }]

                data = {
                    'b_wyz': {'value': v['b_wyz']},
                    'gz_date': {'value': gz_date},
                    'gz_nianyue': {'value': gz_nianyue},
                    'sx_years_code': {'value': sx_years_code},
                    'customer_code': {'value': customer_code},
                    'customer_name': {'value': customer_name},
                    # 'total': {'value': v['b_15']},
                    'total_sales': {'value': total_sales},
                    'person': {'value': JdySerialize.member_err_to_none(v, 'b_person')},
                    'person_name': {'value': v['b_person_name']},
                    'person_no': {'value': v['b_person_no']},
                    'nianyuegh': {'value': v['b_nianyuegh']},
                    'gzjb': {'value': v['b_gzjb']},
                    'business': JdySerialize.subform('business', b)['business'],
                }

                jdy3 = jdy_list[3]
                res, err = await jdy3.get_form_data(
                    data_filter={
                        "cond": [
                            {
                                "field": 'b_wyz',
                                "type": 'text',
                                "method": "eq",
                                "value": v['b_wyz']  # 唯一值
                            },
                        ],
                    },
                )
                await errFn(err)
                if res:
                    _, err = await jdy3.update_data(
                        dataId=res[0]['_id'],
                        data=data
                    )
                    await errFn(err)
                else:
                    _, err = await jdy3.create_data(
                        data=data,
                        is_start_workflow=True,
                    )
                    await errFn(err)
            elif v['b_form'] == '底薪业代工资' and v['b_is_bzy'] != '是':
                s = {
                    '_id': v['_id'],
                    'gz_nianyue': gz_nianyue,
                    'person': JdySerialize.member_err_to_none(v, 'b_person'),
                    'person_name': v['b_person_name'],
                    'person_no': v['b_person_no'],
                    'gzjb': v['b_gzjb'],
                    'total': v['b_15'],
                }
                c = {
                    '_id': v['_id'],
                    'b_person_name': v['b_person_name'],
                    'b_1': v['b_1'],
                    'b_2': v['b_2'],
                    'b_3': v['b_3'],
                    'b_4': v['b_4'],
                    'b_5': v['b_5'],
                    'b_6': v['b_6'],
                    'b_7': v['b_7'],
                    'b_8': v['b_8'],
                    'b_9': v['b_9'],
                    'b_10': v['b_10'],
                    'b_11': v['b_11'],
                    'b_12': v['b_12'],
                    'b_13': v['b_13'],
                    'b_14': v['b_14'],
                    'b_15': v['b_15'],
                }
                s_list.append(s)
                c_list.append(c)
            else:
                continue

        if c_list and s_list:

            jdy2 = jdy_list[2]

            data = {
                'serial_number': {'value': whi.data['serial_number']},
                'gz_date': {'value': gz_date},
                'gz_nd': {'value': gz_nianyue},
                'customer_code': {'value': customer_code},
                'customer_name': {'value': customer_name},
                'dx_content': JdySerialize.subform('dx_content', s_list)['dx_content'],
                'business': JdySerialize.subform('business', c_list)['business'],
            }
            res, err = await jdy2.get_form_data(
                data_filter={
                    "cond": [
                        {
                            "field": 'serial_number',
                            "method": "eq",
                            "value": whi.data['serial_number']  # 唯一值
                        }, ], },
            )
            await errFn(err)
            if res:
                _, err = await jdy2.update_data(
                    dataId=res[0]['_id'],
                    data=data
                )
                await errFn(err)
            else:
                _, err = await jdy2.create_data(
                    data=data,
                    is_start_workflow=True,
                )
                await errFn(err)

        # 新客户实销量奖励核算申请
        if whi.data['balance_payment'] is None:
            pass
        else:
            if whi.data['balance_payment'] > 0:
                jdy4 = jdy_list[4]

                if whi.data['self_sales_subform']:
                    self_sales = whi.data['self_sales_subform'][0]

                    subform = [
                        {
                            '_id': '60bf5e3456262300083b2001',
                            's_xl': '小口口淳礼盒系列',
                            's_sxl': none_to_0(self_sales['s_1']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b2002',
                            's_xl': '大口口淳系列',
                            's_sxl': none_to_0(self_sales['s_2']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b2003',
                            's_xl': '罗伯克系列',
                            's_sxl': none_to_0(self_sales['s_3']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b2004',
                            's_xl': '捷虎系列',
                            's_sxl': none_to_0(self_sales['s_4']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b2005',
                            's_xl': '大椰泰系列',
                            's_sxl': none_to_0(self_sales['s_5']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b2006',
                            's_xl': '小椰泰标箱系列',
                            's_sxl': none_to_0(self_sales['s_6']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b2007',
                            's_xl': '小椰泰礼盒系列',
                            's_sxl': none_to_0(self_sales['s_7']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b2008',
                            's_xl': '小轻甘系列',
                            's_sxl': none_to_0(self_sales['s_8']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b2009',
                            's_xl': '艾尔牧系列',
                            's_sxl': none_to_0(self_sales['s_9']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b20010',
                            's_xl': '杯装果汁椰汁系列',
                            's_sxl': none_to_0(self_sales['s_10']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b20011',
                            's_xl': '果以鲜系列',
                            's_sxl': none_to_0(self_sales['s_11']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b20012',
                            's_xl': '方盒系列',
                            's_sxl': none_to_0(self_sales['s_12']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b20013',
                            's_xl': '高端方盒系列',
                            's_sxl': none_to_0(self_sales['s_13']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                        {
                            '_id': '60bf5e3456262300083b20014',
                            's_xl': '特级系列',
                            's_sxl': none_to_0(self_sales['s_14']),
                            's_khzt': None,
                            's_zxljl': None
                        },
                    ]
                    data = {
                        'serial_number': {'value': whi.data['serial_number']},
                        'gz_date': {'value': gz_date},
                        'gz_nianyue': {'value': gz_nianyue},
                        'customer_code': {'value': customer_code},
                        'customer_name': {'value': customer_name},
                        'sx_years_code': {'value': sx_years_code},
                        'reward_method': {'value': '自销量奖励'},
                        'total_self_sales': {'value': whi.data['total_self_sales']},
                        'self_sales_subform': JdySerialize.subform('self_sales_subform', subform)['self_sales_subform'],
                    }
                    _, err = await jdy4.query_update_data_one(
                        data_filter={
                            "cond": [
                                {
                                    "field": 'serial_number',
                                    "method": "eq",
                                    "value": whi.data['serial_number']  # 唯一值
                                },
                            ],
                        },
                        data=data,
                        non_existent_create=True,
                        is_start_workflow=True
                    )
                    await errFn(err)

        # 生成主表 客户实销量核对过渡表
        for v in b_subform:
            data = {
                'b_wyz': {'value': v['b_wyz']},
                'gz_date': {'value': gz_date},
                'gz_nianyue': {'value': gz_nianyue},
                'sx_years_code': {'value': sx_years_code},
                'customer_code': {'value': customer_code},
                'customer_name': {'value': customer_name},
                'subtotal': {'value': v['b_15']},
                'total_sales': {'value': total_sales},
                'b_person': {'value': JdySerialize.member_err_to_none(v, 'b_person')},
                'b_person_name': {'value': v['b_person_name']},
                'b_person_no': {'value': v['b_person_no']},
                'b_nianyuegh': {'value': v['b_nianyuegh']},
                'b_gzjb': {'value': v['b_gzjb']},
                'b_1': {'value': v['b_1']},
                'b_2': {'value': v['b_2']},
                'b_3': {'value': v['b_3']},
                'b_4': {'value': v['b_4']},
                'b_5': {'value': v['b_5']},
                'b_6': {'value': v['b_6']},
                'b_7': {'value': v['b_7']},
                'b_8': {'value': v['b_8']},
                'b_9': {'value': v['b_9']},
                'b_10': {'value': v['b_10']},
                'b_11': {'value': v['b_11']},
                'b_12': {'value': v['b_12']},
                'b_13': {'value': v['b_13']},
                'b_14': {'value': v['b_14']},
            }

            jdy5 = jdy_list[5]
            res, err = await jdy5.query_update_data_one(
                data_filter={
                    "cond": [
                        {
                            "field": 'b_wyz',
                            "type": 'text',
                            "method": "eq",
                            "value": v['b_wyz']  # 唯一值
                        },
                    ],
                },
                data=data,
                non_existent_create=True,
            )
            await errFn(err)

    # 结束时间
    elapsed = (time.perf_counter() - start)
    logger.info(f'[+] 程序处理耗时 {elapsed}s')


def none_to_0(value):
    if value is None:
        return 0
    return value
