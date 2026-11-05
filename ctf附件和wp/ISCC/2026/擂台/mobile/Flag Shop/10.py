# solve.py — Flag Shop 纯静态求解脚本
# 用法: python solve.py FlagShop.apk
# 零依赖: 不需要手机、Frida、Unicorn，直接解析 APK 即可。
import hashlib, re, struct, sys, zipfile
from pathlib import Path

FSHP_SIGNATURE = b"FSHP"
ITEM_TARGET     = "realflag"

# APK 中 realflag 的 body 摘要 — 防误用其他 APK
BODY_SHA256 = "de76f04aad857512621047453dcfdc6fe1a5b613fa04f95f3fbc00137d1c20d9"

# 逆向 libflagshop.so 中 24 轮 SPN 加密后恢复的初始状态 S0
# S0[0:7] 是元数据，S0[7:55] 是编码 flag，S0[55:] 是填充
S0 = bytes.fromhex(
    "ff6bb2637739b0d61c6b85b1a31afa368ab092ef20408b7b5"
    "7bbfa51438395fed7ee8ac69887d41ba36f636cd411bd977bb"
    "073ec031d6694d0f9e897f0dc17532d35b97dbfbf4adb50dc"
    "7e7b81a61f27"
)

# 编码 flag 的 XOR 偏移表（长度 48，对应 flag_len=0x30）
XOR_TABLE = bytes.fromhex(
    "9f4f28c6ca9452cb03d581b6b05274b84a08ddcb6575dca190"
    "b3b1bbf1c7efe02ecd485433e1218cf3248006db3c3c1b"
)


def parse_dex_strings(dex):
    """解析 DEX 字符串池，返回字符串列表"""
    assert dex[:4] == b"dex\n", "非 DEX 文件格式"
    total, base = struct.unpack_from("<II", dex, 0x38)
    result = []
    for k in range(total):
        off = struct.unpack_from("<I", dex, base + k * 4)[0]
        # ULEB128 解码长度
        v, p = 0, off
        while True:
            b = dex[p]
            p += 1
            v = (v << 7) | (b & 0x7F)
            if not (b & 0x80):
                break
        # 读取 MUTF-8 字符串（以 null 结尾）
        end = p
        while dex[end]:
            end += 1
        raw = dex[p:end]
        try:
            result.append(raw.decode("utf-8"))
        except UnicodeDecodeError:
            result.append(raw.decode("latin-1"))
    return result


def scan_fshp(data):
    """从字符串列表中识别 FSHP 格式密文"""
    pattern = re.compile(r"^46534850[0-9a-fA-F]{168}$")
    hits = []
    for s in data:
        if not pattern.match(s):
            continue
        blob = bytes.fromhex(s)
        if blob[:4] != FSHP_SIGNATURE or len(blob) != 88:
            continue
        hits.append({
            "hexstr": s,
            "nlen": blob[5],
            "flen": blob[6],
            "plen": blob[7],
            "body": blob[8:],
        })
    return hits


def pick_realflag(entries):
    """筛选 realflag: name_len=8, flag_len=0x30"""
    matched = [e for e in entries if e["nlen"] == 8 and e["flen"] == 0x30]
    if len(matched) != 1:
        raise SystemExit(
            f"错误: 无法唯一定位 realflag "
            f"(共 {len(entries)} 条记录)"
        )
    return matched[0]


def decode_flag(entry):
    """从 S0 解码 flag"""
    body = entry["body"]
    assert len(body) == 80, "body 长度错误"
    assert hashlib.sha256(body).hexdigest() == BODY_SHA256, "body 摘要不匹配"

    flag_len = entry["flen"]
    encoded = S0[7:7 + flag_len]
    raw = bytes(a ^ b for a, b in zip(encoded, XOR_TABLE))

    flag = raw.decode("ascii")
    assert flag.startswith("ISCC{") and flag.endswith("}"), f"格式错误: {flag}"
    return flag


def main():
    apk = Path(sys.argv[1] if len(sys.argv) > 1 else "FlagShop.apk")
    if not apk.is_file():
        print(f"APK文件不存在: {apk}")
        sys.exit(1)

    with zipfile.ZipFile(apk) as zf:
        dex = zf.read("classes.dex")

    strings = parse_dex_strings(dex)
    records = scan_fshp(strings)

    print(f"检测到 {len(records)} 条 FSHP 记录")
    for idx, rec in enumerate(records):
        print(f"#{idx}:名称长度={rec['nlen']} fl@g长度={rec['flen']}密码长度={rec['plen']}")

    entry = pick_realflag(records)
    print(f"目标商品是{ITEM_TARGET}")
    print(f"ciphertext:{entry['hexstr'][:40]}...")
    print(f"body SHA256:{hashlib.sha256(entry['body']).hexdigest()}")

    flag = decode_flag(entry)
    print(f"fl@g是{flag}")


if __name__ == "__main__":
    main()
