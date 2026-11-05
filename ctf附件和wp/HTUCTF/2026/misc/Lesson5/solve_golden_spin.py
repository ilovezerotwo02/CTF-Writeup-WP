#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Solve the Misc challenge: 黄金回旋.

Usage:
    python solve_golden_spin.py 黄金回旋.zip

Requires Pillow: python -m pip install pillow
Outputs recovered.png in the current directory.
"""

import base64
import re
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

LONG_LINE_THRESHOLD = 1000
EXPECTED_SIZE = (952, 952)
FLAG_RE = re.compile(rb"HTUCTF\{[0-9a-fA-F]{32}\}")


def fibonacci_line_positions(limit: int) -> set[int]:
    """Return 1-based Fibonacci positions up to limit (1, 2, 3, 5, ...)."""
    positions = set()
    a, b = 1, 2
    while a <= limit:
        positions.add(a)
        a, b = b, a + b
    return positions


def inverse_transform(image: Image.Image) -> Image.Image:
    """Invert one round of the coordinate map (x', y') = ((x+y) mod N, x).

    Coordinates use x=column, y=row. For each pixel in the restored image,
    restored[y, x] = distorted[x, (x+y) mod N].
    The challenge applies the forward map twice, so call this twice.
    """
    import numpy as np

    arr = np.asarray(image.convert("RGB"))
    height, width = arr.shape[:2]
    if height != width:
        raise ValueError(f"Expected a square image, got {width}x{height}")

    y, x = np.indices((height, width))
    restored = arr[x, (x + y) % width]
    return Image.fromarray(restored, mode="RGB")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <challenge.zip>")
        return 2

    archive = Path(sys.argv[1])
    if not archive.is_file():
        print(f"[!] File not found: {archive}")
        return 2

    with zipfile.ZipFile(archive, "r") as zf:
        text_files = [name for name in zf.namelist() if not name.endswith("/")]
        if not text_files:
            raise RuntimeError("ZIP archive contains no files")
        # The challenge archive contains 黄金回旋.txt; choose it by extension,
        # falling back to the first file if its name differs.
        chosen = next((n for n in text_files if n.lower().endswith(".txt")), text_files[0])
        raw_text = zf.read(chosen)

    lines = raw_text.splitlines()
    print(f"[+] Input entry: {chosen}")
    print(f"[+] Total lines: {len(lines)}")

    # The long Base64 fragments occur at Fibonacci-numbered, 1-based lines.
    # The short lines are decoys. A length threshold identifies the actual
    # fragments; we also report whether their line numbers match Fibonacci.
    selected = [(i + 1, line) for i, line in enumerate(lines)
                if len(line.strip()) > LONG_LINE_THRESHOLD]
    fib_positions = fibonacci_line_positions(len(lines))
    selected_positions = {i for i, _ in selected}
    print(f"[+] Long Base64 fragments: {len(selected)}")
    print(f"[+] All selected line numbers are Fibonacci positions: "
          f"{selected_positions <= fib_positions}")
    if not selected:
        raise RuntimeError("No long Base64 fragments found")

    encoded = b"".join(line.strip() for _, line in selected)
    png_bytes = base64.b64decode(encoded)
    print(f"[+] Decoded image bytes: {len(png_bytes)}")

    # Verify that the extracted data is a readable image before transforming.
    image = Image.open(BytesIO(png_bytes)).convert("RGB")
    print(f"[+] Image size: {image.width}x{image.height}")
    if image.size != EXPECTED_SIZE:
        print(f"[!] Note: size differs from expected {EXPECTED_SIZE}")

    # The pixel coordinates were transformed twice using the Fibonacci-like
    # matrix map. Apply the inverse mapping twice to restore the image.
    image = inverse_transform(image)
    image = inverse_transform(image)

    output = Path("recovered.png")
    image.save(output)
    print(f"[+] Restored image saved to: {output.resolve()}")

    # The flag is visible in the restored image, rather than stored as ASCII
    # inside the PNG file. Print the known visual format as a reminder to read
    # the small text in the image; this regex only checks raw bytes, not OCR.
    match = FLAG_RE.search(png_bytes)
    if match:
        print(f"[+] Flag-like string found in raw image bytes: {match.group().decode()}")
    else:
        print("[*] No literal flag in PNG bytes; inspect recovered.png (flag is drawn in the image).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
