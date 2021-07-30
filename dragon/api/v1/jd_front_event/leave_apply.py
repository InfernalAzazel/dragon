from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field
from conf import Settings, Micro
from dragon_micro_client import AsyJDAPI


class Inputs(BaseModel):
    job_number: Optional[str] = Field(None, description='申请人工号')


class Outputs(BaseModel):
    flow_state: Optional[int] = Field(None, description='流程状态')


# 请假申请表单-获取流程状态是否进行中


doc = '''
   请假申请表单-获取流程进行中状态

'''


def register(router: APIRouter):
    @router.post('/leave-apply/get-flow-state-is-ongoing', tags=['请假申请表单-获取流程进行中状态'], description=doc)
    async def leave_apply(inputs: Inputs, token: Optional[str] = Header(None)):
        if token != Settings.DRAGON_TOKEN:
            return 'fail', 401
            # 请假申请表单

        jd_leave_apply_form = AsyJDAPI(
            app_id=Settings.JD_APP_ID_MINISTRY_OF_PERSONNEL,
            entry_id='5e7aa499fe9288000704f1e5',
            api_key=Settings.JD_API_KEY,
            mcc=Micro.mcc
        )
        res = await jd_leave_apply_form.get_form_data(
            data_filter={
                "cond": [
                    {
                        "field": 'job_number',
                        "type": 'text',
                        "method": "eq",
                        "value": inputs.job_number  # 申请人工号
                    }
                ]
            })
        outputs = Outputs(flow_state=-1)
        if not res:
            return outputs.dict()
        for value in res:
            # 有一条在进行中
            if value['flowState'] == 0:
                outputs = Outputs(flow_state=0)
                return outputs.dict()
        return outputs.dict()
