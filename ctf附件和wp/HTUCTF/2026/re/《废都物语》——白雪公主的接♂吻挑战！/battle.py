"""打接吻比赛：显式等待每个提示，再按策略出招。"""
import re, sys, time
from pwn import *
context.log_level = 'error'

EXE = sys.argv[1] if len(sys.argv) > 1 else 'duel_patched3.exe'
POLICY = sys.argv[2] if len(sys.argv) > 2 else '2'
MAXT = int(sys.argv[3]) if len(sys.argv) > 3 else 40


def parse(txt):
    me = re.findall(r'你\s+氧气\(HP\)\s*(\d+)\s+气力\(MP\)\s*(\d+)/(\d+)', txt)
    en = re.findall(r'夜族王\s+氧气\(HP\)\s*(\d+)\s+气力\(MP\)\s*(\d+)/(\d+)', txt)
    if not me or not en:
        return None
    a, b = me[-1], en[-1]
    return dict(hp=int(a[0]), mp=int(a[1]), mpmax=int(a[2]), ehp=int(b[0]), emp=int(b[1]), empmax=int(b[2]))


p = process([EXE])
p.recvuntil('选择 > '.encode()); p.sendline(b'1')          # 给公主献上热吻
p.recvuntil('选择 > '.encode()); p.sendline(b'2')          # 由同伴献吻
p.recvuntil('（y/n）'.encode()); p.sendline(b'n')          # 不看 CG
p.recvuntil('按回车继续'.encode()); p.sendline(b'')
p.recvuntil('选择 > '.encode()); p.sendline(b'1')          # 查看挑战规则
p.recvuntil('按回车继续'.encode()); p.sendline(b'')
p.recvuntil('选择 > '.encode()); p.sendline(b'4')          # 开始接吻挑战

for turn in range(MAXT):
    try:
        data = p.recvuntil('行动 > '.encode(), timeout=10)
    except Exception:
        try:
            rest = p.recv(timeout=3).decode('utf-8', 'replace')
        except Exception:
            rest = ''
        print('== 战斗结束/无提示, 剩余输出:\n', rest)
        break
    txt = data.decode('utf-8', 'replace')
    st = parse(txt)
    if st is None:
        print('== 解析失败，输出:\n', txt[-800:])
        break
    print('T%-2d 我 HP%3d MP%3d/%3d | 王 HP%3d MP%3d/%3d' % (turn, st['hp'], st['mp'], st['mpmax'], st['ehp'], st['emp'], st['empmax']))
    act = POLICY[min(turn, len(POLICY) - 1)]
    p.sendline(act.encode())

time.sleep(1.0)
try:
    print('TAIL:', p.recv(timeout=3).decode('utf-8', 'replace')[:1500])
except Exception:
    pass
p.close()
