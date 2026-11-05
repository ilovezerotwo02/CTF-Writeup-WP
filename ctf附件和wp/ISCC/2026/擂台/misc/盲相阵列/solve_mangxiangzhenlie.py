#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盲相阵列 / Blind Phase Array solve script
输入: array_iq.csv
输出: BP1 frame 和 flag
"""
import sys
import zlib
import numpy as np

FS = 48000
BAUD = 1200
SPS = FS // BAUD
CFO = 1700.0
TIMING_OFFSET = 17
TRAINING_SYMBOLS = 80
PAYLOAD_BITS = 560


def load_iq(path: str) -> np.ndarray:
    data = np.genfromtxt(path, delimiter=",", names=True)
    return data["i"] + 1j * data["q"]


def pn8_mask(nbits: int, seed: int = 0xA5) -> np.ndarray:
    """8-bit PN/LFSR mask.
    状态左移，输出最低位，反馈位 = bit7 ^ bit5 ^ bit4 ^ bit3。
    """
    st = seed & 0xFF
    out = np.empty(nbits, dtype=np.uint8)
    for i in range(nbits):
        out[i] = st & 1
        fb = ((st >> 7) ^ (st >> 5) ^ (st >> 4) ^ (st >> 3)) & 1
        st = ((st << 1) & 0xFF) | fb
    return out


def demod_bpsk(z: np.ndarray) -> np.ndarray:
    """频偏校正 + 按符号平均 + 盲相位校正 + BPSK 判决。"""
    n = np.arange(len(z))
    mixed = z * np.exp(-1j * 2 * np.pi * CFO * n / FS)

    nsym = (len(mixed) - TIMING_OFFSET) // SPS
    symbols = np.array([
        mixed[TIMING_OFFSET + k * SPS: TIMING_OFFSET + (k + 1) * SPS].mean()
        for k in range(nsym)
    ])

    # BPSK: 平方后相位翻倍，用 mean(symbol^2)/2 估计未知公共相位。
    theta = np.angle(np.mean(symbols ** 2)) / 2
    symbols = symbols * np.exp(-1j * theta)

    # 取前 640 个符号：80 个训练 + 560 个 payload。
    bits = (symbols.real < 0).astype(np.uint8)
    return bits[:TRAINING_SYMBOLS + PAYLOAD_BITS], symbols[:TRAINING_SYMBOLS + PAYLOAD_BITS]


def undo_column_dma(bits: np.ndarray) -> np.ndarray:
    """16-lane column DMA 逆变换：接收端为 16 列 × 35 行的列优先输出。"""
    return bits.reshape(16, 35).T.reshape(-1)


def hamming74_decode(bits: np.ndarray):
    """标准 Hamming(7,4) 解码。
    码字位序: [p1, p2, d1, p4, d2, d3, d4]
    偶校验；syndrome 非 0 时翻转对应 bit。
    """
    nibbles = []
    corrections = []
    for idx in range(0, len(bits), 7):
        b = [int(x) for x in bits[idx:idx + 7]]
        s1 = b[0] ^ b[2] ^ b[4] ^ b[6]
        s2 = b[1] ^ b[2] ^ b[5] ^ b[6]
        s4 = b[3] ^ b[4] ^ b[5] ^ b[6]
        syndrome = s1 + 2 * s2 + 4 * s4
        if syndrome:
            b[syndrome - 1] ^= 1
            corrections.append((idx // 7, syndrome))

        nibble = (b[2] << 3) | (b[4] << 2) | (b[5] << 1) | b[6]
        nibbles.append(nibble)

    frame = bytearray()
    for i in range(0, len(nibbles), 2):
        frame.append((nibbles[i] << 4) | nibbles[i + 1])
    return bytes(frame), corrections


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/blind/blind-phase/bundle/array_iq.csv"
    z = load_iq(path)
    bits, symbols = demod_bpsk(z)

    train = bits[:TRAINING_SYMBOLS]
    train_bytes = bytes(int("".join(map(str, train[i:i + 8])), 2) for i in range(0, TRAINING_SYMBOLS, 8))
    print(f"[+] symbols used: {len(bits)} = 80 training + 560 payload")
    print(f"[+] training/sync bytes: {train_bytes.hex()}  ({train_bytes!r})")

    payload = bits[TRAINING_SYMBOLS:]
    unmasked = payload ^ pn8_mask(len(payload), seed=0xA5)
    reordered = undo_column_dma(unmasked)
    frame, corrections = hamming74_decode(reordered)

    print(f"[+] Hamming corrected codewords: {corrections}")
    print(f"[+] BP1 frame hex: {frame.hex()}")
    print(f"[+] BP1 frame raw: {frame!r}")

    if not frame.startswith(b"BP1 "):
        raise SystemExit("[-] BP1 magic not found")

    flag = frame[4:-4]
    crc_tail = int.from_bytes(frame[-4:], "big")
    crc_calc = zlib.crc32(flag) & 0xFFFFFFFF
    print(f"[+] CRC32(flag): calculated={crc_calc:08x}, tail={crc_tail:08x}")
    if crc_calc != crc_tail:
        raise SystemExit("[-] CRC check failed")

    print(f"[+] flag: {flag.decode()}")


if __name__ == "__main__":
    main()
