from typing import Optional

from dragon_micro_client import AsyJDAPI
from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from conf import Settings, Micro


class Item(BaseModel):
    activity_code: Optional[str] = Field(None, description='申请批号')


doc = '''
   获取活动已延期计数

'''


def register(router: APIRouter):
    @router.post('/activity-postponed-count', tags=['活动延期申请-获取活动已延期计数'], description=doc)
    async def activity_postponed_count(item: Item, token: Optional[str] = Header(None)):
        if token != Settings.DRAGON_TOKEN:
            return 'fail', 401

        if item.activity_code is not None:

            # 活动延期申请
            activity_apply_form = AsyJDAPI(
                Settings.JD_APP_ID_BUSINESS,
                '60df03e9200c6a00072fdb4d',
                Settings.JD_API_KEY,
                mcc=Micro.mcc
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
