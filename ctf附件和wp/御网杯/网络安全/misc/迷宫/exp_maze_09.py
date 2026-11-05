from __future__ import annotations

import argparse
import base64
import re
import shutil
import zipfile
from pathlib import Path


BASE64_PREFIX = re.compile(rb"^([A-Za-z0-9+/]+={0,2})")


def extract_nested_zip(start_zip: Path, workdir: Path) -> tuple[list[Path], Path]:
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    chain = [start_zip]
    current = start_zip
    level = 0

    while zipfile.is_zipfile(current):
        level_dir = workdir / f"layer_{level}"
        level_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(current) as zf:
            zf.extractall(level_dir)
            files = [level_dir / info.filename for info in zf.infolist() if not info.is_dir()]

        if not files:
            raise RuntimeError(f"No files extracted from {current}")

        current = files[0]
        chain.append(current)
        level += 1

    return chain, current


def decode_vault(vault_path: Path) -> str:
    raw = vault_path.read_bytes().strip()
    match = BASE64_PREFIX.match(raw)
    if not match:
        raise ValueError(f"Could not locate a base64 prefix in {vault_path}")

    decoded = base64.b64decode(match.group(1)).decode("ascii")
    return decoded


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve maze_09.zip and recover the flag")
    parser.add_argument(
        "zip_path",
        nargs="?",
        default=Path(__file__).with_name("maze_09.zip"),
        type=Path,
        help="Path to maze_09.zip",
    )
    parser.add_argument(
        "--workdir",
        default=Path(__file__).with_name("_maze09_extract"),
        type=Path,
        help="Directory used for recursive extraction",
    )
    args = parser.parse_args()

    chain, final_file = extract_nested_zip(args.zip_path.resolve(), args.workdir.resolve())
    credential = decode_vault(final_file)
    flag = f"flag{{{credential}}}"

    print("[*] Extraction chain:")
    for item in chain:
        print(f"    {item}")

    print(f"[*] Final file: {final_file}")
    print(f"[*] Credential: {credential}")
    print(f"[+] Flag: {flag}")


if __name__ == "__main__":
    main()
