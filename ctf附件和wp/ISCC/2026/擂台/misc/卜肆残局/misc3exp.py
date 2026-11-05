#!/usr/bin/env python3
"""
[!] 卜肆残局 - Full Exploit Script
    城南旧庙怪卦摊 · 四象破局全自动化解器

Usage:
    python3 exp.py [--dir <challenge_directory>]

Environment:
    - Python 3.8+
    - pip install pycryptodome
    - 7z command available in PATH (for extraction fallback)
"""

import hashlib
import re
import sys
import zipfile
from base64 import b64decode
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
except ImportError:
    sys.exit("[!] Missing pycryptodome. Run: pip install pycryptodome")


# =============================================================================
# Constants
# =============================================================================

B64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

# Fragment values extracted from the four "old items" (天象·人言·地盘·时令)
FRAGMENTS = {
    "heaven":   "qW2O0z",   # 天象 — from 洛书九宫 SVG
    "human":    "5bnImG",   # 人言 — from 签筒布局 64-sign arrangement
    "earth":    "4yFuUc",   # 地盘 — from 六爻卦象 BMP LSB stego
    "season":   "4Y0nV9",   # 时令 — from 节气漏刻 CSV time series
}

# Order specified by the challenge: 天 → 人 → 地 → 时
FRAGMENT_ORDER = ["heaven", "human", "earth", "season"]

ZIP_COMMENT_EXPECTED = "q7LxP0aR9Yv+u1kC3wFjI2sQmD4oJ6GfXr5hN8KpTtUVeBylHcSgZdWiEOAbMn/z"
EXPECTED_TXT_COUNT = 64

# Final encrypted payload
CIPHERTEXT_B64 = "7jgRTVRxS/HSsI673SWW2yglLJbYZq295x7Eu6qCEvymWnnhkwyDg/8CduA2gQpF"


# =============================================================================
# Stage 1: Build the intermediate key from four fragments
# =============================================================================

def assemble_mid_key() -> Tuple[str, str]:
    """
    Concatenate the four fragments in 天-人-地-时 order,
    then compute MD5 as the ZIP password.

    Returns:
        (mid_key_string, md5_password_hex)
    """
    mid = "".join(FRAGMENTS[k] for k in FRAGMENT_ORDER)
    md5_pwd = hashlib.md5(mid.encode()).hexdigest()
    return mid, md5_pwd


# =============================================================================
# Stage 2: ZIP comment indexing extraction
# =============================================================================

def extract_zip_comment(archive_path: Path) -> str:
    """Read the Comment field from a ZIP archive."""
    with zipfile.ZipFile(archive_path, "r") as zf:
        return zf.comment.decode("utf-8")


def locate_txt_files(directory: Path) -> List[Path]:
    """
    Find all .txt files in the given directory and sort them
    by the first numeric group in their filename.
    """
    files = list(directory.glob("*.txt"))
    if not files:
        files = list(directory.rglob("*.txt"))

    def numeric_sort_key(p: Path) -> int:
        matches = re.findall(r"\d+", p.stem)
        return int(matches[0]) if matches else 9999

    files.sort(key=numeric_sort_key)
    return files


def index_lookup_extraction(comment: str, txt_files: List[Path]) -> str:
    """
    For each character position i in the comment:
      1. Look up the character's index in the Base64 alphabet
      2. Read the i-th TXT file and extract the character at that index

    Returns the concatenated password string.
    """
    result_chars: List[str] = []

    for i, comment_char in enumerate(comment):
        if i >= len(txt_files):
            break
        alphabet_pos = B64_ALPHABET.index(comment_char)
        content = txt_files[i].read_text("utf-8", errors="ignore")
        result_chars.append(content[alphabet_pos])

    return "".join(result_chars)


# =============================================================================
# Stage 3: AES-CBC Decryption
# =============================================================================

def decrypt_flag(mid: str, seven_pwd: str, ciphertext_b64: str) -> str:
    """
    Decrypt the AES-CBC payload.
      - Key = first 16 bytes of mid
      - IV  = first 16 bytes of seven_pwd
    """
    key = mid.encode("utf-8")[:16]
    iv = seven_pwd.encode("utf-8")[:16]
    ciphertext = b64decode(ciphertext_b64)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plaintext.decode("utf-8")


# =============================================================================
# UI Helpers
# =============================================================================

def banner() -> None:
    print()
    print("  ╔═══════════════════════════════════════╗")
    print("  ║   城南旧庙 · 卦摊破局自动化解器       ║")
    print("  ║   卜肆残局 — Multi-Stage CTF Solver   ║")
    print("  ╚═══════════════════════════════════════╝")
    print()


def check_7z_available() -> bool:
    """Return True if 7z command is available."""
    import shutil
    return shutil.which("7z") is not None


# =============================================================================
# Extraction helpers
# =============================================================================

def extract_with_7z(archive: Path, password: str, output_dir: Path) -> bool:
    """Extract using 7z with password. Returns True on success."""
    import subprocess
    result = subprocess.run(
        ["7z", "x", str(archive), f"-p{password}", "-y", f"-o{output_dir}"],
        capture_output=True, text=True, timeout=60
    )
    return result.returncode == 0


def extract_with_python_zip(zip_path: Path, password: str, output_dir: Path) -> bool:
    """Extract password-protected ZIP with Python. Returns True on success."""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(output_dir, pwd=password.encode())
        return True
    except Exception:
        return False


# =============================================================================
# Main orchestrator
# =============================================================================

def solve(workdir: Path) -> None:
    banner()

    # ------------------------------------------------------------------
    # Phase 1: Mid-key assembly → password for 窥得天机.zip
    # ------------------------------------------------------------------
    print("[Phase 1/4]  Assembling intermediate key from four fragments...")

    mid, zip_pwd = assemble_mid_key()
    print(f"  ├─ Mid key (拼合):  {mid}")
    print(f"  └─ MD5 password:   {zip_pwd}")

    # Locate 窥得天机.zip
    tianji_zip = workdir / "窥得天机.zip"
    if not tianji_zip.exists():
        sys.exit(f"[!] 窥得天机.zip not found in {workdir}")

    # Extract 窥得天机.zip
    print("\n[Phase 2/4]  Extracting 窥得天机.zip...")
    out_dir = workdir / ".extract_tmp"
    extract_ok = extract_with_python_zip(tianji_zip, zip_pwd, out_dir)

    if not extract_ok:
        # Fallback to 7z
        print("  ├─ Python zipfile failed, trying 7z...")
        if not check_7z_available():
            sys.exit("[!] Cannot extract: no 7z in PATH and Python zipfile failed")
        extract_ok = extract_with_7z(tianji_zip, zip_pwd, out_dir)

    if not extract_ok:
        sys.exit("[!] Failed to extract 窥得天机.zip — wrong password?")

    print(f"  └─ Extracted to:   {out_dir}/")

    # Locate the extracted TXT files (may be in subdirectories)
    txt_files = locate_txt_files(out_dir)
    print(f"\n  ├─ TXT files found: {len(txt_files)}")

    if len(txt_files) != EXPECTED_TXT_COUNT:
        sys.exit(f"[!] Expected {EXPECTED_TXT_COUNT} txt files, got {len(txt_files)}")

    # ------------------------------------------------------------------
    # Phase 3: ZIP comment indexing → password for 终局.7z
    # ------------------------------------------------------------------
    print("\n[Phase 3/4]  Extracting ZIP comment index mapping...")

    comment = extract_zip_comment(tianji_zip)
    print(f"  ├─ ZIP comment:    {comment}")

    if comment != ZIP_COMMENT_EXPECTED:
        print(f"  ├─ [!] Warning: comment differs from expected")
        print(f"  │   Expected: {ZIP_COMMENT_EXPECTED}")

    seven_pwd = index_lookup_extraction(comment, txt_files)
    print(f"  └─ 7z password:    {seven_pwd}")

    # ------------------------------------------------------------------
    # Phase 4: AES-CBC final decryption
    # ------------------------------------------------------------------
    print("\n[Phase 4/4]  AES-CBC final decryption...")

    flag = decrypt_flag(mid, seven_pwd, CIPHERTEXT_B64)
    print(f"  └─ FLAG:          {flag}")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    import shutil
    if out_dir.exists():
        shutil.rmtree(out_dir, ignore_errors=True)
    print("\n[*] Temporary files cleaned up. Done.")

    return flag


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="卜肆残局 — 城南旧庙卦摊多阶段 CTF 自动化解器"
    )
    parser.add_argument(
        "--dir", "-d",
        type=Path,
        default=Path.cwd(),
        help="Challenge working directory (default: current directory)"
    )
    args = parser.parse_args()

    if not args.dir.exists():
        sys.exit(f"[!] Directory does not exist: {args.dir}")

    result = solve(args.dir.resolve())
    print(f"\n  ╔═══ 最终 Flag ═══╗")
    print(f"  ║ {result} ║")
    print(f"  ╚══════════════════╝")
    print()
