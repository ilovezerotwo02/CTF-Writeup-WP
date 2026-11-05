
import argparse
import ctypes
import os
import struct
import subprocess
import sys

try:
    import pefile
except ImportError:
    pefile = None

EXE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "DualStageChallenge.exe")

BASE = 0x400000
ADDR = {
    "table1": 0x4B9000,
    "ct2":    0x4B9010,
    "key8":   0x4B9020,
    "ct":     0x4B9040,
    "table2": 0x4B9080,
}
LEN_A = 13
LEN_B = 14
LEN_FLAG = 40
MOD = 57          # check_A 中的 magic 除数 (0x8fb823ee08fb823f >> 69 == 1/57)


def load_tables(exe_path=EXE_PATH):
    """从 exe 里按 VA 提取 5 张数据表。"""
    if pefile is None:
        raise RuntimeError("需要 pefile: pip install pefile")
    pe = pefile.PE(exe_path)

    def grab(va, n):
        off = pe.get_offset_from_rva(va - BASE)
        return pe.__data__[off:off + n]

    return {
        "table1": grab(ADDR["table1"], LEN_A),
        "ct2":    grab(ADDR["ct2"], LEN_B),
        "key8":   grab(ADDR["key8"], 8),
        "ct":     grab(ADDR["ct"], LEN_FLAG),
        "table2": grab(ADDR["table2"], MOD),
    }


def stage_a_password(tick, t):
    """Stage A: 13 字节，依赖 GetTickCount64>>20。"""
    seed = ((tick >> 20) ^ 0xA7) & 0xFF
    out = bytearray()
    for i in range(LEN_A):
        idx = (t["table1"][i] + seed + i * 11) % MOD
        out.append(t["table2"][idx])
    return bytes(out)


def stage_b_password(t):
    """Stage B: 14 字节，循环 8 字节 XOR 密钥。"""
    return bytes(t["ct2"][i] ^ t["key8"][i % 8] for i in range(LEN_B))


def generate_flag(t):
    """flag 生成（与 check_A/check_B 通过与否无关，纯静态）。"""
    out = bytearray()
    for i in range(LEN_FLAG):
        key = ((i * 3 + 0x11) ^ 0x5A) & 0xFF
        out.append(t["ct"][i] ^ key)
    return bytes(out)


def get_tick64():
    try:
        return ctypes.windll.kernel32.GetTickCount64()
    except Exception:
        return 0


def run_exe(pass_a: bytes, pass_b: bytes):
    """管道喂两阶段密码，动态验证 flag 输出。"""
    payload = pass_a + b"\n" + pass_b + b"\n"
    r = subprocess.run([EXE_PATH], input=payload,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
    return r.stdout.decode("utf-8", errors="replace"), r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tick", type=int, default=None,
                    help="指定 GetTickCount64 值（默认取当前系统）")
    ap.add_argument("--run", action="store_true",
                    help="动态运行 exe 验证（需 Windows）")
    args = ap.parse_args()

    t = load_tables()
    tick = args.tick if args.tick is not None else get_tick64()
    pass_a = stage_a_password(tick, t)
    pass_b = stage_b_password(t)
    flag = generate_flag(t)

    print(f"[*] table1 : {t['table1'].hex()}")
    print(f"[*] ct2    : {t['ct2'].hex()}")
    print(f"[*] key8   : {t['key8'].hex()}")
    print(f"[*] ct     : {t['ct'].hex()}")
    print(f"[*] table2 : {t['table2'].decode('ascii')}")
    print()
    print(f"[*] GetTickCount64 = {tick} (0x{tick:x}), seed = {((tick >> 20) ^ 0xA7) & 0xFF:02x}")
    print(f"[+] Stage A password ({LEN_A}): {pass_a.decode('ascii')}")
    print(f"[+] Stage B password ({LEN_B}): {pass_b.decode('ascii')}")
    print(f"[+] FLAG: {flag.decode('ascii')}")

    if args.run:
        out, rc = run_exe(pass_a, pass_b)
        print("\n----- exe output -----")
        print(out)
        print(f"exit code: {rc}")
        if flag.decode("ascii") in out:
            print("[*] 验证通过：exe 输出与静态计算 flag 一致")
        else:
            print("[!] 未在输出中找到 flag（Stage A 可能因 tick 跨界变化而失败，可 --tick 重试）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
