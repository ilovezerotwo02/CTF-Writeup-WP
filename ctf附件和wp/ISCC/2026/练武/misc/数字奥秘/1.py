import ast
import base64
import hashlib
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
FLAG_RE = re.compile(rb"ISCC\{[ -~]+\}")


def read_png_from_attachment(path: Path) -> bytes:
    raw = path.read_bytes()
    if raw.startswith(PNG_SIGNATURE):
        return raw
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            for item in zf.infolist():
                if item.is_dir():
                    continue
                data = zf.read(item)
                if data.startswith(PNG_SIGNATURE):
                    return data
    raise ValueError("no PNG data found")


def parse_png(data: bytes):
    pos = len(PNG_SIGNATURE)
    texts = {}
    trailer = b""
    while pos + 8 <= len(data):
        size = int.from_bytes(data[pos:pos + 4], "big")
        chunk_type = data[pos + 4:pos + 8]
        start = pos + 8
        end = start + size
        crc_end = end + 4
        if crc_end > len(data):
            raise ValueError("broken PNG chunk")
        chunk_data = data[start:end]
        if chunk_type == b"tEXt" and b"\x00" in chunk_data:
            key, value = chunk_data.split(b"\x00", 1)
            texts[key.decode("latin1")] = value.decode("latin1")
        pos = crc_end
        if chunk_type == b"IEND":
            trailer = data[pos:]
            break
    return texts, trailer


def select_text(texts: dict, suffix: str) -> str:
    for key, value in texts.items():
        if key.endswith(suffix):
            return value
    raise ValueError(f"missing text field *{suffix}")


def build_jump_table(code: str) -> dict:
    stack = []
    table = {}
    for index, char in enumerate(code):
        if char == "[":
            stack.append(index)
        elif char == "]":
            left = stack.pop()
            table[left] = index
            table[index] = left
    if stack:
        raise ValueError("unmatched [")
    return table


def round_tenth(value: int) -> int:
    if value >= 0:
        return (value + 5) // 10
    return -((-value + 5) // 10)


def run_fixed_vm(code: str):
    memory = [0] * 30000
    pointer = 0
    pc = 0
    steps = 0
    step_limit = max(1000000, len(code) * 1000)
    fp_tenths = 0
    output = []
    jump_table = build_jump_table(code)
    while pc < len(code):
        steps += 1
        if steps > step_limit:
            raise ValueError("VM step limit exceeded")
        cmd = code[pc]
        if cmd == ">":
            pointer = (pointer + 1) % len(memory)
        elif cmd == "<":
            pointer = (pointer - 1) % len(memory)
        elif cmd == "+":
            memory[pointer] += 1
        elif cmd == "-":
            memory[pointer] -= 1
        elif cmd == "[" and memory[pointer] == 0:
            pc = jump_table[pc]
        elif cmd == "]" and memory[pointer] != 0:
            pc = jump_table[pc]
        elif cmd == ".":
            output.append(memory[pointer])
        elif cmd == ",":
            memory[pointer] = 0
        elif cmd == "*":
            fp_tenths = memory[pointer]
        elif cmd == "#":
            output.append(round_tenth(fp_tenths))
        pc += 1
    return output


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def crt_pair(a1: int, m1: int, a2: int, m2: int):
    g = gcd(m1, m2)
    delta = a2 - a1
    if delta % g != 0:
        raise ValueError("inconsistent CRT data")
    left = m1 // g
    right = m2 // g
    step = (delta // g * pow(left, -1, right)) % right
    modulus = m1 * right
    value = (a1 + m1 * step) % modulus
    return value, modulus


def solve_crt(residues, moduli) -> int:
    value = 0
    modulus = 1
    for residue, mod in zip(residues, moduli):
        value, modulus = crt_pair(value, modulus, int(residue) % int(mod), int(mod))
    return value


def xor_repeat(data: bytes, key: bytes) -> bytes:
    return bytes(byte ^ key[index % len(key)] for index, byte in enumerate(data))


def extract_sync_prefix(texts: dict) -> str:
    prefixes = []
    for key in texts:
        if "_" in key:
            head = key.split("_", 1)[0]
            if head.isalpha():
                prefixes.append(head.upper())
    if not prefixes:
        raise ValueError("no metadata prefix found")
    return Counter(prefixes).most_common(1)[0][0]


def extract_sensor_word(texts: dict, trailer: bytes) -> str:
    combined = "\n".join(texts.values()) + "\n" + trailer.decode("utf-8", "ignore")
    match = re.search(r"\bsensor\b", combined, re.IGNORECASE)
    if not match:
        raise ValueError("no sensor marker found")
    return match.group(0).upper()


def candidate_key_materials(merged_result: int, texts: dict, trailer: bytes):
    prefix = extract_sync_prefix(texts)
    sensor = extract_sensor_word(texts, trailer)
    base = f"{prefix}_{sensor}_"
    yield str(merged_result)
    for number in range(10000):
        salt = f"{base}{number:04d}"
        yield f"{merged_result}:{salt}"
        yield f"{merged_result}{salt}"


def decrypt_payload(payload: bytes, merged_result: int, texts: dict, trailer: bytes) -> str:
    for material in candidate_key_materials(merged_result, texts, trailer):
        key = hashlib.sha256(material.encode()).digest()
        plain = xor_repeat(payload, key)
        if FLAG_RE.fullmatch(plain):
            return plain.decode("utf-8")
    raise ValueError("flag not recovered")


def recover_flag(path: Path) -> str:
    png_data = read_png_from_attachment(path)
    texts, trailer = parse_png(png_data)
    code = select_text(texts, "_CODE")
    periods = ast.literal_eval(texts["PERIODS"])
    payload = base64.b64decode(select_text(texts, "_PAYLOAD"))
    residues = run_fixed_vm(code)
    merged_result = solve_crt(residues, periods)
    return decrypt_payload(payload, merged_result, texts, trailer)


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("attachment-65.zip")
    try:
        print(recover_flag(path))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
