from typing import Optional, List

from dragon_micro_client import MicroClientConfig, AsyJDAPI
from fastapi import APIRouter, Request, Header
from pydantic import BaseModel, Field

import settings
from utils import JdAPI


class Item(BaseModel):
    activity_code: Optional[str] = Field(None, description='申请批号')


doc = '''
   获取活动已延期计数

'''


def register(router: APIRouter):
    @router.post('/activity-postponed-count', tags=['活动延期申请-获取活动已延期计数'], description=doc)
    async def activity_postponed_count(item: Item, token: Optional[str] = Header(None)):
        if token != settings.Default.DRAGON_TOKEN:
            return 'fail', 401

        if item.activity_code is not None:
            # 配置腾龙微服务
            mcc = MicroClientConfig(
                mcc_url=settings.Default.MCC_BASIC_URL,
                token=settings.Default.MCC_BASIC_TOKEN
            )
            # 活动延期申请
            activity_apply_form = AsyJDAPI(
                JdAPI.APP_ID_BUSINESS,
                '60df03e9200c6a00072fdb4d',
                settings.Default.JD_API_KEY,
                mcc
            )

            res = await activity_apply_form.get_form_data(data_filter={
                "cond": [
                    {
                        "field": 'activitycode',
                        "type": 'text',
                        "method": "eq",
                        "value": item.activity_code  # 申请批号
                    }
                ]
            })
            n = 0
            if res:
                for i in range(len(res)):
                    if res[i]['flowState'] == 1:
                        n = n + 1
                return {'count': n}
        return {'count': 0}
