from fastapi import APIRouter, BackgroundTasks

from utils import JdAPI

doc = '''
    测试

'''

# 客户档案
jd_customer_profile = JdAPI(JdAPI.APP_ID_BUSINESS, '5dd102e307747e0006801bee')


async def write_notification():
    res = await jd_customer_profile.get_form_data()
    print(len(res))


def register(router: APIRouter):
    @router.post('/test', tags=['测试'], description=doc)
    async def test(background_tasks: BackgroundTasks):
        background_tasks.add_task(write_notification)
        return {'res': 2}
