"""
游戏王大师决斗 (Master Duel) 爬虫骨架 - 数据源与解析逻辑待实现
"""
import os

from src.spiders.base import BaseSpider

_LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, "scrapy.log")


class MasterduelSpider(BaseSpider):
    name = "masterduel"
    target_type = "game"

    custom_settings = {
        "LOG_FILE": _LOG_FILE,
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_TIMEOUT": 30,
        "DOWNLOAD_HANDLERS": {
            "https": "src.middlewares.curl_cffi_handler.CurlCffiDownloadHandler",
        },
    }

    # TODO(数据源待定): 采集卡牌数据与卡牌图片
    # 数据源、API/页面结构调研后，参考 autohome 的请求/解析模式实现

    async def start(self):
        # TODO: 入口请求，数据源待定
        pass

    def parse(self, response):
        # TODO: 解析卡牌数据，数据源待定
        pass
