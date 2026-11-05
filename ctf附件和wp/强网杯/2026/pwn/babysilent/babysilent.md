# 强网杯 babysilent Writeup

## 1. 题目信息
- 题目：babysilent，提示“嘘~ keep silent!”
- 附件：pwn / wrapper / libc.so.6 (Ubuntu GLIBC 2.27-3ubuntu1.6) / ld-linux-x86-64.so.2
- 容器：nc 123.57.250.177 38913
- 结果：**flag{fd6b7904-b90a-4b0a-b379-7f350c28435d}**

## 2. 保护与程序逻辑
保护全开：Full RELRO / Canary / NX / PIE。

main 的关键流程（pwn 未 strip，函数名可直接看）：

```c
init();
open_flag();                            // open("flag", O_RDONLY) -> fd 3（沙箱前打开）
puts("Please input your name size: ");
int size = getnum();                    // read(0,..,15) + atoi，0 <= size <= 0x88
if (size > 0x88) exit(-1);
printf("Please input your name:\n> ");
get_input(buf, size);                   // buf = rbp-0x60，最多写 size 字节
printf("Your name is: %s\n", buf);      // 唯一的有效回显
puts("Now you have 1 choice to change your name.");
get_input(buf, size);
sleep(1);
blind();                                // close(1); close(2); setup_sandbox();
printf("there is no output right?");    // fd1 已关闭，静默
```

沙箱（seccomp-tools dump）：

```
0000: A = arch
0001: if (A != ARCH_X86_64) goto 0010
0002: A = sys_number
0003: if (A < 0x40000000) goto 0005
0004: if (A != 0xffffffff) goto 0010      ; 禁 x32
0005: if (A == read) goto 0009
0006: if (A == exit) goto 0009
0007: if (A == exit_group) goto 0009
0008: return ERRNO(1)
0009: return ALLOW
0010: return KILL                          ; 非 x86_64 直接杀
```

即**只允许 read / exit / exit_group**，且 fd1/fd2 已关闭 —— 全程无法输出，只能做时序侧信道。

wrapper：父进程 fork 后，子进程（pwn）stdin 换成 pipe，父进程把 socket 数据转发进 pipe（60s 写超时），stdout 仍是 socket。
子进程死亡后，父进程要**再写一次管道（EPIPE）**才会退出并关闭连接 —— 这个“poke 一下才断开”就是远端可观测的信道。

## 3. 漏洞与一次泄漏拿 canary + PIE

1. 栈溢出：buf 距 canary 0x58，而 size 最大 0x88，可覆盖 canary(8) + saved rbp(8) + ret(8) + 其后 0x20 字节（返回地址后仅 4 个 qword）。
2. `%s` 越界读：把 canary 最低字节覆盖成非 0（如 `'B'`），`printf("%s")` 会继续打印 canary 高 7 字节以及 saved rbp，直到遇到 0。
3. glibc 2.27 的 `__libc_start_main` 调 main 前把 rbp 设为 `__libc_csu_init`，main 开头 `push rbp`，所以 **saved rbp == &__libc_csu_init == PIE+0x2005a0**。

因此发送 `0x58*'A' + 'B' + '\n'` 一次即可同时泄漏：

- canary = `\x00` + 泄漏的 7 字节
- PIE = `u64(saved rbp 的前 6 字节 + 0x00 0x00)` - 0x2005a0（用 2MB 对齐做校验）

## 4. 绕过“返回地址后只有 4 个 qword”

main+0xc3（0x200515）有一段内联代码：

```asm
mov edx, [rbp-0x64]      ; size
lea rax, [rbp-0x60]      ; buf
mov esi, edx
mov rdi, rax
call get_input
```

返回地址填 0x200515、saved rbp 填 `PIE+0x601088` 后：

- `[PIE+0x601024]` = stdout FILE* 的高 32 位 ≈ 0x7fxx —— 一个巨大的 size
- 写入目标 = `PIE+0x601028`（.bss 可写页 0x601000~0x602000）
- 注意先把真实 canary 放到 `[PIE+0x601080]`（payload 偏移 0x58）

于是 main 会替我们把 ~3.6KB 的 ROP 链写进 .bss；main 收尾的 `leave; ret` 以 rbp=PIE+0x601088 弹出 rbp 并跳到链首。

链首再 `pop rsp; pop r13; pop r14; pop r15; ret` 二次迁移到 .bss 页中部 0x601c00，给后续 libc 调用留足栈空间（.bss 下面一页是 RELRO 只读页，栈不能越界）。

## 5. 时序侧信道 oracle

链用 ret2csu 调 GOT 里的 read，把 flag 读到 .bss 已知地址 DEST：

```
[CSUpop][rbx=0][rbp=1][r12=&GOT.read][r13=3][r14=DEST-i][r15=c1][CSUcall]
... 第二段 read(3, DEST-i+c1, c2) ...
[CSUcall 退出路径: pop rbp = DEST+0x1c ...]
[getnum]      -> eax = 阈值 T（从 stdin 读十进制）
[0x20038b]    -> cmp dword [rbp-0x1c], eax ; ja 0x200343 ; jmp 0x200393
```

- `flag_byte > T`：跳到 get_input 内层循环 `read(0, DEST+0xf, 1)` **阻塞** → 连接保持（alive）
- 否则：0x200393 处用泄漏的 canary 校验伪造栈帧 → `leave; ret` → exit@plt → 进程退出；远端 wrapper 在下一次收到字节（EPIPE）后关闭连接（dead）

对每字节做二分搜索（0x20~0x7e），并用 `T=v-1 必 alive / T=v 必 dead` 双向确认。

## 6. 踩坑记录

- **atoi 参数被覆盖**：最初把阈值字符串放在 .bss，链上调用 atoi 时指针被 .bss 栈帧污染 → 改为调用程序自带 getnum，直接读 stdin 取数值。
- **0x0a 截断**：`get_input` 以 `'\n'` 结束，payload 中任何 0x0a 字节都会截断。而读取长度 `i+1` 在 i=9 时正好是 10(0x0a) → 把 flag 读取拆成两段 read，两个计数都避开 0x0a。
- **.bss 栈空间**：链若放在 0x601090，exit 的栈会撞到 0x601000 下的只读页 → 必须二次迁移到页中部。
- **poke 写指针**：阻塞分支里 get_input 会把收到的字节写到 `[dest+4]+i`，该指针必须落在 .bss 同一可写页内，否则 poke 时 SIGSEGV。
- **远端断开检测**：wrapper 需要再写一次管道才感知子进程死亡 → 判定 dead 需要连续 poke 若干次（约 4 次内出现 FIN）。
- 每连接都是新进程，flag 偏移从 0 开始，所以第 i 字节需要先读 i+1 字节。

## 7. EXP 与运行结果

见同目录 `exp.py`（远端：`python3 exp.py`；本地：`python3 exp.py local`）。

```
[+] byte[41]='}'  ->  b'flag{fd6b7904-b90a-4b0a-b379-7f350c28435d}'
[+] FLAG = flag{fd6b7904-b90a-4b0a-b379-7f350c28435d}
```
