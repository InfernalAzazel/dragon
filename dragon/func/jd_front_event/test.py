from fastapi import APIRouter, BackgroundTasks
from lunar_you_ying import JDSDK
from conf import Settings

doc = '''
    测试

'''


async def write_notification():
    async def errFn(e):
        if e is not None:
            print(e)
            return
            # 客户档案
    jd_customer_profile = JDSDK(
        Settings.JD_APP_ID_BUSINESS,
        '5dd102e307747e0006801bee',
    )
    res, err = await jd_customer_profile.get_form_data()
    await errFn(err)
    print(len(res))


def register(router: APIRouter):
    @router.post('/test', tags=['测试'], description=doc)
    async def test(background_tasks: BackgroundTasks):
        background_tasks.add_task(write_notification)
        return {'res': 2}
