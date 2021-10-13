from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from conf import Settings


class Item(BaseModel):
    a: Optional[str] = Field(None, description='')


doc = '''
    
    
'''


def register(router: APIRouter):
    @router.post('/test', tags=['测试'], description=doc)
    async def test(item: Item, token: Optional[str] = Header(None)):
        if token != Settings.DRAGON_TOKEN:
            return 'fail', 401

        print(item.a)

        return
