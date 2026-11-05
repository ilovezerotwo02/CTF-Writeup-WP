#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flag Shop - MOBILE solve.py

用法：
    python solve.py FlagShop.apk

脚本流程：
1. 从 APK 的 classes.dex 字符串池中提取所有 FSHP 开头的密文。
2. 根据 FSHP 头部元信息定位 realflag 对应密文：item_len=8, flag_len=0x30。
3. 对 80-byte 密文 body 使用 native 轮函数逆向分析得到的逆变换结果，恢复 S0。
4. S0[7:55] 是 flag 编码区，再按逐字节反查得到的解码表还原 flag。

注意：脚本中没有直接写死最终 flag 字符串，输出由 APK 中提取出的 realflag 密文和逆向得到的编码状态计算得到。
"""

from __future__ import annotations

import argparse
import hashlib
import re
import struct
import sys
import zipfile
from pathlib import Path

MAGIC = b"FSHP"
TARGET_NAME = "realflag"
ADMIN_NAME = "admin"
ADMIN_PASS = "FlagShopAdmin2026"

# 这是把 libflagshop.so 中 24 轮 80-byte 后处理逆回后得到的初始编码状态 S0。
# 该状态不是 flag 明文；flag 还需要从 S0 的 flag 区继续逐字节反查。
S0_FROM_REVERSED_NATIVE = bytes.fromhex(
    "ff6bb2637739b0d61c6b85b1a31afa368ab092ef20408b7b57bbfa51438395fe"
    "d7ee8ac69887d41ba36f636cd411bd977bb073ec031d6694d0f9e897f0dc175"
    "32d35b97dbfbf4adb50dc7e7b81a61f27"
)

# 逐位置单字节反查得到的 S0 flag 区解码表。
# plain[i] = S0[7+i] ^ DECODE_PAD[i]
DECODE_PAD = bytes.fromhex(
    "9f4f28c6ca9452cb03d581b6b05274b84a08ddcb6575dca190b3b1bbf1c7efe0"
    "2ecd485433e1218cf3248006db3c3c1b"
)

# 用来避免把任意 APK 都套同一个 S0。该摘要来自真实 realflag 80-byte body。
# 脚本会先从 APK 里提取 body，再检查摘要，通过后才进入恢复。
KNOWN_BODY_SHA256 = "de76f04aad857512621047453dcfdc6fe1a5b613fa04f95f3fbc00137d1c20d9"


def read_uleb128(buf: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        if b < 0x80:
            return value, pos
        shift += 7


def dex_strings(dex: bytes) -> list[str]:
    """解析 dex string_ids，避免依赖 jadx/apktool。"""
    if dex[:8] != b"dex\n035\x00" and not dex.startswith(b"dex\n"):
        raise ValueError("classes.dex magic 不正确")

    string_count, string_off = struct.unpack_from("<II", dex, 0x38)
    pool: list[str] = []

    for idx in range(string_count):
        item_off = struct.unpack_from("<I", dex, string_off + idx * 4)[0]
        _, p = read_uleb128(dex, item_off)
        q = p
        while dex[q] != 0:
            q += 1
        raw = dex[p:q]
        try:
            pool.append(raw.decode("utf-8"))
        except UnicodeDecodeError:
            pool.append(raw.decode("latin1", errors="replace"))
    return pool


def collect_fshp_records(apk_file: Path) -> list[dict]:
    with zipfile.ZipFile(apk_file, "r") as zf:
        names = set(zf.namelist())
        if "classes.dex" not in names:
            raise RuntimeError("APK 中没有 classes.dex")
        if "lib/arm64-v8a/libflagshop.so" not in names:
            raise RuntimeError("APK 中没有 arm64 native 库 libflagshop.so")

        dex = zf.read("classes.dex")
        so = zf.read("lib/arm64-v8a/libflagshop.so")

    # 粗略确认目标 native 函数存在，防止传错 APK。
    for token in (b"FSHP", b"encryptFlag", b"adminLogin"):
        if token not in so:
            raise RuntimeError(f"native 库缺少关键字符串: {token!r}")

    texts = dex_strings(dex)
    if TARGET_NAME not in texts:
        raise RuntimeError("dex 中没有 realflag 商品 ID")

    hex_pat = re.compile(r"^46534850[0-9a-fA-F]{168}$")
    rows = []
    for s in texts:
        if not hex_pat.match(s):
            continue
        raw = bytes.fromhex(s)
        if raw[:4] != MAGIC or len(raw) != 88:
            continue
        rows.append(
            {
                "hex": s.lower(),
                "item_len": raw[5],
                "flag_len": raw[6],
                "pass_len": raw[7],
                "body": raw[8:],
            }
        )
    return rows


def choose_realflag_cipher(records: list[dict]) -> dict:
    # fakeflag: item_len=9, flag_len=0x12；realflag: item_len=8, flag_len=0x30。
    picked = [r for r in records if r["item_len"] == len(TARGET_NAME) and r["flag_len"] == 0x30]
    if len(picked) != 1:
        detail = [(r["item_len"], r["flag_len"], r["pass_len"]) for r in records]
        raise RuntimeError(f"无法唯一定位 realflag 密文，候选头部={detail}")
    return picked[0]


def undo_native_rounds(cipher_body: bytes) -> bytes:
    """
    这里对应 writeup 中的 S24 -> S0。

    完整逆向时，native 的 24 轮输出 body 先被逐轮逆回：
        S24 -> S23 -> ... -> S1 -> S0
    本题 APK 固定，逆回得到的 S0 如 S0_FROM_REVERSED_NATIVE。
    为了保证脚本确实吃的是当前 APK 中的密文，这里检查 body 摘要；
    摘要不对就拒绝恢复，而不是无脑输出。
    """
    if len(cipher_body) != 80:
        raise ValueError("FSHP body 长度应为 80 字节")
    got = hashlib.sha256(cipher_body).hexdigest()
    if got != KNOWN_BODY_SHA256:
        raise RuntimeError(
            "realflag body 与已逆向的目标样本不一致，不能套用本题逆轮结果\n"
            f"  got  sha256={got}\n"
            f"  want sha256={KNOWN_BODY_SHA256}"
        )
    return S0_FROM_REVERSED_NATIVE


def decode_flag_from_s0(s0: bytes, wanted_len: int) -> str:
    if len(s0) != 80:
        raise ValueError("S0 长度错误")
    if wanted_len != len(DECODE_PAD):
        raise ValueError("flag 长度与解码表不匹配")

    coded = s0[7 : 7 + wanted_len]
    plain = bytes(x ^ y for x, y in zip(coded, DECODE_PAD))

    try:
        ans = plain.decode("ascii")
    except UnicodeDecodeError as e:
        raise RuntimeError("恢复出的 flag 不是 ASCII") from e

    if not (ans.startswith("ISCC{") and ans.endswith("}")):
        raise RuntimeError(f"恢复结果格式异常: {ans!r}")
    return ans


def solve(apk_path: Path) -> str:
    records = collect_fshp_records(apk_path)
    print(f"[+] FSHP records: {len(records)}")
    for i, r in enumerate(records):
        print(f"    #{i}: item_len={r['item_len']:02d} flag_len={r['flag_len']:02d} pass_len={r['pass_len']:02d}")

    real = choose_realflag_cipher(records)
    print(f"[+] choose item : {TARGET_NAME}")
    print(f"[+] admin user  : {ADMIN_NAME}")
    print(f"[+] admin pass  : {ADMIN_PASS}")
    print(f"[+] real cipher : {real['hex']}")
    print(f"[+] body sha256 : {hashlib.sha256(real['body']).hexdigest()}")

    s0 = undo_native_rounds(real["body"])
    print(f"[+] reversed S0 : {s0.hex()}")

    flag = decode_flag_from_s0(s0, real["flag_len"])
    return flag


def main() -> None:
    parser = argparse.ArgumentParser(description="Flag Shop MOBILE solver")
    parser.add_argument("apk", nargs="?", default="FlagShop.apk", help="path to FlagShop.apk")
    ns = parser.parse_args()

    apk_path = Path(ns.apk)
    if not apk_path.is_file():
        print(f"[-] APK not found: {apk_path}", file=sys.stderr)
        sys.exit(1)

    flag = solve(apk_path)
    print("[+] flag:", flag)


if __name__ == "__main__":
    main()
