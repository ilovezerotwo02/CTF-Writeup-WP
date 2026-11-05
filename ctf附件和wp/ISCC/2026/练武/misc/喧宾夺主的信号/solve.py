#!/usr/bin/env python3
"""
CTF Challenge: 喧宾夺主的信号 (MISC)
"声东击西" — UDP 组播是「东」(噪声)，TCP 才是「西」(真正的攻击)

Step 1: 分析 pcapng，发现 1500 个 UDP 组播包 + 9 个 TCP 包
Step 2: TCP 中提取加密 ZIP（base64 编码的 instruction 字段）
Step 3: UDP 组播噪声中找到含 "=" 的包，base64 解码得密码
Step 4: 解密 ZIP 得到 image.png（100×100，8 色，LSB 隐写）
Step 5: 提取 RGB 各通道 LSB，拼接得 flag
"""

import base64
import json
import io

from scapy.all import *
from PIL import Image


PCAP = "attachment-17.pcapng"


def main():
    # ── 1. 读取流量 ──
    packets = rdpcap(PCAP)
    print(f"[+] 总包数: {len(packets)}")

    tcp_packets = [p for p in packets if TCP in p and Raw in p]
    udp_packets = [p for p in packets if UDP in p]

    # ── 2. 从 TCP POST 请求提取加密 ZIP ──
    tcp_raw = tcp_packets[0][Raw].load
    # 解析 HTTP body 中的 JSON
    body = tcp_raw.split(b'\r\n\r\n')[1]
    data = json.loads(body)
    zip_data = base64.b64decode(data['instruction'])
    print(f"[+] 加密 ZIP 大小: {len(zip_data)} bytes")

    # ── 3. 从 UDP 组播噪声中提取 ZIP 密码 ──
    # 1500 个 UDP 包中，4 个包含 "=" base64 填充（位置 200/500/800/1100）
    password = None
    for p in udp_packets:
        if Raw in p and b'=' in p[Raw].load:
            password = base64.b64decode(p[Raw].load).decode()
            print(f"[+] UDP 包密码: {password}")
            break
    assert password is not None, "未找到密码"

    # ── 4. 解密 ZIP（AES 加密）──
    import pyzipper
    with pyzipper.AESZipFile(io.BytesIO(zip_data)) as zf:
        zf.setpassword(password.encode())
        zf.extractall("extracted")
    print("[+] ZIP 解密成功")

    # ── 5. LSB 隐写提取 flag ──
    img = Image.open("extracted/image.png")
    pixels = list(img.getdata())

    bits = []
    for r, g, b in pixels:
        bits.append(str(r & 1))   # R 通道 LSB
        bits.append(str(g & 1))   # G 通道 LSB
        bits.append(str(b & 1))   # B 通道 LSB

    # 每 8 bit 组成一个字节
    flag_bytes = bytes(
        int(''.join(bits[i:i+8]), 2)
        for i in range(0, len(bits) - 7, 8)
    )

    # 定位 flag
    start = flag_bytes.find(b'ISCC{')
    end = flag_bytes.find(b'}', start) + 1
    flag = flag_bytes[start:end].decode()
    print(f"\n[+] FLAG: {flag}")

    return flag


if __name__ == "__main__":
    main()
