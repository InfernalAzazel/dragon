import os

from robak import JdyLog


class Settings:
    # web 服务器 -----------------------------
    # API 认证
    DRAGON_TOKEN = 'eYhUCuXBGaqv6AeD2W1X3PwC'

    # 简道云 -------------------------------------------------
    # API 认证密钥
    JD_API_KEY = 'Q20Prk3r78ih4w0ZYOr6iEFfj9g6cEk0'
    # web hook 加密
    JD_SECRET = 'jIYbq5RGrjeA1AsrNGdWfpH0'
    # 学习板块
    JD_APP_ID_LEARNING_SECTION = '5e3e162d6e511b00067f066b'
    # 业务管理
    JD_APP_ID_BUSINESS = '5dde829086f77b0006f3833e'
    # 人事管理
    JD_APP_ID_MINISTRY_OF_PERSONNEL = '5df62d315fb7f10006a0b21e'
    # (生产) 质量管理
    JD_APP_ID_QUALITY = '5e44a6166adcd20006eb515f'
    # 仓库管理系统（在使用）
    JD_APP_ID_WAREHOUSE_M_SYSTEM = '5e0db1ac3e79d40006ceaedd'
    # 空白区域管理（正式系统）
    JD_APP_ID_BLANK_AREA_MANAGEMENT = '5df633e09a7d50000618e78a'
    # 配置异常处理
    log = JdyLog(
        app_id=JD_APP_ID_BUSINESS,
        exe_name='dragon',
        entry_id='617649d05253940008e471d8',
        api_key=JD_API_KEY,
        root_path=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

