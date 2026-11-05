
import os
import re
import sys

from pwn import *

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

context.log_level = args.LOG or 'info'
context.arch = 'amd64'

HOST = args.HOST or '103.163.47.230'
PORT = int(args.PORT or 35125)

# 卡片上的那句话（本地 ELF .rodata 0x2538）
CARD = args.CARD or '七夕快乐，我喜欢你。愿意和我在一起吗？'


def main():
    io = remote(HOST, PORT, timeout=10)

    banner = io.recvrepeat(1.5)
    if banner:
        print(banner.decode('utf-8', 'replace'), end='')

    io.sendline(CARD.encode('utf-8'))
    resp = io.recvrepeat(2.5)
    print(resp.decode('utf-8', 'replace'), end='')

    io.close()

    out = (banner + resp).decode('utf-8', 'replace')
    m = re.search(r'HTUCTF\{[^}]*\}', out)
    if not m:
        log.failure('没看到 flag，可能投递员没听懂（台词里别多带空格）')
        return 1

    log.success('FLAG = %s', m.group(0))
    dst = os.path.join(HERE, 'flag.txt')
    if os.path.exists(dst):
        open(dst + '.old', 'wb').write(open(dst, 'rb').read())   # 老内容留档
    open(dst, 'wb').write(m.group(0).encode())
    return 0


if __name__ == '__main__':
    sys.exit(main())
