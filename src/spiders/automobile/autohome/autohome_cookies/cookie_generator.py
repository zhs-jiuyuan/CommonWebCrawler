#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie 生成器 — 完整 Cookie 字典生成

支持两种来源的合并:
  1. 客户端 JS 生成: _ac, __ah_uuid_ng, cookieCityId, area, ahpvno, v_no, ref
  2. 服务端 Set-Cookie: sessionid, visit_info_ad, sessionvid, autoid, sessionip
"""

import uuid
from datetime import datetime
from typing import Dict, Optional

from ._ac_generator import generate_ac


class CookieGenerator:
    """
    汽车之家 Cookie 生成器。

    可纯本地生成，也可合并服务端下发的 Cookie。
    """

    # 服务端下发的 cookie 名称（本地生成时用 UUID 占位）
    SERVER_SET_COOKIES = {
        "sessionid",
        "visit_info_ad",
        "sessionvid",
        "autoid",
        "sessionip",
    }

    def __init__(self, city_id: str = "510100", area_id: str = "510104"):
        """
        Args:
            city_id: 城市编码 (如 510100 = 成都)
            area_id: 区县编码 (如 510104)
        """
        self.city_id = city_id
        self.area_id = area_id

        # 本地生成的 UUID
        self._user_uuid = str(uuid.uuid4()).upper()
        self._session_uuid = str(uuid.uuid4()).upper()

    # ----------------------------------------------------------------
    # 客户端 JS 生成的 Cookie (完全可本地生成)
    # ----------------------------------------------------------------

    def _generate_ac(self, is_app: bool = False) -> str:
        """生成 _ac (AES-128-GCM 加密)"""
        return generate_ac(is_app=is_app)

    def _generate_ah_uuid_ng(self) -> str:
        """生成 __ah_uuid_ng (UUID 前缀)"""
        return f"c_{self._user_uuid}"

    def _generate_city_cookie(self) -> str:
        """生成 cookieCityId"""
        return self.city_id

    def _generate_area_cookie(self) -> str:
        """生成 area"""
        return self.area_id

    def _generate_counters(self, visit_count: int) -> Dict[str, str]:
        """生成访问计数 cookie"""
        cnt = str(visit_count)
        return {"ahpvno": cnt, "v_no": cnt}

    def _generate_ref(self, now: datetime) -> str:
        """生成 ref (来源追踪)"""
        ts = now.strftime("%Y-%m-%d+%H:%M:%S.000")
        return f"0%7C0%7C0%7C0%7C{ts}%7C{ts}"

    # ----------------------------------------------------------------
    # 服务端 Set-Cookie (本地生成 UUID 占位格式)
    # ----------------------------------------------------------------

    def _generate_sessionid(self, now: datetime) -> str:
        """生成 sessionid 占位符 (格式: UUID||timestamp||0)"""
        ts = now.strftime("%Y-%m-%d+%H:%M:%S.000")
        return f"{self._user_uuid}%7C%7C{ts}%7C%7C0"

    def _generate_visit_info_ad(self, visit_count: int) -> str:
        """生成 visit_info_ad 占位符"""
        return f"{self._user_uuid}||{self._session_uuid}||-1||-1||{visit_count}"

    def _generate_sessionvid(self) -> str:
        """生成 sessionvid 占位符 (UUID)"""
        return self._session_uuid

    def _generate_autoid_placeholder(self) -> str:
        """生成 autoid 占位符 (格式: 32 位 hex)"""
        return uuid.uuid4().hex

    @staticmethod
    def _generate_sessionip_placeholder() -> str:
        """生成 sessionip 占位符"""
        return "127.0.0.1"

    # ----------------------------------------------------------------
    # 主入口
    # ----------------------------------------------------------------

    def generate_all(
        self,
        visit_count: int = 1,
        is_app: bool = False,
        server_cookies: Optional[Dict[str, str]] = None,
        client_ip: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        生成完整 Cookie 字典。

        Args:
            visit_count: 访问计数
            is_app: 是否为 App 环境
            server_cookies: 服务端 Set-Cookie (通过 HTTP 截获)
            client_ip: 客户端 IP

        Returns:
            Cookie 字典，key=cookie_name, value=cookie_value
        """
        now = datetime.now()
        server = server_cookies or {}

        cookies: Dict[str, str] = {}

        # — 客户端 JS 生成 —
        cookies["_ac"] = self._generate_ac(is_app=is_app)
        cookies["__ah_uuid_ng"] = self._generate_ah_uuid_ng()
        cookies["cookieCityId"] = self._generate_city_cookie()
        cookies["area"] = self._generate_area_cookie()
        cookies["ref"] = self._generate_ref(now)
        cookies.update(self._generate_counters(visit_count))

        # — 服务端 Set-Cookie (优先使用截获的真实值) —
        cookies["sessionid"] = server.get(
            "sessionid", self._generate_sessionid(now)
        )
        cookies["visit_info_ad"] = server.get(
            "visit_info_ad", self._generate_visit_info_ad(visit_count)
        )
        cookies["sessionvid"] = server.get(
            "sessionvid", self._generate_sessionvid()
        )
        cookies["autoid"] = server.get(
            "autoid", self._generate_autoid_placeholder()
        )
        cookies["sessionip"] = server.get(
            "sessionip", client_ip or self._generate_sessionip_placeholder()
        )

        # 额外携带已截获但未在核心列表中的 cookie
        for key in ("fvlid", "ahpvno", "v_no", "ref"):
            if key in server and key not in cookies:
                cookies[key] = server[key]

        return cookies

    def to_header_string(self, cookies: Dict[str, str]) -> str:
        """将 cookie 字典转为 HTTP 请求头字符串"""
        return "; ".join(f"{k}={v}" for k, v in cookies.items())
