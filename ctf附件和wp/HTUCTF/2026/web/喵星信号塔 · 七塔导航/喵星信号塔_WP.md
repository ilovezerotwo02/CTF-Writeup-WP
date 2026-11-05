# 喵星信号塔 · 七塔导航 — Writeup

**题目类别：** Web（HTTP 协议）  
**目标：** `http://103.163.47.230:32854/`（Server: `MeowSignal/1.0 Python/3.12.15`，一次解出动态容器）  
**Flag：** `HTUCTF{2999bbc1-1aab-45b5-a34a-7aad5f53c932}`

## 题目分析

Flask 风格的七关题，每关一颗 base64 星核碎片。**七颗碎片按 1→7 顺序原文拼接**，提交到 `/tower/vault`（表单字段 `answer`），服务端自行校验。

> 校验技巧：七段各自 base64 解码后拼起来就是完整 flag，可用来交叉验证拼接是否正确。

## 七关解法

| # | 路由 | 考点 | 做法 | 碎片 |
|---|---|---|---|---|
| 1 | `/tower/echo` 回响塔 | 查询串 + HTML 注释 | `GET ?code=MEOW7`，碎片在响应源码的 `<!-- -->` 注释里 | `SFRVQ1RG` |
| 2 | `/tower/beacon` 信标塔 | POST 表单 | "海上为迷航者引路、长明不灭的灯" = lighthouse，`POST signal=lighthouse` | `ezI5OTli` |
| 3 | `/tower/ghost` 幽影塔 | 请求头伪装 | 头 `X-Forwarded-For: 127.0.0.1`，碎片藏在**响应头** `X-Star-Core: CORE3=xxx` | `YmMxLTFh` |
| 4 | `/tower/mirror` 镜塔 | 前端混淆 | `User-Agent: MeowBrowser`，碎片在 `<script>eval(String.fromCharCode(...))`，还原后是 `console.log("★ 星核碎片 4 号：xxx")` | `YWItNDViNQ==` |
| 5 | `/tower/badge` 徽章塔 | Cookie | `Cookie: user=star_cat`（cookie 又名"小饼干"，身份"星猫"） | `LWEzNGEt` |
| 6 | `/tower/compass` 罗盘塔 | Referer | `Referer: http://moonbase/launch` | `N2FhZDVm` |
| 7 | `/tower/void` 虚空塔 | HTTP 方法 | 必须用 **`PUT`**，body 为 `rebirth`（以"覆"代"取"） | `NTNjOTMyfQ==` |

拼接后 base64 解码即得 flag：

```bash
echo -n 'SFRVQ1RGezI5OTliYmMxLTFhYWItNDViNWEtYTM0ZS03YWFkNWY1M2MyM30=' | base64 -d
# HTUCTF{2999bbc1-1aab-45b5-a34a-7aad5f53c932}
```

## 踩坑记录

1. **手工拼接易敲错**：曾把第 2 段 `ezI5` 误敲成 `e3I5`，导致 `/tower/vault` 校验失败。拼接完先做一次 base64 解码自检，能立刻发现错误。
2. **碎片不只在 body 里**：第 3 关在响应头、第 4 关在 JS 混淆代码里，只 `curl` 看 body 会漏；用 `curl -i` 看全响应。
3. **第 7 关方法名是题眼**：常规 GET/POST 都回同一句提示，换 `PUT` 才放行。

## Burp 复现（七关完整报文）

> 目标 `103.163.47.230:32854`，换容器只改 `Host`。
> 全部用 **Repeater**：先 `GET /` 抓一条，之后改方法和头即可。
> 每关的碎片位置见上表（**第 3 关在响应头、第 4 关在 JS 里**，所以要看 Response 的 **Raw**，
> 别只看 Render）。

### 第 1 关 · 回响塔

```http
GET /tower/echo?code=MEOW7 HTTP/1.1
Host: 103.163.47.230:32854
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

Response 源码注释里：`<!-- ★ 星核碎片 1 号：SFRVQ1RG -->` → 碎片 `SFRVQ1RG`

### 第 2 关 · 信标塔（POST 表单）

```http
POST /tower/beacon HTTP/1.1
Host: 103.163.47.230:32854
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 20
Connection: close

signal=lighthouse
```

→ 碎片 `ezI5OTli`

### 第 3 关 · 幽影塔（请求头伪装，碎片在**响应头**）

```http
GET /tower/ghost HTTP/1.1
Host: 103.163.47.230:32854
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
X-Forwarded-For: 127.0.0.1
Accept: */*
Connection: close

```

```http
HTTP/1.1 200 OK
X-Star-Core: CORE3=YmMxLTFh
```

→ 碎片 `YmMxLTFh`

### 第 4 关 · 镜塔（UA 伪装，碎片在 JS 混淆里）

```http
GET /tower/mirror HTTP/1.1
Host: 103.163.47.230:32854
User-Agent: MeowBrowser
Accept: */*
Connection: close

```

Response 的 `<script>` 里是 `eval(String.fromCharCode(...))`，还原后：
`console.log("★ 星核碎片 4 号：YWItNDViNQ==")` → 碎片 `YWItNDViNQ==`

### 第 5 关 · 徽章塔（Cookie）

```http
GET /tower/badge HTTP/1.1
Host: 103.163.47.230:32854
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Cookie: user=star_cat
Accept: */*
Connection: close

```

→ 碎片 `LWEzNGEt`

### 第 6 关 · 罗盘塔（Referer）

```http
GET /tower/compass HTTP/1.1
Host: 103.163.47.230:32854
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Referer: http://moonbase/launch
Accept: */*
Connection: close

```

→ 碎片 `N2FhZDVm`

### 第 7 关 · 虚空塔（必须 PUT）

```http
PUT /tower/void HTTP/1.1
Host: 103.163.47.230:32854
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 7
Connection: close

rebirth
```

> Repeater 里改方法：右键请求区 → **Change request method** → PUT。
> GET/POST 都回同一句提示，只有 PUT 放行。

→ 碎片 `NTNjOTMyfQ==`

### 提交：拼接后 POST 到 `/tower/vault`

七段按 1→7 顺序**原文拼接**（注意第 2 段是 `ezI5OTli`，别敲成 `e3I5...`）：

```
SFRVQ1RGezI5OTliYmMxLTFhYWItNDViNWEtYTM0ZS03YWFkNWY1M2MyM30=
```

```http
POST /tower/vault HTTP/1.1
Host: 103.163.47.230:32854
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 76
Connection: close

answer=SFRVQ1RGezI5OTliYmMxLTFhYWItNDViNWEtYTM0ZS03YWFkNWY1M2MyM30%3D
```

（`=` 在表单里最好编码成 `%3D`。）Response 返回 flag：

```
HTUCTF{2999bbc1-1aab-45b5-a34a-7aad5f53c932}
```

> 自检技巧：把拼好的串 base64 解码（`echo -n '...' | base64 -d`），
> 能直接解出完整 flag 就说明七段顺序和内容都对，再提交就不会白跑。
>
> `solve_meow7.py` 只是把上面 8 条请求自动化（纯标准库）。
