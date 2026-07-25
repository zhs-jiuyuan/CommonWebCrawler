#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汽车之家 Cookie 生成包 — autohome_cookies
==========================================

一键生成汽车之家全站 Cookie，支持两种模式：
  - 本地生成模式：_ac, __ah_uuid_ng 等 JS 生成的 cookie 本地计算
  - 会话捕获模式：sessionid, autoid 等服务端 Set-Cookie 通过访问页面截获

用法:
    from autohome_cookies import AutoHomeCookies

    # 方式1: 纯本地生成 (适用于 treeMenu 等无需服务端 cookie 的 API)
    ah = AutoHomeCookies()
    cookies = ah.generate()           # -> Dict[str, str]

    # 方式2: 通过访问页面截获服务端 Set-Cookie (适用于需要完整 cookie 的场景)
    ah = AutoHomeCookies()
    cookies = await ah.capture()      # -> Dict[str, str]
    # 或同步版:
    cookies = ah.capture_sync()       # -> Dict[str, str]

"""

import logging
from typing import Dict, Optional

from ._ac_generator import generate_ac
from .cookie_generator import CookieGenerator
from .session import capture_cookies_sync, capture_cookies_async

__version__ = "1.0.0"
__all__ = ["AutoHomeCookies", "generate_ac", "CookieGenerator"]


class AutoHomeCookies:
    """
    汽车之家 Cookie 生成器主类。

    支持两种生成模式:
      generate()   — 纯本地生成（不发起网络请求）
      capture()    — 通过访问页面截获服务端 Set-Cookie（发起 HTTP 请求）
    """

    def __init__(
        self,
        city_id: str = "510100",
        area_id: str = "510104",
        visit_count: int = 1,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Args:
            city_id: 城市编码，默认 510100 (成都)
            area_id: 区县编码，默认 510104
            visit_count: 访问计数，默认 1
            logger: 可选的日志记录器
        """
        self.city_id = city_id
        self.area_id = area_id
        self.visit_count = visit_count
        self.log = logger or logging.getLogger(__name__)
        self._generator = CookieGenerator(city_id, area_id)

    # ---- 本地生成 ----

    def generate(self, is_app: bool = False) -> Dict[str, str]:
        """
        纯本地生成所有可本地生成的 Cookie。

        不会发起任何网络请求。服务端下发的 cookie (sessionid, autoid 等)
        会使用 UUID 占位符填充（格式正确但值非真实服务端下发）。

        适用于 treeMenu 等对 cookie 不做校验的 API。
        """
        return self._generator.generate_all(visit_count=self.visit_count,
                                             is_app=is_app)

    # ---- 会话捕获 (同步) ----

    def capture_sync(
        self,
        url: str = "https://www.autohome.com.cn/chengdu/",
        is_app: bool = False,
    ) -> Dict[str, str]:
        """
        同步版: 访问汽车之家页面，截获服务端 Set-Cookie。

        工作流程:
          1. GET url → 捕获服务端 Set-Cookie (sessionid, autoid, sessionip 等)
          2. 本地生成客户端 JS cookie (_ac, __ah_uuid_ng 等)
          3. 合并返回完整 cookie 字典

        Args:
            url: 用于捕获 cookie 的页面 URL
            is_app: 是否为 App 环境

        Returns:
            完整的 cookie 字典
        """
        server_cookies, client_ip = capture_cookies_sync(url)
        return self._generator.generate_all(
            visit_count=self.visit_count,
            is_app=is_app,
            server_cookies=server_cookies,
            client_ip=client_ip,
        )

    # ---- 会话捕获 (异步) ----

    async def capture(
        self,
        url: str = "https://www.autohome.com.cn/chengdu/",
        is_app: bool = False,
    ) -> Dict[str, str]:
        """
        异步版: 访问汽车之家页面，截获服务端 Set-Cookie。

        用法:
            cookies = await ah.capture()
        """
        server_cookies, client_ip = await capture_cookies_async(url)
        return self._generator.generate_all(
            visit_count=self.visit_count,
            is_app=is_app,
            server_cookies=server_cookies,
            client_ip=client_ip,
        )

    # ---- Cookie Header 快捷方法 ----

    def cookie_header(self, is_app: bool = False) -> str:
        """生成本地 Cookie 请求头字符串"""
        cookies = self.generate(is_app=is_app)
        return "; ".join(f"{k}={v}" for k, v in cookies.items())

    def cookie_header_sync(self, url: str = "https://www.autohome.com.cn/chengdu/",
                           is_app: bool = False) -> str:
        """同步获取完整 Cookie 请求头字符串"""
        cookies = self.capture_sync(url=url, is_app=is_app)
        return "; ".join(f"{k}={v}" for k, v in cookies.items())
