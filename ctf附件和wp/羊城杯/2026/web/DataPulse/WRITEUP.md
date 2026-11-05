# DataPulse (DASCTF) — Web 完整 Writeup

## Flag

```
DASCTF{41856911396513263813290317421930}
```

来源：RCE 后执行 setuid 二进制 `/readflag`（`/flag.txt` 权限 `-r-------- root`，普通用户不可读）。

## 漏洞链（6 步）

### 1. 功能发现：任务 + Webhook
注册登录后，Dashboard 可创建分析任务，字段 `webhook_url`；另有 **Webhook Test**（`POST /tasks/<id>/retry-webhook/`，可带自定义 `url`）。
`GET /tasks/<id>/webhook-logs/` 会**回显目标响应体**（full-read SSRF）。

### 2. SSRF：URL 校验是主机名黑名单
`http://127.0.0.1/`、`http://localhost/`、`http://0.0.0.0/` → `URL validation failed`（精确匹配 hostname）。
绕过：`http://127.0.0.1.nip.io/`、`http://2130706433/`、`http://0x7f000001/`、`http://127.1/` 均可解析到 127.0.0.1。

### 3. 协议白名单包含 gopher
`http`/`https`/`gopher` 允许；`file`/`ftp`/`dict`/`data` 等拒绝。
gopher 可向任意端口发送任意字节 → 直接打 Redis 6379（HTTP 打 Redis 会断连，gopher 才是正解）。

### 4. Redis 两库
- db0：`dp:heartbeat:*`（HMAC 签名心跳，诱饵）、`celery-task-meta-*`
- db1：Django session cache，key `:1:django.contrib.sessions.cache<sid>`
  - `fake_admin_session_1/2`：`user_id=999, role=admin, _auth_user_hash=fake_hash_do_not_use` — **诱饵**（user_id 不存在 → Invalid session）
  - 伪造 `role=admin` 无效：**role 从 DB 读**，session 只用于取 `user_id`

### 5. Pickle 反序列化 RCE（根因）
`settings.py`：
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache',
                      'LOCATION': 'redis://127.0.0.1:6379/1'}}
```
- session 值是 **pickle**；unpickler 有类白名单，但 **`builtins.eval` / `builtins.exec` 放行**，`os.system` 拦截
- 经 gopher `SELECT 1` + `SET :1:django.contrib.sessions.cache<sid> <恶意pickle>`
- 带该 cookie 请求 → 反序列化时执行代码
- 利用：`eval("exec(code) or {'user_id':1,'role':'analyst'}")`（返回合法 session，不影响回显）
- 外带回显：`from django.core.cache import cache; cache.set('dp:pwned', data)` → 再经 gopher GET `:1:dp:pwned`（值本身也是 pickle）

### 6. 提权读 flag
容器内 `uid=1000(ctf)`，`/flag.txt` root-only；`/readflag` 为 `-rwsr-xr-x root`（setuid）。
RCE 执行 `/readflag` → `DASCTF{41856911396513263813290317421930}`

## 关键环境信息
- `PULSE_SECRET_SEED`（随机 md5）→ `SECRET_KEY = md5(seed)`
- 心跳 HMAC key = `settings.HEARTBEAT_HMAC_KEY`（另一条诱饵路线）
- `start.sh` 会 unset `DASFLAG` 环境变量
- Django + gunicorn + Celery(只接受 json) + Redis 7.0.15

## 利用脚本
同目录 `exploit_datapulse.py`：一键 SSRF→gopher→Redis→pickle RCE→`/readflag`。
