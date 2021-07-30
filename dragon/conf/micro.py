# 配置腾龙微服务
from dragon_micro_client import MicroClientConfig

from conf import Settings


class Micro:
    mcc = MicroClientConfig(
        mcc_url=Settings.MCC_BASIC_URL,
        token=Settings.MCC_BASIC_TOKEN
    )
