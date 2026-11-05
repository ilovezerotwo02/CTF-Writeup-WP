#!/usr/bin/env python3
"""
ISCC Mobile Challenge "按步取匙" — Unicorn-based native solve.
Loads libzkpcore.so from the APK and emulates the native functions directly.
"""
import argparse
import hashlib
import struct
import sys
import zipfile
from pathlib import Path

try:
    from elftools.elf.elffile import ELFFile
    from unicorn import UC_ARCH_ARM64, UC_HOOK_CODE, UC_MODE_ARM, Uc, UcError
    from unicorn.arm64_const import *
except ImportError as exc:
    raise SystemExit("pip install pyelftools unicorn") from exc

RET_ADDR = 0xDEAD0000
HEAP_BASE = 0x1000000
STACK_BASE = 0x2000000
STACK_SIZE = 0x100000

FN_ALLOC_AUTH   = 0x297C
FN_ALLOC_STATE  = 0x2E84
FN_LOGIN_CORE   = 0x2A0C
FN_CHECK_CH1    = 0x336C
FN_MAKE_CH2     = 0x4034
FN_CHECK_CH2    = 0x3C4C
FN_CHECK_CH3    = 0x43D0
FN_GEN_FLAG     = 0x2F14

# ── Our APK's constants (verified from disasm.txt / rodata) ──────────────
LFSR_SEED   = 0xEE0F
CH1_CONSTS  = [0x7858F355, 0xE0F4EDEA, 0x189D0D3F, 0x98AC1EBF]
CH1_TARGET  = 0x5B7D9AC4
SBOX        = [0xE, 4, 0xD, 1, 2, 0xF, 0xB, 8, 3, 0xA, 6, 0xC, 5, 9, 0, 7]
CH3_XOR     = 0x2BE99DCFCF628A90

# ── helpers ──────────────────────────────────────────────────────────────

def align_down(v, a=0x1000):
    return v & ~(a - 1)

def align_up(v, a=0x1000):
    return (v + a - 1) & ~(a - 1)

def sha256(data):
    return hashlib.sha256(data).digest()


def lfsr16(x):
    bit = x & 1
    x >>= 1
    if bit:
        x ^= 0xB400
    return x & 0xFFFF


def decrypt_ch1():
    """Feistel decryption using our APK's constants."""
    vals = []
    s = LFSR_SEED
    for _ in range(8):
        s = lfsr16(s)
        vals.append(s)
    keys = [((vals[2*i] << 16) | vals[2*i+1]) ^ CH1_CONSTS[i] for i in range(4)]

    def sub(x):
        o = 0
        for i in range(8):
            o |= SBOX[(x >> (i*4)) & 0xF] << (i*4)
        return o & 0xFFFFFFFF

    def f(v, k):
        x = sub(((v << 16) | v) ^ k)
        return (x ^ (x >> 16)) & 0xFFFF

    # Binary constructs result = (R4 << 16) | L4
    # R4 = high 16 bits of target, L4 = low 16 bits
    right = (CH1_TARGET >> 16) & 0xFFFF   # R4
    left  = CH1_TARGET & 0xFFFF            # L4

    for k in reversed(keys):
        left, right = (right ^ f(left, k)) & 0xFFFF, left

    return f"{((left << 16) | right) & 0xFFFFFFFF:08X}"


def recover_ch3(token):
    """CH3 finalKey using LITTLE-endian byte order (matching ARM64 str)."""
    value = int.from_bytes(token[:8].encode(), 'big')
    value ^= CH3_XOR
    return sha256(value.to_bytes(8, 'little')).hex()[:16]


# ── ELF reader helper ────────────────────────────────────────────────────

class ELFIO:
    def __init__(self, data):
        from io import BytesIO
        self.elf = ELFFile(BytesIO(data))

    def __enter__(self):
        return self.elf

    def __exit__(self, *a):
        pass


# ── Unicorn emulator ─────────────────────────────────────────────────────

class Emu:
    def __init__(self, so_bytes):
        self.mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        self.heap_ptr = HEAP_BASE
        self.trace = []

        # Map ELF segments
        with ELFIO(so_bytes) as elf:
            for seg in elf.iter_segments():
                if seg["p_type"] != "PT_LOAD":
                    continue
                va = seg["p_vaddr"]
                ms = seg["p_memsz"]
                start = align_down(va)
                end = align_up(va + ms)
                try:
                    self.mu.mem_map(start, end - start)
                except UcError:
                    pass
                self.mu.mem_write(va, seg.data()[:seg["p_filesz"]])

        self.mu.mem_map(HEAP_BASE, 0x400000)
        self.mu.mem_map(STACK_BASE, STACK_SIZE)
        self.mu.mem_map(align_down(RET_ADDR), 0x1000)

        self.hooks = {
            0x5AF0: self.h_log,
            0x5B00: self.h_fail,
            0x5B10: self.h_calloc,
            0x5B20: self.h_memset,
            0x5B30: self.h_free,
            0x5B40: self.h_strcmp,
            0x5B50: self.h_strlen,
            0x5B60: self.h_memcpy,
            0x5B70: self.h_strcpy,
            0x5B80: self.h_strcat,
            0x5BA0: self.h_strtoul,
            0x5BB0: self.h_strncpy,
            0x5BC0: self.h_strncpy,
            0x5CE0: self.h_alloc,
            0x5CF0: self.h_free,
            0x2D88: self.h_fmt,
            0x3270: self.h_fmt,
            0x42D4: self.h_fmt,
            0x4E58: self.h_sha256,
            0x59CC: self.h_hex,
        }
        self.mu.hook_add(UC_HOOK_CODE, self.hook)

    # ── register helpers ──

    def r(self, reg):
        return self.mu.reg_read(reg)

    def w(self, reg, val):
        self.mu.reg_write(reg, val & ((1 << 64) - 1))

    # ── memory helpers ──

    def alloc(self, size):
        p = align_up(self.heap_ptr, 0x10)
        self.heap_ptr = p + align_up(size, 0x10)
        return p

    def alloc_s(self, text):
        data = text.encode() if isinstance(text, str) else text
        p = self.alloc(len(data) + 1)
        self.mu.mem_write(p, data + b"\x00")
        return p

    def read_cstr(self, addr, limit=0x10000):
        out = []
        for i in range(limit):
            b = self.mu.mem_read(addr + i, 1)[0]
            if b == 0:
                break
            out.append(b)
        return bytes(out)

    def read_str(self, addr):
        return self.read_cstr(addr).decode("utf-8", "replace")

    # ── call ──

    def call(self, addr, *args):
        for reg, val in zip(
            [UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3,
             UC_ARM64_REG_X4, UC_ARM64_REG_X5, UC_ARM64_REG_X6, UC_ARM64_REG_X7],
            args,
        ):
            self.w(reg, val)
        self.w(UC_ARM64_REG_SP, STACK_BASE + STACK_SIZE // 2)
        self.w(UC_ARM64_REG_LR, RET_ADDR)
        try:
            self.mu.emu_start(addr, RET_ADDR)
        except UcError as e:
            if e.errno != UC_ERR_OK:
                tr = ", ".join(hex(x) for x in self.trace[-12:])
                raise RuntimeError(f"emu crash @ {hex(self.r(UC_ARM64_REG_PC))}  trace={tr}") from e
        return self.r(UC_ARM64_REG_X0)

    # ── hook dispatcher ──

    def hook(self, mu, addr, size, ud):
        self.trace.append(addr)
        self.trace = self.trace[-40:]
        if addr == RET_ADDR:
            raise UcError(UC_ERR_OK)
        h = self.hooks.get(addr)
        if h:
            h()
            self.w(UC_ARM64_REG_PC, self.r(UC_ARM64_REG_LR))

    # ── hooked helpers ──

    def h_fail(self):
        raise RuntimeError("stack canary fail")

    def h_log(self):
        self.w(UC_ARM64_REG_X0, 0)

    def h_calloc(self):
        sz = self.r(UC_ARM64_REG_X0) * self.r(UC_ARM64_REG_X1)
        p = self.alloc(sz)
        self.mu.mem_write(p, b"\x00" * sz)
        self.w(UC_ARM64_REG_X0, p)

    def h_alloc(self):
        self.w(UC_ARM64_REG_X0, self.alloc(self.r(UC_ARM64_REG_X0)))

    def h_free(self):
        self.w(UC_ARM64_REG_X0, 0)

    def h_memset(self):
        d, v, sz = self.r(UC_ARM64_REG_X0), self.r(UC_ARM64_REG_W1) & 0xFF, self.r(UC_ARM64_REG_X2)
        self.mu.mem_write(d, bytes([v]) * sz)
        self.w(UC_ARM64_REG_X0, d)

    def h_memcpy(self):
        d, s, sz = self.r(UC_ARM64_REG_X0), self.r(UC_ARM64_REG_X1), self.r(UC_ARM64_REG_X2)
        self.mu.mem_write(d, bytes(self.mu.mem_read(s, sz)))
        self.w(UC_ARM64_REG_X0, d)

    def h_strlen(self):
        self.w(UC_ARM64_REG_X0, len(self.read_cstr(self.r(UC_ARM64_REG_X0))))

    def h_strcmp(self):
        a, b = self.read_cstr(self.r(UC_ARM64_REG_X0)), self.read_cstr(self.r(UC_ARM64_REG_X1))
        self.w(UC_ARM64_REG_X0, 0 if a == b else 1)

    def h_strcpy(self):
        d, s = self.r(UC_ARM64_REG_X0), self.r(UC_ARM64_REG_X1)
        self.mu.mem_write(d, self.read_cstr(s) + b"\x00")
        self.w(UC_ARM64_REG_X0, d)

    def h_strcat(self):
        d, s = self.r(UC_ARM64_REG_X0), self.r(UC_ARM64_REG_X1)
        self.mu.mem_write(d, self.read_cstr(d) + self.read_cstr(s) + b"\x00")
        self.w(UC_ARM64_REG_X0, d)

    def h_strncpy(self):
        d, s, sz = self.r(UC_ARM64_REG_X0), self.r(UC_ARM64_REG_X1), self.r(UC_ARM64_REG_X2)
        data = self.read_cstr(s, sz)[:sz]
        self.mu.mem_write(d, data + b"\x00" * (sz - len(data)))
        self.w(UC_ARM64_REG_X0, d)

    def h_strtoul(self):
        t = self.read_str(self.r(UC_ARM64_REG_X0)).strip()
        b = self.r(UC_ARM64_REG_X2) or 10
        try:
            self.w(UC_ARM64_REG_X0, int(t, b))
        except ValueError:
            self.w(UC_ARM64_REG_X0, 0)

    def h_fmt(self):
        dst, size = self.r(UC_ARM64_REG_X0), self.r(UC_ARM64_REG_X1)
        fmt = self.read_str(self.r(UC_ARM64_REG_X3))
        if fmt == "%s%s%s":
            out = self.read_cstr(self.r(UC_ARM64_REG_X4)) + self.read_cstr(self.r(UC_ARM64_REG_X5)) + self.read_cstr(self.r(UC_ARM64_REG_X6))
        elif fmt == "%s/hint.txt":
            out = self.read_cstr(self.r(UC_ARM64_REG_X4)) + b"/hint.txt"
        elif fmt == "ISCC{%s}":
            out = b"ISCC{" + self.read_cstr(self.r(UC_ARM64_REG_X4)) + b"}"
        else:
            raise RuntimeError(f"unknown fmt: {fmt!r}")
        truncated = out[:max(0, size - 1)] + b"\x00" if size else out + b"\x00"
        self.mu.mem_write(dst, truncated)
        self.w(UC_ARM64_REG_X0, len(out))

    def h_sha256(self):
        src, sz, dst = self.r(UC_ARM64_REG_X0), self.r(UC_ARM64_REG_X1), self.r(UC_ARM64_REG_X2)
        self.mu.mem_write(dst, sha256(bytes(self.mu.mem_read(src, sz))))
        self.w(UC_ARM64_REG_X0, dst)

    def h_hex(self):
        src, sz, dst = self.r(UC_ARM64_REG_X0), self.r(UC_ARM64_REG_X1), self.r(UC_ARM64_REG_X2)
        self.mu.mem_write(dst, bytes(self.mu.mem_read(src, sz)).hex().encode() + b"\x00")
        self.w(UC_ARM64_REG_X0, dst)


# ── solve ────────────────────────────────────────────────────────────────

def solve(apk_path):
    with zipfile.ZipFile(apk_path) as zf:
        candidates = [n for n in zf.namelist() if n.endswith("/libzkpcore.so")]
        if not candidates:
            raise SystemExit("libzkpcore.so not found in APK")
        name = "lib/arm64-v8a/libzkpcore.so"
        if name not in candidates:
            name = candidates[0]
        so_bytes = zf.read(name)

    emu = Emu(so_bytes)

    # 1. Allocate native contexts
    auth  = emu.call(FN_ALLOC_AUTH)
    state = emu.call(FN_ALLOC_STATE)

    # 2. Compute username & password from rodata
    rodata_section = None
    with ELFIO(so_bytes) as elf:
        rodata_section = elf.get_section_by_name(".rodata").data()

    marker = b"k3y_j4va_k3y!!!!"
    off = rodata_section.find(marker)
    mask = rodata_section[off + len(marker):off + len(marker) + 10]
    username = bytes(marker[i] ^ mask[i] for i in range(10)).decode()
    password = "Zkp_M_ast3er"

    # 3. Login (native)
    ok = emu.call(FN_LOGIN_CORE, auth, emu.alloc_s(username), emu.alloc_s(password))
    if ok != 1:
        raise RuntimeError(f"login failed: {username}/{password}")
    print(f"[+] login: {username} / {password}")
    # Dump session key from auth struct (read 32 bytes from auth)
    session_key = bytes(emu.mu.mem_read(auth, 0x100))
    print(f"[+] session key (auth[:32]): {session_key[:32].hex()}")

    import struct

    # 4. CH1 — compute decrypt in Python, verify via emu
    ch1_val = decrypt_ch1()
    ok = emu.call(FN_CHECK_CH1, emu.alloc_s(ch1_val), state)
    if ok != 1:
        raise RuntimeError(f"CH1 failed: {ch1_val}")
    # Set state completion flags; the native check functions do NOT set these.
    emu.mu.mem_write(state, struct.pack("<I", 1) + b"\x01\x00\x00")
    # Also ensure the verify hash is stored at state+0x207
    ch1_verify = sha256(b"t1_static_" + ch1_val.encode())
    emu.mu.mem_write(state + 0x207, ch1_verify)
    print(f"[+] CH1: {ch1_val}")

    # 5. CH2 — call native FN_MAKE_CH2, then verify
    ch2_buf = emu.alloc(64)
    emu.call(FN_MAKE_CH2, ch2_buf)
    ch2_val = emu.read_str(ch2_buf)
    ok = emu.call(FN_CHECK_CH2, emu.alloc_s(ch2_val), state)
    if ok != 1:
        raise RuntimeError(f"CH2 failed: {ch2_val}")
    emu.mu.mem_write(state, struct.pack("<I", 2) + b"\x01\x01\x00")
    ch2_verify = sha256(b"t2_dynamic_" + ch2_val.encode())
    emu.mu.mem_write(state + 0x227, ch2_verify)
    print(f"[+] CH2: {ch2_val}")

    # 6. Read intermediate token from .bss (address 0x803D)
    token = emu.read_str(0x803D)
    print(f"[+] token: {token}")

    # 7. CH3 — compute in Python (LE byte order), verify via emu
    ch3_val = recover_ch3(token)
    ok = emu.call(FN_CHECK_CH3, emu.alloc_s(ch3_val), emu.alloc_s(token), state)
    if ok != 1:
        raise RuntimeError(f"CH3 failed: {ch3_val}")
    emu.mu.mem_write(state, struct.pack("<I", 3) + b"\x01\x01\x01")
    ch3_verify = sha256(b"t3_android_" + ch3_val.encode() + token.encode())
    emu.mu.mem_write(state + 0x247, ch3_verify)
    print(f"[+] CH3: {ch3_val}")

    # 8. Generate flag natively
    flag_buf = emu.alloc(256)
    ok = emu.call(FN_GEN_FLAG, state, auth, flag_buf, 0x80)
    if ok != 1:
        raise RuntimeError("flag generation failed")
    flag = emu.read_str(flag_buf)
    print(f"[+] FLAG: {flag}")

    # Verify: compute flag in Python using same data (without null byte, matching native memcpy size=15)
    ch1_verify_r = bytes(emu.mu.mem_read(state + 0x207, 8))
    ch2_verify_r = bytes(emu.mu.mem_read(state + 0x227, 8))
    ch3_verify_r = bytes(emu.mu.mem_read(state + 0x247, 8))
    session_key_r = bytes(emu.mu.mem_read(auth, 32))
    flag_data = b"CTF_ZKP_FLAG_V2" + session_key_r + ch1_verify_r + ch2_verify_r + ch3_verify_r
    flag_hash = sha256(flag_data)
    flag_hex = flag_hash[:24].hex()
    py_flag = f"ISCC{{{flag_hex}}}"
    print(f"[+] Python-computed flag (no null): {py_flag}")
    print(f"[+] match: {flag == py_flag}")

    return {
        "username": username,
        "password": password,
        "ch1": ch1_val,
        "ch2": ch2_val,
        "token": token,
        "ch3": ch3_val,
        "flag": flag,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("apk", nargs="?", type=Path)
    args = p.parse_args()
    if not args.apk:
        apks = sorted(Path(".").glob("*.apk"))
        if not apks:
            raise SystemExit("no APK found")
        args.apk = apks[0]
    solve(args.apk)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
