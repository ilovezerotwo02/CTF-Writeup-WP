#!/usr/bin/env python3
"""
喧宾夺主的信号 — EXP
====================
MISC 杂项 CTF 解题脚本

解题思路：声东击西
  - UDP 组播是「东」(噪声)，TCP 才是「西」(真正的攻击指令)
  - ZIP 密码隐藏在 UDP 广播中
  - 图片用 LSB 隐写了 flag

用法：
  pip install scapy pillow pyzipper
  python 喧宾夺主的信号exp.py
"""

import base64
import json
import io
import os
import struct

from scapy.all import *
from PIL import Image


PCAP = "attachment-17.pcapng"
EXTRACT_DIR = "extracted"


def main():
    # ——————————————————————————————————————————————
    # 1. 读取 pcapng 流量
    # ——————————————————————————————————————————————
    print("[*] 读取 pcap 文件...")
    packets = rdpcap(PCAP)

    # 分类：1500 UDP + 9 TCP
    udp_packets = [p for p in packets if UDP in p]
    tcp_packets = [p for p in packets if TCP in p and Raw in p]

    print(f"    总包数: {len(packets)}")
    print(f"    UDP (组播噪声): {len(udp_packets)}")
    print(f"    TCP (含数据):   {len(tcp_packets)}")

    # ——————————————————————————————————————————————
    # 2. 从 TCP 中提取加密 ZIP
    #    这是「声东击西」中的「西」— 真正的攻击
    # ——————————————————————————————————————————————
    print("\n[*] 提取 TCP POST 请求中的加密 ZIP...")
    tcp_raw = tcp_packets[0][Raw].load
    print(f"    TCP 原始数据:\n{tcp_raw[:200].decode(errors='replace')}\n    ...")

    # 解析 HTTP 请求体 (JSON)
    body = tcp_raw.split(b'\r\n\r\n')[1]
    data = json.loads(body)
    zip_b64 = data['instruction']
    zip_data = base64.b64decode(zip_b64)

    print(f"    加密 ZIP 大小: {len(zip_data)} bytes")

    # ——————————————————————————————————————————————
    # 3. 从 UDP 组播噪声中提取 ZIP 密码
    #    提示: "在那些看似无意义的广播中，藏着钥匙"
    # ——————————————————————————————————————————————
    print("\n[*] 扫描 UDP 组播包寻找密码...")
    password = None
    for p in udp_packets:
        if Raw in p and b'=' in p[Raw].load:
            raw = p[Raw].load
            password = base64.b64decode(raw).decode()
            print(f"    发现带 '=' 的 UDP 包: {raw} -> {password}")

    assert password is not None, "[!] 未找到密码!"
    print(f"    ZIP 密码: {password}")

    # ——————————————————————————————————————————————
    # 4. 解密 ZIP (AES-256)
    # ——————————————————————————————————————————————
    print("\n[*] 解密 ZIP...")
    import pyzipper  # 支持 AES 加密的 ZIP

    os.makedirs(EXTRACT_DIR, exist_ok=True)
    with pyzipper.AESZipFile(io.BytesIO(zip_data)) as zf:
        zf.setpassword(password.encode())
        zf.extractall(EXTRACT_DIR)

    img_path = os.path.join(EXTRACT_DIR, "image.png")
    print(f"    解密成功: {img_path}")

    # ——————————————————————————————————————————————
    # 5. LSB 隐写提取 Flag
    #    图片是 100×100, 只有 8 种颜色
    #    RGB 各通道仅 LSB 不同 => 3 bits/pixel
    # ——————————————————————————————————————————————
    print("\n[*] LSB 隐写提取...")
    img = Image.open(img_path)
    px = img.load()
    width, height = img.size

    print(f"    图片尺寸: {img.size}")
    print(f"    像素总数: {width * height}")

    # 从每个像素的 R, G, B 通道提取 LSB
    bits = []
    for y in range(height):
        for x in range(width):
            r, g, b = px[x, y]
            bits.append(str(r & 1))   # R 通道 LSB
            bits.append(str(g & 1))   # G 通道 LSB
            bits.append(str(b & 1))   # B 通道 LSB

    # 每 8 bit 转换成一个字节
    flag_bytes = bytes(
        int(''.join(bits[i:i+8]), 2)
        for i in range(0, len(bits) - 7, 8)
    )

    # 定位 flag
    start = flag_bytes.find(b'ISCC{')
    end = flag_bytes.find(b'}', start) + 1
    flag = flag_bytes[start:end].decode()

    print(f"\n{'='*50}")
    print(f"[+] FLAG: {flag}")
    print(f"{'='*50}")

    return flag


if __name__ == "__main__":
    main()
