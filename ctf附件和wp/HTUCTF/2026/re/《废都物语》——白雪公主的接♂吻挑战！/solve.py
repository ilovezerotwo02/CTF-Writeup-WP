"""《废都物语》——白雪公主的接♂吻挑战！ 一键通关脚本（原版 duel_arena.exe，不 patch）

完整正路：
  1) 剧情 1 -> 2 -> n -> Enter
  2) 主菜单 1 查看规则（没看过规则，选项 4 会被矮人拦住）
  3) 3 调查石棺 -> 1 Search the wall      => 解锁选项 5（纸条）
  4) 3 调查石棺 -> 2 Inspect surroundings => 解锁选项 6（壁中凹痕）
  5) 5 读纸条                             => 全局 0x12108D=1，并把 .data:0x1400E8010 改写成 'e'
  6) 6 壁中凹痕 -> 输入密钥 7391          => 解锁真正的战斗
  7) 4 开始战斗 -> 依次 2 3 1 4 连招      => "You unleashed a move beyond the rules!" 秒杀
  8) y 看 CG -> Enter                     => 打印 HTUCTF{YOU ARE AINNER！！！}
"""
import sys
import time

from pwn import *

context.log_level = 'error'
EXE = sys.argv[1] if len(sys.argv) > 1 else 'duel_arena.exe'

p = process([EXE])
OUT = []


def rd(until, tmo=8):
    d = p.recvuntil(until.encode() if isinstance(until, str) else until, tmo)
    OUT.append(d.decode('utf-8', 'replace'))
    return OUT[-1]


rd('选择 > '); p.sendline(b'1')      # 给公主献上热吻
rd('选择 > '); p.sendline(b'2')      # 由同伴献吻
rd('（y/n）'); p.sendline(b'n')      # 不看剧情 CG
rd('按回车继续'); p.sendline(b'')

rd('选择 > '); p.sendline(b'1')      # 查看挑战规则
rd('按回车继续'); p.sendline(b'')

rd('选择 > '); p.sendline(b'3')      # 调查石棺
rd('Choice > '); p.sendline(b'1')    # Search the wall -> 解锁纸条
rd('按回车继续'); p.sendline(b'')

rd('选择 > '); p.sendline(b'3')      # 再调查一次
rd('Choice > '); p.sendline(b'2')    # Inspect the surroundings -> 解锁凹痕
rd('按回车继续'); p.sendline(b'')

rd('选择 > '); p.sendline(b'5')      # 读纸条（必须！它顺手把 0x1400E8010 改成 'e'）
rd('按回车继续'); p.sendline(b'')

rd('选择 > '); p.sendline(b'6')      # 壁中凹痕
rd('hidden route > '); p.sendline(b'7391')   # .rdata:0x1400ED9AC "mick" ^ 0x5A
rd('按回车继续'); p.sendline(b'')

rd('选择 > '); p.sendline(b'4')      # 正式开始战斗
rd('行动 > ')
for a in '2314':                     # 连招表 .rdata:0x1400ED9A8 = 02 03 01 04
    p.sendline(a.encode())
    if a != '4':
        rd('行动 > ')

rd('（y/n）'); p.sendline(b'y')      # 看失败 CG（CG 会弹图片窗口）
rd('按回车继续'); p.sendline(b'')

for _ in range(8):
    try:
        d = p.recv(timeout=2)
    except Exception:
        break
    if not d:
        break
    OUT.append(d.decode('utf-8', 'replace'))
p.close()
txt = ''.join(OUT)
print('\n'.join(txt.splitlines()[-12:]))
print('===== FLAG =====')
import re as _re
for m in _re.findall(r'HTUCTF\{[^}]*\}', txt):
    print(m)
