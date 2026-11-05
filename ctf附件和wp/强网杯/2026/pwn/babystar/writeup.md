# babystar Writeup

> 题目：强网杯 pwn babystar
> 目标：从模拟卫星的文件系统 `/cf/host/flag` 中读取 flag
> 服务：`nc <host> <port>`，题目无附件，容器初始化约 2 分钟

**Flag：`flag{f7df1bed-ffa6-4689-907e-b1e7140e929d}`**

## 0. TL;DR

测控站协议的最外层是 `类型字节 + 大端 u32 长度 + 载荷`：

| 帧 | 方向 | 含义 |
|---|---|---|
| C | 地面→卫星 | CCSDS 命令包 |
| F | 双向 | CFDP PDU |
| T | 卫星→地面 | CCSDS 遥测包 |
| E | 卫星→地面 | ASCII 错误文本 |

卫星本体是真实的 **NASA cFS 7.0.1（Draco）**，运行 CF(CFDP)/DS/HS/LC/HK/MD/MM/SC/SBN/SCH/TO_LAB 等应用；地面站侧有一层"有限权限"策略网关：

- C 帧：按 (MID, fcn) 白名单放行，绝大多数应用只允许 Noop/Reset；
  - TBL：额外允许 LOAD(2)/VALIDATE(4)/ACTIVATE(5)/SEND_REGISTRY(7)/ABORT_LOAD(9)，但对 LOAD 的文件名有路径白名单（只允许 `/cf/<名字>.tbl` 与 `/cf/uplink/<名字>.tbl`，basename ≤ 36 字符）；
  - MM：额外允许 PEEK(2)/DUMP_IN_EVENT(7)（但本环境 PSP 未实现内存读，形同虚设）；
  - TO_LAB：额外允许 OUTPUT_ENABLE(6)。
- F 帧：
  - Metadata 的目标文件名必须是小写 `.tbl` 结尾、不含 `/`、长度 ≤ 32 的 basename，随后被改写为 `/cf/uplink/<name>.tbl`；
  - 文件数据 PDU 默认被拦截；仅当文件内容在偏移 76 处的 40 字节表名属于白名单（实测放行 `HK.CopyTable`、`SAMPLE_APP.ExampleTable`）时才转发。
- T 帧：遥测（含 EVS 长事件文本，MID 0x0808）。
- E 帧：网关 ASCII 报错。

利用三个要点：

1. **CFDP 文件数据块重叠**可绕过网关的表名检查（首块写允许的表名，后续块覆盖为任意表名，CF 最终落盘的是后者）；
2. 借助该绕过把恶意 **HS.MsgActs_Tbl / HS.AppMon_Tbl** 上传并激活：HS 的 AppMon 在监视到"不存在的应用"时会执行 MAT 中预存的消息，消息从卫星内部 `CFE_SB_TransmitMsg` 发出，从而**绕过地面白名单**向 CF 发送 `DISABLE_ENGINE/ENABLE_ENGINE`；
3. 借助 CF 的"引擎禁用时才会导入配置表"的逻辑，在禁用期间把恶意 **CF.config_table**（轮询 `/cf/host`，目标文件名 `flag`）加载并激活，再启用引擎，卫星就会通过 CFDP 主动把 `/cf/host/flag` 下传；我们在地面收 F 帧即可重组出 flag。

## 1. 协议与 cFS 识别

连接后立刻收到大量 T 帧。T 帧载荷即 cFS 的 CCSDS 包：

```
6 字节主头 | 6 字节时间 | 4 字节对齐填充 | 载荷
```

主头 MID 采用 cFS "MsgId v1"（原始 16 位），命令 MID 形如 `0x18XX`，遥测 `0x08XX`。通过给各 MID 发 Noop（fcn=0）从 EVS 长事件的 AppName 字段识别应用：

| MID | 应用 | 说明 |
|---|---|---|
| 0x1804 | CFE_TBL | 表服务 |
| 0x1880/1881 | TO_LAB | 遥测输出 |
| 0x1882/1883 | SAMPLE_APP | 样例应用 |
| 0x1884/1885 | CI_LAB | 命令注入 |
| 0x1888/1889 | MM | 内存管理 |
| 0x188C/188D | FM | 文件管理 |
| 0x1890-1892 | MD | 内存驻留 |
| 0x189A/189B | HK | 综合健康 |
| 0x189F/18A0 | CS | 校验和 |
| 0x18A4/18A5 | LC | 限制检查 |
| 0x18A9-18AB | SC | 存储指令 |
| 0x18B3-18B5 | CF | CFDP |
| 0x18BB/18BC | DS | 数据存储 |

注册表（TBL SEND_REGISTRY + TBL SEND_HK 的 0x080C 包）还能看到表名/尺寸，如 `CF.config_table=1392`、`HS.EventMon_Tbl=416`、`HS.MsgActs_Tbl=192`、`HS.AppMon_Tbl=832` 等。

## 2. "有限权限"网关的行为

### 2.1 C 命令白名单

枚举 0x1800-0x18FF 与各 MID 的功能码，可得到白名单（除特别注明，均只允许 0/1）：

```
0x1804 TBL: 0,1,2,4,5,7,9
0x1880 TO_LAB: 0,1,6,7
0x1888 MM: 0,1,2,7
其余各应用: 0,1
0x1800/1801/1803/1805/1806(ES/EVS/SB/TIME/ES) 等核心命令全部拒绝
```

TBL LOAD 的文件名策略（用 E 帧"TBL LOAD path not permitted"做精确判定）：
- 只允许 `/cf/<name>` 或 `/cf/uplink/<name>`，其中 `<name>` 不以 `/` 开头、不以 `/` 结尾、basename ≤36 字符、且以 `.tbl` 结尾；
- `/cf/host/flag`、`/cf/uplink/../host/flag`、`/cf//a.tbl` 等全部拒绝。

### 2.2 CFDP 目标文件名策略

Metadata 的 dst LV 必须满足：纯 basename、无 `/`、≤32 字符、小写 `.tbl` 结尾；满足时网关把目标改写为 `/cf/uplink/<name>.tbl` 再交给卫星。非法时回 E：`unsafe CFDP destination filename`。

### 2.3 文件数据（FD）拦截

FD PDU 默认被静默丢弃；当文件内容（偏移 76 处）能解析出 40 字节表名时，网关按白名单判定，非法则回 E：`table not permitted`。

关键实验（固定 MD 尺寸、只改内容）表明：

```
文件长度 < 116 字节：FD 被丢弃（无 E，不落盘）
文件长度 >= 116 字节且表名非白名单：E "table not permitted"
文件长度 >= 116 字节且表名 = HK.CopyTable / SAMPLE_APP.ExampleTable：FD 被转发
```

> 116 = 64（CFE FS 头）+ 12（TBL 头固定字段）+ 40（表名）——网关只校验表名。

另外 CF 的 EOF 校验 CRC 是"32 位大端字累加和"（不是标准 CRC32），必须自己算，否则事务以 `CRC mismatch` 失败：

```python
def cfsum(data):
    r = 0
    for i in range(0, len(data), 4):
        r = (r + int.from_bytes(data[i:i+4].ljust(4, b'\0'), 'big')) & 0xffffffff
    return r
```

## 3. 漏洞一：重叠数据块绕过表名检查

网关只在数据首次累计跨过 116 字节时解析表名，此后同一事务里再用 **offset=76 的数据块覆盖表名字段**，它不会再检查；而卫星 CF 按偏移写入，最终落盘的文件是覆盖后的内容。

```
MD(size=len(file), name="x.tbl")
FD(offset=0,   前 480 字节，其中偏移 76 处填 "HK.CopyTable")   # 过网关
FD(offset=76,  真实的 40 字节表名，如 "CF.config_table")        # 覆盖
FD(offset=480, 其余内容)
EOF(size, cfsum(整个真实文件))
```

验证：上传一个表名原本为 `DS.FILTER_TBL`（默认被网关禁止）的文件，随后 `TBL LOAD /cf/uplink/x.tbl` 的事件显示
`LoadFile,file=/cf/uplink/x.tbl,tbl=DS.FILTER_TBL:...` —— 绕过成功。

## 4. 漏洞二：HS 表带来的内部命令注入

cFS HS（Health & Safety）应用允许通过表配置在特定条件下发送**原始 SB 消息**：

- `HS.AppMon_Tbl`（832B，32 项 × 26B）：`{AppName[20], NullTerm u16, CycleCount u16, ActionType u16}`。
  监视不到的应用会按 CycleCount 周期触发 ActionType 对应的动作；
- `HS.MsgActs_Tbl`（192B，8 项 × 24B）：`{EnableState u16, Cooldown u16, pad4, Msg[16]}`，
  ActionType = 3 + N 表示"发送第 N 条 MAT 消息"；
- HS 在运行中每周期调用 `CFE_TBL_Manage`，所以 TBL LOAD + VALIDATE + ACTIVATE 后新表立即生效；
- 触发动作时 `CFE_SB_TransmitMsg(&MAT.Msg, true)`，**消息的 MID 完全由我们填写**。

于是把两条 8 字节的 CF 命令藏进 MAT：

```
MAT[0] = 18 B3 C0 00 00 01 17 <cksum>   # CF CMD, fcn=23 DISABLE_ENGINE
MAT[1] = 18 B3 C0 00 00 01 16 <cksum>   # CF CMD, fcn=22 ENABLE_ENGINE
```

AMT 中放两条"监视不存在的应用"的规则（AppName=NOAPP1/NOAPP2，CycleCount=1，ActionType=4/5），
激活后 HS 会按顺序从卫星内部把这两条命令发给 CF，成功绕过地面白名单（E 通道全程无 "command not permitted"）。

## 5. 漏洞三：CF 配置表与轮询

CF 只有在**引擎禁用**时才处理配置表更新（`CF_CheckTables: if (!engine->enabled)`）。

因此链是：

1. `TBL LOAD /cf/uplink/<cf>.tbl`（恶意 CF.config_table，见下）；
2. 触发 AMT1（HS 从内部发 DISABLE_ENGINE）→ E 事件 `CF: disabled CFDP engine`；
3. `TBL VALIDATE` + `TBL ACTIVATE` CF.config_table → `CF validation successful...`、`CF Successfully Updated 'CF.config_table'`；
4. 触发 AMT2（内部发 ENABLE_ENGINE）→ `CF: enabled CFDP engine`；
5. CF 每 3 秒轮询 `/cf/host`，把 `flag` 以 CFDP class 1 下传（MD/FD/EOF → CH0 TX 0x08C2）；地面收 F 帧按偏移重组即可。

恶意 CF.config_table 镜像为 1392 字节的**本机小端**结构（注意：表镜像不是网络字节序！）：

```
u32 ticks=10, u32 rx_crc_bytes=16384, u32 local_eid=25
chan[2] (644B each):
  u32 max_out=5, u32 rx_max=5, u32 ack=3, nak=3, inactivity=30,
  u8 ack_limit=4, nak_limit=4, pad2,
  u32 mid_input=0x18C8, u32 mid_output=0x08C2, u16 depth=16, pad2,
  polldir[5] (104B each):
     u32 interval=3, u8 priority=25, u8 class=0(class1), pad2,
     u32 dest_eid=1,
     char src_dir[44]="/cf/host", char dst_dir[44]="",
     u8 enabled=1, pad3
  char sem[20]="", u8 dequeue=1, char move_dir[64]="/cf/host"
u16 chunk=480, char tmp_dir[44]="/cf/tmp", char fail_dir[44]="/cf/fail", pad2
```

（`move_dir=/cf/host` 使发送完成后"移动"到原路径而不是删除，保护 flag 文件。）

## 6. 完整利用步骤

见 `final_exploit.py`：

1. 用重叠块绕过上传 4 个文件：
   - `HS.MsgActs_Tbl`（192B，含 DISABLE/ENABLE 两条 8 字节命令）
   - `HS.AppMon_Tbl`（832B，NOAPP1→MAT[0]，NOAPP2→MAT[1]）
   - `CF.config_table`（1392B，轮询 `/cf/host`，dest_eid=1，class1）
2. TBL LOAD/VALIDATE/ACTIVATE `HS.MsgActs_Tbl`；
3. TBL LOAD `CF.config_table`；
4. 激活 AMT1 → 内部禁用 CF 引擎；
5. VALIDATE/ACTIVATE `CF.config_table`（引擎禁用时 CF 才会导入）；
6. 激活 AMT2 → 内部启用 CF 引擎；
7. 持续发 CF WAKE_UP（0x18B5，白名单允许）驱动引擎；
8. 收 F 帧，按 CFDP FD 的 offset 重组 `/cf/host/flag`。

## 7. Flag

实际运行 `final_exploit.py` 的关键输出：

```
CF RX ready (attempt 1)
== upload (gate bypass) ==
paths: ['/cf/uplink/m60833.tbl', '/cf/uplink/d60833.tbl', '/cf/uplink/e60833.tbl', '/cf/uplink/c60833.tbl']
== activate MAT ==
MAT VALID: ('CFE_TBL', 36, "HS validation successful for inactive 'HS.MsgActs_Tbl'")
MAT ACTIVE: ('CFE_TBL', 37, "HS Successfully Updated 'HS.MsgActs_Tbl'")
== disable CF engine (HS AppMon action) ==
DISABLE: ('CF', 117, 'CF: disabled CFDP engine')
== validate+activate CF config (engine disabled) ==
CF VALID:  ('CFE_TBL', 36, "CF validation successful for inactive 'CF.config_table'")
CF ACTIVE: ('CFE_TBL', 37, "CF Successfully Updated 'CF.config_table'")
== re-enable CF engine ==
ENABLE: ('CF', 116, 'CF: enabled CFDP engine')
== watch downlink ==
FD tsn=1 off=0 len=42 b'flag{f7df1bed-ffa6-4689-907e-b1e7140e929d}'
```

```
flag{f7df1bed-ffa6-4689-907e-b1e7140e929d}
```

## 8. 复现要点/踩坑记录

- 表镜像（`CF.config_table`/`HS.*`）是**本机小端内存布局**，只有 cFE 文件头/表头是大端；写反会导致 mid_input 变成非法值，CF 启用引擎时 `CreatePipe` 成功后 `Subscribe` 失败，留下 `CF_CHAN_0` 占名，之后再也无法启用引擎（整个实例只能重启）。
- CF 的 EOF 校验值是"32 位大端字累加和"，不是 CRC32；不填对会 `CRC mismatch`。
- F 通道的零长度事务可以创建空文件并验证 CF RX 是否在线，适合容器 2 分钟初始化期间做就绪探测。
- 触发 HS 动作使用的是"监视不存在的应用 + CycleCount=1"，每次表激活只触发一次，便于精确控制禁用/启用顺序。
