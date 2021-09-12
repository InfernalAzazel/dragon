"""
    -这里放 web hook 公用的模型
"""

from typing import Optional
from pydantic import BaseModel, Field


class WebHookItem(BaseModel):
    op: Optional[str] = Field(None, description='推送事件')
    data: Optional[dict] = Field(None, description='具体数据内容')

