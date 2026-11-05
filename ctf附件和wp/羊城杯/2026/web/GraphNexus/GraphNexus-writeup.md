# GraphNexus CTF 解题报告

## 结果

目标：`1.14.76.59:17542`

Flag：

```text
DASCTF{32427948461411035398641214819788}
```

## Scope 摘要

- 授权场景：CTF 沙盒
- 目标：`1.14.76.59:17542`
- 覆盖面：Web、WebSocket、自定义二进制协议、H2 查询引擎
- 详细 scope：`../scope.md`

## 解题路径

1. 访问 `/graph`，从页面注释恢复 WebSocket 端点 `/ws/collab` 和 NexusFrame 格式：
   `MAGIC(4B) + OPCODE(1B) + LENGTH(4B, big-endian) + PAYLOAD`。
2. 连接后接收 `HELLO (0x01)`，发送空 `SUBSCRIBE (0x03)`，服务端返回
   `permissions=read,query,export,import`。
3. 发送 `QUERY (0x05)`，DSL 错误提示泄露 `SQL(query)` 命令。
4. 通过 `SQL(...)` 查询 H2 `INFORMATION_SCHEMA` 和应用表，确认 SQL 可直接执行，并观察到
   `GRAPH_USERS` 等表。
5. 使用 H2 `CREATE ALIAS ... AS $$...$$` 创建 Java 别名，执行系统命令。
6. `/flag.txt` 对 `appuser` 不可读，但根目录存在 SUID `/readflag`；调用它得到 flag。

## 最小复现

```powershell
python.exe D:\文档\ChatGPT\yasctf\work\GraphNexus\notes\solve.py
```

成功输出的最后一行包含：

```text
DASCTF{32427948461411035398641214819788}
```

## 关键证据

- `E-001`: NexusFrame 握手、session token 和订阅权限。
- `E-002`: 未知 DSL 命令错误直接泄露 `SQL(query)`。
- `E-003`: H2 查询确认应用表和管理员 API token。
- `E-004`: `CREATE ALIAS` 执行命令并通过 SUID `/readflag` 读取 flag。

## Evidence -> Finding -> Path

### F-001

- title: WebSocket query channel exposes unrestricted H2 SQL
- severity: critical
- category: vuln
- status: validated
- evidence_ids: [E-001, E-002, E-003, E-004]
- location: `ws://{target_ip}:{port}/ws/collab`, `QUERY (0x05)`
- impact: Java alias creation enables OS command execution and flag recovery.
- confidence: high

### P-001

- title: NexusFrame to flag
- path_type: solve
- start: `/graph`
- goal: recover the flag
- steps:
  1. Read the WebSocket endpoint and frame layout from `/graph` - evidence: E-001 - finding: none
  2. Send `HELLO`/`SUBSCRIBE`, then `QUERY` - evidence: E-001,E-002 - finding: F-001
  3. Execute H2 `CREATE ALIAS` Java code - evidence: E-003,E-004 - finding: F-001
  4. Invoke `/readflag` through the alias - evidence: E-004 - finding: F-001

## 根因

WebSocket 查询通道将未认证或弱认证会话直接连接到 H2 SQL 执行器，并允许 `CREATE ALIAS`。H2 的 Java 源别名能力导致应用进程获得任意命令执行能力。

## 修复建议

- 将查询 DSL 与 SQL 执行彻底隔离，禁止客户端提交任意 SQL。
- 禁止 `CREATE ALIAS`、脚本化别名和危险 H2 管理语句。
- WebSocket 建立后强制绑定真实用户身份和服务端权限，不以订阅动作授予权限。
- 移除容器内 SUID `readflag` 类高权限辅助程序，并使用最小权限运行应用。
- 管理员 token 和密码哈希不得通过图谱查询接口返回。
