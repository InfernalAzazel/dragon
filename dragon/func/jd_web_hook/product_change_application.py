import time

from func.jd_web_hook.models import WebHookItem
from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger
from robak import Jdy, JdySerialize
from conf import Settings

doc = '''
    
    新增或修改产品信息申请 -> 流程完成 -> 触发
    
    1. 更新客户下的所有分销商产品信息

    2. 过渡表更新每一条分销商产品信息 

'''


def register(router: APIRouter):
    @router.post('/product-change-application', tags=['新增或修改产品信息申请'], description=doc)
    async def product_change_application(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
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
                data=whi.dict()
            )
            return

    # 启动时间
    start = Settings.log.start_time()

    if whi.data['flowState'] == 1 and whi.op == 'data_update':

        jd = Jdy.auto_init(
            app_id_list=[
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS
            ],
            entry_id_list=[
                '5e38e4dffe24c90006f3ec37',
                '5dd102e307747e0006801bee',
                '5de228733b001e000659af62',

            ],
            api_key=Settings.JD_API_KEY,
        )
        customer_profile = jd[0]  # 客户档案
        product_change_application_table = jd[1]  # 新增或修改产品信息申请
        customer_sales_product_table = jd[2]  # 客户销售产品过渡表

        # 新增或修改产品信息申请
        widgets = await product_change_application_table.get_form_widgets()

        for val in widgets:
            if val['label'] == '客户代码' and val['type'] == 'text':
                whi_data_subform_customer_code_field = val['name']
            elif val['label'] == '新增或修改产品信息' and val['type'] == 'subform':  # 新增或修改产品信息申请 -> 销售产品（子表单）
                whi_data_subform_field = val['name']
                # 历遍子表单
                for items in val['items']:
                    if items['label'] == '产品名称':
                        whi_data_subform_name_field = items['name']
                    elif items['label'] == '产品代码':
                        whi_data_subform_coode_field = items['name']
                    elif items['label'] == '客户名称+产品代码':
                        whi_data_subform_customer_add_product_field = items['name']

        # 客户档案
        widgets, err = await customer_profile.get_form_widgets()
        await errFn(err)

        for val in widgets:

            if val['label'] == '客户名称' and val['type'] == 'text':
                customer_profile_cname_field = val['name']
            elif val['label'] == '客户代码' and val['type'] == 'text':
                customer_profile_ccode_field = val['name']
            elif val['label'] == '客户类型' and val['type'] == 'combo':
                customer_profile_ctype_field = val['name']
            elif val['label'] == '归属经销商' and val['type'] == 'text':
                customer_profile_cdistributor_field = val['name']
            elif val['label'] == '归属经销商代码' and val['type'] == 'text':
                customer_profile_cdistributor_code_field = val['name']
            elif val['label'] == '销售产品' and val[
                'type'] == 'subform':  # 客户档案->销售产品（子表单）
                customer_profile_product_subform_field = val['name']
                # 历遍子表单
                for items in val['items']:
                    if items['label'] == '产品状态':
                        customer_profile_product_state_field = items['name']
                    elif items['label'] == '产品名称':
                        customer_profile_product_name_field = items['name']

                        # 过渡表
        widgets, err = await customer_sales_product_table.get_form_widgets()
        await errFn(err)

        for val in widgets:
            if val['label'] == '客户名称' and val['type'] == 'text':
                sales_cname_field = val['name']
            elif val['label'] == '客户代码' and val['type'] == 'text':
                sales_ccode_field = val['name']
            elif val['label'] == '客户类型' and val['type'] == 'text':
                sales_ctype_field = val['name']
            elif val['label'] == '归属经销商' and val['type'] == 'text':
                sales_cdistributor_field = val['name']
            elif val['label'] == '归属经销商代码' and val['type'] == 'text':
                sales_cdistributor_code_field = val['name']
            elif val['label'] == '产品状态' and val['type'] == 'text':
                sales_product_state_field = val['name']
            elif val['label'] == '产品名称' and val['type'] == 'combo':
                sales_product_name_field = val['name']
            elif val['label'] == '产品代码' and val['type'] == 'text':
                sales_product_code_field = val['name']
            elif val['label'] == '客户名称+产品代码' and val['type'] == 'text':  # 客户档案->销售产品（子表单）
                sales_customer_add_product_field = val['name']

        # 客户档案 -> 查询表单多条数据
        result, err = await customer_profile.get_form_data(
            data_filter={
                "cond": [
                    {
                        "field": customer_profile_cdistributor_code_field,  # 经销商代码
                        "type": 'text',
                        "method": "eq",  # 相等的
                        "value": whi.data[whi_data_subform_customer_code_field]  # 客户代码
                    },

                ]
            })
        await errFn(err)
        if not result:  # 空值
            logger.info('[!] 按条件查询客户档案返回空值')
            # 结束时间
            elapsed = (time.perf_counter() - start)
            logger.info(f'[+] 程序处理耗时 {elapsed}s')
            return '2xx'

        whi_data_subform, err = whi.data[whi_data_subform_field]  # 临时 新增或修改产品信息申请->销售产品（子表单）
        await errFn(err)
        for ii in range(len(result)):

            cpp_subform = result[ii][customer_profile_product_subform_field]  # 客户档案->销售产品（子表单）
            match_whi_data_subform = []
            match_cpp_subform = []
            # 客户档案->销售产品（子表单） == [] 直接更新
            if not cpp_subform:
                await customer_profile.update_data(
                    dataId=result[ii]['_id'],
                    data=JdySerialize.subform(subform_field=customer_profile_product_subform_field,
                                             data=whi_data_subform))
            else:

                # 客户档案更新
                for ccp_val in cpp_subform:
                    match_cpp_subform.append(ccp_val[customer_profile_product_name_field])
                for wd_val in whi_data_subform:
                    match_whi_data_subform.append(
                        wd_val[whi_data_subform_name_field])  # 新增或修改产品信息申请->销售产品（子表单）->产品名称

                for i in range(len(match_whi_data_subform)):
                    # 构造 产品名称+客户代码
                    whi_data_subform[i][whi_data_subform_customer_add_product_field] = result[i][
                                                                                           customer_profile_cname_field] + \
                                                                                       whi_data_subform[i][
                                                                                           whi_data_subform_coode_field]

                    if match_whi_data_subform[i] not in match_cpp_subform:

                        cpp_subform.append(whi_data_subform[i])
                    else:
                        for ccp_val in cpp_subform:
                            if ccp_val[customer_profile_product_name_field] == match_whi_data_subform[i]:
                                ccp_val[customer_profile_product_state_field] = "启用"

                _, err = await customer_profile.update_data(
                    dataId=result[ii]['_id'],
                    data=JdySerialize.subform(subform_field=customer_profile_product_subform_field,
                                             data=cpp_subform))
                await errFn(err)

        # ====================================================================================================

        for ii in range(len(result)):
            for n in range(len(whi_data_subform)):
                result2, err = await customer_sales_product_table.get_form_data(
                    data_filter={
                        "cond": [
                            {
                                "field": sales_customer_add_product_field,
                                "type": 'text',
                                "method": "eq",  # 相等的
                                "value": whi_data_subform[n][whi_data_subform_customer_add_product_field]
                            },

                        ]
                    }
                )
                await errFn(err)
                if not result2:
                    _, err = await customer_sales_product_table.create_data(
                        data={
                            # 客户代码
                            sales_ccode_field: {
                                "value": result[ii][customer_profile_ccode_field]
                            },
                            # 客户名称
                            sales_cname_field: {
                                "value": result[ii][customer_profile_cname_field]
                            },
                            # 客户类型
                            sales_ctype_field: {
                                "value": result[ii][customer_profile_ctype_field]
                            },
                            # 归属经销商
                            sales_cdistributor_field: {
                                "value": result[ii][customer_profile_cdistributor_field]
                            },
                            # 归属经销商代码
                            sales_cdistributor_code_field: {
                                "value": result[ii][customer_profile_cdistributor_code_field]
                            },
                            # 产品状态
                            sales_product_state_field: {
                                "value": '启用'
                            },
                            # 产品名称
                            sales_product_name_field: {
                                "value": whi_data_subform[n][whi_data_subform_name_field]
                            },
                            # 产品代码
                            sales_product_code_field: {
                                "value": whi_data_subform[n][whi_data_subform_coode_field]
                            },
                            # 客户名称-产品代码
                            sales_customer_add_product_field: {
                                "value": whi_data_subform[n][whi_data_subform_customer_add_product_field]
                            },

                        }
                    )
                    await errFn(err)
                else:

                    _, err = await customer_sales_product_table.update_data(
                        dataId=result2[0]['_id'],
                        data={
                            # 产品状态
                            sales_product_state_field: {
                                "value": '启用'
                            }
                        }
                    )
                    await errFn(err)

        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
