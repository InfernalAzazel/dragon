from typing import Optional

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, Field
from conf import Settings
from robak import Jdy


class Inputs(BaseModel):
    job_number: Optional[str] = Field(None, description='申请人工号')


class Outputs(BaseModel):
    flow_state: Optional[str] = Field(None, description='流程状态')


# 请假申请表单-获取流程状态是否进行中


doc = '''
   请假申请表单-获取流程进行中状态

'''


def register(router: APIRouter):
    @router.post('/leave-apply/get-flow-state-is-ongoing', tags=['请假申请表单-获取流程进行中状态'], description=doc)
    async def leave_apply(inputs: Inputs, req: Request, token: Optional[str] = Header(None)):
        async def errFn(e):
            if e is not None:
                Settings.log.print(name=str(req.url), info=e)
                return
        if token != Settings.DRAGON_TOKEN:
            return 'fail', 401
            # 请假申请表单

        jd_leave_apply_form = Jdy(
            app_id=Settings.JD_APP_ID_MINISTRY_OF_PERSONNEL,
            entry_id='5e7aa499fe9288000704f1e5',
            api_key=Settings.JD_API_KEY,
        )
        res, err = await jd_leave_apply_form.get_form_data(
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
        await errFn(err)
        outputs = Outputs(flow_state='否')
        if not res:
            return outputs.dict()
        for value in res:
            # 有一条在进行中
            if value['flowState'] == 0:
                outputs = Outputs(flow_state='是')
                return outputs.dict()
        return outputs.dict()
