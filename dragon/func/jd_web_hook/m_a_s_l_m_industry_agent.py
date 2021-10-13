import time

from fastapi import APIRouter, Request, BackgroundTasks
from loguru import logger

from func.jd_web_hook.models import WebHookItem
from conf import Settings
from yetai import JDSDK

doc = '''
    修改市场、业代销量级别申请 -> 流程完成 -> 触发
    
    目标表单：全国区域汇总表

'''


def register(router: APIRouter):
    @router.post('/m-a-s-l-m-industry-agent', tags=['修改市场、业代销量级别申请-全国区域汇总表'], description=doc)
    async def m_a_s_l_m_industry_agent(whi: WebHookItem, req: Request, background_tasks: BackgroundTasks):
        # 验证签名
        if req.headers['x-jdy-signature'] != JDSDK.get_signature(
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

    if whi.op == 'data_create':
        # 全国区域汇总表
        national_regional_summary_form = JDSDK(
            app_id=Settings.JD_APP_ID_BLANK_AREA_MANAGEMENT,
            entry_id='5e168acd24a2980006c49bdb',
            api_key=Settings.JD_API_KEY,
        )
        data = {}
        try:
            data = {
                'market_level': {'value': whi.data['market_level']},  # 市场级别
                'industry_r_p': {'value': whi.data['industry_r_p']},  # 业代负责人口（万）
                'number_business_r': {'value': whi.data['number_business_r']},  # 业代配置人数
                'sales_level_industry_agent': {'value': whi.data['sales_level_industry_agent']},  # 业代销量级别
                'per_capita_index': {'value': whi.data['per_capita_index']},  # 人均指标（件）
                'market_sales_standard': {'value': whi.data['market_sales_standard']},  # 市场销量标准
            }
        except Exception as e:
            await errFn(e)

        res, err = await national_regional_summary_form.query_update_data_one(
            data_filter={
                "rel": "and",  # 或者"or"
                "cond": [
                    {
                        "field": 'province',
                        "type": 'text',
                        "method": "eq",
                        "value": whi.data['province']  # 省份
                    },
                    {
                        "field": 'city',
                        "type": 'text',
                        "method": "eq",
                        "value": whi.data['city']  # 城市
                    },
                    {
                        "field": 'district_county',
                        "type": 'text',
                        "method": "eq",
                        "value": whi.data['district_county']  # 区县
                    },
                ]
            },
            data=data
        )
        await errFn(err)
        # 结束时间
        elapsed = (time.perf_counter() - start)
        logger.info(f'[+] 程序处理耗时 {elapsed}s')
