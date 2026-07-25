#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话捕获 — 通过 HTTP 请求截获服务端 Set-Cookie

通过访问汽车之家页面，从响应头 Set-Cookie 中提取:
  sessionid, visit_info_ad, sessionvid, autoid, sessionip 等

同时获取客户端外网 IP (sessionip 的值).
"""

from typing import Dict, Optional, Tuple

import requests

# 请求头伪装
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 需要从服务端截获的 Cookie 名称
_TARGET_COOKIES = {
    "sessionid",
    "visit_info_ad",
    "sessionvid",
    "autoid",
    "sessionip",
    "fvlid",
}


def _extract_target_cookies(session: requests.Session) -> Dict[str, str]:
    """从 Session 中提取目标 Cookie"""
    result: Dict[str, str] = {}
    for cookie in session.cookies:
        if cookie.name in _TARGET_COOKIES:
            val = cookie.value
            if val:
                result[cookie.name] = val
    return result


def _get_public_ip(session: requests.Session) -> str:
    """尝试获取客户端外网 IP"""
    try:
        resp = session.get(
            "https://httpbin.org/ip",
            timeout=5,
            headers={"Accept": "application/json"},
        )
        return resp.json().get("origin", "").split(",")[0].strip()
    except Exception:
        return ""


def capture_cookies_sync(
    url: str = "https://www.autohome.com.cn/chengdu/",
) -> Tuple[Dict[str, str], str]:
    """
    同步访问页面并截获服务端 Set-Cookie。

    工作流程:
      1. 创建 requests.Session (自动管理 cookie jar)
      2. GET url → 服务端返回 Set-Cookie → Session 自动保存
      3. 提取目标 cookie + 获取外网 IP
      4. 返回 (cookies_dict, client_ip)

    Args:
        url: 用于截获 cookie 的页面 URL

    Returns:
        (server_cookies, client_ip) 元组

    Example:
        >>> cookies, ip = capture_cookies_sync()
        >>> print(cookies["sessionid"])
        'A132BFE7-C258-42FC-...||2026-07-25 21:27:04.133||0'
    """
    session = requests.Session()
    session.headers.update(_HEADERS)

    # 发起请求，Session 自动管理 Set-Cookie
    resp = session.get(url, timeout=30)
    resp.raise_for_status()

    # 提取目标 cookie
    cookies = _extract_target_cookies(session)

    # 获取外网 IP (作为 sessionip 的后备)
    ip = cookies.get("sessionip", "") or _get_public_ip(session)

    return cookies, ip


async def capture_cookies_async(
    url: str = "https://www.autohome.com.cn/chengdu/",
) -> Tuple[Dict[str, str], str]:
    """
    异步版: 访问页面截获服务端 Set-Cookie。

    需要安装 httpx:
        pip install httpx

    用法:
        cookies, ip = await capture_cookies_async()
    """
    try:
        import httpx
    except ImportError:
        raise ImportError(
            "异步模式需要 httpx: pip install httpx"
        )

    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True) as client:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()

        # 从 httpx Cookies 提取
        cookies: Dict[str, str] = {}
        for cookie in client.cookies.jar:
            if cookie.name in _TARGET_COOKIES:
                cookies[cookie.name] = cookie.value

        # 获取外网 IP
        ip = cookies.get("sessionip", "")
        if not ip:
            try:
                r = await client.get(
                    "https://httpbin.org/ip",
                    timeout=5,
                    headers={"Accept": "application/json"},
                )
                ip = r.json().get("origin", "").split(",")[0].strip()
            except Exception:
                pass

        return cookies, ip
