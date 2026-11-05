"""通用交互驱动：按顺序把答案喂给 duel_arena，并把每步输出打出来。
用法: python probe.py exe ans1 ans2 ...   (^\n 表示直接回车)
"""
import sys
from pwn import *
context.log_level = 'error'

exe = sys.argv[1]
ans = [a.replace('\\n', '') for a in sys.argv[2:]]

PROMPTS = ['选择 > ', 'Choice > ', '（y/n）', '按回车继续', '行动 > ', 'route > ', '> ']

p = process([exe], cwd='.')
buf = b''


def pump(timeout=1.0):
    global buf
    try:
        d = p.recv(timeout=timeout)
        buf += d
    except Exception:
        pass


def show(tag):
    global buf
    t = buf.decode('utf-8', 'replace')
    print('=========== %s' % tag)
    print(t)
    buf = b''


pump(1.0)
show('banner')
for i, a in enumerate(ans):
    p.sendline(a.encode())
    pump(1.2)
    show('after %r' % a)
pump(1.5)
show('tail')
p.close()
