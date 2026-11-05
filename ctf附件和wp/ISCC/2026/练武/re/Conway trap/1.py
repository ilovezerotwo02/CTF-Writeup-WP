import re
import sys
import zipfile
from pathlib import Path


def read_attachment(path: Path) -> bytes:
    data = path.read_bytes()
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if not n.endswith('/')]
            if not names:
                raise ValueError('zip archive is empty')
            exe_names = [n for n in names if n.lower().endswith('.exe')]
            name = exe_names[0] if exe_names else names[0]
            data = zf.read(name)
    return data


def rol8(x: int, n: int) -> int:
    return ((x << n) | (x >> (8 - n))) & 0xff


def ror8(x: int, n: int) -> int:
    return ((x >> n) | (x << (8 - n))) & 0xff


def inv_seed_round(buf: bytes) -> bytes:
    b = list(buf)
    b = [b[-1]] + b[:-1]
    for i in range(0, 16, 2):
        new_a = b[i]
        new_b = b[i + 1]
        old_b = ror8(new_b, 1) ^ new_a
        old_a = (new_a - old_b) & 0xff
        b[i] = old_a
        b[i + 1] = old_b
    return bytes(b)


def recover_seed(data: bytes) -> bytes:
    hits = re.findall(rb'(?<![0-9A-Fa-f])([0-9A-Fa-f]{32})\x00', data)
    if not hits:
        raise ValueError('seed target was not found')
    target = bytes.fromhex(hits[0].decode())
    seed = target
    for _ in range(5):
        seed = inv_seed_round(seed)
    return seed


def extract_hidden_secret(data: bytes) -> bytes:
    pattern = (
        rb'\xc7\x45\xe4(.{4})\xc7\x45\xe8(.{4})\xc7\x45\xec(.{4})'
        rb'\xc7\x45\xf0(.{4})\xc7\x45\xf4(.{4})\x66\xc7\x45\xf8(.{2})\xc6\x45\xfa(.)'
    )
    match = re.search(pattern, data, re.S)
    if not match:
        raise ValueError('hidden checker constants were not found')
    enc = b''.join(match.groups())
    return bytes(x ^ 0xcc for x in enc)


def recover_flag_body(seed: bytes, secret: bytes) -> str:
    out = []
    for i, value in enumerate(secret):
        t = ror8(value ^ 0xaa, 3)
        t = (t - ((i * 0x17) & 0xff)) & 0xff
        out.append(t ^ seed[i & 0x0f])
    return bytes(out).decode('latin1')


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('./附件')
    data = read_attachment(path)
    seed = recover_seed(data)
    secret = extract_hidden_secret(data)
    body = recover_flag_body(seed, secret)
    print('seed:', seed.hex())
    print('flag:', f'ISCC{{{body}}}')


if __name__ == '__main__':
    main()