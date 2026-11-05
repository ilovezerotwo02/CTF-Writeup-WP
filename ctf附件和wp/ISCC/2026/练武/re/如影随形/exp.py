import struct
import sys
from pathlib import Path


TARGET_RVA = 0x4000
M_RVA = 0x4020
MAP_XOR_RVA = 0x50E0
MAP_LEN = 95
HIDDEN = b"iscc_{this_is_not_flag}"


def u16(data, off):
    return struct.unpack_from("<H", data, off)[0]


def u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def parse_sections(blob):
    pe_off = u32(blob, 0x3C)
    if blob[pe_off:pe_off + 4] != b"PE\x00\x00":
        raise ValueError("not a PE file")

    file_header = pe_off + 4
    number_of_sections = u16(blob, file_header + 2)
    size_of_optional_header = u16(blob, file_header + 16)
    section_table = file_header + 20 + size_of_optional_header

    sections = []
    for i in range(number_of_sections):
        off = section_table + i * 40
        virtual_size = u32(blob, off + 8)
        virtual_address = u32(blob, off + 12)
        size_of_raw_data = u32(blob, off + 16)
        ptr_to_raw_data = u32(blob, off + 20)
        sections.append(
            {
                "va": virtual_address,
                "vs": virtual_size,
                "raw_size": size_of_raw_data,
                "raw_ptr": ptr_to_raw_data,
            }
        )
    return sections


def rva_to_off(sections, rva):
    for sec in sections:
        start = sec["va"]
        end = start + max(sec["vs"], sec["raw_size"])
        if start <= rva < end:
            return sec["raw_ptr"] + (rva - start)
    raise ValueError(f"RVA 0x{rva:x} not found in section table")


def read_rva(blob, sections, rva, size):
    off = rva_to_off(sections, rva)
    return blob[off:off + size]


def derive_xor_key(blob):
    hits = []
    tail = bytes.fromhex("88 48 ff 48 39 c7 75 e9")
    for i in range(len(blob) - (2 + 1 + len(tail))):
        if blob[i:i + 2] == b"\x83\xf1" and blob[i + 3:i + 3 + len(tail)] == tail:
            hits.append(blob[i + 2])
    if len(hits) != 1:
        raise ValueError(f"expected exactly one xor-key pattern, got {len(hits)}")
    return hits[0]


def rot_printable(ch, key):
    return ((ch + key - 32) % 95) + 32


def pass1(data, seed):
    out = bytearray()
    prev = seed % 95
    for b in data:
        if 32 <= b <= 126:
            cur = rot_printable(b, prev)
            out.append(cur)
            prev = cur - 32
        else:
            out.append(b)
    return bytes(out)


def pass1_inv(data, seed):
    out = bytearray()
    prev = seed % 95
    for b in data:
        if 32 <= b <= 126:
            cur = ((b - 32 - prev) % 95) + 32
            out.append(cur)
            prev = b - 32
        else:
            out.append(b)
    return bytes(out)


def pass2_char(ch, row_diff, mapping):
    if row_diff <= 0:
        return ch
    seed = HIDDEN[row_diff] % 95
    cur = ch
    for _ in range(row_diff):
        cur = ((seed + mapping[cur - 32]) % 95) + 32
    return cur


def pass2_inv_char(ch, row_diff, inv_mapping):
    if row_diff <= 0:
        return ch
    seed = HIDDEN[row_diff] % 95
    cur = ch
    for _ in range(row_diff):
        mapped = (cur - 32 - seed) % 95
        cur = inv_mapping[mapped] + 32
    return cur


def build_ops(m_bytes):
    ops = []
    for row in range(4):
        for col in range(4):
            val = m_bytes[row * 4 + col]
            target_row, target_col = divmod(val, 4)
            ops.append((row, col, abs(target_col - col), abs(target_row - row)))
    return ops


def u8_forward(mat, row, col, col_diff, row_diff, mapping):
    stage = bytearray(pass1(mat, col_diff))
    idx = row * 4 + col
    stage[idx] = pass2_char(stage[idx], row_diff, mapping)
    return bytes(stage)


def u8_inverse(mat, row, col, col_diff, row_diff, inv_mapping):
    stage = bytearray(mat)
    idx = row * 4 + col
    stage[idx] = pass2_inv_char(stage[idx], row_diff, inv_mapping)
    return pass1_inv(bytes(stage), col_diff)


def solve_family(exe_path):
    blob = Path(exe_path).read_bytes()
    sections = parse_sections(blob)

    target = read_rva(blob, sections, TARGET_RVA, 16)
    m_bytes = read_rva(blob, sections, M_RVA, 16)
    map_xor = read_rva(blob, sections, MAP_XOR_RVA, MAP_LEN)
    xor_key = derive_xor_key(blob)
    mapping = bytes(b ^ xor_key for b in map_xor)
    inv_mapping = {value: idx for idx, value in enumerate(mapping)}
    if len(inv_mapping) != MAP_LEN:
        raise ValueError("mapping is not a permutation")

    mat = bytes(target)
    for row, col, col_diff, row_diff in reversed(build_ops(m_bytes)):
        mat = u8_inverse(mat, row, col, col_diff, row_diff, inv_mapping)

    inner = mat.decode("ascii")

    check = inner.encode("ascii")
    for row, col, col_diff, row_diff in build_ops(m_bytes):
        check = u8_forward(check, row, col, col_diff, row_diff, mapping)
    if check != target:
        raise ValueError("verification failed")

    return xor_key, inner


def main():
    if len(sys.argv) != 2:
        print(f"usage: python {Path(sys.argv[0]).name} <attachment-22.exe>")
        raise SystemExit(1)

    exe_path = sys.argv[1]
    xor_key, inner = solve_family(exe_path)
    print(f"[+] xor_key = 0x{xor_key:02x}")
    print(f"[+] inner   = {inner}")
    print(f"[+] flag    = ISCC{{{inner}}}")


if __name__ == "__main__":
    main()
