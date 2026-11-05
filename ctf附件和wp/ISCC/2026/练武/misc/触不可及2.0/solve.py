#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
触不可及2.0 - ISCC Misc Challenge Exploit
===========================================
流程:
  1. PKF + WAV 分析 → 提取隐藏数据
  2. 图片OCR提取呼号 → 作为密码
  3. 解压 untouchable.zip
  4. 从 equality.txt / FLAC / WAV 中提取 flag

用法:
  python solve.py [--callsign CALLSIGN]
"""

import numpy as np
import wave
import struct
import zipfile
import os
import sys
import re
from collections import Counter

# ================================================================
# 配置
# ================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PKF_PATH = os.path.join(BASE_DIR, "Ludovico Einaudi-Una Mattina.pkf")
WAV_PATH = os.path.join(BASE_DIR, "Ludovico Einaudi-Una Mattina.wav")
ZIP_PATH = os.path.join(BASE_DIR, "untouchable.zip")
IMAGE_PATH = os.path.join(BASE_DIR, "..", "相框里的图片.png")


# ================================================================
# Part 1: 分析PKF文件
# ================================================================
def parse_pkf(path):
    """解析CHIRP格式PKF文件，提取数据组"""
    data = open(path, 'rb').read()

    # 头部 (64 bytes)
    magic = data[:4]  # k$!\x00
    wav_frames = struct.unpack('<I', data[4:8])[0]
    channels = struct.unpack('<I', data[12:16])[0]
    val_0x18 = struct.unpack('<I', data[24:28])[0]  # 35486
    val_0x1C = struct.unpack('<I', data[28:32])[0]  # 128

    print(f"[PKF] Magic: {magic}")
    print(f"[PKF] WAV帧数: {wav_frames}")
    print(f"[PKF] 声道数: {channels}")

    # 数据体 (body = 总大小 - 64)
    body = data[64:]
    groups = np.frombuffer(body, dtype=np.uint8).reshape(-1, 4)
    print(f"[PKF] 数据体: {len(body)} bytes, {len(groups)} 组")

    return groups, wav_frames, channels, val_0x18, val_0x1C


# ================================================================
# Part 2: 分析WAV文件
# ================================================================
def parse_wav(path):
    """读取WAV音频文件"""
    with wave.open(path, 'rb') as wav:
        sr = wav.getframerate()
        nframes = wav.getnframes()
        nchannels = wav.getnchannels()

        print(f"[WAV] 采样率: {sr} Hz")
        print(f"[WAV] 帧数: {nframes} ({nframes/sr:.1f}s)")
        print(f"[WAV] 声道: {nchannels}")

        frames = wav.readframes(nframes)
        samples = np.frombuffer(frames, dtype=np.int16)
        left = samples[0::2]
        right = samples[1::2]

        return sr, nframes, left, right


# ================================================================
# Part 3: PKF-WAV关联分析
# ================================================================
def analyze_relation(groups, sr, left):
    """分析PKF数据与WAF的对应关系"""
    byte0 = groups[:, 0]
    byte1 = groups[:, 1]
    byte2 = groups[:, 2]
    byte3 = groups[:, 3]

    # byte3有15种值: 0, 0x38-0x3E(7种低频), 0xB8-0xBE(7种高频)
    print(f"\n[分析] byte3唯一值: {sorted(set(byte3))} (15种)")
    print(f"[分析] byte0非零位置: {np.where(byte0 != 0)[0]}")
    print(f"[分析] byte1非零起始: {(np.where(byte1 != 0)[0][0]) if np.any(byte1 != 0) else 'none'}")

    # 映射byte3到0-14
    bt3_mapped = np.zeros(len(byte3), dtype=np.uint8)
    for i, v in enumerate(byte3):
        if v == 0:
            bt3_mapped[i] = 0
        elif 0x38 <= v <= 0x3E:
            bt3_mapped[i] = v - 0x38 + 1
        elif 0xB8 <= v <= 0xBE:
            bt3_mapped[i] = v - 0xB8 + 8

    # byte1的top2位编码数据流
    top2 = (byte1.astype(int) >> 6) & 3
    data_bytes = []
    for i in range(0, len(top2) - 3, 4):
        b = (top2[i] << 6) | (top2[i+1] << 4) | (top2[i+2] << 2) | top2[i+3]
        data_bytes.append(b)
    result = bytes(data_bytes)

    # 搜索可打印字符串
    strings = re.findall(b'[A-Za-z0-9_{} \\-.,:;!?@#$%^&*()\']{6,}', result)
    if strings:
        print(f"[分析] byte1数据流中发现字符串: {strings[:20]}")
    else:
        print("[分析] byte1数据流中无可读字符串")

    return bt3_mapped, top2


# ================================================================
# Part 4: 用密码解压ZIP
# ================================================================
def try_password(zip_path, password):
    """尝试用密码解压ZIP"""
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall("extracted", pwd=password.encode())
            print(f"\n[ZIP] *** 密码正确: '{password}' ***")
            # 列出所有文件
            for info in zf.infolist():
                if info.file_size > 0:
                    data = zf.read(info.filename, pwd=password.encode())
                    if info.filename.endswith('.txt'):
                        print(f"[ZIP] {info.filename}: {data[:500]}")
                        # 搜索flag
                        for line in data.split(b'\n'):
                            if b'ISCC{' in line or b'flag' in line.lower() or b'ISCC' in line:
                                print(f"[FLAG] {line.decode('utf-8', errors='replace')}")
                    else:
                        print(f"[ZIP] {info.filename}: {len(data)} bytes")
            return True
    except RuntimeError:
        return False
    except Exception as e:
        print(f"[ZIP] 错误: {e}")
        return False


def try_multiple_passwords(zip_path, passwords):
    """尝试多个密码"""
    for pwd in set(passwords):
        if try_password(zip_path, pwd):
            return pwd
    return None


def crack_with_bkcrack(zip_path, output_dir="extracted"):
    """使用bkcrack进行已知明文攻击"""
    print("\n[Crack] 尝试bkcrack攻击...")

    bkcrack_paths = [
        "/tmp/_MEI218562/res/cmd/bkcrack.exe",
        "/tmp/_MEI219402/res/cmd/bkcrack.exe",
    ]

    bkcrack = None
    for p in bkcrack_paths:
        if os.path.exists(p):
            bkcrack = p
            break

    if not bkcrack:
        print("[Crack] bkcrack未找到，跳过")
        return False

    from subprocess import run

    # 方法1: 使用FLAC文件的已知开头 (fLaC + STREAMINFO头部)
    flac_known = "664c6143"  # "fLaC" as hex
    print(f"[Crack] FLAC头已知明文: {flac_known}")

    result = run([
        bkcrack, "-C", zip_path,
        "-c", "untouchable/respect/Ludovico Einaudi - Writing Poems.flac",
        "-x", f"0 {flac_known}"
    ], capture_output=True, text=True, timeout=120)

    if "keys" in result.stdout and "found" in result.stdout.lower():
        print(f"[Crack] bkcrack成功!")
        print(result.stdout)
        return True

    print(f"[Crack] bkcrack攻击失败")
    return False


# ================================================================
# Part 5: 密码字典生成
# ================================================================
def generate_passwords(callsign=None):
    """生成可能的密码列表"""
    pws = set()

    # 类别1: 呼号相关
    if callsign:
        pws.add(callsign)
        pws.add(callsign.lower())
        pws.add(callsign.upper())

    # 类别2: 挑战名称
    pws.update(["untouchable", "Untouchable", "UNTOUCHABLE",
                 "触不可及", "触不可及2.0"])

    # 类别3: 无线电相关
    pws.update(["ham", "HAM", "radio", "RADIO", "baofeng", "BAOFENG",
                 "chirp", "CHIRP", "k$!", "k$21",
                 "UV5R", "uv5r", "UV-5R"])

    # 类别4: 阿波罗/月球
    pws.update(["apollo", "Apollo", "APOLLO", "apollo11", "Apollo11",
                 "moon", "MOON", "lunar", "LUNAR", "moonlanding",
                 "nasa", "NASA", "阿波罗", "aboluo"])

    # 类别5: 音乐相关
    pws.update(["Einaudi", "einaudi", "LudovicoEinaudi",
                 "UnaMattina", "unamattina",
                 "WritingPoems", "Fly", "fly",
                 "equality", "respect", "sincere"])

    # 类别6: "oooe"变体
    pws.update(["oooe", "OOOE", "Oooe", "oooE",
                 "eooo", "EOOO",
                 "oooe2022", "oooe2025",
                 "OscarOscarOscarEcho", "oscaroscaroscarecho"])

    # 类别7: 频率/数字
    pws.update(["4542300", "22050", "88200", "567804", "567868",
                 "141951", "35486",
                 "145.920", "145920", "434.000", "434000",
                 "144.640", "144640", "438.500", "438500"])

    # 类别8: 年份/ISCC
    pws.update(["iscc", "ISCC", "iscc2022", "ISCC2022",
                 "2022", "2025", "2.0", "v2.0"])

    # 类别9: 常见弱密码
    pws.update(["123456", "password", "admin", "flag", "ctf",
                 "passw0rd", "Passw0rd", "welcome",
                 "12345678", "qwerty", "12345"])

    # 类别10: 组合密码
    for base in ["oooe", "einaudi", "unamattina", "fly", "equality",
                  "apollo", "radio", "ham", "moon", "chirp", "iscc"]:
        for year in ["2022", "2025", "20"]:
            pws.add(f"{base}{year}")
            pws.add(f"{year}{base}")

    return list(pws)


# ================================================================
# Part 6: 从图片提取呼号 (需配合OCR)
# ================================================================
def extract_callsign_from_image(img_path):
    """尝试OCR提取呼号 - 需要tesseract"""
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(img_path)
        # 先尝试英文
        text_en = pytesseract.image_to_string(img, lang='eng')
        print(f"[OCR] 英文识别结果: {text_en[:200]}")

        # 再尝试中文
        text_cn = pytesseract.image_to_string(img, lang='chi_sim+eng')
        print(f"[OCR] 中文识别结果: {text_cn[:200]}")

        # 搜索呼号模式 (B + 数字 + 字母)
        callsigns = re.findall(r'[B][0-9][A-Za-z]{2,4}', text_en + text_cn)
        if callsigns:
            print(f"[OCR] 发现呼号: {callsigns}")
            return callsigns[0]

    except ImportError:
        print("[OCR] pytesseract未安装")
    except Exception as e:
        print(f"[OCR] 错误: {e}")

    return None


# ================================================================
# Main
# ================================================================
if __name__ == "__main__":
    # 解析参数
    callsign = None
    if len(sys.argv) > 1 and sys.argv[1].startswith("--callsign="):
        callsign = sys.argv[1].split("=", 1)[1]

    print("=" * 60)
    print("  触不可及2.0 - ISCC Misc Challenge Exploit")
    print("=" * 60)

    # 1. 分析PKF和WAV
    print("\n[1] 分析PKF文件...")
    groups, wav_frames, channels, val1, val2 = parse_pkf(PKF_PATH)

    print("\n[2] 分析WAV文件...")
    sr, nframes, left, right = parse_wav(WAV_PATH)

    print("\n[3] PKF-WAV关联分析...")
    bt3_mapped, top2 = analyze_relation(groups, sr, left)

    # 2. 尝试OCR提取呼号
    if not callsign:
        print("\n[4] 尝试从图片OCR提取呼号...")
        callsign = extract_callsign_from_image(IMAGE_PATH)

    # 3. 生成密码字典并尝试
    print(f"\n[5] 生成密码字典..." +
          (f" (包含呼号: {callsign})" if callsign else ""))
    passwords = generate_passwords(callsign)
    print(f"    共 {len(passwords)} 个候选密码")

    print("\n[6] 尝试密码...")
    found = try_multiple_passwords(ZIP_PATH, passwords)

    # 4. 尝试bkcrack攻击
    if not found:
        print("\n[7] 字典攻击失败，尝试bkcrack...")
        crack_with_bkcrack(ZIP_PATH)

    if not found:
        print("\n[!] 未能找到密码。请尝试:")
        print("    pip install pytesseract  (确保已安装)")
        print("    或手动从增强图片中识别呼号:")
        print("    查看 callsign_stretch_1_99.png 等文件")
        print("    然后运行: python solve.py --callsign=BH1XXX")
