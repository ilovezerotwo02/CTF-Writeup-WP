---
title: "CovertChannel"
ctf: "数据安全练习"
date: 2026-05-31
category: forensics
difficulty: easy
points: 300
flag_format: "flag{...}"
author: "Codex"
---

# CovertChannel

## Summary

题目给了一份 `pcapng` 流量，表面上 `10.10.20.33` 同时发送了大量异常 ICMP 和 DNS 请求。真正的外泄链路是：

1. `ICMP -> 45.76.188.23` 的 `IP.ttl` 只取 `0/1`，按比特流还原出十六进制密文和提示语。
2. `DNS TXT secret.exfil-cdn.com.` 返回 Base64 字符串，解码后就是 AES-128 的密钥。
3. 用 `AES-ECB` 解密还原最终 flag。

## Solution

### Step 1: 提取 TTL 比特流和 DNS TXT 密钥

先过滤出两条关键流量：

- `10.10.20.33 -> 45.76.188.23` 的 ICMP Echo Request
- `10.10.20.1 -> 10.10.20.33` 中 `secret.exfil-cdn.com.` 的 DNS TXT 响应

ICMP 这条流的 984 个包里，`IP.ttl` 只有 `0` 和 `1`，可以直接按 bit 拼接；DNS TXT 响应内容是 `TW9yZVNlY3VyZUFlczEyOA==`，Base64 解码后得到密钥 `MoreSecureAes128`。

### Step 2: AES-ECB 解密

TTL 比特流按 8 bit 还原后得到：

```text
60226d3cd3cf345df0baa3c8dec0d9d225b3ff91634498db4f5a7d4452dd1a2c208d4efc9da73eb8884fb69c3b1202c5|AES-ECB, key is in DNS TXT
```

按提示使用 `AES-ECB`、密钥 `MoreSecureAes128` 解密前面的十六进制密文即可得到 flag。

```python
from base64 import b64decode
from pathlib import Path

from Crypto.Cipher import AES
from scapy.all import DNS, ICMP, IP, UDP, rdpcap


pcap = Path(r"D:\桌面\yuwang\数据安全\CovertChannel\extracted\tempdir\MISC附件\suspicious_traffic.pcapng")
packets = rdpcap(str(pcap))

key = None
for pkt in packets:
    if (
        IP in pkt
        and UDP in pkt
        and DNS in pkt
        and pkt[IP].src == "10.10.20.1"
        and pkt[DNS].qr == 1
        and pkt[DNS].qd
        and pkt[DNS].qd.qname == b"secret.exfil-cdn.com."
    ):
        key = b64decode(pkt[DNS].an.rdata[0])
        break

bits = []
for pkt in packets:
    if (
        IP in pkt
        and ICMP in pkt
        and pkt[IP].src == "10.10.20.33"
        and pkt[IP].dst == "45.76.188.23"
        and pkt[ICMP].type == 8
    ):
        bits.append(str(pkt[IP].ttl))

ttl_message = bytes(
    int("".join(bits)[i : i + 8], 2) for i in range(0, len(bits), 8)
).decode()

ciphertext_hex, _ = ttl_message.split("|", 1)
flag = AES.new(key, AES.MODE_ECB).decrypt(bytes.fromhex(ciphertext_hex)).rstrip(b"\n").decode()
print(flag)
```

输出：

```text
flag{5f356e09a565c656c6d8ae31f7973452}
```

## Flag

```text
flag{5f356e09a565c656c6d8ae31f7973452}
```
