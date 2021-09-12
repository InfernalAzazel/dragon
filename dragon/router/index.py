"""
  主要路由
"""

from fastapi import FastAPI

from control.route import jd_front_event_router, jd_web_hook_router

# 接口版本
api_v1 = '/api/v1'


def register(app: FastAPI):
    # 路由注册
    # 简道云 前端事件
    app.include_router(jd_front_event_router,
                       prefix=f'{api_v1}/jd/front-event',
                       )
    # 简单云 web hook
    app.include_router(jd_web_hook_router,
                       prefix=f'{api_v1}/jd/web-hook',
                       )
    # u8
    # app.include_router(u8_router,
    #                    prefix=f'{api_v1}/u8',
    #                    )
