from __future__ import annotations

import base64
import re
import sys
import zipfile
from pathlib import Path


FLAG_RE = re.compile(rb"flag\{[0-9a-zA-Z\-_:]+\}")
BASE64_RE = re.compile(r"^[A-Za-z0-9+/=]+$")


def extract_flag_from_zip(zip_path: Path) -> tuple[str, int, str]:
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        if not names:
            raise ValueError("zip is empty")

        payload = zf.read(names[0]).decode("latin1", errors="ignore")

    lines = [line.strip() for line in payload.splitlines() if line.strip()]
    candidates = [line for line in lines if BASE64_RE.fullmatch(line)]
    if not candidates:
        raise ValueError("no base64-like line found")

    raw = base64.b64decode(candidates[-1])
    for key in range(256):
        decoded = bytes(b ^ key for b in raw)
        match = FLAG_RE.search(decoded)
        if match:
            return match.group().decode(), key, names[0]

    raise ValueError("no flag found after XOR brute force")


def main() -> int:
    base_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    zip_files = sorted(base_dir.glob("shadow_*.zip"))
    if not zip_files:
        print(f"[!] no shadow_*.zip found in {base_dir}")
        return 1

    for zip_path in zip_files:
        try:
            flag, key, inner_name = extract_flag_from_zip(zip_path)
            print(f"{zip_path.name}: {flag}  (xor_key={key}, inner_file={inner_name})")
        except Exception as exc:
            print(f"{zip_path.name}: ERROR - {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
