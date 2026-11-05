# ISCC 2026 Misc — 镜厅中的回响 解题报告

| 项目 | 内容 |
|------|------|
| 题目 | 镜厅中的回响 (Echoes in the Mirror Hall) |
| 考点 | ZIP 伪加密、Echo Hiding 音频隐写、Morse 码、Atbash 密码 |

**Flag:** `ISCC{M9"J@@WC$YVE6:M}`

---

## 0x01 题目分析

题目描述提到"镜厅"、"重复播放的音乐"、"回响"，强烈暗示信息隐藏在音频的回声之中。附件是一个 ZIP 包，解压后得到一段 40 秒的 H.264 视频。

解题链路：

```
attachment-4.zip → task.mp4 → audio.wav
                                   ↓
                             倒谱分析 → 定位双回声延迟
                                   ↓
                             Echo Hiding → 800 bits
                                   ↓
                             Morse 解码 → 14 字符
                                   ↓
                             Atbash 置换 → Flag body
                                   ↓
                            ISCC{...}
```

---

## 0x02 ZIP 伪加密

直接解压提示密码。检查 ZIP 结构：

- 局部文件头 (PK\x03\x04) GPB flag = `0x00` → 未加密
- 中央目录头 (PK\x01\x02) GPB flag = `0x01` → 声称加密

这是标准的伪加密手法。将所有中央目录头和第 6 字节 bit 0 清零即可：

```python
data = bytearray(open("attachment-4.zip", "rb").read())
for pattern in [b"PK\x03\x04", b"PK\x01\x02"]:
    off = 6 if pattern == b"PK\x03\x04" else 8
    pos = 0
    while (pos := data.find(pattern, pos)) >= 0:
        data[pos + off] &= 0xFE
        pos += 4
open("fixed.zip", "wb").write(data)
```

修复后用 `zipfile` 或 `unzip` 正常提取，得到 `task.mp4`。

---

## 0x03 音频提取与回声分析

使用 ffmpeg 抽取 PCM 音频：

```bash
ffmpeg -i task.mp4 -vn -acodec pcm_s16le audio.wav
```

参数：44100 Hz、16-bit、立体声，时长约 40 秒，共 1,764,352 采样点。

左右声道相关系数 > 0.999，取均值作为单声道信号。

### 倒谱 (Cepstrum)

Echo Hiding 的原理是在原始信号上叠加一个延迟衰减副本：`y[n] = x[n] + α·x[n−d]`。在倒谱域中，回声延迟 d 会表现为一个尖峰。

倒谱定义：

$$c[n] = \mathcal{F}^{-1}\{\log|\mathcal{F}\{x[n]\}|^2\}$$

对前约 23 秒（2^20 采样点）计算倒谱，取前 500 个倒谱系数的峰值排序：

```python
import numpy as np
from scipy.io import wavfile

sr, x = wavfile.read("audio.wav")
mono = x[:, 0].astype(np.float64) * 0.5 + x[:, 1].astype(np.float64) * 0.5

spec = np.fft.rfft(mono[:1 << 20])
cepstrum = np.fft.irfft(np.log(np.abs(spec) ** 2 + 1e-12))
peaks = np.argsort(cepstrum[1:500])[::-1][:10]
print(peaks + 1)  # → [100, 130, 200, 260, ...]
```

发现两个主导延迟：

| 延迟 (samples) | 时间 (ms) | 含义 |
|---|---|---|
| d0 = 100 | ≈ 2.27 ms | 代表 bit 0 |
| d1 = 130 | ≈ 2.95 ms | 代表 bit 1 |

---

## 0x04 Echo Hiding 解码

以 2205 采样点（50 ms）为窗宽，对每个窗口：

1. 去直流分量
2. 计算倒谱
3. 比较 d0 和 d1 附近（±3）的峰值能量
4. 能量高者即对应的比特值

```python
def decode_echo(mono, d0=100, d1=130, ws=2205):
    bits = []
    for offset in range(0, len(mono) - ws + 1, ws):
        seg = mono[offset:offset + ws] - mono[offset:offset + ws].mean()
        cep = np.fft.irfft(np.log(np.abs(np.fft.rfft(seg)) ** 2 + 1e-12))
        p0 = np.max(cep[max(d0 - 3, 1):d0 + 4])
        p1 = np.max(cep[max(d1 - 3, 1):d1 + 4])
        bits.append(int(p1 > p0))
    return bits
```

共解码 800 bits = 100 bytes。前 79 字节是可打印 ASCII 字符（空格、点、划、斜杠），之后变为 `\x00` 和乱码——这正是 Morse 码的有效载荷与其边界。

### 窗宽的选择

窗宽决定了比特率。尝试 1000–8000 范围的窗宽，2205（即 50 ms）时前段全部为有效 Morse 字符，且比特判决置信度最高，因此确定为最优窗宽。

---

## 0x05 Morse 解码

提取前 79 字节得到 Morse 电文：

```
-. ----. .-..-. --.- .--.-. .--.-. -.. -..- ...-..- -... . ...- -.... ---... -.
```

查 ITU-R M.1677 完整码表（含标点符号）逐组解码：

| Morse | 字符 |
|-------|------|
| `-.` | N |
| `----.` | 9 |
| `.-..-.` | " |
| `--.-` | Q |
| `.--.-.` | @ |
| `.--.-.` | @ |
| `-..` | D |
| `-..-` | X |
| `...-..-` | $ |
| `-...` | B |
| `.` | E |
| `...-` | V |
| `-....` | 6 |
| `---...` | : |
| `-.` | N |

拼接得到：`N9"Q@@DX$BEV6:N`

---

## 0x06 Atbash 置换

观察上述字符串中的字母部分，可以推断出题人使用了 **Atbash 密码**（字母表反转映射）：

$$A \leftrightarrow Z,\ B \leftrightarrow Y,\ C \leftrightarrow X,\ \dots$$

```python
table = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "ZYXWVUTSRQPONMLKJIHGFEDCBA"
)
body = "N9\"Q@@DX$BEV6:N".translate(table)
print(body)  # M9"J@@WC$YVE6:M
```

数字和符号保持不变，仅字母置换：

- N → M, Q → J, D → W, X → C, B → Y, E → V, V → E

得到最终 flag 主体：`M9"J@@WC$YVE6:M`

---

## 0x07 Flag

```
ISCC{M9"J@@WC$YVE6:M}
```

---

## 0x08 完整解题脚本

```python
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
    raise RuntimeError("ffmpeg not found")


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

    wav_path = extract_audio(zip_path, work_dir)
    print(f"[*] WAV: {wav_path}")

    sr, signal = wavfile.read(wav_path)
    mono = signal[:, 0].astype(np.float64) * 0.5 + signal[:, 1].astype(np.float64) * 0.5

    ws = 2205
    bitseq = cepstrum_decode(mono, win_size=ws)
    print(f"[*] Total bits decoded: {len(bitseq)}")

    raw_bytes = bits_to_bytes(bitseq)
    print(f"[*] Raw bytes: {len(raw_bytes)}")

    morse_end = 0
    while morse_end < len(raw_bytes) and chr(raw_bytes[morse_end]) in ".- /":
        morse_end += 1
    morse_text = raw_bytes[:morse_end].decode("ascii")
    print(f"[*] Morse text ({len(morse_text)} chars):")
    print(f"    {morse_text}")

    decoded = decode_morse(morse_text)
    print(f"[*] Morse decoded: {decoded}")

    flag_body = atbash(decoded)
    print(f"[*] After Atbash: {flag_body}")

    flag = f"ISCC{{{flag_body}}}"
    print(f"[*] FLAG: {flag}")

    assert flag == 'ISCC{M9"J@@WC$YVE6:M}', f"Flag mismatch: {flag}"


if __name__ == "__main__":
    main()
```

---

## 踩坑记录

1. **视频的 SEI NAL 段包含约 2.7 MB 的附加数据**，一开始怀疑是隐写载体，尝试 AES、RC4、XOR 均无结果。实际为干扰项/填充数据，不应在此消耗时间。
2. **窗宽的搜索**：Echo Hiding 的比特率未知。扫描 1000–8000 逐一验证前 N 字节是否全为可打印 ASCII，锁定 2205。
3. **Morse 表必须包含标点**：电文中包含 `.-..-.`（"）、`.--.-.`（@）、`...-..-`（$）等符号，标准字母表无法解码。
4. **Atbash 容易被忽略**：Morse 解码得到的字符串 `N9"Q@@DX$BEV6:N` 并非直接可用的 flag body，需要经过 Atbash 置换。题面"镜厅"中的"镜像"即暗示了字母反转。
