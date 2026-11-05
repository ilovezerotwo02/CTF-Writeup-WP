from __future__ import annotations

import binascii
import shutil
import struct
import zlib
from pathlib import Path

import pyzipper


BASE = Path(__file__).resolve().parent
OUTER_ZIP = BASE / "10：SecretBackup的附件.zip"
WORK_DIR = BASE / "work_script"
INNER_ZIP = WORK_DIR / "tempdir" / "MISC附件" / "backup_2025Q1.zip"
EXTRACT_DIR = WORK_DIR / "extracted"


def prepare_workspace() -> None:
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(OUTER_ZIP), str(WORK_DIR))


def build_candidates() -> list[str]:
    parts = [
        "2025",
        "202501",
        "2025Q1",
        "2025q1",
        "secret",
        "backup",
        "SecretBackup",
        "secretbackup",
        "backup_2025Q1",
        "202501_secret",
    ]
    suffixes = ["", "!", "123", "2025", "202501", "Q1"]
    seps = ["", "_", "-", "@"]

    seen: set[str] = set()
    candidates: list[str] = []

    def add(value: str) -> None:
        if value and value not in seen:
            seen.add(value)
            candidates.append(value)

    for part in parts:
        variants = {part, part.lower(), part.upper(), part.capitalize()}
        for variant in variants:
            for suffix in suffixes:
                add(variant + suffix)
                if suffix:
                    for sep in seps:
                        add(variant + sep + suffix)

    for left in parts:
        for right in parts:
            if left == right:
                continue
            for sep in seps:
                add(f"{left}{sep}{right}")
                add(f"{left}{sep}{right}2025")
                add(f"{left}{sep}{right}202501")

    return candidates


def crack_password(zip_path: Path) -> str:
    candidates = build_candidates()
    with pyzipper.AESZipFile(zip_path) as zf:
        target = zf.namelist()[0]
        for password in candidates:
            try:
                zf.setpassword(password.encode("utf-8"))
                zf.read(target)
                return password
            except RuntimeError:
                continue
    raise RuntimeError("Password not found in the candidate set.")


def extract_inner(zip_path: Path, password: str) -> Path:
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with pyzipper.AESZipFile(zip_path) as zf:
        zf.setpassword(password.encode("utf-8"))
        zf.extractall(EXTRACT_DIR)
    return next(EXTRACT_DIR.glob("*.png"))


def repair_png(png_path: Path) -> Path:
    data = bytearray(png_path.read_bytes())

    # Restore the PNG signature.
    data[:8] = bytes.fromhex("89504E470D0A1A0A")

    width = struct.unpack(">I", data[16:20])[0]
    encoded_height = struct.unpack(">I", data[20:24])[0]

    # The IDAT stream expands to 800 rows even though IHDR says 400.
    idat_offset = 33
    idat_length = struct.unpack(">I", data[idat_offset : idat_offset + 4])[0]
    idat_data = data[idat_offset + 8 : idat_offset + 8 + idat_length]
    raw = zlib.decompress(idat_data)
    bytes_per_row = 1 + 3 * width
    actual_height = len(raw) // bytes_per_row
    if actual_height != encoded_height:
        data[20:24] = struct.pack(">I", actual_height)

    # Recalculate the IHDR CRC so image libraries accept the file.
    ihdr_offset = 8
    length = struct.unpack(">I", data[ihdr_offset : ihdr_offset + 4])[0]
    chunk_type = data[ihdr_offset + 4 : ihdr_offset + 8]
    chunk_data = data[ihdr_offset + 8 : ihdr_offset + 8 + length]
    crc = binascii.crc32(chunk_type)
    crc = binascii.crc32(chunk_data, crc) & 0xFFFFFFFF
    crc_offset = ihdr_offset + 8 + length
    data[crc_offset : crc_offset + 4] = struct.pack(">I", crc)

    repaired = png_path.with_name("202501_secret_repaired.png")
    repaired.write_bytes(data)
    return repaired


def main() -> None:
    prepare_workspace()
    password = crack_password(INNER_ZIP)
    extracted = extract_inner(INNER_ZIP, password)
    repaired = repair_png(extracted)

    print(f"inner zip: {INNER_ZIP}")
    print(f"password : {password}")
    print(f"xtracted: {extracted}")
    print(f"epaired: {repaired}")
    print("recovered: 2025 Q1 Financial Report")


if __name__ == "__main__":
    main()
