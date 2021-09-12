import uvicorn
from fastapi import FastAPI

import router.index


def create_app():
    apps = FastAPI(
        title="腾龙",
        description="简道云 u8 企业微信 交互 服务器",
        version="stable 0.1.1",
        docs_url="/docs",  # 自定义文档地址
        openapi_url="/openapi.json",  #
        redoc_url='/redoc',  # redoc文档
    )

    # 注册路由
    router.index.register(apps)

    return apps


fast_app = create_app()


@fast_app.on_event('startup')
async def startup():
    pass


def main():
    uvicorn.run(app=fast_app, host="0.0.0.0", port=6666, debug=False)


if __name__ == '__main__':
    main()
