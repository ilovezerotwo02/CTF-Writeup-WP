import struct


TARGET_HEX = "d097c3f6d23a8577e1"

# Correct key and nonce extracted from libmyapplication.so
# Key at file offset 0xf2cb (GOT 0x58ed0 - 0x49c05)
# Nonce at file offset 0xf2eb (GOT 0x58ed0 - 0x49be5)
KEY = bytes.fromhex("149263a16f2d89cbf0375b1ca94e78d3226017ee9abc4d0853e1762a8dc4903f")
NONCE = bytes.fromhex("44332211abcdef668899aa55")
COUNTER = 1


def rotl32(value: int, shift: int) -> int:
    return ((value << shift) & 0xFFFFFFFF) | (value >> (32 - shift))


def quarter_round(state: list[int], a: int, b: int, c: int, d: int) -> None:
    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = rotl32(state[d], 16)

    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = rotl32(state[b], 12)

    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = rotl32(state[d], 8)

    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = rotl32(state[b], 7)


def chacha20_block(key: bytes, counter: int, nonce: bytes) -> bytes:
    """ChaCha20 IETF variant: 32-bit counter, 96-bit (12-byte) nonce."""
    constants = b"expand 32-byte k"
    initial = list(struct.unpack("<4I", constants))
    initial += list(struct.unpack("<8I", key))
    initial.append(counter)
    initial += list(struct.unpack("<3I", nonce))

    working = initial.copy()
    for _ in range(10):
        # Column round
        quarter_round(working, 0, 4, 8, 12)
        quarter_round(working, 1, 5, 9, 13)
        quarter_round(working, 2, 6, 10, 14)
        quarter_round(working, 3, 7, 11, 15)
        # Diagonal round
        quarter_round(working, 0, 5, 10, 15)
        quarter_round(working, 1, 6, 11, 12)
        quarter_round(working, 2, 7, 8, 13)
        quarter_round(working, 3, 4, 9, 14)

    result = [(working[i] + initial[i]) & 0xFFFFFFFF for i in range(16)]
    return struct.pack("<16I", *result)


def xor_stream(data: bytes, key: bytes, nonce: bytes, counter: int = 1) -> bytes:
    out = bytearray()
    block_index = 0
    offset = 0

    while offset < len(data):
        stream = chacha20_block(key, counter + block_index, nonce)
        chunk = data[offset : offset + 64]
        out.extend(x ^ y for x, y in zip(chunk, stream))
        offset += len(chunk)
        block_index += 1

    return bytes(out)


def main() -> None:
    ciphertext = bytes.fromhex(TARGET_HEX)
    plaintext = xor_stream(ciphertext, KEY, NONCE, COUNTER)

    print("target hex:", TARGET_HEX)
    print("key hex   :", KEY.hex())
    print("nonce hex :", NONCE.hex())
    print("counter   :", COUNTER)
    print("plain hex :", plaintext.hex())
    print("flag      :", plaintext.decode("utf-8"))


if __name__ == "__main__":
    main()
