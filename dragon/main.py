import uvicorn
from fastapi import FastAPI

import router.v1.index
from task.v1.task_list import TaskList


def create_app():
    app = FastAPI(
        title="腾龙",
        description="简道云 u8 企业微信 交互 服务器",
        version="stable 0.1.1",
        docs_url="/docs",  # 自定义文档地址
        openapi_url="/openapi.json",  #
        redoc_url='/redoc',  # redoc文档
    )

    # 注册路由
    router.v1.index.register(app)

    return app


app = create_app()


@app.on_event('startup')
async def startup():
   pass


def main():
    uvicorn.run(app=app, host="0.0.0.0", port=6666, debug=False)


if __name__ == '__main__':
    main()
