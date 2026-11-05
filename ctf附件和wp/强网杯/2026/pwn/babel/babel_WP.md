# 强网杯 2026 - Reverse - babel Writeup

## 0. 题目信息

- 题目：babel（Reverse，100 分）
- 附件：`babel`（419480 字节，ELF 64-bit PIE，stripped）+ `Dockerfile`
- 容器：`nc 39.105.35.192 24682`
- **Flag：`flag{c70c6955-ee68-4815-b580-2728a1a4a1f9}`**

服务器行为：xinetd 以 `ctf` 用户运行 `/app/babel`，flag 位于 `/flag`；二进制 `main` 里用 `prctl(PR_SET_SECCOMP, ...)` 安装了 seccomp-BPF，白名单仅：
`read(0) / write(1) / exit(60) / exit_group(231) / close(3) / openat(257) / brk(12) / rt_sigprocmask(14)`，
其余 syscall 一律 `SECCOMP_RET_KILL_PROCESS`。

所以本题实质是：**逆向一个自定义虚拟机 -> 找类型混淆漏洞 -> 在 seccomp 下 ROP 执行 openat/read/write 读 /flag**。

---

## 1. 二进制初探

`file` 显示 PIE + stripped；`strings` 里同时出现两套东西：

- OCaml 运行时字符串：`Pervasives.array_bound_error`、`Marshal...`、`/home/ctf/babel/src/ext/ext.ml`；
- 自定义 VM 字符串：`babel: type trap`、`babel: bad opcode`、`babel_dispatch`。

结合 `.eh_frame`/`.data` 里的 `Ext.fn_hash`、`Ext.fn_repeat`、`Ext.fn_build` 可确认：

- **VM 解释器是 C 写的**（`main` 在 `0xd710`，分发器 `babel_dispatch` 在 `0xdb80`）；
- OCaml 只编译了 `src/ext/ext.ml`，通过 `Callback.register "babel_dispatch"` 暴露 3 个扩展函数给 VM（`Ext.fn_hash/fn_repeat/fn_build`）。

### 1.1 输入协议

`main` 启动后（0xd91c 起）：

```
loop:
  read(0, &len, 4)          ; 必须读满 4 字节
  if !(1 <= len <= 0x10000) exit
  read(0, buf=0x65e40, len) ; 必须读满
  ret = babel_dispatch(buf, len)
  if ret != 0 exit
  goto loop
```

即：**帧 = 4 字节小端长度 + 长度字节的字节码**，可连续发送多帧（VM 的全局变量、arena 跨帧保留）。之后 `close(3..63)`，再装 seccomp。

### 1.2 字节码分发

`babel_dispatch`（0xdb80）：

```
op = code[pc++];
cls = table_75f60[op];          // 256 字节, 非法为 0x40
if (cls >= 0x40) { write(2,"babel: bad opcode\n"); return -1; }
return handler[cls](&state);    // 64 项函数指针表 @0x76060
```

- 类表由 `core_init`（0xdc20）从 `.rodata` 解密/拷贝；
- 64 个 handler 指针由 `0x46b50` 处 64 字节（异或 0x5a）作置换，从 `.data.rel.ro:0x58840` 取地址。

解出后有效操作码只有 28 个（见下表），且 **没有跳转/比较指令**，是纯直线栈式字节码。

---

## 2. 虚拟机语义（逆向结论）

### 2.1 值表示

64 位 tagged value：

| 低位 | 类型 |
|---|---|
| 偶数 | 整数，值 = raw >> 1 |
| `...1` | 字符串（tag 1） |
| `...3` | 元组（tag 3） |
| `...5` | 数组（tag 5） |
| `...7` | 外部函数引用（tag 7） |
| `...9` | 缓冲区（tag 9，绑定 mmap 缓冲） |

对象值 = `(offset << 4) | tag`，offset 为 16 字节对齐的 arena 内偏移。

### 2.2 arena

`core_init` 先 `mmap(16MB)` 作为 arena（指针 @0x76260），bump 指针 @0x76268，分配位图 @0x7627c（0x20000 字节，按 16 字节粒度）。对象头 0x20 字节：

```
+0x00 u16 type   (+2 u16 mark)
+0x04 u32 count（append 用）
+0x08 u32 数据区 rounded size
+0x10 u32 length/capacity
+0x14 u32 size|0x80000000（字符串/缓冲） 或 0xffffffff（元组/数组）
+0x18 u32 数据偏移(offset+0x20) / 原生指针(内建引用) / 槽位号(缓冲)
+0x20 数据
```

### 2.3 指令表（关键）

| op | 语义 |
|---|---|
| 0x00 | nop |
| 0x01 | push imm64（raw = imm<<1） |
| 0x02 | push 字符串字面量（u32 len + bytes） |
| 0x03/0x04 | dup / drop |
| 0x05/0x06/0x07 | add / sub / mul（对 raw 取 `&~1` 后运算） |
| 0x08/0x09 | 弹 n 个值造元组(tag3)/数组(tag5) |
| 0x0a/0x0b | `容器[imm]` 读 / 写（e1b0 长度校验） |
| 0x0c/0x0d | 字符串/字节数组下标读 / 写（校验 `idx<hdr14&0x7fffffff`、`data_off+idx<cursor`） |
| 0x0e | 取长度/计数（e550） |
| 0x0f | 字符串拼接 |
| 0x10/0x11 | 读/写全局槽（256 个 @0x9f290） |
| 0x12 | 打印值（字符串原样，整数十进制+换行） |
| 0x13 | 原样输出栈顶 8 字节 |
| 0x14 | 生成 tag7 内建引用对象（hdr+0x18 = 0x59098+idx*8） |
| 0x15/0x20 | 调用内建（rdi=0x59010, rsi=argc, rdx=&vm_stack[sp]） |
| 0x16 | 申请缓冲（4MB 区，登记 8 槽 {ptr,size} @0x75e40） |
| 0x17/0x18 | 缓冲字节读/写（槽号取 hdr+0x18，需 <8） |
| **0x19** | **写 16 项表 `[0x75e40+idx*16] = {value>>1, 0x100000}`**（要求 tag9 且 hdr+0x14==-1、hdr+0x18<16） |
| 0xfe/0xff | 正常/异常结束当前帧 |

栈：`sp @0x97288`，`stack @0x97290`，上限 0xfff。

### 2.4 内建函数

`op 0x20` 会从表 `[0x75e40+0x80+idx*8]`（=0x75ec0，共 3 项）调用；OCaml 侧按 selector 分发：

- 0：`Ext.fn_hash`（FNV 变体哈希）
- 1：`Ext.fn_repeat`（字符串重复）
- 2：`Ext.fn_build`（构造模板）

它们把 VM argv 指针当作 OCaml int 传来传去，返回的 OCaml int 被 `sar 1` 后**直接当成 VM 值压栈**（不做类型检查）。

---

## 3. 漏洞链

### 3.1 长度 0 字符串造成 1 字节越界「类型字节」写

对 `len==0` 的字符串（`op 0x02` 长度 0，或 `Ext.fn_build` 内部 `make_string ""`）：

- `hdr+0x10 = 0`（长度）
- `hdr+0x14 = 0x80000001`（size = max(len,1) = 1）
- `hdr+0x18 = offset+0x20 =` 该分配块的**末尾**，也就是**下一个对象的起始地址**
- 总分配 = 0x10 头 + 0x10 = 0x20，数据区为 0

而 `op 0x0d`（字符串写）用 `hdr+0x14 & 0x7fffffff = 1` 做长度检查、用 `hdr+0x18` 做数据指针，只校验 `data_off+idx < cursor`：

```
write_byte(next_object + 0, value)   // idx = 0
```

即：**可以读写紧跟在空串后面的那个对象的头 type 字节**（实测把元组的 type 从 1 改成 0/2/4 均成功）。

### 3.2 GC 按 header type 决定是否扫描子元素

`0xe710` 是标记-压缩 GC（软上限 0x59000 初值 0x8000，每次 GC 后 +0x8000）：

- 根：VM 栈、256 个全局槽、512 项 root 表（0x96280）；
- 标记：只对 `hdr+0 type ∈ {1,2}`（元组/数组）扫描 `hdr+0x10` 个元素（+0x18 起，容量做 min 截断）；
- 压缩：搬移存活块、重建位图、把字符串 `hdr+0x18` 修正为 `dst+0x20`、把容器元素里的奇数指针按段表重定位。

**漏洞**：只要把容器的 type 字节改成 0（字符串）或 3/4（内建/缓冲），GC 就不会扫描/重定位它的元素。于是：

1. 元素里保存一个对象的旧值；
2. 该对象只被这个「伪装容器」引用 → 被 GC 当成垃圾回收；
3. 压缩后，另一个存活对象被搬到它原来的偏移；
4. 伪装容器里的旧值没有更新 → **悬垂值**，指向一个类型完全不同的对象。

GC 只会更新「根里」的值，容器元素是否更新完全取决于我们伪造的 type —— 这就是整个题的核心类型混淆。

### 3.3 从悬垂值到任意读写

把被回收对象选成 **缓冲对象**（`op 0x16`，tag 9），把搬过来的对象选成我们控制的 **元组 B**：

- 悬垂值 = `(X_old<<4)|9`，仍带 tag 9；
- 它现在指向 B：`hdr+0x14 = 0xffffffff`、`hdr+0x18 = B[0]`（可控 u32）；
- 正好满足 **`op 0x19`** 的检查（tag9、hdr14==-1、hdr18<16）。

`op 0x19` 会往 `0x75e40 + idx*16` 写 `{value>>1, 0x100000}`：

- idx 0..7 → 覆盖缓冲槽 `{ptr,size}`；
- idx 8..15 → 覆盖 0x75ec0 处的内建函数表。

于是：

- 把槽 0 的 ptr 改成任意地址、size=0x100000，再用带 `hdr+0x18=0` 的 tag9 值调 `op 0x17/0x18` → **任意地址字节读/写**；
- 把 builtin[0] 改成任意地址，再 `op 0x20` → **任意函数调用**（rdi 固定 0x59010，rsi=参数个数，rdx=VM 栈指针）。

### 3.4 地址泄露

1. **PIE 基址**：`op 0x14 idx` 产生的 tag7 对象，`hdr+0x18 = &0x59098+idx*8`（原生指针）。用上面的悬垂手法造一个「tag3 悬垂值」指向该 tag7 对象，`op 0x0a` 读元素 0 就能把该指针原样压栈，`op 0x13` 打出 8 字节 → `PIE = leak - 0x590a0`（idx=1）。
2. **libc 基址**：用槽 0 指向 `read@got = PIE+0x58d30`，`op 0x17` 逐字节读 8 字节，按 `acc=acc*256+byte` 组装 → `libc = read - 0x11bd20`（libc 2.39-0ubuntu8.9，与 Dockerfile 中 `LIBC_REV=2.39-0ubuntu8.9` 完全一致，WSL 本地同版本，偏移可直接用）。

### 3.5 控制流劫持

`op 0x20` 调用内建时：`rdi = 0x59010`（.data 内固定地址，内容我们能用字节写完全控制）、`rdx = VM 栈`。

用 `op 0x19`（idx=8）把 builtin[0] 写成 **`setcontext`**（libc+0x4a960），再把 0x59010 布置成伪 ucontext：

- `[0xa0] = rsp`，`[0xa8] = rip`；
- `[0x68]=rdi, [0x70]=rsi, [0x88]=rdx, [0x98]=rcx, [0x28]=r8, [0x30]=r9`；
- `[0xe0] = fpstate 指针`（指向一块清零区，供 `fldenv`）；
- `[0x1c0] = mxcsr = 0`。

`setcontext` 入口先做 `rt_sigprocmask`（syscall 14，白名单内），随后从 ucontext 恢复 rsp/rip/寄存器并 `ret` → **寄存器与栈完全受控**。

**ROP 链**（全部用我们通过槽 0 写进 .data 的立即数，不依赖 pop rdx）：

```
ucontext1: rdi="/flag", rsi=0, rdx=0, rsp=chain1, rip=open64@plt
chain1: pop rdi; uctx2; setcontext
ucontext2: rdi=3, rsi=flagbuf, rdx=0x200, rsp=chain2, rip=read@plt
chain2: pop rdi; uctx3; setcontext
ucontext3: rdi=1, rsi=flagbuf, rdx=0x200, rsp=chain3, rip=write@plt
chain3: pop rdi; 0; exit@plt
```

（`open64@plt = PIE+0xd380`，`read@plt=+0xd1e0`，`write@plt=+0xd610`，`exit@plt=+0xd1a0`；glibc 的 `open64` 内部走 `openat`，在白名单内。之所以用多次 `setcontext`，是因为该 libc 可执行段内没有 `pop rdx; ret` 可用。）

---

## 4. 利用流程（3 帧）

帧 1（32KB）：
1. 造 `E1(空串)/T1(元组,2)/X1(元组)/B1(op14 idx=1)`，`T1[1]=X1`，用空串把 `T1.type` 写成 0；
2. 发 0x8000 字节字面量触发第一次 GC → X1 被回收，`T1[1]` 成为悬垂值指向 B1（tag7 对象）；
3. `T1[1] → [0]` 读出 `&0x59098+8`，`op 0x13` 输出 → 外部拿到 PIE 基址。

帧 2（32KB）：
1. 同样手法，但 `X2=op 0x16` 缓冲对象、`B2` 为元组（`B2[0]=0`）；
2. 精心排布大小，让 GC 压缩后 **B2 恰好落在 X2 原偏移**（E1/T1/B1/G1 保持存活使 live 总量 = 当前 cursor，B2 下移 0x20）；
3. `T2[1]` 得到悬垂 tag9 值 → 存全局，后面复用；
4. 用它在帧内算 PIE、把槽 0 指向 `read@got` 逐字节读出 → 输出 libc 基址。

帧 3（约 5.5KB，拿到两个泄露值后按实际基址现算立即数生成）：
1. `op 0x19` 把槽 0 指向 `.data`（PIE+0x59000）；
2. 字节写构造 `/flag`、fpstate、3 个 ucontext、3 条 ROP 链；
3. `B2[0]=8` 后 `op 0x19` 把 builtin[0] 改成 `setcontext`；
4. `op 0x20 idx=0` → setcontext → open/read/write → 打印 flag。

完整 exp 见同目录 `babel_exp.py`，关键运行结果：

```
[+] leak1 a0f0af5800560000        -> PIE  base = 0x560058aa6000
[+] leak2 407ae33be3fe0000        -> libc base = 0x7f719de00000
[+] out: b'flag{c70c6955-ee68-4815-b580-2728a1a4a1f9}...'
```

---

## 5. 关键偏移速查

| 项 | 偏移 |
|---|---|
| `babel_dispatch` | 0xdb80 |
| opcode 类表 / handler 表 | 0x75f60 / 0x76060 |
| VM 栈 / sp / 全局槽 | 0x97290 / 0x97288 / 0x9f290 |
| root 表 | 0x96280 |
| arena ptr / cursor / bitmap | 0x76260 / 0x76268 / 0x7627c |
| 缓冲&内建表 | 0x75e40（缓冲 0..7，内建 8..15 @0x75ec0，计数 0x75f40） |
| tag7 对象原生指针表 | 0x59098 |
| `read@got` | 0x58d30 |
| `open64/read/write/exit@plt` | 0xd380 / 0xd1e0 / 0xd610 / 0xd1a0 |
| libc `read` / `setcontext` / `pop rdi` | 0x11bd20 / 0x4a960 / 0x10c08d |

---

## 6. 一句话总结

空串的 `data_off` 落在分配末尾、`size` 却是 1，造成对「下一个对象 type 字节」的越界写；把容器 type 改成 0 让 GC 漏掉其元素，从而留下跨 GC 的悬垂 tag9 值；该值指向被搬到该位置的元组后满足 `op 0x19` 的 `hdr14==-1` 检查，进而改写缓冲槽/内建表，拿到任意读写与任意调用，最后用 `setcontext` 做栈迁移 ROP，在 seccomp 白名单内 `openat("/flag") + read + write` 取 flag。
