#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_ac 生成器 — AES-128-GCM 加密实现

完全逆向自汽车之家页面内联 <script> 中的 function v():
  1. 生成 21 位 nanoid 随机串
  2. 插入分隔符 "0." (Web) 或 "1." (App)
  3. AES-128-GCM 加密
  4. base64url 编码

常量来源:
  Key: JAOvl2fXQKBrrIuM0LAznA (base64url → 16 bytes)
  IV:  DDQ4EHLgEHCjTxt5       (base64url → 12 bytes)
  Alphabet: nanoid 64 字符集
"""

import base64
import os
import random

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ---- 常量 ----

_ALPHABET = "useandom-26T198340PX75pxJACKVERYMINDBUSHWOLF_GQZbfghjklqvwyzrict"

# AES-GCM Key (base64url encoded, 16 bytes / 128 bits)
_KEY_B64 = "JAOvl2fXQKBrrIuM0LAznA"

# AES-GCM IV/Nonce (base64url encoded, 12 bytes / 96 bits)
_IV_B64 = "DDQ4EHLgEHCjTxt5"

# nanoid 随机串默认长度
_DEFAULT_LENGTH = 21

# 延迟初始化 (避免每次调用都解码)
_key: bytes = b""
_iv: bytes = b""


def _get_key() -> bytes:
    """获取 AES-GCM 密钥 (懒加载)"""
    global _key
    if not _key:
        _key = base64.urlsafe_b64decode(_KEY_B64 + "==")
    return _key


def _get_iv() -> bytes:
    """获取 AES-GCM IV (懒加载)"""
    global _iv
    if not _iv:
        _iv = base64.urlsafe_b64decode(_IV_B64 + "==")
    return _iv


def _nanoid(length: int = _DEFAULT_LENGTH) -> str:
    """生成 nanoid 风格随机串 (cryptographically random)"""
    mask = 63
    rand_bytes = os.urandom(length)
    return "".join(_ALPHABET[b & mask] for b in rand_bytes)


def generate_ac(is_app: bool = False, length: int = _DEFAULT_LENGTH) -> str:
    """
    生成 _ac cookie 值。

    算法:
      plaintext = nanoid[:pos] + "0." + nanoid[pos:]   (Web)
      ciphertext = AES-128-GCM(plaintext, key, iv)
      _ac = base64url(ciphertext)

    Args:
        is_app: True → 分隔符 "1."，False → 分隔符 "0."
        length: nanoid 随机串长度 (默认 21)

    Returns:
        _ac cookie 值，如 "Pia_yRmglYU34zkIb8MvyCh7BFZyeJ7_-i7vleVb_YDhiJINouwp"
    """
    # 1. 生成分隔符
    separator = "1." if is_app else "0."

    # 2. 生成 nanoid
    rand_str = _nanoid(length)

    # 3. 随机插入位置
    pos = random.randint(0, length)

    # 4. 拼接明文
    plaintext = rand_str[:pos] + separator + rand_str[pos:]

    # 5. AES-128-GCM 加密
    aesgcm = AESGCM(_get_key())
    ciphertext = aesgcm.encrypt(_get_iv(), plaintext.encode(), None)

    # 6. base64url 编码
    return base64.urlsafe_b64encode(ciphertext).decode().rstrip("=")
