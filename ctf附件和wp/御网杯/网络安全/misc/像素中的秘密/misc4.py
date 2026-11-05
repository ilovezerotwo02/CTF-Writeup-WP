import zipfile
from pathlib import Path

ZIP_PATH = "image_08.zip"


def extract_png_from_zip(zip_path):
    with zipfile.ZipFile(zip_path, "r") as z:
        for name in z.namelist():
            if name.lower().endswith(".png"):
                print(f"[+] png name: {name}")
                return z.read(name)
    raise RuntimeError("zip 中没有找到 png 文件")


def get_png_trailer(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("不是合法 PNG 文件")

    pos = 8
    while pos < len(data):
        length = int.from_bytes(data[pos:pos+4], "big")
        chunk_type = data[pos+4:pos+8]
        chunk_end = pos + 12 + length

        print(f"[chunk] {chunk_type.decode(errors='ignore')} length={length} offset={pos}")

        pos = chunk_end
        if chunk_type == b"IEND":
            break

    extra = data[pos:]
    return extra


def lcg_xor_decrypt(extra):
    seed = int.from_bytes(extra[:8], "big")
    ct = extra[8:]

    print(f"[+] seed hex: {extra[:8].hex()}")
    print(f"[+] seed int: {seed}")
    print(f"[+] ciphertext length: {len(ct)}")

    a = 1664525
    c = 1013904223
    m = 2 ** 32

    state = seed
    pt = bytearray()

    for b in ct:
        state = (a * state + c) % m
        key = state & 0xff
        pt.append(b ^ key)

    return bytes(pt).rstrip(b"\x00")


def base62_decode(s):
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    n = 0
    for ch in s.decode():
        n = n * 62 + alphabet.index(ch)

    return n.to_bytes((n.bit_length() + 7) // 8, "big")


def main():
    png = extract_png_from_zip(ZIP_PATH)
    extra = get_png_trailer(png)

    print(f"[+] trailer length: {len(extra)}")
    print(f"[+] trailer hex: {extra.hex()}")

    base62_data = lcg_xor_decrypt(extra)
    print(f"[+] base62: {base62_data.decode()}")

    flag = base62_decode(base62_data)
    print(f"[+] flag: {flag.decode()}")


if __name__ == "__main__":
    main()