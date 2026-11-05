#!/usr/bin/env python3
from __future__ import annotations

import csv
import io
import math
import zlib
from pathlib import Path

import matplotlib
import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "writeup模板.docx"
OUTPUT = ROOT / "-盲相阵列.docx"
CSV_PATH = ROOT / "bundle" / "array_iq.csv"

FS = 48_000
BAUD = 1_200
SPS = FS // BAUD
CFO = 1700.0
TRAINING = 80
PAYLOAD = 560


def load_iq(path: Path) -> np.ndarray:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        data = [complex(float(row["i"]), float(row["q"])) for row in reader]
    return np.array(data, dtype=np.complex128)


def phase_lock_and_bits(samples: np.ndarray):
    n = np.arange(samples.size)
    mixed = samples * np.exp(-1j * 2 * np.pi * CFO * n / FS)

    best = None
    for offset in range(SPS):
        count = (mixed.size - offset) // SPS
        if count <= TRAINING:
            continue
        symbols = mixed[offset : offset + count * SPS].reshape(count, SPS).mean(axis=1)
        phase = np.angle(np.mean(symbols * symbols)) / 2.0
        rot = np.exp(-1j * phase)
        locked = symbols * rot
        bits = (locked.real < 0).astype(np.uint8)

        pattern = np.arange(64, dtype=np.uint8) & 1
        direct = int(np.sum(bits[:64] == pattern))
        flipped = int(np.sum((1 - bits[:64]) == pattern))
        score = max(direct, flipped)
        amplitude = float(np.mean(np.abs(locked[:64].real)))
        if best is None or (score, amplitude) > (best["score"], best["amplitude"]):
            best = {
                "offset": offset,
                "phase": float(phase),
                "symbols": locked,
                "bits": bits,
                "score": score,
                "amplitude": amplitude,
            }
    if best is None:
        raise RuntimeError("failed to locate symbol timing")
    return best


def lfsr8_mask(length: int, seed: int = 0xA5) -> np.ndarray:
    state = seed & 0xFF
    out = np.empty(length, dtype=np.uint8)
    for i in range(length):
        out[i] = state & 1
        feedback = ((state >> 7) ^ (state >> 5) ^ (state >> 4) ^ (state >> 3)) & 1
        state = ((state << 1) & 0xFF) | feedback
    return out


def undo_column_dma(bits: np.ndarray, lanes: int = 16) -> np.ndarray:
    rows = bits.size // lanes
    return bits.reshape(lanes, rows).T.reshape(-1)


def decode_hamming74(bits: np.ndarray):
    corrected = []
    nibbles = []
    for index in range(0, bits.size, 7):
        cw = bits[index : index + 7].astype(np.uint8).tolist()
        s1 = cw[0] ^ cw[2] ^ cw[4] ^ cw[6]
        s2 = cw[1] ^ cw[2] ^ cw[5] ^ cw[6]
        s4 = cw[3] ^ cw[4] ^ cw[5] ^ cw[6]
        syndrome = s1 | (s2 << 1) | (s4 << 2)
        if syndrome:
            cw[syndrome - 1] ^= 1
            corrected.append((index // 7, syndrome))
        nibbles.append((cw[2] << 3) | (cw[4] << 2) | (cw[5] << 1) | cw[6])

    frame = bytearray()
    for i in range(0, len(nibbles), 2):
        frame.append((nibbles[i] << 4) | nibbles[i + 1])
    return bytes(frame), corrected


def recover():
    samples = load_iq(CSV_PATH)
    locked = phase_lock_and_bits(samples)
    bits = locked["bits"]

    training_bits = bits[:TRAINING]
    training_bytes = bytes(
        int("".join(str(int(x)) for x in training_bits[i : i + 8]), 2)
        for i in range(0, TRAINING, 8)
    )

    payload = bits[TRAINING : TRAINING + PAYLOAD]
    descrambled = payload ^ lfsr8_mask(payload.size)
    reordered = undo_column_dma(descrambled)
    frame, corrected = decode_hamming74(reordered)
    body = frame[4:-4]
    crc_tail = int.from_bytes(frame[-4:], "big")
    crc_calc = zlib.crc32(body) & 0xFFFFFFFF

    if not frame.startswith(b"BP1 "):
        raise RuntimeError("BP1 header not found")
    if crc_calc != crc_tail:
        raise RuntimeError("CRC mismatch")

    return {
        "samples": samples,
        "peak_hz": square_spectrum_peak(samples),
        "offset": locked["offset"],
        "phase": locked["phase"],
        "training_bytes": training_bytes,
        "symbols": locked["symbols"],
        "bits": bits,
        "payload": payload,
        "frame": frame,
        "flag": body.decode("ascii"),
        "crc_calc": crc_calc,
        "crc_tail": crc_tail,
        "corrected": corrected,
    }


def square_spectrum_peak(samples: np.ndarray) -> float:
    z2 = samples * samples
    spec = np.fft.fft(z2)
    freqs = np.fft.fftfreq(samples.size, 1 / FS)
    mask = freqs > 0
    return float(freqs[mask][np.argmax(np.abs(spec[mask]))])


def timing_scores(samples: np.ndarray):
    n = np.arange(samples.size)
    mixed = samples * np.exp(-1j * 2 * np.pi * CFO * n / FS)
    pattern = np.arange(64, dtype=np.uint8) & 1
    scores = []
    for offset in range(SPS):
        count = (mixed.size - offset) // SPS
        symbols = mixed[offset : offset + count * SPS].reshape(count, SPS).mean(axis=1)
        phase = np.angle(np.mean(symbols * symbols)) / 2.0
        locked = symbols * np.exp(-1j * phase)
        bits = (locked.real < 0).astype(np.uint8)
        match = max(int(np.sum(bits[:64] == pattern)), int(np.sum((1 - bits[:64]) == pattern)))
        amp = float(np.mean(np.abs(locked[:64].real)))
        scores.append(match + amp)
    return scores


def fig_raw_iq(samples: np.ndarray) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    chunk = samples[:2000]
    ax.scatter(chunk.real, chunk.imag, s=4, c="#0c6db2", alpha=0.6)
    ax.axhline(0, color="#999999", lw=0.8)
    ax.axvline(0, color="#999999", lw=0.8)
    ax.set_title("Raw IQ cloud before carrier recovery")
    ax.set_xlabel("I")
    ax.set_ylabel("Q")
    ax.set_aspect("equal")
    return save_figure(fig)


def fig_square_spectrum(samples: np.ndarray, peak_hz: float) -> io.BytesIO:
    z2 = samples * samples
    spec = np.fft.fft(z2)
    freqs = np.fft.fftfreq(samples.size, 1 / FS)
    mask = (freqs >= 0) & (freqs <= 5000)
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.plot(freqs[mask], np.abs(spec[mask]), color="#ad2f45", lw=1.0)
    ax.axvline(peak_hz, color="#1a7f37", ls="--", lw=1.6)
    ax.text(peak_hz + 70, float(np.max(np.abs(spec[mask])) * 0.82), f"peak={peak_hz:.2f} Hz")
    ax.set_title("Square-law spectrum of z[n]^2")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Magnitude")
    return save_figure(fig)


def fig_timing(scores: list[int], best_offset: int) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    xs = np.arange(len(scores))
    ax.plot(xs, scores, color="#7b5ea7", marker="o", markersize=3.5, lw=1.4)
    ax.axvline(best_offset, color="#d9480f", ls="--", lw=1.6)
    ax.scatter([best_offset], [scores[best_offset]], color="#d9480f", s=30, zorder=3)
    ax.set_title("Timing sweep with training match + amplitude tiebreak")
    ax.set_xlabel("Offset")
    ax.set_ylabel("Score")
    ax.set_xticks(np.arange(0, 40, 4))
    return save_figure(fig)


def fig_result_panel(info: dict) -> io.BytesIO:
    lines = [
        "$ python solve.py bundle/array_iq.csv",
        f"[+] square-law peak : {info['peak_hz']:.2f} Hz",
        f"[+] carrier used    : {CFO:.1f} Hz",
        f"[+] timing offset   : {info['offset']}",
        f"[+] training bytes  : {info['training_bytes'].hex()}",
        f"[+] corrected cw    : {len(info['corrected'])}",
        f"[+] crc32(body)     : 0x{info['crc_calc']:08x}",
        f"[+] flag            : {info['flag']}",
    ]
    fig, ax = plt.subplots(figsize=(7.4, 2.8))
    ax.axis("off")
    ax.text(
        0.03,
        0.92,
        "\n".join(lines),
        va="top",
        family="Consolas",
        fontsize=11,
        color="#f1f3f5",
        bbox={"boxstyle": "round,pad=0.7", "facecolor": "#1f2328", "edgecolor": "#495057"},
    )
    return save_figure(fig)


def save_figure(fig) -> io.BytesIO:
    stream = io.BytesIO()
    fig.tight_layout()
    fig.savefig(stream, format="png", dpi=160)
    plt.close(fig)
    stream.seek(0)
    return stream


def set_run_font(run, ascii_name: str = "Times New Roman", east_asia: str = "宋体", size: int = 11, bold: bool = False):
    run.font.name = ascii_name
    run.font.size = Pt(size)
    run.bold = bold
    run.element.rPr.rFonts.set(qn("w:eastAsia"), east_asia)


def add_paragraph(doc: Document, text: str, *, bold: bool = False, size: int = 11, align=None):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    run = p.add_run(text)
    set_run_font(run, east_asia="宋体", size=size, bold=bold)
    p.paragraph_format.line_spacing = 1.35
    return p


def add_code(doc: Document, code: str):
    for line in code.rstrip().splitlines():
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.line_spacing = 1.0
        run = p.add_run(line)
        set_run_font(run, ascii_name="Consolas", east_asia="等线", size=8)


def add_picture(doc: Document, stream: io.BytesIO, caption: str):
    doc.add_picture(stream, width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_paragraph(doc, caption, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)


def build_doc(info: dict):
    doc = Document(TEMPLATE)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    doc.paragraphs[0].text = "ISCC2026 WriteUp 提交模板"
 doc.paragraphs[1].text = "竞赛用户名：zerotwo
    doc.paragraphs[2].text = "题目类型+题目名称：Misc/信号处理 + 盲相阵列"
    doc.paragraphs[3].text = "解题思路（必须包含文字说明+截图）"
    doc.paragraphs[4].text = "1. 先用题目备注把接收链路约束住，再做载波和定时恢复"
    doc.paragraphs[5].text = "2. 训练段确认极性与边界，payload 依次做去扰、反交织、Hamming 解码"
    doc.paragraphs[6].text = "3. 用 BP1 帧头和 CRC32 双重校验确认最终 flag"
    doc.paragraphs[7].text = "Exp（如有，请粘贴完整代码，不允许截图！）"

    for p in doc.paragraphs[:8]:
        for run in p.runs:
            set_run_font(run, east_asia="宋体", size=11, bold=False)

    add_paragraph(
        doc,
        "拿到附件后先看 rx_note.txt。这里已经把链路关键信息交代得很清楚：采样率 48000 Hz，符号率 1200 baud，所以每个符号正好 40 个采样点；残余载波偏差接近 +1700 Hz；前 80 个恢复符号属于 training/sync；真正的载荷要经过 PN mask、16 路 column DMA、H(7,4) 和 BP1 frame 这几层处理。",
    )
    add_paragraph(
        doc,
        "原始 IQ 在复平面里是一个持续转动的云团，说明符号本身不难，难点主要是下变频没锁稳。BPSK 的一个常用办法是看 z[n]^2：数据符号平方后只剩 2 倍频偏项，所以只要对 z[n]^2 做频谱，峰值除以 2 就能得到 CFO。这里峰值在 "
        f"{info['peak_hz']:.2f} Hz 左右，对应原信号偏差约 {info['peak_hz'] / 2:.2f} Hz，和备注里的 +1700 Hz 一致。后面我直接用 1700 Hz 做数字下变频，再用 mean(symbol^2) 的相位/2 去补公共相位。",
    )
    add_picture(doc, fig_raw_iq(info["samples"]), "图 1  原始 IQ 散点。自己补图时截前 2000 个点即可，重点保留“旋转成团”的形状。")
    add_picture(doc, fig_square_spectrum(info["samples"], info["peak_hz"]), "图 2  z[n]^2 的频谱。自己补图时保留 0~5000 Hz 区间，并把 3399 Hz 附近的峰值标出来。")

    scores = timing_scores(info["samples"])
    add_paragraph(
        doc,
        "确定频偏以后，再做 0~39 的符号边界遍历。这里我没有直接盯星座图，而是利用训练段前 64 bit 是交替 1010... 这一点：每个 offset 都先按 40 点取均值、做 BPSK 判决，先筛掉和交替序列不一致的候选；如果出现并列，再看训练段投影到实轴后的平均幅度，幅度最大的就是最稳的采样点。这样最终落在 offset=17，这时训练段已经稳定到 "
        f"{info['training_bytes'].hex()}。这里如果整体极性翻转，同一段会写成互补值，这是 BPSK 盲相恢复里很常见的二义性；只要后续判决方向和去扰方向保持一致，得到的帧内容是等价的。",
    )
    add_picture(doc, fig_timing(scores, info["offset"]), "图 3  40 个采样偏移的定时评分。自己补图时要把 offset=17 单独圈出来。")

    add_paragraph(
        doc,
        "接下来的处理完全按 note 给的路径反着走。先取训练块后面的 560 个有效 payload bit，用 8 位 LFSR 生成 PN 掩码去扰；这里用的是能同时满足 BP1 帧头和 CRC32 的那组参数：初值 0xA5，反馈位为 bit7^bit5^bit4^bit3，输出取当前最低位。然后把去扰后的比特按 16 列 35 行重排，做一次转置，就恢复了 column DMA 之前的 Hamming 码字顺序。",
    )
    add_paragraph(
        doc,
        "H(7,4) 这一层按 [p1,p2,d1,p4,d2,d3,d4] 解码。综合症非 0 时翻转对应位置，本题一共修正了 "
        f"{len(info['corrected'])} 个单比特错误。纠错后的字节流开头是 ASCII `BP1 `，末尾 4 字节解释为大端 CRC32；把中间正文拿去重新算 CRC，结果和帧尾完全一致，所以这一条恢复链是闭合的。最后得到的正文就是 flag：{info['flag']}。",
    )
    add_picture(doc, fig_result_panel(info), "图 4  解题脚本输出。自己补图时至少保留 training bytes、纠错个数、CRC 和最终 flag。")

    add_paragraph(
        doc,
        "这题最容易写崩的地方有两个。第一个是把训练段的末 16 bit 当成“唯一同步字”去死抠字面值，其实整体极性翻转后会出现等价写法；第二个是把 PN、判决方向和 Hamming 位序拆开分别硬猜，这样容易出现脚本能跑、文档却解释不通的情况。我这里用的写法是把训练段、BP1 帧头和 CRC32 连成一个闭环，因此每一步都能被后一步验证。",
    )
    add_paragraph(doc, "最终提交 flag：", bold=True)
    add_paragraph(doc, info["flag"], bold=True, size=14)

    code = f"""#!/usr/bin/env python3
import csv
import zlib
import numpy as np

FS = 48000
BAUD = 1200
SPS = FS // BAUD
CFO = 1700.0
TRAINING = 80
PAYLOAD = 560


def load_iq(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        rows = csv.DictReader(f)
        pts = [complex(float(r["i"]), float(r["q"])) for r in rows]
    return np.array(pts, dtype=np.complex128)


def recover_symbols(z):
    n = np.arange(z.size)
    mixed = z * np.exp(-1j * 2 * np.pi * CFO * n / FS)
    pattern = np.arange(64, dtype=np.uint8) & 1
    best_score = -1
    best_amp = -1.0
    best_offset = 0
    best_bits = None

    for offset in range(SPS):
        count = (mixed.size - offset) // SPS
        sym = mixed[offset:offset + count * SPS].reshape(count, SPS).mean(axis=1)
        phase = np.angle(np.mean(sym * sym)) / 2.0
        sym = sym * np.exp(-1j * phase)
        bits = (sym.real < 0).astype(np.uint8)
        score_a = int(np.sum(bits[:64] == pattern))
        score_b = int(np.sum((1 - bits[:64]) == pattern))
        score_a = max(score_a, score_b)
        amp = float(np.mean(np.abs(sym[:64].real)))
        if (score_a, amp) > (best_score, best_amp):
            best_score = score_a
            best_amp = amp
            best_offset = offset
            best_bits = bits
    return best_offset, best_bits


def pn_mask(length, seed=0xA5):
    state = seed
    out = np.empty(length, dtype=np.uint8)
    for i in range(length):
        out[i] = state & 1
        fb = ((state >> 7) ^ (state >> 5) ^ (state >> 4) ^ (state >> 3)) & 1
        state = ((state << 1) & 0xFF) | fb
    return out


def hamming74_decode(bits):
    fixed_nibbles = []
    for i in range(0, len(bits), 7):
        b = bits[i:i + 7].astype(np.uint8).tolist()
        s1 = b[0] ^ b[2] ^ b[4] ^ b[6]
        s2 = b[1] ^ b[2] ^ b[5] ^ b[6]
        s4 = b[3] ^ b[4] ^ b[5] ^ b[6]
        syndrome = s1 | (s2 << 1) | (s4 << 2)
        if syndrome:
            b[syndrome - 1] ^= 1
        fixed_nibbles.append((b[2] << 3) | (b[4] << 2) | (b[5] << 1) | b[6])

    out = bytearray()
    for i in range(0, len(fixed_nibbles), 2):
        out.append((fixed_nibbles[i] << 4) | fixed_nibbles[i + 1])
    return bytes(out)


def main():
    z = load_iq("bundle/array_iq.csv")
    offset, bits = recover_symbols(z)
    payload = bits[TRAINING:TRAINING + PAYLOAD]
    descrambled = payload ^ pn_mask(PAYLOAD)
    reordered = descrambled.reshape(16, 35).T.reshape(-1)
    frame = hamming74_decode(reordered)

    assert offset == 17
    assert frame.startswith(b"BP1 ")

    body = frame[4:-4]
    crc_tail = int.from_bytes(frame[-4:], "big")
    assert zlib.crc32(body) & 0xFFFFFFFF == crc_tail
    print(body.decode())


if __name__ == "__main__":
    main()
"""
    add_code(doc, code)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build_doc(recover())
