# 强网杯 2026·ldsvr (oldsvr) Writeup

## 0. 题目信息

- 附件：`oldsvr_4b45328a7f5ecd66b635346d68ee1975.zip`
  - `server`：ELF64 **MIPS 大端**、PIE、动态链接、stripped
  - `lib/ld64-uClibc-1.0.32.so`、`lib/libuClibc-1.0.32.so`（uClibc-ng 1.0.32）
- 远程：`nc 47.105.126.181 2883`（1883 拒绝连接）
- 结果：**flag{1ec6896ee054f9cab370a5a8473c30ee}**

本地运行：

```bash
cp lib/ld64-uClibc-1.0.32.so root/lib/ld64-uClibc.so.0
cp lib/libuClibc-1.0.32.so   root/lib/libc.so.0
cp lib/ld64-uClibc-1.0.32.so root/lib/ld64-uClibc.so.1
qemu-mips64 -L root ./server
```

题目是 xinetd/socat 风格：一次连接 = 一个进程，stdin/stdout 就是连接，`alarm(80)`。

## 1. 逆向：一个手写的 MQTT 服务

关键字符串：`MQTT`、`QWB_Client`、`QWB_Client`、16 字节常量、`LJ_/-/+B\ypts`、`QWB2026_News`。

经 IDA（MIPS 反编译器）还原，逻辑是一个极简 MQTT broker：

- `sub_439C`：主循环。先读 5 字节解析 MQTT Remaining Length，按类型分发：
  - `0x10` CONNECT -> `sub_3200` 认证
  - `0x30` PUBLISH -> `sub_3A34`（查找/更新主题表，可回显）
  - `0x80` SUBSCRIBE -> `sub_3E80`（14 项主题表）
  - `0xA0` UNSUBSCRIBE -> `sub_40CC`
  - `0xC0` PINGREQ -> 递增 `state[3]`，回 `D0 00`
- 全局状态：`calloc(1,16)`，`state[1]` 已认证、`state[2]` 已订阅 News、`state[3]` ping 计数。
- 主题表：BSS 14 项 × 32 字节 `{topic_ptr, u16 topiclen, data_ptr, u16 datalen}`。

### 1.1 认证与「预期解」密码

CONNECT 校验固定字段（`MQTT`、level 4、flags 0xC2、keepalive 0x4321），然后：

- client id 必须为 `QWB_Client`
- username 每个字节 XOR 0x1D 后必须等于 `LJ_/-/+B\ypts`
  → 实际用户名为 `QWB2026_Admin`
- password 做 MD5，与常量 `unk_6E98 ^ 0x59` 比较：

```
target = 52 2a 00 e8 8c a7 7d 1f 0b a2 f4 fd 95 4b da ec
```

**认证 bug**：比较用的是 `strncmp(digest, target, 16)`，而 `target[2] == 0x00`。strncmp 在两个字符串同时遇到 `\0` 时提前返回 0，所以**只需要 MD5(password) 的前 3 字节为 `52 2a 00`**，不需要完整 preimage。

爆破（约 2^24）：

```
password = 9kmidaaa
md5 = 522a003d76e5c9f0df9d30d861280e86   # 前 3 字节 52 2a 00
```

本地原版与远程均验证返回 `CONNACK 20 02 00 00`。

## 2. 漏洞

### 2.1 SUBSCRIBE 堆溢出（可控 272 字节）

`sub_3E80`：

```c
len = topic_length_from_packet();          // u16
buf = malloc((u16)(len + 1) + 1);          // len=0xFFFF => malloc(1)
...
if (len >= 272) len = 272;
memcpy(buf, topic_ptr, 272);               // 写 272 字节
```

topic 长度填 `0xFFFF` 时 `malloc(1)`（uClibc MINSIZE=0x20 的 chunk），却 memcpy 272 字节：
**堆溢出**，可以改后续 chunk 头与 fastbin fd。

### 2.2 UAF 回显（堆泄漏）

`sub_37D8`（PUBLISH 到 `QWB2026_News` 且 `state[2]==1 && state[3]==6`）：

```c
tmp = malloc(topiclen + datalen);  free(tmp);
if (datalen < 0x21) free(entry->data);
if (state[2]==1 && state[3]==6)
    sub_2584("QWB2026_News", entry->data, datalen);   // 释放后读，发给客户端
```

即：认证 -> 订阅 `QWB2026_News` -> 发 6 次 PINGREQ -> 发布 24 字节 payload，
服务端会把已 `free` 的 data chunk 内容当 PUBLISH 发回来（fastbin fd 泄漏 heap）。

## 3. 利用：uClibc-ng fastbin 任意写

### 3.1 分配器特性

uClibc-ng 1.0.32 的 malloc 是 dlmalloc 2.7.2（malloc-standard）的改版：

- `max_fast = 0x53`，0x20/0x30/0x40/0x50 走 fastbin；
- **malloc 从 fastbin 取块时不校验 victim 的 size**：

```c
fb = &fastbins[fastbin_index(nb)];
if ((victim = *fb) != 0) { *fb = victim->fd; return chunk2mem(victim); }
```

所以只要改掉一个已释放 fastbin 块的 `fd`，下一次同 size 的 malloc 就会返回
`fd → chunk2mem = fd + 0x10` 指定的任意地址，再由 `SUBSCRIBE` 的
`memset(dst,0,len+2); memcpy(dst,topic,len)` 完成**任意 8~34 字节写**。

### 3.2 堆布局

认证后 fastbin 里是 clientid/username/password 三块 0x20；订阅 News 用掉一块；
泄漏阶段 `sub_2610` 回显时还会临时分配 `v12/v13(0x20)`、`v16(0x40)`，
free 后留下 0x20/0x30/0x40 类残留。为了让 A/B 物理相邻，利用开始先做：

1. 订阅 5 个 drain 块（0x20×2、0x30×2、0x40×1）把残留 bin 全弹空；
2. 从 top 顺序分配：
   - Pair20：A20(0x20) 、B20(0x20)、C20(0x100，吸收溢出/放 argv)
   - Pair30：A30(0x20) 、B30(0x30)、C30(0x100，吸收溢出)
3. 用 `UNSUBSCRIBE` 按 **B 先 A 后** 释放，使 A 成为 fastbin 头，
   且 A 的物理后继正好是 B。

以泄漏到的 `temp`（0x30 chunk）为基准，实测布局固定为：

```
A20_user = temp + 0x80     B20_user = temp + 0xA0     C20_user = temp + 0xC0
A30_user = temp + 0x1C0    B30_user = temp + 0x1E0    C30_user = temp + 0x210
```

溢出（272B）从 A 开始写：

- Pair20：offset 0x18 -> B20.size=0x21；0x20 -> B20.fd=target-0x10；
  0x30/0x38 -> C20 header；0x40 -> argv[0]；0x48=NULL；0x50="/bin/sh"
- Pair30：offset 0x18 -> B30.size=0x31；0x20 -> B30.fd=target-0x10；
  0x40/0x48 -> C30 header

随后 `W1`（同 class 订阅）弹出 B，`W2`（同 class）弹出 fake chunk（target），
把 W2 的 topic 字节写到 target。

### 3.3 PIE 泄漏

heap 泄漏值 `temp` 与 PIE 基址固定相差 `0x22120`（多次实测，极偶发 `0x21110`，
若 `temp-0x22120` 非页对齐换下一个候选）。本地 gdb 多次验证：

```
pie = temp - 0x22120
```

远程 fastbin 写测试：把 `pie+0x2ce8`（PIE 内回 PINGRESP 的函数）写进
memcmp GOT，触发后收到 `D0 00`，证明 PIE 与任意写均正确。

### 3.4 远程 libc 每次连接随机：同连接去认证 oracle

远程实测 libc 地址每次连接都变（例如 `0xfff7…`、`0xf6e9…`），
之前用崩溃型 oracle 跨连接逐字节读 GOT 得到的数据不可拼接。
必须**同一条连接内**完成泄漏与利用。

构造一个**不崩、可重复**的字节预言机：

1. 用一次任意写把表中某个空 entry 改成：
   - `topic_ptr = pie + GOT(memcmp) + i`（要读的字节地址）
   - `topiclen = 1`
   - `data_ptr = pie + 0x22080`（client state 堆块）
   - `datalen = 24`
2. 发一个 `topiclen=1, payload=24 个 0` 的 PUBLISH，topic 字节 = 猜测值 c。
3. 若猜中，`memcmp` 返回 0，进入 match 分支：
   `memset(state, 0, 24)` —— `state[1]` 被清零（掉认证），**进程不崩**；
   若没猜中，什么都不发生。
4. 探测后发 PINGREQ：`state[1]==1` 回 `D0 00`，`state[1]==0` 无响应 → 命中。
   再发 CONNECT 重新认证，继续下一个 c。

把 256 次 “PUBLISH + PING + CONNECT” 一次性流水线发过去，
解析响应中 `D0 00` 的个数即可定位命中值（命中那次没有 `D0 00`），
一次连接即可快速读完一个字节。

**两个必须处理的细节（踩坑）**：

- `sub_3E80` 的 fake malloc 在返回 target 前会执行 `*fb = victim->fd`。
  若 fake chunk 就是 entry 本身，fd 读到的是 `topic_ptr`（GOT 地址），
  会把 fastbin 头污染成 GOT 地址，下一次同 class 分配直接写坏 GOT。
  → 把 fake chunk 目标前移 8 字节（写 `entry13-8`），使 fd 读到
  前一 entry 的 datalen/padding（恒 0），弹出后 fastbin 头被清 0。
- `SUBSCRIBE` 在拷贝前会 `memset(dst, 0, topiclen+2)`。
  写 entry0 的 topic 指针时只写 8 字节会把 `entry0.topiclen` 清 0，
  导致触发时 `topiclen` 不等于 12，查找直接跳过。
  → 一次写 10 字节：指针 + `0x000C`。

另外，回收 A 块靠 `UNSUBSCRIBE` 匹配恶意订阅存下的 272 字节 topic。
由于该 topic 覆盖到 B 的用户区，B 被 W1 重写、以及下一次回收时
`free(B)` 把 fastbin 头写到 B 用户区，都会改动 A 的 topic 内容，
所以回收时要按「pattern → W1 memset+memcpy → free(B) 写入的 fd」重建
这 272 字节，才能匹配成功。fd 值可由 fake chunk 目标处的旧 qword 推得
（Pair30 为 0；Pair20 第一次为原 News 主题块指针 `pie+0x220e0`）。

### 3.5 最终劫持

1. 用 Pair20 任意写把 `entry0.topic` 改成 `C20_user`（该块内容 = argv 数组：
   `{ C20_user+0x10, NULL }`，字符串 `"/bin/sh"`）。
2. 再用 Pair20 把 `memcmp` GOT 改成 `libc_base + execv(0x62fe0)`。
3. 发 PUBLISH：`type=0x30, topiclen=12, topic="/bin/sh"`。
   查找 entry0（len 12）时 `memcmp` 实际跳进 `execv`：
   - `a0` = 包内 `"/bin/sh"`
   - `a1` = `entry0.topic` = `C20_user`（argv）
   
   qemu-user 对 guest 的 execve 是**直通宿主**的，于是服务进程被替换成
   宿主机上的 `/bin/sh`，stdin/stdout 仍是题目连接 → 拿到宿主 shell。

### 3.6 一些排除过的路线

- 堆上执行 shellcode：qemu-user 会按 guest 页权限判 NX，堆/数据段不可执行
  （独立程序验证：把 shellcode 放 `.data` 再跳转必 SIGSEGV）。
- libc `system()`：在 qemu 下 uClibc 的 fork/exec 路径不可用（`touch` 无副作用）；
  `execv` 正常。
- 跨连接 oracle：远程 libc ASLR 每次连接随机，只能同连接完成。

## 4. Exploit

`exp.py`（入口）+ `exploit_same.py`（利用实现）+ `pktlib.py`（协议封装），
依赖 pwntools：

```bash
python3 exp.py        # 默认打 47.105.126.181:2883，拿到 shell 后读 /flag
```

同连接流程概要：

```
CONNECT(9kmidaaa)                      # 认证绕过
SUB News / 6×PING / PUB 24B            # UAF 回显 -> temp
pie = temp - 0x22120
drain bins; alloc Pair20/Pair30 + 吸收块
for i in 2..7:                         # 高位字节 00 00 假定
    cycle30(entry13-8, GOT+i, len=1, data=state, datalen=24)
    流水线 256×(PUB byte / PING / CONNECT)，解析命中字节
libc = GOT(memcmp) - 0x4f0d0
cycle20(entry0, C20_user + topiclen 0x000C)
cycle20(GOT(memcmp), libc+execv)
PUB topiclen=12 topic="/bin/sh"        # execv -> 宿主 /bin/sh
```

远程实际输出：

```
SHELL_OK
...
-r--r--r-- 1 0 0 38 Oct 22 08:16 flag
flag{1ec6896ee054f9cab370a5a8473c30ee}
```

## 5. Flag

```
flag{1ec6896ee054f9cab370a5a8473c30ee}
```
