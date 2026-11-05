#!/usr/bin/env python3
import argparse
import zlib
import numpy as np
import pandas as pd

FS = 48000
RS = 1200
SPS = FS // RS
F_CFO = 1700.0
SYNC_EXPECT = 0x1A5D

# H(7,4): [p1,p2,d1,p4,d2,d3,d4], even parity
H = np.array([
    [1, 0, 1, 0, 1, 0, 1],
    [0, 1, 1, 0, 0, 1, 1],
    [0, 0, 0, 1, 1, 1, 1],
], dtype=np.uint8)


def pn8_mask(nbits: int) -> np.ndarray:
    """PN8 mask used by the old FPGA path.

    State is shifted right; feedback is bit0 ^ bit2 ^ bit3 ^ bit4 and is inserted
    into bit7.  The transmitted whitening mask is the inverted MSB output.
    """
    state = 0xA5
    out = []
    for _ in range(nbits):
        bit = (state >> 7) & 1          # MSB output
        out.append(bit ^ 1)             # inverted mask bit
        fb = ((state >> 0) ^ (state >> 2) ^ (state >> 3) ^ (state >> 4)) & 1
        state = (state >> 1) | (fb << 7)
    return np.array(out, dtype=np.uint8)


def bits_to_int(bits):
    v = 0
    for b in bits:
        v = (v << 1) | int(b)
    return v


def hamming74_decode(bitstream: np.ndarray):
    corrected = []
    nibbles = []
    syndromes = []
    cws = bitstream.reshape(-1, 7).copy()
    for idx, cw in enumerate(cws):
        syndrome_bits = (cw @ H.T) & 1
        syndrome = int(syndrome_bits[0] | (syndrome_bits[1] << 1) | (syndrome_bits[2] << 2))
        syndromes.append(syndrome)
        if syndrome:
            cw[syndrome - 1] ^= 1
            corrected.append((idx, syndrome - 1))  # codeword index, zero-based bit index
        data = cw[[2, 4, 5, 6]]
        nibbles.append(bits_to_int(data))
    return nibbles, corrected, syndromes


def nibbles_to_bytes(nibbles):
    return bytes((nibbles[i] << 4) | nibbles[i + 1] for i in range(0, len(nibbles) - 1, 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv', help='array_iq.csv')
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    z = df['i'].to_numpy() + 1j * df['q'].to_numpy()
    n = np.arange(len(z))

    # Residual carrier: BPSK square-law estimation; note says close to +1700 Hz.
    phase = np.angle(np.mean((z ** 2) * np.exp(-1j * 2 * 2 * np.pi * F_CFO * n / FS))) / 2
    zc = z * np.exp(-1j * (2 * np.pi * F_CFO * n / FS + phase))

    # Symbol boundary: first 64 training symbols are alternating 0101...
    best = None
    for off in range(SPS):
        m = (len(zc) - off) // SPS
        sym = zc[off:off + m * SPS].reshape(m, SPS).mean(axis=1)
        bits = (sym.real > 0).astype(np.uint8)
        pat = np.arange(64, dtype=np.uint8) & 1
        alt_score = max(np.mean(bits[:64] == pat), np.mean(bits[:64] == (1 - pat)))
        amp = np.mean(np.abs(sym[:64].real))
        score = (alt_score, amp)
        if best is None or score > best[0]:
            best = (score, off, sym, bits)

    (_, _), off, sym, bits = best
    sync_bits = bits[64:80]
    sync = bits_to_int(sync_bits)
    payload = bits[80:80 + 560]  # one trailing dump bit is not part of the Hamming stream

    # Undo PN mask and 16-lane column DMA.
    unmasked = payload ^ pn8_mask(len(payload))
    de_dma = unmasked.reshape(16, 35).T.flatten()

    # Decode H(7,4) nibbles and rebuild BP1 frame.
    nibbles, corrected, syndromes = hamming74_decode(de_dma)
    frame = nibbles_to_bytes(nibbles)
    flag = frame[4:-4]
    crc_tail = int.from_bytes(frame[-4:], 'big')
    crc_calc = zlib.crc32(flag) & 0xFFFFFFFF

    print(f'[+] samples            : {len(z)}')
    print(f'[+] carrier offset     : {F_CFO:.1f} Hz')
    print(f'[+] residual phase     : {phase:.6f} rad')
    print(f'[+] symbol boundary    : sample offset {off}')
    print(f'[+] training sync      : 0x{sync:04x}')
    print(f'[+] payload bits       : {len(payload)}')
    print(f'[+] H(7,4) corrections : {len(corrected)} -> {corrected}')
    print(f'[+] BP1 frame hex      : {frame.hex()}')
    print(f'[+] CRC32(flag)        : calc=0x{crc_calc:08x}, tail=0x{crc_tail:08x}')
    print(f'[+] flag               : {flag.decode()}')

    if sync != SYNC_EXPECT:
        raise SystemExit('sync check failed')
    if crc_calc != crc_tail:
        raise SystemExit('CRC check failed')


if __name__ == '__main__':
    main()
