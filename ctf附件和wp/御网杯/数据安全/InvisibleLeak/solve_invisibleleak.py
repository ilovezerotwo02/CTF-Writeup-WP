from __future__ import annotations

import io
import struct
import zipfile
from pathlib import Path

from PIL import Image
from pyzbar.pyzbar import decode


ROOT = Path(__file__).resolve().parent
POSTER = next(ROOT.rglob("poster.png"))
NOTICE = next(ROOT.rglob("notice.docx"))
PYC = next(ROOT.rglob("exfil_tool.pyc"))

ZW_MAP = {"\u200b": "00", "\u200c": "01", "\u200d": "10", "\ufeff": "11"}
ROT = list(range(8))
CIPHER_HEX = "c76a46ef52b009aafebc2553a0939c4e95de0b1dd6509f00f81a74638093cb6698d44a758359"


def inverse_cat_map(img: Image.Image, rounds: int = 7) -> Image.Image:
    w = img.width
    cur = img.copy()
    for _ in range(rounds):
        tmp = cur.copy()
        src = tmp.load()
        dst = cur.load()
        for x in range(w):
            for y in range(w):
                nx = (2 * x - y) % w
                ny = (-x + y) % w
                dst[nx, ny] = src[x, y]
    return cur


def extract_lsb_payload(img: Image.Image) -> bytes:
    px = img.load()
    w, h = img.size
    bits: list[int] = []
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y][:3]
            bits.extend((r & 1, g & 1, b & 1))

    raw = bytearray()
    for i in range(0, len(bits) - 7, 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        raw.append(byte)

    size = struct.unpack(">I", raw[:4])[0]
    return bytes(raw[4 : 4 + size])


def extract_doc_key(docx_path: Path) -> bytes:
    with zipfile.ZipFile(docx_path) as zf:
        document = zf.read("word/document.xml").decode("utf-8", "ignore")
    zw = [ch for ch in document if ch in ZW_MAP]
    bits = "".join(ZW_MAP[ch] for ch in zw)
    return bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits) - 7, 8))


def extract_qr_key(poster_path: Path) -> tuple[bytes, Image.Image]:
    poster = Image.open(poster_path).convert("RGB")
    restored = inverse_cat_map(poster, 7)
    payload = extract_lsb_payload(restored)
    hidden = Image.open(io.BytesIO(payload))
    qr_text = decode(hidden)[0].data.decode()
    return bytes.fromhex(qr_text), hidden


def ror8(value: int, shift: int) -> int:
    shift %= 8
    return ((value >> shift) | ((value << (8 - shift)) & 0xFF)) & 0xFF


def decrypt(cipher: bytes, key: bytes) -> bytes:
    out = bytearray()
    for i, b in enumerate(cipher):
        x = b ^ key[i % len(key)]
        out.append(ror8(x, ROT[i % 8]))
    return bytes(out)


def main() -> None:
    doc_key = extract_doc_key(NOTICE)
    qr_key, hidden_qr = extract_qr_key(POSTER)
    key = qr_key + doc_key
    flag = decrypt(bytes.fromhex(CIPHER_HEX), key).decode()

    out_dir = ROOT / "solution_artifacts"
    out_dir.mkdir(exist_ok=True)
    hidden_qr.save(out_dir / "hidden_qr.png")

    print(f"poster key: {qr_key.hex()}")
    print(f"notice key: {doc_key.hex()}")
    print(f"full key  : {key.hex()}")
    print(f"flag      : {flag}")


if __name__ == "__main__":
    main()
