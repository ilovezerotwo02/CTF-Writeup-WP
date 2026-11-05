import base64
import gzip
import hashlib
import argparse
import zipfile
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image


CHANNEL_SEEDS = {
    "R": 863148490,
    "G": 72199925,
    "B": 2239801264,
}


CHANNEL_INDEX = {
    "R": 0,
    "G": 1,
    "B": 2,
}


def extract_lsb_payload(img: Image.Image, channel: int, max_bytes: int = 16) -> bytes:
    arr = np.array(img.convert("RGB"))
    bits = (arr[:, :, channel] & 1).reshape(-1)[: max_bytes * 8]
    return np.packbits(bits, bitorder="big").tobytes()


def scramble_between_markers(
    data: bytes,
    prefix: bytes = b"ISCC{",
    suffix: bytes = b"}",
    seed: int = 0,
) -> bytes:
    start = data.find(prefix)
    end = data.find(suffix, start + len(prefix))
    if start < 0 or end < 0:
        return data

    left = data[: start + len(prefix)]
    mid = np.frombuffer(data[start + len(prefix) : end], dtype=np.uint8).copy()
    right = data[end:]

    idx = np.arange(len(mid), dtype=np.int64)
    np.random.RandomState(seed).shuffle(idx)
    return left + bytes(mid[idx].tolist()) + right


def inner_flag_piece(data: bytes) -> str:
    text = data.decode()
    return text[text.index("{") + 1 : text.rindex("}")]


def solve_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as zf:
        img = Image.open(BytesIO(zf.read("Input.png")))
        state = np.load(BytesIO(zf.read("model_state.npz")))

    hint = gzip.decompress(base64.b64decode(bytes(state["base_hint_bytes"]))).decode()

    input_payloads = {
        ch: extract_lsb_payload(img, CHANNEL_INDEX[ch])
        for ch in ("R", "G", "B")
    }

    # In the recovered normal mode, apply_channel_transform permutes channels
    # as (R, G, B) -> (G, B, R), so logical B lands in the final G channel.
    output_g = scramble_between_markers(input_payloads["B"], seed=CHANNEL_SEEDS["B"])

    flag1_r = inner_flag_piece(input_payloads["R"])
    flag2_g = inner_flag_piece(output_g)
    digest = hashlib.md5((flag1_r + flag2_g).encode()).hexdigest()
    flag = f"ISCC{{{digest}}}"

    return {
        "path": path,
        "hint": hint,
        "input_payloads": input_payloads,
        "output_g": output_g,
        "flag1R": flag1_r,
        "flag2G": flag2_g,
        "flag": flag,
    }


def iter_targets(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(p) for p in paths]
    return sorted(Path(".").glob("*.zip"), key=lambda p: p.name.lower())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Solve TrainModel-style ISCC misc attachments."
    )
    parser.add_argument(
        "zipfiles",
        nargs="*",
        help="zip attachments to solve; defaults to all zip files in the current directory",
    )
    args = parser.parse_args()

    for path in iter_targets(args.zipfiles):
        result = solve_zip(path)
        print(f"== {result['path']} ==")
        print(result["hint"])
        for ch in ("R", "G", "B"):
            print(f"input {ch}: {result['input_payloads'][ch].decode()}")
        print(f"mapped final G: {result['output_g'].decode()}")
        print(f"flag1R = {result['flag1R']}")
        print(f"flag2G = {result['flag2G']}")
        print(result["flag"])
        print()


if __name__ == "__main__":
    main()
