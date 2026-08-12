"""
汽车之家品牌信息爬虫 - 测试入口地址
"""
import json
import os

import scrapy

from src.spiders.base import BaseSpider
from .autohome_cookies import get_cookies

_LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, "scrapy.log")


class AutohomeSpider(BaseSpider):
    name = "autohome"
    target_type = "automobile"
    allowed_domains = ["autohome.com.cn"]

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

    BASE_URL = "https://www.autohome.com.cn"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.info("[Autohome] fetching cookies...")
        self.cookies = get_cookies()
        self.logger.info("[Autohome] cookies fetched, %d pairs", len(self.cookies))

    def _build_headers(self, api: str, method: str = "GET", ref: str = BASE_URL) -> dict:
        return {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Google Chrome\";v=\"150\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "Referer": ref,
        }

    async def start(self):
        url = f"{self.BASE_URL}/web-main/car/web/price/treeMenu?extendseries=1"
        headers = self._build_headers(api=url, method="GET", ref="https://www.autohome.com.cn/price/brandid_33")
        headers["cookies"] = self.cookies
        self.logger.info("[Autohome] request entry URL: %s", url)
        yield scrapy.Request(
            url=url,
            method="GET",
            headers=headers,
            callback=self.parse_entry,
            dont_filter=True,
        )

    def parse_entry(self, response):
        self.logger.info("[Autohome] response status=%d", response.status)
        try:
            resp = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error("[Autohome] JSON decode error: %s", e)
            return

        if resp.get("message") == "success":
            self.logger.info("[Autohome] entry response success")
            # [TEMP-DEBUG-START] 临时实验：只 yield 一个请求，程序写好后删除此块
            sent = False
            # [TEMP-DEBUG-END]
            for res in resp["result"]:
                for branditem in res["branditems"]:
                    brand_name = branditem["name"]
                    brand_id = branditem["id"]
                    brand_logo = branditem["logo"]
                    for producer in branditem["fctitems"]:
                        producer_id = producer["id"]
                        producer_name = producer["name"]
                        for item in producer["seriesitems"]:
                            model_name = item["name"]
                            model_id = item["id"]
                            model_isnewenergy = item["isnewenergy"]
                            model_state = item["state"]
                            model_speccount = item["speccount"]
                            basic_info = {
                                "brand_name": brand_name,
                                "brand_id": brand_id,
                                "brand_logo": brand_logo,
                                "producer_id": producer_id,
                                "producer_name": producer_name,
                                "model_name": model_name,
                                "model_id": model_id,
                                "model_isnewenergy": model_isnewenergy,
                                "model_state": model_state,
                                "model_speccount": model_speccount
                            }
                            param_url = f"{self.BASE_URL}/web-main/car/param/getParamConf?mode=1&site=1&seriesid={model_id}"
                            param_headers = self._build_headers(
                                api=param_url, method="GET",
                                ref=f"https://www.autohome.com.cn/config/series/{model_id}.html",
                            )
                            param_headers["accept"] = "application/json"
                            param_headers["cookies"] = self.cookies
                            self.logger.info("[Autohome] request param conf | model_id=%s name=%s", model_id, model_name)
                            yield scrapy.Request(
                                url=param_url,
                                method="GET",
                                headers=param_headers,
                                callback=self.parse_param_conf,
                                meta={"model_id": model_id},
                                dont_filter=True,
                            )
                            class_url = f"{self.BASE_URL}/web-main/car/pic/getclainfo?seriesid={model_id}"
                            class_headers = self._build_headers(
                                api=class_url, method="GET",
                                ref=f"https://www.autohome.com.cn/cars/imgs-{model_id}-x-1-x/0.html",
                            )
                            class_headers["accept"] = "application/json"
                            class_headers["cookies"] = self.cookies
                            self.logger.info("[Autohome] request pic class info | model_id=%s name=%s", model_id, model_name)
                            yield scrapy.Request(
                                url=class_url,
                                method="GET",
                                headers=class_headers,
                                callback=self.parse_class_info,
                                meta={"model_id": model_id},
                                dont_filter=True,
                            )
                            # [TEMP-DEBUG-START] 临时实验：只 yield 一个请求，程序写好后删除此块
                            sent = True
                            break
                        if sent:
                            break
                    if sent:
                        break
                if sent:
                    break
            # [TEMP-DEBUG-END]
        else:
            message = resp.get("message", "unknown error")
            self.logger.error("[Autohome] entry response failed | message=%s", message)
            self.crawler.engine.close_spider(self, reason=f"entry request failed: {message}")

    def parse_param_conf(self, response):
        self.logger.info("[Autohome] param conf response status=%d", response.status)
        model_id = response.meta["model_id"]
        try:
            configuration = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error("[Autohome] param conf JSON decode error: %s", e)
            return
        if configuration.get("message") != "success":
            self.logger.error(
                "[Autohome] param conf failed | model_id=%s message=%s",
                model_id, configuration.get("message"),
            )
            return
        # [TEMP-DEBUG-START] 临时打印调试，程序写好后删除此行
        print(configuration)
        # [TEMP-DEBUG-END]
        self.logger.info(
            "[Autohome] param conf received | model_id=%s message=%s",
            model_id, configuration.get("message"),
        )

    def parse_class_info(self, response):
        self.logger.info("[Autohome] pic class info response status=%d", response.status)
        model_id = response.meta["model_id"]
        try:
            class_info = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error("[Autohome] pic class info JSON decode error: %s", e)
            return
        if class_info.get("message") != "success":
            self.logger.error(
                "[Autohome] pic class info failed | model_id=%s message=%s",
                model_id, class_info.get("message"),
            )
            return
        # [TEMP-DEBUG-START] 临时打印调试，程序写好后删除此行
        print(class_info)
        # [TEMP-DEBUG-END]
        model_classinfo = class_info.get("result", {})
        self.logger.info(
            "[Autohome] pic class info received | model_id=%s classcount=%d speccount=%d",
            model_id, len(model_classinfo.get("classinfo", [])), len(model_classinfo.get("specitems", [])),
        )
