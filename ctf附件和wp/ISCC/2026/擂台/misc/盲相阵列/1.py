#!/usr/bin/env python3
import cmath
import csv
import math
import sys
import zlib


SAMPLE_RATE = 48_000
SYMBOL_RATE = 1_200
SAMPLES_PER_SYMBOL = SAMPLE_RATE // SYMBOL_RATE
NOMINAL_OFFSET_HZ = 1700.0
TRAINING_SYMBOLS = 80
PAYLOAD_BITS = 560
LANES = 16
ROWS = 35


def read_complex_csv(path):
    points = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            points.append(complex(float(row["i"]), float(row["q"])))
    return points


def compensate_carrier(samples):
    rotated = []
    step = -2.0 * math.pi * NOMINAL_OFFSET_HZ / SAMPLE_RATE
    for idx, value in enumerate(samples):
        rotated.append(value * cmath.exp(1j * step * idx))
    return rotated


def average_symbol_windows(samples, start):
    out = []
    cursor = start
    while cursor + SAMPLES_PER_SYMBOL <= len(samples):
        window = samples[cursor : cursor + SAMPLES_PER_SYMBOL]
        out.append(sum(window) / SAMPLES_PER_SYMBOL)
        cursor += SAMPLES_PER_SYMBOL
    return out


def remove_common_phase(symbols):
    phasor = sum(value * value for value in symbols)
    phase = cmath.phase(phasor) / 2.0
    rotator = cmath.exp(-1j * phase)
    return [value * rotator for value in symbols]


def training_metric(symbols):
    # Training preamble is alternating BPSK. Use correlation magnitude rather than
    # hard-equality counts so timing is selected by the strongest real-axis energy.
    expected = [1.0 if i % 2 == 0 else -1.0 for i in range(64)]
    corr = sum(expected[i] * symbols[i].real for i in range(64))
    return abs(corr)


def select_timing(samples):
    best = None
    for offset in range(SAMPLES_PER_SYMBOL):
        coarse = average_symbol_windows(samples, offset)
        if len(coarse) < TRAINING_SYMBOLS:
            continue
        locked = remove_common_phase(coarse)
        metric = training_metric(locked)
        if best is None or metric > best[0]:
            best = (metric, offset, locked)
    if best is None:
        raise RuntimeError("timing search failed")
    return best[1], best[2]


def slice_bpsk(symbols):
    return [1 if value.real < 0 else 0 for value in symbols]


def whitening_bits(count, seed=0xA5):
    state = seed & 0xFF
    for _ in range(count):
        yield state & 1
        feedback = ((state >> 7) ^ (state >> 5) ^ (state >> 4) ^ (state >> 3)) & 1
        state = ((state << 1) & 0xFF) | feedback


def undo_lane_dump(bits):
    restored = [0] * len(bits)
    src = 0
    for lane in range(LANES):
        for row in range(ROWS):
            restored[row * LANES + lane] = bits[src]
            src += 1
    return restored


def hamming74_codebook():
    table = []
    for nibble in range(16):
        d1 = (nibble >> 3) & 1
        d2 = (nibble >> 2) & 1
        d3 = (nibble >> 1) & 1
        d4 = nibble & 1
        p1 = d1 ^ d2 ^ d4
        p2 = d1 ^ d3 ^ d4
        p4 = d2 ^ d3 ^ d4
        table.append((nibble, [p1, p2, d1, p4, d2, d3, d4]))
    return table


def decode_hamming_stream(bits):
    codebook = hamming74_codebook()
    nibbles = []
    corrected_words = 0
    for pos in range(0, len(bits), 7):
        word = bits[pos : pos + 7]
        if len(word) < 7:
            break
        best_nibble = None
        best_dist = 8
        for nibble, codeword in codebook:
            dist = sum(a ^ b for a, b in zip(word, codeword))
            if dist < best_dist:
                best_dist = dist
                best_nibble = nibble
        if best_dist:
            corrected_words += 1
        nibbles.append(best_nibble)

    packed = bytearray()
    for idx in range(0, len(nibbles), 2):
        packed.append((nibbles[idx] << 4) | nibbles[idx + 1])
    return bytes(packed), corrected_words


def decode_frame(path):
    raw = read_complex_csv(path)
    mixed = compensate_carrier(raw)
    offset, locked_symbols = select_timing(mixed)
    bits = slice_bpsk(locked_symbols)
    training_bits = bits[:TRAINING_SYMBOLS]
    training_bytes = bytearray()
    for start in range(0, TRAINING_SYMBOLS, 8):
        value = 0
        for bit in training_bits[start : start + 8]:
            value = (value << 1) | bit
        training_bytes.append(value)

    payload = bits[TRAINING_SYMBOLS : TRAINING_SYMBOLS + PAYLOAD_BITS]
    unwhitened = [bit ^ mask for bit, mask in zip(payload, whitening_bits(PAYLOAD_BITS))]
    ordered = undo_lane_dump(unwhitened)
    frame, corrected_words = decode_hamming_stream(ordered)

    if offset != 17:
        raise RuntimeError(f"unexpected timing offset: {offset}")
    if not frame.startswith(b"BP1 "):
        raise RuntimeError("frame header check failed")

    body = frame[4:-4]
    expected_crc = int.from_bytes(frame[-4:], "big")
    actual_crc = zlib.crc32(body) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise RuntimeError("CRC validation failed")
    return {
        "flag": body.decode("ascii"),
        "timing_offset": offset,
        "training_bytes": bytes(training_bytes).hex(),
        "corrected_words": corrected_words,
        "crc_calc": actual_crc,
        "crc_tail": expected_crc,
    }

def main():
    source = sys.argv[1] if len(sys.argv) > 1 else "bundle/array_iq.csv"
    result = decode_frame(source)
    print(f"符号边界偏移: {result['timing_offset']}")
    print(f"训练段字节: {result['training_bytes']}")
    print(f"纠错码字数量: {result['corrected_words']}")
    print(f"正文 CRC32: 0x{result['crc_calc']:08x}")
    print(f"帧尾 CRC32: 0x{result['crc_tail']:08x}")
    print(f"最终 flag: {result['flag']}")
if __name__ == "__main__":
    main()
