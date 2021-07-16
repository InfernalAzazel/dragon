
"""
    -这里放 web hook 公用的模型
"""

from typing import Optional

from pydantic import BaseModel, Field


class WebHookItem(BaseModel):
    appid: Optional[str] = Field(None, description='推送事件')
    entry_id: Optional[dict] = Field(None, description='具体数据内容')


