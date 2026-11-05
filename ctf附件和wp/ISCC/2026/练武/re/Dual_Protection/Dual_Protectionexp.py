#!/usr/bin/env python3
import struct

# === PE 解析 ===
def read_pe_bytes(filepath, rva, size):
    with open(filepath, 'rb') as f:
        dos = f.read(0x40)
        e_lfanew = struct.unpack_from('<I', dos, 0x3C)[0]
        f.seek(e_lfanew)
        assert f.read(4) == b'PE\x00\x00'
        fh = f.read(20)
        num_sections = struct.unpack_from('<H', fh, 2)[0]
        opt_size = struct.unpack_from('<H', fh, 16)[0]
        f.read(opt_size)

        sections = []
        for _ in range(num_sections):
            raw = f.read(40)
            sections.append({
                'name': raw[:8].rstrip(b'\x00').decode(errors='replace'),
                'vaddr': struct.unpack_from('<I', raw, 12)[0],
                'vsize': struct.unpack_from('<I', raw, 8)[0],
                'rptr': struct.unpack_from('<I', raw, 20)[0],
                'rsize': struct.unpack_from('<I', raw, 16)[0],
            })

        for sec in sections:
            if sec['vaddr'] <= rva < sec['vaddr'] + sec['vsize']:
                offset = rva - sec['vaddr'] + sec['rptr']
                avail = min(size, sec['rptr'] + sec['rsize'] - offset)
                f.seek(offset)
                data = bytearray(f.read(avail))
                if len(data) < size:
                    data.extend(b'\x00' * (size - len(data)))
                return data
        raise ValueError(f"RVA 0x{rva:X} not found")

# === LCG 解密 ===
def lcg_decrypt(data, seed=0xDEADBEEF, mul=0x19660D, add=0x3C6EF35F):
    out = bytearray()
    state = seed
    for b in data:
        state = (state * mul + add) & 0xFFFFFFFF
        out.append(b ^ ((state >> 24) & 0xFF))
    return out

# === 提取比较常量 ===
def extract_targets(shellcode):
    targets = [0] * 36
    i = 0
    while i < len(shellcode) - 4:
        if shellcode[i] == 0x8A and shellcode[i+1] == 0x46 and shellcode[i+3] == 0x34:
            pos = shellcode[i+2]
            if pos < 36:
                targets[pos] = shellcode[i+4]
                i += 5
                continue
        i += 1
    return targets

# === 主流程 ===
def main():
    key_tbl = [0x12, 0x34, 0x56, 0x78, 0x90, 0xAB, 0xCD, 0xEF]

    # 1. 从 PE 读取加密 shellcode
    encrypted = read_pe_bytes("Dual Protection.exe", 0xFEE0, 0x118)

    # 2. LCG 解密
    shellcode = lcg_decrypt(encrypted)

    # 3. 提取 36 个比较常量
    target = extract_targets(shellcode)

    # 4. 逆向三层变换
    flag = bytearray(target)

    # 逆 T3
    for i in range(36):
        flag[i] ^= (i + 0x20) & 0xFF

    # 逆 T2
    for i in range(36):
        flag[i] = (flag[i] - 0x7F) & 0xFF
        flag[i] ^= key_tbl[i & 7]

    # 逆 T1
    for i in range(36):
        x = (flag[i] - i) & 0xFF
        x = ((x >> 2) | (x << 6)) & 0xFF  # ROR2
        x ^= 0x55
        flag[i] = x

    print(f"FLAG: {flag.decode()}")

if __name__ == "__main__":
    main()