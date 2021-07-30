from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from conf import Settings


class Item(BaseModel):
    value_int: Optional[int] = Field(None, description='数字类字段值')
    value_str: Optional[str] = Field(None, description='文本类型字段值')
    value_list: Optional[list] = Field([], description='数组类型字段值')
    value_json: Optional[dict] = Field({}, description='JSON类型字段值')
    division: Optional[bool] = Field(False, description='是否分割，只支持str类型')


doc = '''
    支持类型
    
    -   数字类字段值
    -   文本类型字段值      ( 支持分割)
    -   数组类型字段值
    -   JSON类型字段值
    
'''


def register(router: APIRouter):
    @router.post('/copy_value_to_field', tags=['复制一个字段到另一个字段'], description=doc)
    async def copy_value_to_field(item: Item, token: Optional[str] = Header(None)):

        if token != Settings.DRAGON_TOKEN:
            return 'fail', 401

        outs = {}

        if item.value_int is not None:
            outs['value_int'] = item.value_int
        if item.value_str is not None and item.division is True:
            l = item.value_str.split(',')
            l.pop()
            outs['value_str'] = l
        if item.value_str is not None and item.division is False:
            outs['value_str'] = item.value_str
        if item.value_list:
            outs['value_list'] = item.value_list
        if item.value_json:
            outs['value_dict'] = item.value_json
        return outs
