#!/usr/bin/env python3
"""ISCC 2026 misc - 镜厅中的回响 solver"""
import re, shutil, struct, subprocess, sys, zipfile
from pathlib import Path

import numpy as np
from scipy.io import wavfile

MORSE_TABLE = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
    "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
    "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
    ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
    "--..": "Z",
    "-----": "0", ".----": "1", "..---": "2", "...--": "3", "....-": "4",
    ".....": "5", "-....": "6", "--...": "7", "---..": "8", "----.": "9",
    ".-.-.-": ".", "--..--": ",", "..--..": "?", "-.-.--": "!",
    "-....-": "-", "-..-.": "/", "-.--.": "(", "-.--.-": ")",
    ".----.": "'", "---...": ":", "-.-.-.": ";", ".-.-.": "+",
    "-...-": "=", "..--.-": "_", ".-..-.": '"', "...-..-": "$",
    ".--.-.": "@", ".-...": "&",
}

ATBASH_TRANSLIT = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba",
)


def fix_zip_fake_encrypt(src: Path, dst: Path) -> None:
    """Reset GPB encryption bit in all local & central directory headers."""
    raw = bytearray(src.read_bytes())
    for magic in [b"PK\x03\x04", b"PK\x01\x02"]:
        off = 0
        while True:
            pos = raw.find(magic, off)
            if pos < 0:
                break
            flag_offset = pos + (6 if magic == b"PK\x03\x04" else 8)
            raw[flag_offset] &= 0xFE
            off = pos + 4
    dst.write_bytes(raw)


def find_ffmpeg() -> str:
    """Locate ffmpeg binary."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    local = Path(__file__).resolve().parent / "ffmpeg.exe"
    if local.exists():
        return str(local)
    raise RuntimeError("ffmpeg not found — install it or place ffmpeg.exe next to this script")


def extract_audio(zip_path: Path, work_dir: Path) -> Path:
    """Unzip (fixing fake encryption) and extract WAV audio."""
    work_dir.mkdir(parents=True, exist_ok=True)
    fixed = work_dir / "fixed.zip"
    fix_zip_fake_encrypt(zip_path, fixed)

    with zipfile.ZipFile(fixed) as zf:
        mp4_name = next(n for n in zf.namelist() if n.endswith(".mp4"))
        zf.extract(mp4_name, work_dir)

    mp4_path = work_dir / mp4_name
    wav_path = work_dir / "audio.wav"
    ffmpeg_bin = find_ffmpeg()
    subprocess.run(
        [ffmpeg_bin, "-y", "-v", "error",
         "-i", str(mp4_path), "-vn",
         "-acodec", "pcm_s16le", str(wav_path)],
        check=True,
    )
    return wav_path


def cepstrum_decode(samples, win_size=2205, d0=100, d1=130):
    """Decode echo-hiding bits via cepstrum peak comparison."""
    bits = []
    for start in range(0, len(samples) - win_size + 1, win_size):
        seg = samples[start:start + win_size]
        seg -= seg.mean()
        spec = np.fft.rfft(seg)
        cep = np.fft.irfft(np.log(np.abs(spec) ** 2 + 1e-12))
        e0 = np.max(cep[max(d0 - 3, 1):d0 + 4])
        e1 = np.max(cep[max(d1 - 3, 1):d1 + 4])
        bits.append(int(e1 > e0))
    return bits


def bits_to_bytes(bitseq):
    """Pack bits into bytes (MSB first)."""
    return bytes(
        int("".join(str(b) for b in bitseq[i:i + 8]), 2)
        for i in range(0, len(bitseq) - 7, 8)
    )


def decode_morse(morse_text):
    """Split morse groups and decode via table."""
    return "".join(MORSE_TABLE[tok] for tok in morse_text.split())


def atbash(text):
    """Apply Atbash cipher to letters only."""
    return text.translate(ATBASH_TRANSLIT)


def main():
    script_dir = Path(__file__).resolve().parent

    # Locate zip
    zip_path = None
    if len(sys.argv) > 1:
        zip_path = Path(sys.argv[1])
    else:
        for candidate in ["attachment-4.zip", "镜厅中的回响.zip"]:
            p = script_dir / candidate
            if p.exists():
                zip_path = p
                break
    if zip_path is None or not zip_path.exists():
        print("[!] Cannot find attachment-4.zip")
        sys.exit(1)

    work_dir = script_dir / "work" / "solve_v2"
    print(f"[*] Using zip: {zip_path}")

    # Step 1: extract audio
    wav_path = extract_audio(zip_path, work_dir)
    print(f"[*] WAV: {wav_path}")

    # Step 2: read audio and decode echo hiding
    sr, signal = wavfile.read(wav_path)
    # Average stereo channels, use float64
    mono = signal[:, 0].astype(np.float64) * 0.5 + signal[:, 1].astype(np.float64) * 0.5

    ws = 2205  # 50 ms at 44100 Hz
    bitseq = cepstrum_decode(mono, win_size=ws)
    print(f"[*] Total bits decoded: {len(bitseq)}")

    raw_bytes = bits_to_bytes(bitseq)
    print(f"[*] Raw bytes: {len(raw_bytes)}")

    # Step 3: extract Morse payload (everything before first null/control byte)
    morse_end = 0
    while morse_end < len(raw_bytes) and chr(raw_bytes[morse_end]) in ".- /":
        morse_end += 1
    morse_text = raw_bytes[:morse_end].decode("ascii")
    print(f"[*] Morse text ({len(morse_text)} chars):")
    print(f"    {morse_text}")

    # Step 4: decode Morse groups
    decoded = decode_morse(morse_text)
    print(f"[*] Morse decoded: {decoded}")

    # Step 5: Atbash substitution
    flag_body = atbash(decoded)
    print(f"[*] After Atbash: {flag_body}")

    # Step 6: wrap flag
    flag = f"ISCC{{{flag_body}}}"
    print(f"[*] FLAG: {flag}")

    # Verify
    assert flag == "ISCC{M9\"J@@WC$YVE6:M}", f"Flag mismatch: {flag}"


if __name__ == "__main__":
    main()
