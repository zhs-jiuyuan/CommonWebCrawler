"""
Scrapy download handler using curl_cffi for TLS fingerprint impersonation.
"""
import random

from curl_cffi import requests as curl_requests
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.settings import Settings
from twisted.internet import threads

_BROWSER_ALIASES = [
    "chrome120",
    "chrome123",
    "chrome124",
    "safari15_5",
    "safari17_0",
]


class CurlCffiDownloadHandler:

    def __init__(self, settings: Settings):
        self.session = curl_requests.Session()
        self.session.headers.update(
            {
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Cache-Control": "no-cache",
            }
        )
        self.force_http11 = settings.getbool("CURL_CFFI_HTTP11", False)

    @classmethod
    def from_settings(cls, settings: Settings):
        return cls(settings)

    @classmethod
    def from_crawler(cls, crawler):
        handler = cls(crawler.settings)
        crawler.signals.connect(handler._close, signal=signals.spider_closed)
        return handler

    def download_request(self, request, spider):
        return threads.deferToThread(self._do_request, request, spider)

    def _close(self):
        if self.session:
            self.session.close()

    def _do_request(self, request, spider):
        method = request.method.decode() if isinstance(request.method, bytes) else request.method
        url = request.url
        headers = {k.decode(): v[0].decode() for k, v in request.headers.items()}
        body = request.body or None
        cookies = request.cookies

        alias = random.choice(_BROWSER_ALIASES)

        proxy = request.meta.get("proxy")
        req_kwargs = dict(
            method=method,
            url=url,
            headers=headers,
            data=body,
            cookies=cookies,
            impersonate=alias,
            http_version=1 if self.force_http11 else 2,
        )
        if proxy:
            req_kwargs["proxies"] = {"http": proxy, "https": proxy}

        resp = self.session.request(**req_kwargs)

        raw_headers = {}
        skip_keys = {"content-encoding", "content-length", "transfer-encoding"}
        for k, v in resp.headers.items():
            if k.lower() in skip_keys:
                continue
            raw_headers[k.lower()] = v.encode() if isinstance(v, str) else v

        return HtmlResponse(
            url=str(resp.url),
            status=resp.status_code,
            headers=raw_headers,
            body=resp.content,
            request=request,
        )
