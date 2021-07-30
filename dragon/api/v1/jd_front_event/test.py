from fastapi import APIRouter, BackgroundTasks
from dragon_micro_client import AsyJDAPI
from conf import Settings, Micro

doc = '''
    测试

'''


async def write_notification():
    # 客户档案
    jd_customer_profile = AsyJDAPI(
        Settings.JD_APP_ID_BUSINESS,
        '5dd102e307747e0006801bee',
        mcc=Micro.mcc
    )
    res = await jd_customer_profile.get_form_data()
    print(len(res))


def register(router: APIRouter):
    @router.post('/test', tags=['测试'], description=doc)
    async def test(background_tasks: BackgroundTasks):
        background_tasks.add_task(write_notification)
        return {'res': 2}
