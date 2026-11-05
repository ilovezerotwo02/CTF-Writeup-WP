import argparse
import io
import re
import sys
import tempfile
import zipfile
import zlib
from itertools import permutations
from pathlib import Path

try:
    import lief
    import py7zr
    from capstone import CS_ARCH_X86, CS_MODE_64, Cs
    from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_ECX, X86_REG_EDX, X86_REG_R14, X86_REG_R14D, X86_REG_RIP
    from loguru import logger

    logger.remove()
    from androguard.core.dex import DEX
except ImportError as exc:
    raise SystemExit(
        "Missing dependency. Install first: pip install py7zr lief capstone androguard loguru"
    ) from exc


LABELS = ["CWJ", "XMAS", "FLOW", "STAR", "ROSE", "GOAL", "DANCE", "MAGI"]
PKG = "com.example.mobile04"


def u32(x):
    return x & 0xFFFFFFFF


def rol(x, r):
    x &= 0xFFFFFFFF
    r &= 31
    return u32((x << r) | (x >> (32 - r)))


def ror(x, r):
    x &= 0xFFFFFFFF
    r &= 31
    return u32((x >> r) | (x << (32 - r)))


def jint(x):
    x &= 0xFFFFFFFF
    return x - 0x100000000 if x & 0x80000000 else x


def java_hash(s):
    h = 0
    for ch in s:
        h = (31 * h + ord(ch)) & 0xFFFFFFFF
    return jint(h)


def bit_swap_bytes(bs):
    return bytes((((b & 0x55) << 1) | ((b & 0xAA) >> 1)) & 0xFF for b in bs)


def fnv1a64(bs):
    h = 0xCBF29CE484222325
    for b in bs:
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def tea_enc(v0, v1, key):
    s = 0
    delta = 0x9E3779B9
    for _ in range(32):
        s = u32(s + delta)
        v0 = u32(v0 + ((((v1 << 4) + key[0]) ^ (v1 + s) ^ ((v1 >> 5) + key[1]))))
        v1 = u32(v1 + ((((v0 << 4) + key[2]) ^ (v0 + s) ^ ((v0 >> 5) + key[3]))))
    return v0, v1


def e1_v(input_sequence, video_size, magic_mask, derive_words):
    seed = u32(java_hash(PKG) ^ video_size ^ magic_mask)
    key = [u32(seed ^ w) for w in derive_words]
    h = fnv1a64(bit_swap_bytes(input_sequence.encode()))
    o0, o1 = tea_enc(h & 0xFFFFFFFF, (h >> 32) & 0xFFFFFFFF, key)
    arr = o0.to_bytes(4, "little") + o1.to_bytes(4, "little")
    return f"cw:{arr.hex()}:{zlib.crc32(arr) & 0xFFFFFFFF:08x}"


def b58decode(s):
    alpha = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    mp = {c: i for i, c in enumerate(alpha)}
    num = 0
    for ch in s:
        num = num * 58 + mp[ch]
    out = []
    while num:
        out.append(num & 0xFF)
        num >>= 8
    raw = bytes(out[::-1]) if out else b""
    return (b"\x00" * (len(s) - len(s.lstrip("1")))) + raw


def rc6_key_schedule(seed1, seed2, k2, p_xor, q_add):
    p = u32(rol(seed2, 13) ^ seed1 ^ p_xor)
    q = u32((rol(seed2, 25) ^ seed1) + q_add) | 1
    s = [0] * 44
    s[0] = p
    for i in range(1, 44):
        s[i] = u32(s[i - 1] + q)

    l = [int.from_bytes(k2[i : i + 4], "little") for i in range(0, 16, 4)]
    a = b = i = j = 0
    for _ in range(132):
        a = s[i] = rol(u32(s[i] + a + b), 3)
        b = l[j] = rol(u32(l[j] + a + b), (a + b) & 31)
        i = (i + 1) % 44
        j = (j + 1) % 4
    return s


def rc6_decrypt_block(block16, s):
    a, b, c, d = [int.from_bytes(block16[i : i + 4], "little") for i in range(0, 16, 4)]
    c = u32(c - s[43])
    a = u32(a - s[42])
    for i in range(20, 0, -1):
        a, b, c, d = d, a, b, c
        u = rol(u32(d * u32(2 * d + 1)), 5)
        t = rol(u32(b * u32(2 * b + 1)), 5)
        c = ror(u32(c - s[2 * i + 1]), t & 31) ^ u
        a = ror(u32(a - s[2 * i]), u & 31) ^ t
    d = u32(d - s[1])
    b = u32(b - s[0])
    return b"".join(x.to_bytes(4, "little") for x in [a, b, c, d])


def expected_middle(cw, db_bytes, consts):
    first16 = db_bytes[:16]
    rest = bytearray(db_bytes[16:])
    crc = zlib.crc32(cw.encode() + first16) & 0xFFFFFFFF
    for i in range(len(rest)):
        rest[i] ^= (((crc >> (8 * (i % 4))) & 0xFF) + i) & 0xFF

    seed1 = int.from_bytes(rest[0x80:0x84], "little")
    seed2 = int.from_bytes(rest[0xB4:0xB8], "little")
    schedule = rc6_key_schedule(seed1, seed2, consts["k2"], consts["p_xor"], consts["q_add"])
    target = b58decode(consts["tgt"]).rjust(32, b"\x00")[-32:]
    enc = bytes(target[i] ^ consts["k1"][i % len(consts["k1"])] for i in range(32))
    return rc6_decrypt_block(enc[:16], schedule) + rc6_decrypt_block(enc[16:], schedule)


def read_container(path):
    path = Path(path)
    suffix = path.suffix.lower()
    head = path.read_bytes()[:8]
    if suffix == ".apk":
        return path.read_bytes()

    with tempfile.TemporaryDirectory(prefix="m04_unpack_") as td:
        td = Path(td)
        if suffix == ".7z":
            seven_path = path
        elif suffix == ".zip" or head.startswith(b"PK\x03\x04"):
            with zipfile.ZipFile(path, "r") as outer:
                names = outer.namelist()
                if "AndroidManifest.xml" in names and "classes.dex" in names:
                    return path.read_bytes()
                apk_names = [n for n in names if n.lower().endswith(".apk")]
                if apk_names:
                    return outer.read(apk_names[0])
                seven_name = next((n for n in names if n.lower().endswith(".7z")), None)
                if seven_name is None:
                    raise ValueError("zip does not contain apk or 7z")
                seven_path = td / "inner.7z"
                seven_path.write_bytes(outer.read(seven_name))
        else:
            raise ValueError(f"unsupported input suffix: {path.suffix}")

        with py7zr.SevenZipFile(seven_path, "r") as archive:
            archive.extractall(td)
        apk_path = next(td.rglob("*.apk"), None)
        if apk_path is None:
            raise ValueError("7z does not contain apk")
        return apk_path.read_bytes()


def read_apk_bits(apk_bytes):
    with zipfile.ZipFile(io.BytesIO(apk_bytes), "r") as apk:
        db = apk.read("assets/appview_cache.db")
        video_size = apk.getinfo("res/6V.mp4").file_size
        dex = apk.read("classes.dex")
        preferred = "lib/x86_64/libmobile04.so"
        if preferred in apk.namelist():
            so = apk.read(preferred)
            so_name = preferred
        else:
            so_name = next(n for n in apk.namelist() if n.endswith("/libmobile04.so"))
            so = apk.read(so_name)
    return db, video_size, dex, so, so_name


def parse_const_value(output):
    m = re.search(r"const(?:/\w+)?\s+\w+,\s+(-?(?:0x)?[0-9a-fA-F]+)", output)
    if not m:
        m = re.search(r"\w+,\s+(-?(?:0x)?[0-9a-fA-F]+)$", output)
        if not m:
            return None
    return int(m.group(1), 0) & 0xFFFFFFFF


def extract_java_mask(dex_bytes):
    dex = DEX(dex_bytes)
    cls = dex.get_class("Lcom/example/mobile04/K1;")
    if cls is None:
        raise ValueError("K1 class not found")
    for method in cls.get_methods():
        if method.get_name() != "g" or method.get_code() is None:
            continue
        last_const = {}
        for ins in method.get_code().get_bc().get_instructions():
            name = ins.get_name()
            out = ins.get_output()
            if name.startswith("const"):
                parts = out.split(",", 1)
                if parts:
                    reg = parts[0].split()[-1]
                    value = parse_const_value(out)
                    if value is not None:
                        last_const[reg] = value
            if name == "xor-int/2addr" and out.replace(" ", "") == "v1,v0":
                if "v0" in last_const:
                    return last_const["v0"]
    raise ValueError("K1.g method not found")


def parse_native(so_bytes):
    with tempfile.TemporaryDirectory(prefix="m04_lief_") as td:
        so_path = Path(td) / "libmobile04.so"
        so_path.write_bytes(so_bytes)
        binary = lief.parse(str(so_path))
        if binary is None:
            raise ValueError("lief failed to parse libmobile04.so")
        data = so_path.read_bytes()

        def va_to_bytes(va, size):
            off = binary.virtual_address_to_offset(va)
            return data[off : off + size]

        def symbol(name):
            sym = next((s for s in binary.symbols if s.name == name), None)
            if sym is None:
                raise ValueError(f"symbol not found: {name}")
            return sym

        def ptr_symbol_string(name):
            sym = symbol(name)
            rel = next((r for r in binary.relocations if r.address == sym.value), None)
            if rel is None:
                raise ValueError(f"relocation not found for {name}")
            return va_to_bytes(rel.addend, 128).split(b"\x00")[0]

        k1 = ptr_symbol_string("_K1")
        k2 = ptr_symbol_string("_K2")
        tgt = ptr_symbol_string("_TGT").decode("ascii")

        md = Cs(CS_ARCH_X86, CS_MODE_64)
        md.detail = True

        derive = symbol("_Z14_n_derive_implP7_JNIEnvP7_jclassi")
        derive_code = va_to_bytes(derive.value, derive.size)
        derive_words = None
        for ins in md.disasm(derive_code, derive.value):
            if ins.mnemonic == "pxor":
                for op in ins.operands:
                    if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                        target = ins.address + ins.size + op.mem.disp
                        raw = va_to_bytes(target, 16)
                        derive_words = [int.from_bytes(raw[i : i + 4], "little") for i in range(0, 16, 4)]
                        break
            if derive_words:
                break
        if derive_words is None:
            raise ValueError("derive words not found")

        ctor = symbol("_ZN3_C1C2Ejj")
        # The constructor has an opaque invalid branch near the start. Linear
        # disassembly from the symbol entry can stop there, so begin at the
        # real fall-through body that initializes P/Q and the RC6 schedule.
        ctor_body = ctor.value + 0x31
        ctor_code = va_to_bytes(ctor_body, max(0, ctor.size - 0x31))
        p_xor = None
        q_add = None
        seen_xor_r14 = False
        for ins in md.disasm(ctor_code, ctor_body):
            ops = ins.operands
            if ins.mnemonic == "xor" and len(ops) == 2 and ops[0].type == X86_OP_REG and ops[0].reg == X86_REG_ECX and ops[1].type == X86_OP_IMM:
                p_xor = ops[1].imm & 0xFFFFFFFF
            if ins.mnemonic == "xor" and len(ops) >= 1 and ops[0].type == X86_OP_REG and ops[0].reg == X86_REG_R14D:
                seen_xor_r14 = True
                continue
            if seen_xor_r14 and q_add is None:
                if ins.mnemonic == "add" and len(ops) == 2 and ops[0].type == X86_OP_REG and ops[0].reg == X86_REG_R14D and ops[1].type == X86_OP_IMM:
                    q_add = ops[1].imm & 0xFFFFFFFF
                elif ins.mnemonic == "lea" and len(ops) == 2 and ops[0].type == X86_OP_REG and ops[0].reg == X86_REG_EDX and ops[1].type == X86_OP_MEM and ops[1].mem.base == X86_REG_R14:
                    q_add = ops[1].mem.disp & 0xFFFFFFFF
            if p_xor is not None and q_add is not None:
                break
        if p_xor is None or q_add is None:
            raise ValueError(f"RC6 constants not found: p_xor={p_xor}, q_add={q_add}")

    return {
        "k1": k1,
        "k2": k2,
        "tgt": tgt,
        "derive_words": derive_words,
        "p_xor": p_xor,
        "q_add": q_add,
    }


def solve(path):
    apk_bytes = read_container(path)
    db, video_size, dex, so, so_name = read_apk_bits(apk_bytes)
    consts = parse_native(so)
    consts["magic_mask"] = extract_java_mask(dex)

    candidates = []
    for perm in permutations(LABELS):
        seq = "".join(perm)
        cw = e1_v(seq, video_size, consts["magic_mask"], consts["derive_words"])
        middle = expected_middle(cw, db, consts)
        if all(32 <= b < 127 for b in middle):
            candidates.append((perm, seq, middle.decode("ascii"), cw))

    if len(candidates) != 1:
        raise ValueError(f"unexpected candidate count {len(candidates)}: {candidates!r}")

    perm, seq, middle, cw = candidates[0]
    return {
        "so": so_name,
        "sequence": " -> ".join(perm),
        "input": seq,
        "cw": cw,
        "middle": middle,
        "flag": f"ISCC{{{middle}}}",
        "k1": consts["k1"].decode("ascii"),
        "k2": consts["k2"].decode("ascii"),
        "tgt": consts["tgt"],
        "magic_mask": f"0x{consts['magic_mask']:08x}",
        "derive_words": ",".join(f"0x{x:08x}" for x in consts["derive_words"]),
        "p_xor": f"0x{consts['p_xor']:08x}",
        "q_add": f"0x{consts['q_add']:08x}",
    }


def main():
    parser = argparse.ArgumentParser(description="Universal EXP for com.example.mobile04 ISCC variants.")
    parser.add_argument("path", nargs="?", default="app-release.zip", help="zip/7z/apk path, default: app-release.zip")
    parser.add_argument("--verbose", action="store_true", help="print recovered constants")
    args = parser.parse_args()

    result = solve(args.path)
    print("sequence:", result["sequence"])
    print("input:", result["input"])
    print("cw:", result["cw"])
    print("flag:", result["flag"])
    if args.verbose:
        for key in ("so", "k1", "k2", "tgt", "magic_mask", "derive_words", "p_xor", "q_add"):
            print(f"{key}: {result[key]}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
