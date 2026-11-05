from __future__ import annotations

import argparse
import io
import struct
import zipfile
from pathlib import Path


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
LCG_A = 1664525
LCG_C = 1013904223
LCG_MOD = 1 << 32


def pick_png_blob(archive_path: Path) -> tuple[str, bytes]:
    with zipfile.ZipFile(archive_path, "r") as archive:
        png_names = [name for name in archive.namelist() if name.lower().endswith(".png")]
        if not png_names:
            raise ValueError("archive does not contain any PNG file")
        chosen = png_names[0]
        return chosen, archive.read(chosen)


def iterate_png_chunks(blob: bytes):
    if not blob.startswith(PNG_MAGIC):
        raise ValueError("input is not a valid PNG stream")

    cursor = len(PNG_MAGIC)
    total = len(blob)

    while cursor + 12 <= total:
        length = struct.unpack(">I", blob[cursor : cursor + 4])[0]
        chunk_type = blob[cursor + 4 : cursor + 8]
        data_start = cursor + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > total:
            raise ValueError("truncated PNG chunk encountered")

        yield {
            "offset": cursor,
            "type": chunk_type.decode("ascii", errors="replace"),
            "type_raw": chunk_type,
            "length": length,
            "data": blob[data_start:data_end],
            "next_offset": crc_end,
        }

        cursor = crc_end
        if chunk_type == b"IEND":
            break

    return cursor


def get_trailer(blob: bytes) -> bytes:
    trailer_offset = None
    for chunk in iterate_png_chunks(blob):
        print(f"chunk {chunk['type']} len={chunk['length']} offset={chunk['offset']}")
        if chunk["type_raw"] == b"IEND":
            trailer_offset = chunk["next_offset"]
            break

    if trailer_offset is None:
        raise ValueError("IEND chunk was not found")

    return blob[trailer_offset:]


def lcg_byte_stream(seed: int):
    state = seed
    while True:
        state = (LCG_A * state + LCG_C) % LCG_MOD
        yield state & 0xFF


def recover_base62_payload(trailer: bytes) -> bytes:
    if len(trailer) < 8:
        raise ValueError("trailer is too short")

    seed = int.from_bytes(trailer[:8], "big")
    encrypted = trailer[8:]

    print(f"种子: {seed} (0x{trailer[:8].hex()})")
    print(f"enc bytes:{len(encrypted)}")

    ks = lcg_byte_stream(seed)
    decoded = bytes(byte ^ next(ks) for byte in encrypted).rstrip(b"\x00")
    return decoded


def decode_base62_text(text: str) -> bytes:
    value = 0
    for ch in text:
        value = value * 62 + BASE62_ALPHABET.index(ch)
    width = max(1, (value.bit_length() + 7) // 8)
    return value.to_bytes(width, "big")


def solve(archive_path: Path) -> str:
    png_name, png_blob = pick_png_blob(archive_path)
    print(f"embedded png: {png_name}")

    trailer = get_trailer(png_blob)
    print(f"trailer长度: {len(trailer)}")
    print(f"trailer编码: {trailer.hex()}")

    base62_blob = recover_base62_payload(trailer)
    base62_text = base62_blob.decode("ascii")
    print(f"base62文本: {base62_text}")

    flag = decode_base62_text(base62_text).decode("utf-8")
    return flag


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve the PNG trailer challenge.")
    base_dir = Path(__file__).resolve().parent
    parser.add_argument(
        "archive",
        nargs="?",
        default=str(base_dir / "image_06.zip"),
        help="zip file that contains the challenge PNG",
    )
    args = parser.parse_args()

    archive_path = Path(args.archive)
    flag = solve(archive_path)
    print(f"解码:{flag}")


if __name__ == "__main__":
    main()
