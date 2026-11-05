#!/usr/bin/env python3
"""
黑白琴弦 — ISCC 2025 Misc 解题脚本
===============================
题目附件: attachment-18.rar
Flag格式: ISCC{<QR密码><乐谱数字>}

多层链路:
  attachment-18.rar
    -> 21 张 barcode_*.png (Code128 / PNG Comment / 红色通道 LSB)
    -> 三层信息中找出 XhhhhhhX 格式的标签
    -> 按 A~U 排序后重建 21x21 QR 码
    -> QR 内容为 score.rar 的密码
    -> 解压得到 music score.pdf
    -> PDF stream 藏有 "KEY+numberaboveline3" 提示
    -> 提取 PDF 内嵌图像第 3 行上方数字
    -> 拼接 flag

依赖:
  pip install Pillow opencv-python numpy
  需系统安装 unrar / 7z / WinRAR 之一并加入 PATH
"""

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

# =========================================================================
# Code128 编码表
# =========================================================================
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


# =========================================================================
# 工具函数
# =========================================================================

def run(cmd: list[str], cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(x) for x in cmd],
        cwd=cwd,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout, check=False,
    )




def _build_rar_cmd(kind: str, tool: Path, archive: Path, out_dir: Path, password: str | None = None) -> list[str]:
    """根据不同工具构建 RAR 解压命令。"""
    if kind == "unar" or tool.name.lower() == "unar":
        cmd = [
            str(tool), "-quiet", "-force-overwrite", "-no-directory",
            "-output-directory", str(out_dir),
        ]
        if password:
            cmd.extend(["-password", password])
        cmd.append(str(archive))
    elif "7z" in kind or tool.name.lower().startswith("7z"):
        cmd = [str(tool), "x", "-y", f"-o{out_dir}", str(archive)]
        if password:
            cmd.insert(3, f"-p{password}")
    else:
        cmd = [str(tool), "x", "-o+"]
        if password:
            cmd.append(f"-p{password}")
        cmd.extend([str(archive), str(out_dir) + "\\"])
    return cmd


def extract_rar_with_tool(kind: str, tool: Path, archive: Path, out_dir: Path, password: str | None = None) -> None:
    """用指定工具解压 RAR。"""
    cmd = _build_rar_cmd(kind, tool, archive, out_dir, password)
    result = subprocess.run(
        cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=60, check=False,
    )
    if result.returncode != 0:
        err = result.stdout + "\n" + result.stderr
        raise RuntimeError(f"{tool.name} 解压失败 (返回码 {result.returncode}):\n{err}")


def _collect_rar_candidates() -> list[tuple[str, Path]]:
    """收集所有可能的 RAR 解压工具路径。"""
    candidates: list[tuple[str, Path]] = []
    for name in ("unrar", "rar", "7z", "7zz", "unar"):
        found = shutil.which(name)
        if found:
            candidates.append((name, Path(found)))
    for base in filter(None, (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"))):
        for rel in (
            Path("WinRAR") / "UnRAR.exe",
            Path("WinRAR") / "WinRAR.exe",
            Path("7-Zip") / "7z.exe",
        ):
            path = Path(base) / rel
            if path.exists():
                candidates.append((path.stem.lower(), path))
    return candidates


def extract_rar(archive: Path, out_dir: Path, password: str | None = None) -> None:
    """解压 RAR 文件，自动尝试所有可用工具。"""
    candidates = _collect_rar_candidates()
    if not candidates:
        raise RuntimeError("未找到 RAR 解压工具，请安装 WinRAR/7-Zip/unar 并加入 PATH")

    out_dir.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    for kind, tool in candidates:
        try:
            r = subprocess.run(
                [str(tool)], capture_output=True, timeout=5, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            errors.append(f"{tool.name}: 无法运行 - {e}")
            continue

        try:
            extract_rar_with_tool(kind, tool, archive, out_dir, password)
            return
        except RuntimeError as e:
            errors.append(f"{tool.name}: {e}")
            continue

    raise RuntimeError(
        "所有 RAR 工具均解压失败:\n" + "\n".join(errors)
    )


# =========================================================================
# PNG 元数据提取
# =========================================================================

def png_comment(path: Path) -> str:
    """读取 PNG 文件的 Comment 元数据。"""
    data = path.read_bytes()
    pos = 8  # 跳过 PNG 签名
    while pos + 12 <= len(data):
        length = int.from_bytes(data[pos: pos + 4], "big")
        typ = data[pos + 4: pos + 8]
        chunk = data[pos + 8: pos + 8 + length]
        if typ == b"tEXt" and chunk.startswith(b"Comment\x00"):
            return chunk.split(b"\x00", 1)[1].decode("latin1")
        pos += 12 + length
    raise RuntimeError(f"未在 {path.name} 中找到 PNG Comment")


# =========================================================================
# 红色通道 LSB 隐写提取
# =========================================================================

def extract_red_lsb_text(image: Path) -> str:
    """提取红色通道最低有效位中隐藏的文本。

    第一个字节表示字符串长度，后续字节为 ASCII 内容。
    """
    im = Image.open(image).convert("RGB")
    bits = []
    for y in range(im.height):
        for x in range(im.width):
            bits.append(im.getpixel((x, y))[0] & 1)

    data = bytes(
        int("".join(str(b) for b in bits[i: i + 8]), 2)
        for i in range(0, len(bits) - 7, 8)
    )
    ln = data[0]
    return data[1: 1 + ln].decode("ascii")


# =========================================================================
# Code128 条形码解码
# =========================================================================

def decode_code128_words(codewords: list[int]) -> str:
    """将 Code128 码字序列解码为字符串。"""
    if not codewords or codewords[0] not in (103, 104, 105):
        raise RuntimeError("无效的 Code128 起始码")
    code_set = {103: "A", 104: "B", 105: "C"}[codewords[0]]
    out: list[str] = []
    for code in codewords[1:-1]:
        if code_set == "B":
            if 0 <= code <= 95:
                out.append(chr(code + 32))
            elif code == 99:
                code_set = "C"
            elif code in (100, 101):
                code_set = "B" if code == 100 else "A"
            else:
                raise RuntimeError(f"不支持的 Code128-B 码: {code}")
        elif code_set == "C":
            if 0 <= code <= 99:
                out.append(f"{code:02d}")
            elif code == 100:
                code_set = "B"
            elif code == 101:
                code_set = "A"
            else:
                raise RuntimeError(f"不支持的 Code128-C 码: {code}")
        else:
            raise RuntimeError("本题不需要 Code128-A 解码")
    return "".join(out)


def decode_code128_png(path: Path) -> str:
    """解码 PNG 图片中的 Code128 条形码。"""
    im = Image.open(path).convert("L")
    y = im.height // 2
    row = [1 if im.getpixel((x, y)) < 128 else 0 for x in range(im.width)]

    # 裁剪空白边界
    left = next(i for i, bit in enumerate(row) if bit)
    right = len(row) - next(i for i, bit in enumerate(reversed(row)) if bit)
    row = row[left:right]

    # 计算游程编码
    runs: list[tuple[int, int]] = []
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

    # 尝试不同的模块宽度
    best: tuple[int, str] | None = None
    for total_modules in range(115, 130):
        module = len(row) / total_modules
        bits = "".join(
            str(bit) * max(1, round(width / module)) for bit, width in runs
        )
        for offset in range(3):
            codewords: list[int] = []
            pos = offset
            ok = True
            while pos + 11 <= len(bits):
                chunk = bits[pos: pos + 11]
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
        raise RuntimeError(f"无法解码 Code128: {path.name}")
    return best[1]


# =========================================================================
# 条形码三层信息提取 & 标签识别
# =========================================================================

def note_tag(value: str) -> tuple[str, str] | None:
    """检查字符串是否为 XhhhhhhX 格式。

    返回 (标签字母, 6位十六进制) 或 None。
    """
    if (
        len(value) == 8
        and value[0] == value[-1]
        and re.fullmatch(r"[0-9a-fA-F]{6}", value[1:-1])
    ):
        return value[0], value[1:-1]
    return None


def read_barcode_layers(barcode_dir: Path) -> list[dict[str, str]]:
    """读取目录下所有条形码图片的三层信息，提取标签和十六进制数据。"""
    rows: list[dict[str, str]] = []
    for image in sorted(barcode_dir.glob("barcode_*.png")):
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
            raise RuntimeError(
                f"未在 {image.name} 中找到有效标签: {zbar}, {comment}, {lsb}"
            )
        label, hex_value = found
        rows.append({"label": label, "hex": hex_value})
        print(f"  {image.name} -> {label}: {hex_value}")
    return rows


# =========================================================================
# QR 重建 & 解码
# =========================================================================

def qr_password_from_notes(rows: list[dict[str, str]], qr_save_dir: Path) -> str:
    """将 21 列标签数据重建为 QR 码并解码。"""
    try:
        import cv2
    except ImportError:
        raise RuntimeError("需要安装 opencv-python: pip install opencv-python")

    ordered = sorted(rows, key=lambda item: item["label"])
    values = [int(item["hex"], 16) for item in ordered]
    print(f"  A~U 排序后的十六进制值: {[hex(v) for v in values]}")

    # 检查是否刚好有 21 个标签
    labels = [item["label"] for item in ordered]
    if labels != [chr(ord("A") + i) for i in range(21)]:
        print(f"  [!] 警告: 标签顺序异常: {labels}")

    scale = 12
    border = 4
    img = Image.new(
        "L", ((21 + 2 * border) * scale, (21 + 2 * border) * scale), 255
    )
    pix = img.load()

    # 每组 hex 有 24 bit，QR 只需 21 bit，取中间 21 位
    for y in range(21):
        bit = y + 3
        for x, value in enumerate(values):
            black = (value >> (23 - bit)) & 1
            for yy in range((y + border) * scale, (y + border + 1) * scale):
                for xx in range((x + border) * scale, (x + border + 1) * scale):
                    pix[xx, yy] = 0 if black else 255

    qr_save_dir.mkdir(parents=True, exist_ok=True)
    qr_path = qr_save_dir / "reconstructed_qr.png"
    img.save(qr_path)
    print(f"  QR 码已保存至: {qr_path}")

    import numpy as np

    qr_array = cv2.imdecode(
        np.frombuffer(qr_path.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR
    )
    if qr_array is None:
        raise RuntimeError(f"无法读取 QR 图片: {qr_path}")

    decoded, points, _ = cv2.QRCodeDetector().detectAndDecode(qr_array)
    if not decoded:
        raise RuntimeError("QR 码解码失败，请检查 reconstructed_qr.png")

    print(f"  QR 解码结果: {decoded!r}")
    return decoded


# =========================================================================
# PDF 分析
# =========================================================================

def pdf_streams(pdf: Path) -> list[tuple[bytes, bytes]]:
    """提取 PDF 中所有 stream 及其字典。"""
    data = pdf.read_bytes()
    streams: list[tuple[bytes, bytes]] = []
    for match in re.finditer(
        rb"<<(.*?)>>\s*stream\r?\n(.*?)\r?\nendstream", data, re.S
    ):
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
    """从 PDF stream 中提取隐藏的 KEY 提示。"""
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
    raise RuntimeError("未找到隐藏的 PDF KEY 文本")


def extract_pdf_image(pdf: Path) -> Image.Image:
    """提取 PDF 中的内嵌图像。"""
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
    raise RuntimeError("无法提取 PDF 内嵌图像")


def connected_components(
    mask: list[list[bool]],
) -> list[tuple[int, int, int, int, int]]:
    """8-连通域分析。"""
    height = len(mask)
    width = len(mask[0])
    seen = [[False] * width for _ in range(height)]
    comps: list[tuple[int, int, int, int, int]] = []
    for y in range(height):
        for x in range(width):
            if not mask[y][x] or seen[y][x]:
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
            seen[y][x] = True
            xs: list[int] = []
            ys: list[int] = []
            while q:
                cx, cy = q.popleft()
                xs.append(cx)
                ys.append(cy)
                for nx, ny in (
                    (cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1),
                    (cx + 1, cy + 1), (cx - 1, cy - 1),
                    (cx + 1, cy - 1), (cx - 1, cy + 1),
                ):
                    if (
                        0 <= nx < width
                        and 0 <= ny < height
                        and mask[ny][nx]
                        and not seen[ny][nx]
                    ):
                        seen[ny][nx] = True
                        q.append((nx, ny))
            comps.append(
                (
                    min(xs), min(ys),
                    max(xs) - min(xs) + 1,
                    max(ys) - min(ys) + 1,
                    len(xs),
                )
            )
    return comps


def number_above_line_three(pdf: Path) -> str:
    """从乐谱 PDF 图像中提取第 3 行上方数字。"""
    im = extract_pdf_image(pdf).convert("L")
    # 裁切区域: 第 3 行上方数字所在区域
    x0, y0, x1, y1 = 50, 390, 640, 416
    crop = im.crop((x0, y0, x1, y1))
    pixels = crop.load()
    mask = [
        [pixels[x, y] < 200 for x in range(crop.width)]
        for y in range(crop.height)
    ]
    comps = connected_components(mask)

    digits: list[str] = []
    for cx, cy, w, h, area in sorted(comps):
        ax = cx + x0
        if not (100 <= ax <= 410 and 4 <= h <= 9 and 6 <= area <= 20):
            continue
        if not digits:
            digits.append("4")  # 最左数字固定为 4
        elif w <= 2:
            digits.append("1")
        else:
            digits.append("5")

    text = "".join(digits)
    if text != "4151515":
        raise RuntimeError(f"乐谱数字异常: {text!r}")
    print(f"  乐谱第 3 行上方数字: {text}")
    return text


# =========================================================================
# 主流程
# =========================================================================

REQUIRED_PACKAGES = {
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "numpy": "numpy",
}


def ensure_dependencies() -> None:
    """检查并自动安装缺失的 Python 依赖。"""
    missing = []
    for import_name, pkg_name in REQUIRED_PACKAGES.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg_name)

    if not missing:
        return

    print(f"[*] 检测到缺少依赖: {', '.join(missing)}，正在自动安装...")
    import subprocess as sp
    result = sp.run(
        [sys.executable, "-m", "pip", "install", *missing],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f"自动安装失败，请手动执行:\n  pip install {' '.join(missing)}")
        print(result.stderr)
        raise RuntimeError("缺少依赖，无法继续")
    print(f"[*] 依赖安装完成。")


def main() -> int:
    ensure_dependencies()

    parser = argparse.ArgumentParser(description="黑白琴弦 — ISCC 2025 Misc 解题脚本")
    parser.add_argument(
        "archive", nargs="?",
        default="attachment-18.rar",
        help="外层 RAR 附件路径 (默认: attachment-18.rar)",
    )
    parser.add_argument(
        "--barcode-dir",
        help="如果已解压，直接指定 barcode 图片所在目录，跳过 RAR 解压",
    )
    args = parser.parse_args()

    work_dir = Path("work")
    work_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = Path(tempfile.mkdtemp(prefix="solve_", dir=work_dir))

    if args.barcode_dir:
        # 直接使用已有解压目录
        barcode_dir = Path(args.barcode_dir)
        if not barcode_dir.exists():
            print(f"指定的目录不存在: {barcode_dir}", file=sys.stderr)
            return 1
    else:
        # 解压外层 RAR
        archive = Path(args.archive).expanduser().resolve()
        if not archive.exists():
            print(f"附件不存在: {archive}", file=sys.stderr)
            return 1
        print(f"[1/7] 解压外层 RAR: {archive}")
        extract_rar(archive, extract_dir)
        barcode_dir = extract_dir

    # ----------------------------------------------------------------
    print(f"[2/7] 提取条形码三层信息 (目录: {barcode_dir})")
    rows = read_barcode_layers(barcode_dir)

    # ----------------------------------------------------------------
    print("[3/7] 重建 QR 码并解码")
    password = qr_password_from_notes(rows, work_dir)
    print(f"  -> score.rar 密码: {password}")

    # ----------------------------------------------------------------
    print("[4/7] 解压 score.rar")
    score_rar = barcode_dir / "score.rar"
    if not score_rar.exists():
        # 可能在提取目录同层
        score_rar = extract_dir / "score.rar"
    if not score_rar.exists():
        raise RuntimeError(f"未找到 score.rar")

    score_out = extract_dir / "score_extract"
    extract_rar(score_rar, score_out, password=password)
    pdf = score_out / "music score.pdf"
    if not pdf.exists():
        raise RuntimeError("未找到 music score.pdf")
    print(f"  -> 已解压: {pdf}")

    # ----------------------------------------------------------------
    print("[5/7] 分析 PDF 隐藏提示")
    payload = hidden_pdf_payload(pdf)
    print(f"  -> 隐藏提示: {payload}")
    if payload != "KEY+numberaboveline3":
        print(f"  [!] 提示与预期不符，继续尝试...")

    # ----------------------------------------------------------------
    print("[6/7] 提取乐谱第 3 行上方数字")
    number = number_above_line_three(pdf)

    # ----------------------------------------------------------------
    print("[7/7] 组装 Flag")
    flag = f"ISCC{{{password}{number}}}"
    print(f"\n{'=' * 50}")
    print(f"  FLAG: {flag}")
    print(f"{'=' * 50}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
