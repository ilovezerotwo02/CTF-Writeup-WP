import sys
import os

CIPHER = bytes([
    0x31, 0xFE, 0xB4, 0x5D, 0x49, 0x20, 0xCE, 0x5C, 0x15, 0xF7,
    0x85, 0x22, 0xDA, 0xB9, 0x08, 0x63, 0x3B, 0xBE, 0x2E, 0x41, 0x03,
    0x73, 0x9A, 0x28, 0x94, 0xD5, 0x10, 0x35, 0xA1, 0xCB, 0xFF,
    0x2D, 0x58, 0x7D, 0x60, 0x87, 0xC0,
])
SIG = CIPHER[:10]


def find_cipher(path):
    data = open(path, "rb").read()
    off = data.find(SIG)
    if off < 0:
        return None, None
    return off, data[off:off + 0x25]


def decode(cipher):
    cl = 0x1D
    out = bytearray()
    for i in range(0x25):
        al = ((cl * (i & 0xFF)) + (i & 3) * 17 + 0x79) & 0xFF
        out.append(al ^ cipher[i])
        cl = (cl + 3) & 0xFF
    return bytes(out)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "GhostRelay.exe")

    cipher = CIPHER
    if os.path.exists(path):
        off, got = find_cipher(path)
        if got:
            cipher = got
            print("[+] 在 %s 中找到密文，文件偏移 %#x（.rdata:0x140002360）"
                  % (os.path.basename(path), off))
        else:
            print("[!] 没在文件里匹配到特征串，改用内置密文")
    else:
        print("[!] 找不到 %s，用内置密文" % path)

    print("[*] 密文 (%d 字节): %s" % (len(cipher), cipher.hex()))
    flag = decode(cipher)
    print("[*] 解密: %s" % flag.decode("utf-8", "replace"))

    # 自检：必须是 HTUCTF{...}
    s = flag.decode("utf-8", "replace")
    if s.startswith("HTUCTF{") and s.endswith("}"):
        print("[+] FLAG = %s" % s)
        return 0
    print("[-] 结果不像 flag，检查密文/算法")
    return 1


if __name__ == "__main__":
    sys.exit(main())
