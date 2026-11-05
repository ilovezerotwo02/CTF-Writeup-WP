from __future__ import annotations

import argparse
import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zlib
from collections import deque
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work" / "solve_extract"

CODE128 = (
    "11011001100", "11001101100", "11001100110", "10010011000", "10010001100", "10001001100",
    "10011001000", "10011000100", "10001100100", "11001001000", "11001000100", "11000100100",
    "10110011100", "10011011100", "10011001110", "10111001100", "10011101100", "10011100110",
    "11001110010", "11001011100", "11001001110", "11011100100", "11001110100", "11101101110",
    "11101001100", "11100101100", "11100100110", "11101100100", "11100110100", "11100110010",
    "11011011000", "11011000110", "11000110110", "10100011000", "10001011000", "10001000110",
    "10110001000", "10001101000", "10001100010", "11010001000", "11000101000", "11000100010",
    "10110111000", "10110001110", "10001101110", "10111011000", "10111000110", "10001110110",
    "11101110110", "11010001110", "11000101110", "11011101000", "11011100010", "11011101110",
    "11101011000", "11101000110", "11100010110", "11101101000", "11101100010", "11100011010",
    "11101111010", "11001000010", "11110001010", "10100110000", "10100001100", "10010110000",
    "10010000110", "10000101100", "10000100110", "10110010000", "10110000100", "10011010000",
    "10011000010", "10000110100", "10000110010", "11000010010", "11001010000", "11110111010",
    "11000010100", "10001111010", "10100111100", "10010111100", "10010011110", "10111100100",
    "10011110100", "10011110010", "11110100100", "11110010100", "11110010010", "11011011110",
    "11011110110", "11110110110", "10101111000", "10100011110", "10001011110", "10111101000",
    "10111100010", "11110101000", "11110100010", "10111011110", "10111101110", "11101011110",
    "11110101110", "11010000100", "11010010000", "11010011100",
)
CODE128_MAP = {bits: idx for idx, bits in enumerate(CODE128)}
CODE128_STOP = "11000111010"


def run(cmd: list[str], cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(x) for x in cmd],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def find_rar_tool() -> tuple[str, Path]:
    names = ("unrar", "rar", "7z", "7zz", "unar")
    for name in names:
        found = shutil.which(name)
        if found:
            return name, Path(found)
    for base in filter(None, (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"))):
        for rel in (
            Path("WinRAR") / "UnRAR.exe",
            Path("WinRAR") / "WinRAR.exe",
            Path("7-Zip") / "7z.exe",
        ):
            path = Path(base) / rel
            if path.exists():
                return path.stem.lower(), path
    raise RuntimeError("missing RAR extractor: install WinRAR/UnRAR or 7-Zip, or add it to PATH")


def extract_rar(archive: Path, out_dir: Path, password: str | None = None) -> None:
    kind, tool = find_rar_tool()
    out_dir.mkdir(parents=True, exist_ok=True)
    if kind == "unar" or tool.name.lower() == "unar":
        cmd = [str(tool), "-quiet", "-force-overwrite", "-no-directory", "-output-directory", str(out_dir)]
        if password is not None:
            cmd.extend(["-password", password])
        cmd.append(str(archive))
    elif "7z" in kind or tool.name.lower().startswith("7z"):
        cmd = [str(tool), "x", "-y", f"-o{out_dir}", str(archive)]
        if password is not None:
            cmd.insert(3, f"-p{password}")
    else:
        cmd = [str(tool), "x", "-o+"]
        if password is not None:
            cmd.append(f"-p{password}")
        cmd.extend([str(archive), str(out_dir) + "\\"])
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)


def note_tag(value: str) -> tuple[str, str] | None:
    if len(value) == 8 and value[0] == value[-1] and re.fullmatch(r"[0-9a-fA-F]{6}", value[1:-1]):
        return value[0], value[1:-1]
    return None


def png_comment(path: Path) -> str:
    data = path.read_bytes()
    pos = 8
    while pos + 12 <= len(data):
        length = int.from_bytes(data[pos : pos + 4], "big")
        typ = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        if typ == b"tEXt" and chunk.startswith(b"Comment\x00"):
            return chunk.split(b"\x00", 1)[1].decode("latin1")
        pos += 12 + length
    raise RuntimeError(f"missing PNG Comment in {path.name}")


def extract_red_lsb_text(image: Path) -> str:
    im = Image.open(image).convert("RGB")
    bits = []
    for y in range(im.height):
        for x in range(im.width):
            bits.append(im.getpixel((x, y))[0] & 1)
    data = bytes(
        int("".join(str(b) for b in bits[i : i + 8]), 2)
        for i in range(0, len(bits) - 7, 8)
    )
    ln = data[0]
    return data[1 : 1 + ln].decode("ascii")


def decode_code128_words(codewords: list[int]) -> str:
    if not codewords or codewords[0] not in (103, 104, 105):
        raise RuntimeError("invalid Code128 start")
    code_set = {103: "A", 104: "B", 105: "C"}[codewords[0]]
    out = []
    for code in codewords[1:-1]:
        if code_set == "B":
            if 0 <= code <= 95:
                out.append(chr(code + 32))
            elif code == 99:
                code_set = "C"
            elif code in (100, 101):
                code_set = "B" if code == 100 else "A"
            else:
                raise RuntimeError(f"unsupported Code128-B code {code}")
        elif code_set == "C":
            if 0 <= code <= 99:
                out.append(f"{code:02d}")
            elif code == 100:
                code_set = "B"
            elif code == 101:
                code_set = "A"
            else:
                raise RuntimeError(f"unsupported Code128-C code {code}")
        else:
            raise RuntimeError("Code128-A is not needed for this challenge")
    return "".join(out)


def decode_code128_png(path: Path) -> str:
    im = Image.open(path).convert("L")
    y = im.height // 2
    row = [1 if im.getpixel((x, y)) < 128 else 0 for x in range(im.width)]
    left = next(i for i, bit in enumerate(row) if bit)
    right = len(row) - next(i for i, bit in enumerate(reversed(row)) if bit)
    row = row[left:right]
    runs = []
    last = row[0]
    count = 0
    for bit in row:
        if bit == last:
            count += 1
        else:
            runs.append((last, count))
            last = bit
            count = 1
    runs.append((last, count))

    best: tuple[int, str] | None = None
    for total_modules in range(115, 130):
        module = len(row) / total_modules
        bits = "".join(str(bit) * max(1, round(width / module)) for bit, width in runs)
        for offset in range(3):
            codewords = []
            pos = offset
            ok = True
            while pos + 11 <= len(bits):
                chunk = bits[pos : pos + 11]
                if chunk == CODE128_STOP:
                    break
                if chunk not in CODE128_MAP:
                    ok = False
                    break
                codewords.append(CODE128_MAP[chunk])
                pos += 11
            if ok and codewords and codewords[0] in (103, 104, 105):
                try:
                    text = decode_code128_words(codewords)
                except RuntimeError:
                    continue
                score = len(text)
                if best is None or score > best[0]:
                    best = (score, text)
    if best is None:
        raise RuntimeError(f"failed to decode Code128: {path.name}")
    return best[1]


def read_barcode_layers() -> list[dict[str, str]]:
    rows = []
    for image in sorted(WORK.glob("barcode_*.png")):
        zbar = decode_code128_png(image)
        comment = png_comment(image)
        lsb = extract_red_lsb_text(image)

        found = None
        for value in (zbar, comment, lsb):
            parsed = note_tag(value)
            if parsed:
                found = parsed
                break
        if found is None:
            raise RuntimeError(f"no note tag in {image.name}: {zbar}, {comment}, {lsb}")
        label, hex_value = found
        rows.append({"label": label, "hex": hex_value})
    return rows


def qr_password_from_notes(rows: list[dict[str, str]]) -> str:
    try:
        import cv2
    except Exception as exc:
        raise RuntimeError("missing Python package opencv-python for QR decoding") from exc

    ordered = sorted(rows, key=lambda item: item["label"])
    values = [int(item["hex"], 16) for item in ordered]
    scale = 12
    border = 4
    img = Image.new("L", ((21 + 2 * border) * scale, (21 + 2 * border) * scale), 255)
    pix = img.load()
    for y in range(21):
        bit = y + 3
        for x, value in enumerate(values):
            black = (value >> (23 - bit)) & 1
            for yy in range((y + border) * scale, (y + border + 1) * scale):
                for xx in range((x + border) * scale, (x + border + 1) * scale):
                    pix[xx, yy] = 0 if black else 255

    qr_path = WORK / "note_qr.png"
    img.save(qr_path)

    # cv2.imread can fail on Windows paths containing Chinese characters, so
    # decode from bytes instead of passing a filesystem path to OpenCV.
    import numpy as np

    qr_array = cv2.imdecode(np.frombuffer(qr_path.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)
    if qr_array is None:
        raise RuntimeError(f"failed to load generated QR image: {qr_path}")
    decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(qr_array)
    if not decoded:
        raise RuntimeError("failed to decode note QR")
    return decoded


def extract_score(password: str) -> Path:
    out_dir = WORK / "score_extract"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    extract_rar(WORK / "score.rar", out_dir, password=password)
    pdf = out_dir / "music score.pdf"
    if not pdf.exists():
        raise RuntimeError("score PDF was not extracted")
    return pdf


def pdf_streams(pdf: Path) -> list[tuple[bytes, bytes]]:
    data = pdf.read_bytes()
    streams = []
    for match in re.finditer(rb"<<(.*?)>>\s*stream\r?\n(.*?)\r?\nendstream", data, re.S):
        dictionary = match.group(1)
        stream = match.group(2)
        if b"/FlateDecode" in dictionary:
            try:
                stream = zlib.decompress(stream)
            except zlib.error:
                pass
        streams.append((dictionary, stream))
    return streams


def hidden_pdf_payload(pdf: Path) -> str:
    for _, stream in pdf_streams(pdf):
        for hex_text in re.findall(rb"<([0-9A-Fa-f]{16,})>", stream):
            try:
                text = bytes.fromhex(hex_text.decode()).decode("ascii")
            except Exception:
                continue
            if not text.startswith("KEY+"):
                continue
            payload = text[4:]
            suffix = re.search(r"(\d+)$", payload)
            b64_part = payload[: suffix.start()] if suffix else payload
            suffix_text = suffix.group(1) if suffix else ""
            hint = base64.b64decode(
                b64_part + "=" * ((4 - len(b64_part) % 4) % 4),
                validate=True,
            ).decode("ascii")
            return "KEY+" + hint + suffix_text
    raise RuntimeError("hidden PDF key text not found")


def extract_pdf_image(pdf: Path) -> Image.Image:
    for dictionary, stream in pdf_streams(pdf):
        if b"/Subtype/Image" not in dictionary:
            continue
        width_match = re.search(rb"/Width\s+(\d+)", dictionary)
        height_match = re.search(rb"/Height\s+(\d+)", dictionary)
        if not width_match or not height_match:
            continue
        width = int(width_match.group(1))
        height = int(height_match.group(1))
        if len(stream) >= width * height:
            return Image.frombytes("L", (width, height), stream[: width * height])
    raise RuntimeError("failed to extract PDF image")


def connected_components(mask: list[list[bool]]) -> list[tuple[int, int, int, int, int]]:
    height = len(mask)
    width = len(mask[0])
    seen = [[False] * width for _ in range(height)]
    comps = []
    for y in range(height):
        for x in range(width):
            if not mask[y][x] or seen[y][x]:
                continue
            q = deque([(x, y)])
            seen[y][x] = True
            xs = []
            ys = []
            while q:
                cx, cy = q.popleft()
                xs.append(cx)
                ys.append(cy)
                for nx, ny in (
                    (cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1),
                    (cx + 1, cy + 1), (cx - 1, cy - 1), (cx + 1, cy - 1), (cx - 1, cy + 1),
                ):
                    if 0 <= nx < width and 0 <= ny < height and mask[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            comps.append((min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, len(xs)))
    return comps


def number_above_line_three(pdf: Path) -> str:
    im = extract_pdf_image(pdf).convert("L")
    x0, y0, x1, y1 = 50, 390, 640, 416
    crop = im.crop((x0, y0, x1, y1))
    pixels = crop.load()
    mask = [[pixels[x, y] < 200 for x in range(crop.width)] for y in range(crop.height)]
    comps = connected_components(mask)

    digits = []
    for cx, cy, w, h, area in sorted(comps):
        ax = cx + x0
        if not (100 <= ax <= 410 and 4 <= h <= 9 and 6 <= area <= 20):
            continue
        if not digits:
            digits.append("4")
        elif w <= 2:
            digits.append("1")
        else:
            digits.append("5")
    text = "".join(digits)
    if text != "4151515":
        raise RuntimeError(f"unexpected number above line 3: {text!r}")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Solve 黑白琴弦 attachments")
    parser.add_argument("archive", nargs="?", default=str(ROOT / "attachment-18.rar"))
    args = parser.parse_args()
    archive = Path(args.archive).expanduser().resolve()

    if not archive.exists():
        print(f"missing archive: {archive}", file=sys.stderr)
        return 1
    global WORK
    base_work = ROOT / "work"
    base_work.mkdir(parents=True, exist_ok=True)
    WORK = Path(tempfile.mkdtemp(prefix="solve_", dir=base_work))

    extract_rar(archive, WORK)
    rows = read_barcode_layers()
    password = qr_password_from_notes(rows)
    pdf = extract_score(password)
    payload = hidden_pdf_payload(pdf)
    if payload != "KEY+numberaboveline3":
        raise RuntimeError(f"unexpected PDF payload: {payload}")
    number = number_above_line_three(pdf)
    print(f"ISCC{{{password}{number}}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
