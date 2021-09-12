from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field
from conf import Settings
from lunar_you_ying import JDSDK


class Inputs(BaseModel):
    store_name: Optional[str] = Field(None, description='门店名称')
    creator: Optional[str] = Field(None, description='建档人（储存）')
    source_form: Optional[str] = Field(None, description='来源门店档案表单')


class Outputs(BaseModel):
    creator_date: Optional[str] = Field(None, description='建档日期')
    cooperate_date: Optional[str] = Field(None, description='合作时间')
    store_code: Optional[str] = Field(None, description='门店编码')
    store_type: Optional[str] = Field(None, description='门店类型')
    contact_number: Optional[str] = Field(None, description='联系电话')
    terminal_location: Optional[str] = Field(None, description='终端建档位置')


# 补指定开发奖励申请-门店档案1~6的数据


doc = '''
   补指定开发奖励申请-门店档案1~6的数据

'''


def register(router: APIRouter):
    @router.post('/r_a_d_reward_apply', tags=['补指定开发奖励申请-门店档案1~6的数据'], description=doc)
    async def leave_apply(inputs: Inputs, token: Optional[str] = Header(None)):
        async def errFn(e):
            if e is not None:
                print(e)
                return
        if token != Settings.DRAGON_TOKEN:
            return 'fail', 401
        jd = JDSDK.auto_init(
            app_id_list=[
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
                Settings.JD_APP_ID_BUSINESS,
            ],
            entry_id_list=[
                '5f0287f66c800400061de829',
                '6087ddf67159d900085a22a4',
                '6087ddfa1d26c20008a28517',
                '6087de10cb3b6600079c304a',
                '6087de14f233ae0007790424',
                '6087de16c2853f0007f44d35',
            ],
            api_key=Settings.JD_API_KEY,
        )

        jd_store_archives_form_1 = jd[0]
        jd_store_archives_form_2 = jd[1]
        jd_store_archives_form_3 = jd[2]
        jd_store_archives_form_4 = jd[3]
        jd_store_archives_form_5 = jd[4]
        jd_store_archives_form_6 = jd[5]

        if inputs.source_form == '1':
            res, err = await jd_store_archives_form_1.get_form_data(
                data_filter={
                    "rel": "and",  # 或者"or"
                    "cond": [
                        {
                            "field": 'name',
                            "type": 'text',
                            "method": "eq",
                            "value": inputs.store_name  # 门店名称
                        },
                        {
                            "field": 'managername',
                            "type": 'text',
                            "method": "eq",
                            "value": inputs.creator  # 建档人
                        },
                    ]
                }
            )
            await errFn(err)
            if not res:
                return {'err': f'在 门店档案 {inputs.source_form} 查询到符合条件的数据!'}
            outputs = Outputs(
                creator_date=res[0]['createddate'],  # 建档日期
                cooperate_date=res[0]['opendate'],  # 合作日期
                store_code=res[0]['code'],  # 门店编码
                store_type=res[0]['typename'],  # 门店类型
                contact_number=res[0]['contactertel'],  # 联系电话
                terminal_location=res[0]['address'],  # 终端建档位置
            )
            return outputs.dict()
        elif inputs.source_form == '2':
            res, err = await jd_store_archives_form_2.get_form_data(
                data_filter={
                    "rel": "and",  # 或者"or"
                    "cond": [
                        {
                            "field": 'name',
                            "type": 'text',
                            "method": "eq",
                            "value": inputs.store_name  # 门店名称
                        },
                        {
                            "field": 'managername',
                            "type": 'text',
                            "method": "eq",
                            "value": inputs.creator  # 建档人
                        },
                    ]
                }
            )
            await errFn(err)
            if not res:
                return {'err': f'在 门店档案 {inputs.source_form} 查询到符合条件的数据!'}
            outputs = Outputs(
                creator_date=res[0]['createddate'],  # 建档日期
                cooperate_date=res[0]['opendate'],  # 合作日期
                store_code=res[0]['code'],  # 门店编码
                store_type=res[0]['typename'],  # 门店类型
                contact_number=res[0]['contactertel'],  # 联系电话
                terminal_location=res[0]['address'],  # 终端建档位置
            )
            return outputs.dict()
        elif inputs.source_form == '3':
            res, err = await jd_store_archives_form_3.get_form_data(
                data_filter={
                    "rel": "and",  # 或者"or"
                    "cond": [
                        {
                            "field": 'name',
                            "type": 'text',
                            "method": "eq",
                            "value": inputs.store_name  # 门店名称
                        },
                        {
                            "field": 'managername',
                            "type": 'text',
                            "method": "eq",
                            "value": inputs.creator  # 建档人
                        },
                    ]
                }
            )
            await errFn(err)
            if not res:
                return {'err': f'在 门店档案 {inputs.source_form} 查询到符合条件的数据!'}
            outputs = Outputs(
                creator_date=res[0]['createddate'],  # 建档日期
                cooperate_date=res[0]['opendate'],  # 合作日期
                store_code=res[0]['code'],  # 门店编码
                store_type=res[0]['typename'],  # 门店类型
                contact_number=res[0]['contactertel'],  # 联系电话
                terminal_location=res[0]['address'],  # 终端建档位置
            )
            return outputs.dict()
        elif inputs.source_form == '4':
            res, err = await jd_store_archives_form_4.get_form_data(
                data_filter={
                    "rel": "and",  # 或者"or"
                    "cond": [
                        {
                            "field": 'name',
                            "type": 'text',
                            "method": "eq",
                            "value": inputs.store_name  # 门店名称
                        },
                        {
                            "field": 'managername',
                            "type": 'text',
                            "method": "eq",
                            "value": inputs.creator  # 建档人
                        },
                    ]
                }
            )
            await errFn(err)
            if not res:
                return {'err': f'在 门店档案 {inputs.source_form} 查询到符合条件的数据!'}
            outputs = Outputs(
                creator_date=res[0]['createddate'],  # 建档日期
                cooperate_date=res[0]['opendate'],  # 合作日期
                store_code=res[0]['code'],  # 门店编码
                store_type=res[0]['typename'],  # 门店类型
                contact_number=res[0]['contactertel'],  # 联系电话
                terminal_location=res[0]['address'],  # 终端建档位置
            )
            return outputs.dict()
        elif inputs.source_form == '5':
            res, err = await jd_store_archives_form_5.get_form_data(
                data_filter={
                    "rel": "and",  # 或者"or"
                    "cond": [
                        {
                            "field": 'name',
                            "type": 'text',
                            "method": "eq",
                            "value": inputs.store_name  # 门店名称
                        },
                        {
                            "field": 'managername',
                            "type": 'text',
                            "method": "eq",
                            "value": inputs.creator  # 建档人
                        },
                    ]
                }
            )
            await errFn(err)
            if not res:
                return {'err': f'在 门店档案 {inputs.source_form} 查询到符合条件的数据!'}
            outputs = Outputs(
                creator_date=res[0]['createddate'],  # 建档日期
                cooperate_date=res[0]['opendate'],  # 合作日期
                store_code=res[0]['code'],  # 门店编码
                store_type=res[0]['typename'],  # 门店类型
                contact_number=res[0]['contactertel'],  # 联系电话
                terminal_location=res[0]['address'],  # 终端建档位置
            )
            return outputs.dict()
        elif inputs.source_form == '6':
            res, err = await jd_store_archives_form_6.get_form_data(
                data_filter={
                    "rel": "and",  # 或者"or"
                    "cond": [
                        {
                            "field": 'name',
                            "type": 'text',
                            "method": "eq",
                            "value": inputs.store_name  # 门店名称
                        },
                        {
                            "field": 'managername',
                            "type": 'text',
                            "method": "eq",
                            "value": inputs.creator  # 建档人
                        },
                    ]
                }
            )
            await errFn(err)
            if not res:
                return {'err': f'在 门店档案 {inputs.source_form} 查询到符合条件的数据!'}
            outputs = Outputs(
                creator_date=res[0]['createddate'],  # 建档日期
                cooperate_date=res[0]['opendate'],  # 合作日期
                store_code=res[0]['code'],  # 门店编码
                store_type=res[0]['typename'],  # 门店类型
                contact_number=res[0]['contactertel'],  # 联系电话
                terminal_location=res[0]['address'],  # 终端建档位置
            )
            return outputs.dict()

        return {'err': f'找不到 门店档案{inputs.source_form} 表单!'}
