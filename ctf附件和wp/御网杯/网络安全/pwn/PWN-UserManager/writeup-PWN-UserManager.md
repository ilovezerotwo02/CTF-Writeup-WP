---
title: "PWN-UserManager"
date: 2026-05-30
category: pwn
difficulty: easy
points: 400
status: partial
---

# PWN-UserManager

## Summary

这是一个典型的堆 UAF 题。程序维护 `users[10]`，每个元素指向一个 `user` 结构：

```c
struct user {
    char *data;
    void (*p)(char *);
    size_t size;
};
```

核心问题在 `Delete()`：

1. `free(users[id]->data);`
2. `free(users[id]);`
3. 没有把 `users[id]` 置空

因此删除后 `users[id]` 仍然是悬垂指针。后续 `Login()` / `Edit()` 会继续把它当成有效对象使用。

## Key Reverse Points

反汇编恢复出的关键逻辑如下：

### Register

- `id` 范围检查：`0 <= id <= 9`
- `size` 范围检查：`0 <= size <= 0x100`
- `buf = malloc(size)`
- `read(0, buf, size)`
- `u = malloc(0x18)`
- `u->data = buf`
- `u->p = show`
- `u->size = size`
- `users[id] = u`

### Login

- `id` 范围检查：`0 <= id <= 9`
- `len` 范围检查：`0 <= len <= 0xff`
- `read(0, pass, len)`
- `strcmp(pass, users[id]->data)`
- 相等时调用 `users[id]->p(users[id]->data)`

### Edit

- 直接执行 `read(0, users[id]->data, users[id]->size)`

### Delete

- 先 `free(data)`，再 `free(user)`
- 不清空 `users[id]`

## Exploit Idea

### Stable UAF Primitive

如果把两个用户的密码长度都设置成 **不等于 `0x18`** 的同一个 fastbin 大小，那么：

1. `Delete(0)`
2. `Delete(1)`

此时：

- `users[1]` 指向已经释放的 `user1`
- 因为 `user1` 被 free 后首 qword 会被改成 fastbin fd
- 这里要注意：**fastbin fd 指向的是下一个 chunk header，不是用户区指针**
- 所以 `users[1]->data` 实际会变成 `user0_chunk_header`

于是：

- `Edit(1)` 等价于“从 `user0` 的 chunk header 开始写数据”
- 真正的 `user0` 结构体在这个地址后 `0x10` 字节处
- `Login(0)` 会把这个被伪造后的结构体当真，并执行：

```c
fake_user->p(fake_user->data);
```

这就是任意单参数函数调用原语。

### ASLR-Off Intended Chain

如果运行环境关闭了 ASLR，这题可以非常直接地打：

1. 建两个用户，长度取同一 fastbin，但不要用 `0x18`
2. `Delete(0)`、`Delete(1)`
3. `Edit(1)` 写入：
   - 前 `0x10` 字节：任意填充，用来覆盖 `user0` chunk header
   - 再写伪造 `user0` 结构：
     - `data = "sh"` 或 `"/bin/sh"` 的固定地址
     - `p = system`
     - `size` 任意
4. `Login(0)`，输入与 `data` 指向字符串相同的密码
5. 触发 `system(data)`

这条链不需要栈溢出，也不需要改 GOT。

## Fastbin Notes

如果密码长度取 `0x18`，密码块和 `user` 结构块会落进同一个 fastbin，`Delete` 两次再重复 `Delete` 还可以做经典 fastbin dup。这个方向能做更复杂的 chunk 重叠，但这题实际上只靠“悬垂指针 + fastbin fd 改首字段”就够形成核心利用原语。

## Practical Blockers I Hit

### 1. 本地现代 glibc 与附件 libc 不一致

附件给的是 `libc-2.23.so`，但本机 `ubuntu-24` 默认运行时不是 2.23。没有配套 `ld.so`，所以我没法在完全一致的本地环境里直接复现实战地址。

### 2. 远端当前不可交互

在 `2026-05-30` 实测连接：

- `120.27.146.76:21125`

服务一建立 TCP 连接就立即关闭，没有正常菜单返回，所以现在没法从远端直接拿 flag。

### 3. 这个程序的 `scanf("%d")` 后紧跟 `read()`

脚本交互时很容易遇到：

- 多余分隔符被 `read()` 吃掉
- 或者 `read()` 短读导致后续 payload 残留进菜单

所以真正下 exploit 时，交互层需要按目标环境再微调。

## Conclusion

结论是：

1. **题目的漏洞逻辑完全成立**
2. **核心利用原语已经明确**：`Edit(1)` 从 freed `user0` 的 chunk header 开始写，补齐 `0x10` 偏移后，`Login(0)` 触发伪造函数指针
3. **如果远端 ASLR 关闭，这题大概率就是秒 system**
4. **如果远端 ASLR 开启，则还需要补一个地址泄露步骤**
5. **当前附件本身没有直接给出 flag，且远端服务现在不可用，所以今天这个时间点没法实际出远端 flag**
