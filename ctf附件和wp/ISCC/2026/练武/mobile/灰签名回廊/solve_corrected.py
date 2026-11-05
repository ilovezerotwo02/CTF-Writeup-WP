import hashlib
import itertools
import multiprocessing
import re
import struct
import sys
import zipfile
from pathlib import Path


STD_B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
CUSTOM_B64 = "ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba9876543210+/"

# The actual fill_array from DEX SecureValidator.a([B)[B
# byte[7] fill: 0x64, 0x6f, 0x41, 0x5e, 0x7f, 0x4b, 0x34
FILL_ARRAY = bytes([0x64, 0x6f, 0x41, 0x5e, 0x7f, 0x4b, 0x34])

# The java_target string (used in writeup but NOT the actual fill_array)
JAVA_TARGET = b"SB1QTIi"


def pick_apk_path():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    for name in ("./附件", "./attachment.apk", "./attachment-68.apk"):
        path = Path(name)
        if path.exists():
            return path
    raise FileNotFoundError("usage: python solve.py <apk_path>")


def read_u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


def read_u64(buf, off):
    return struct.unpack_from("<Q", buf, off)[0]


def read_lv(buf, off):
    size = read_u32(buf, off)
    off += 4
    return buf[off:off + size], off + size


def extract_v2_cert_sha256(apk_data):
    eocd = apk_data.rfind(b"PK\x05\x06")
    if eocd < 0:
        raise ValueError("EOCD not found")
    central_dir_off = read_u32(apk_data, eocd + 16)
    magic = b"APK Sig Block 42"
    if apk_data[central_dir_off - 16:central_dir_off] != magic:
        raise ValueError("APK Signing Block not found")
    size2 = read_u64(apk_data, central_dir_off - 24)
    block_start = central_dir_off - size2 - 8
    off = block_start + 8
    end = central_dir_off - 24
    v2_block = None
    while off < end:
        pair_size = read_u64(apk_data, off)
        off += 8
        pair_id = read_u32(apk_data, off)
        off += 4
        value = apk_data[off:off + pair_size - 4]
        off += pair_size - 4
        if pair_id == 0x7109871A:
            v2_block = value
    if v2_block is None:
        raise ValueError("APK v2 signature block not found")
    signers, _ = read_lv(v2_block, 0)
    signer, _ = read_lv(signers, 0)
    signed_data, off = read_lv(signer, 0)
    digests, off = read_lv(signed_data, 0)
    certs, off = read_lv(signed_data, off)
    cert, _ = read_lv(certs, 0)
    return hashlib.sha256(cert).digest()


def extract_target_hash(apk_data):
    """Extract the target SHA256 hash from DEX file.
    SecureValidator.b(String) compares SHA256(input) against this hash."""
    matches = re.findall(rb"[0-9a-f]{64}", apk_data)
    for item in matches:
        value = item.decode()
        if value != "0" * 64:
            return value
    # Search in DEX files inside APK
    apk_path = sys.argv[1] if len(sys.argv) > 1 else "attachment-68.apk"
    with zipfile.ZipFile(apk_path) as z:
        for name in z.namelist():
            if name.endswith(".dex"):
                data = z.read(name)
                matches = re.findall(rb"[0-9a-f]{64}", data)
                for item in matches:
                    value = item.decode()
                    if value != "0" * 64:
                        return value
    raise ValueError("target sha256 not found")


def custom_b64_decode(text):
    mapped = "".join(STD_B64[CUSTOM_B64.index(c)] if c in CUSTOM_B64 else c for c in text)
    return __import__("base64").b64decode(mapped)


def rol64(value, bits):
    value &= 0xffffffffffffffff
    return ((value << bits) & 0xffffffffffffffff) | (value >> (64 - bits))


def compute_chain(part, seed, data):
    prime = 0x100000001B3
    value = (seed ^ ((part * prime) & 0xffffffffffffffff)) & 0xffffffffffffffff
    for b in data:
        value = rol64(((value ^ b) * prime) & 0xffffffffffffffff, 13)
    value = (value ^ (value >> 33)) & 0xffffffffffffffff
    value = (value * 0xFF51AFD7ED558CCD) & 0xffffffffffffffff
    value = (value ^ (value >> 33)) & 0xffffffffffffffff
    return value


def rc4_stream(key, size):
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) & 0xff
        s[i], s[j] = s[j], s[i]
    out = []
    i = 0
    j = 0
    for _ in range(size):
        i = (i + 1) & 0xff
        j = (j + s[i]) & 0xff
        s[i], s[j] = s[j], s[i]
        out.append(s[(s[i] + s[j]) & 0xff])
    return bytes(out)


def build_part4_key(chain, fragment4):
    key = bytearray(14)
    low = chain & 0xffffffff
    for i, ch in enumerate(b"Secu"):
        key[i] = ((low >> (8 * i)) & 0xff) ^ ch
    key[4:12] = b"E72TVGSj"
    key[12] = fragment4[0] ^ ord("R")
    key[13] = fragment4[1] ^ ord("V")
    return bytes(key)


def verify_part4_first4(first4, ks):
    d0 = first4[0] ^ ks[0]
    d1 = first4[1] ^ ks[1]
    d2 = first4[2] ^ ks[2]
    d3 = first4[3] ^ ks[3]
    value = ((((d2 ^ (d1 << 3) ^ (d0 << 6)) << 12) ^ (d3 << 9)) & 0x3ff0000)
    return value == 0xe30000


def derive_known_parts_corrected(sig_hash):
    """Corrected version using the actual fill_array from DEX a() method.

    The writeup incorrectly assumed a(sig) returns java_target XOR sig,
    but the actual bytecode shows a(sig) returns fill_array XOR sig.
    """
    # part1 is derived from fill_array, NOT from java_target
    # nativeVerifyPart1(part1, sig) must equal a(sig) = fill_array XOR sig
    # Formula: ((part1[i] + 1) ^ 7) ^ sig[i%4] = fill_array[i] ^ sig[i%4]
    # Therefore: part1[i] = (fill_array[i] ^ 7 - 1) & 0xff
    part1 = bytes(((b ^ 7) - 1) & 0xff for b in FILL_ARRAY)

    # native_part1_return = a(sig) = fill_array XOR sig
    # This is what nativeVerifyPart1 returns and what gets passed to nativeComputeChainToken
    native_part1_return = bytes(FILL_ARRAY[i] ^ sig_hash[i % 4] for i in range(len(FILL_ARRAY)))

    # Fragments are the same (from ContentProvider/BroadcastReceiver)
    fragment2 = bytes(x ^ 23 for x in [82, 32, 37, 67])  # "E72T"
    fragment3 = bytes((i ^ x ^ 90) & 0xff for i, x in enumerate([12, 28, 11, 51]))  # "VGSj"
    fragment4 = b"RV"

    # part2 and part3 from fragment values (native logic reversed)
    part2 = bytes([
        0x1a ^ fragment2[0],
        0x64 ^ fragment2[1],
        0x55 ^ fragment2[2],
        0x32 ^ fragment2[3],
        0x7d ^ fragment2[0],
    ])

    part3 = bytes([
        ((0x9c - fragment3[0]) & 0xff) ^ 0x19,
        ((0xc6 - fragment3[1]) & 0xff) ^ 0x19,
        ((0x81 - fragment3[2]) & 0xff) ^ 0x19,
        ((0xe4 - fragment3[3]) & 0xff) ^ 0x19,
        ((0x80 - fragment3[0]) & 0xff) ^ 0x19,
    ])

    # Chain computation with CORRECTED native_part1_return
    chain = compute_chain(1, 1597463007, native_part1_return)
    chain = compute_chain(2, chain, fragment2)
    chain = compute_chain(3, chain, fragment3)

    ks = rc4_stream(build_part4_key(chain, fragment4), 4)

    return part1, part2, part3, ks


WORKER_DATA = None


def init_worker(prefix, target_hash, charset, ks):
    global WORKER_DATA
    WORKER_DATA = (prefix, target_hash, charset, ks)


def worker(first_char):
    prefix, target_hash, charset, ks = WORKER_DATA
    base = hashlib.sha256()
    base.update(prefix)

    for c2 in charset:
        for c3 in charset:
            for c4 in charset:
                first4 = (first_char + c2 + c3 + c4).encode()

                if not verify_part4_first4(first4, ks):
                    continue

                state = base.copy()
                state.update(first4)

                for tail in itertools.product(charset, repeat=3):
                    last3 = "".join(tail).encode()
                    h = state.copy()
                    h.update(last3 + b"}")

                    if h.hexdigest() == target_hash:
                        return (prefix + first4 + last3 + b"}").decode()

    return None


def solve(apk_path):
    apk_data = apk_path.read_bytes()

    sig_hash = extract_v2_cert_sha256(apk_data)
    target_hash = extract_target_hash(apk_data)

    print(f"[*] Cert SHA256: {sig_hash.hex()}")
    print(f"[*] Target hash: {target_hash}")

    part1, part2, part3, ks = derive_known_parts_corrected(sig_hash)
    prefix = b"ISCC{" + part1 + part2 + part3

    print(f"[*] Corrected Part1: {part1}")
    print(f"[*] Part2: {part2}")
    print(f"[*] Part3: {part3}")
    print(f"[*] Prefix: {prefix}")
    print(f"[*] RC4 key stream (first 4): {ks.hex()}")

    charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    workers = max(1, min(multiprocessing.cpu_count(), len(charset)))

    with multiprocessing.Pool(
        processes=workers,
        initializer=init_worker,
        initargs=(prefix, target_hash, charset, ks),
    ) as pool:
        for result in pool.imap_unordered(worker, charset, chunksize=1):
            if result:
                pool.terminate()
                return result

    raise RuntimeError("flag not found")


if __name__ == "__main__":
    apk_path = pick_apk_path()
    result = solve(apk_path)
    print(f"\n[!!!] FLAG: {result}")
