import struct
from pathlib import Path

TARGET_RVA = 0x4000
M_RVA = 0x4020
MAP_XOR_RVA = 0x50E0
MAP_LEN = 95
HIDDEN = b"iscc_{this_is_not_flag}"

def parse_sections(blob):
    pe_off = struct.unpack_from("<I", blob, 0x3C)[0]
    if blob[pe_off:pe_off+4] != b"PE\x00\x00":
        raise ValueError("not a PE file")
    fh = pe_off + 4
    ns = struct.unpack_from("<H", blob, fh+2)[0]
    soh = struct.unpack_from("<H", blob, fh+16)[0]
    st = fh + 20 + soh
    secs = []
    for i in range(ns):
        off = st + i*40
        secs.append({
            "va": struct.unpack_from("<I", blob, off+12)[0],
            "vs": struct.unpack_from("<I", blob, off+8)[0],
            "raw_size": struct.unpack_from("<I", blob, off+16)[0],
            "raw_ptr": struct.unpack_from("<I", blob, off+20)[0],
        })
    return secs

def rva_to_off(secs, rva):
    for s in secs:
        end = s["va"] + max(s["vs"], s["raw_size"])
        if s["va"] <= rva < end:
            return s["raw_ptr"] + (rva - s["va"])
    raise ValueError(f"RVA 0x{rva:x} not found")

def derive_xor_key(blob):
    hits = []
    tail = bytes.fromhex("88 48 ff 48 39 c7 75 e9")
    for i in range(len(blob)-10):
        if blob[i:i+2]==b"\x83\xf1" and blob[i+3:i+11]==tail:
            hits.append(blob[i+2])
    if len(hits) != 1:
        raise ValueError(f"expected one xor-key, got {len(hits)}")
    return hits[0]

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

def pass2_inv_char(ch, rd, inv_map):
    if rd <= 0:
        return ch
    seed = HIDDEN[rd] % 95
    cur = ch
    for _ in range(rd):
        mapped = (cur - 32 - seed) % 95
        cur = inv_map[mapped] + 32
    return cur

def build_ops(m):
    ops = []
    for r in range(4):
        for c in range(4):
            v = m[r*4+c]
            tr, tc = divmod(v, 4)
            ops.append((r, c, abs(tc-c), abs(tr-r)))
    return ops

def u8_inverse(mat, row, col, cd, rd, inv_map):
    stage = bytearray(mat)
    idx = row * 4 + col
    stage[idx] = pass2_inv_char(stage[idx], rd, inv_map)
    return pass1_inv(bytes(stage), cd)

def main():
    blob = Path("attachment-22.exe").read_bytes()
    secs = parse_sections(blob)
    target = blob[rva_to_off(secs, TARGET_RVA):][:16]
    m_bytes = blob[rva_to_off(secs, M_RVA):][:16]
    mx = blob[rva_to_off(secs, MAP_XOR_RVA):][:MAP_LEN]
    xk = derive_xor_key(blob)
    mapping = bytes(b ^ xk for b in mx)
    inv_m = {v:i for i,v in enumerate(mapping)}
    mat = bytes(target)
    for row, col, cd, rd in reversed(build_ops(m_bytes)):
        mat = u8_inverse(mat, row, col, cd, rd, inv_m)
    inner = mat.decode("ascii")
    print(f"flag = ISCC{{{inner}}}")

if __name__ == "__main__":
    main()

