"""
深海金库 — Exploit Script
ISCC CTF Mobile Challenge

正向变换流程（校验时）：
  flag[5:-1]  --[CryptoEngine.performTransformation()]-->  transform()  --[native Fib XOR]-->  fib_xor()  --[custom base64]-->  target

已知 target = "cUdltutGeWWIUm+7OE4ce3wi"，逆向推导 flag 内层。
"""

# 自定义 Base64 字母表（从 native 库 libsecure_verify.so 中提取）
ALPHABET = "zKJUExRaVtM3Ydv5TQIsWD1frnHC78Lckl6euPh9AGoj0SgN4Zp+OwXi2F/ybmBq"
TARGET = "cUdltutGeWWIUm+7OE4ce3wi"


def custom_b64_decode(s: str) -> bytearray:
    """自定义 Base64 解码"""
    table = {c: i for i, c in enumerate(ALPHABET)}
    vals = [table[c] for c in s if c != "="]
    out = bytearray()
    for i in range(0, len(vals), 4):
        a, b, c, d = vals[i : i + 4]
        out.append((a << 2) | (b >> 4))
        out.append(((b & 0x0F) << 4) | (c >> 2))
        out.append(((c & 0x03) << 6) | d)
    return out


def custom_b64_encode(buf: bytes) -> str:
    """自定义 Base64 编码（用于校验）"""
    out = []
    for i in range(0, len(buf), 3):
        chunk = buf[i : i + 3]
        if len(chunk) == 3:
            b0, b1, b2 = chunk
            out.append(ALPHABET[b0 >> 2])
            out.append(ALPHABET[((b0 << 4) & 0x30) | (b1 >> 4)])
            out.append(ALPHABET[((b1 & 0x0F) << 2) | (b2 >> 6)])
            out.append(ALPHABET[b2 & 0x3F])
        else:
            padded = chunk + b"\x00" * (3 - len(chunk))
            b0, b1, b2 = padded
            vals = [
                b0 >> 2,
                ((b0 << 4) & 0x30) | (b1 >> 4),
                ((b1 & 0x0F) << 2) | (b2 >> 6),
            ]
            for j in range(len(chunk) + 1):
                out.append(ALPHABET[vals[j]])
            out.extend("=" * (3 - len(chunk)))
    return "".join(out)


def fib_xor(buf: bytearray) -> bytearray:
    """
    Fibonacci 序列异或（XOR 是其自身的逆运算）。
    native 函数 process_fib_stream(buf, len) 的逻辑：
      a, b = 1, 1
      for i in range(len):
          buf[i] ^= (a & 0xFF)
          a, b = b, a + b
    """
    out = bytearray(buf)
    a, b = 1, 1
    for i in range(len(out)):
        out[i] ^= a & 0xFF
        a, b = b, (a + b) & 0xFFFFFFFF
    return out


def java_transform(data: bytearray) -> bytearray:
    """
    CryptoEngine.performTransformation() 正向变换
    （同 Java / Smali 实现一致）
    """
    out = bytearray(data)
    prev = 0
    for i in range(len(out)):
        ch = out[i]
        if 0x20 <= ch <= 0x7E:
            ch = ((ch - 0x19) % 0x5F) + 0x20
        delta = 8 if i % 2 == 0 else -8
        prev = (ch + delta + (prev % 4)) & 0xFF
        out[i] = prev
    return out


def inverse_java_transform(buf: bytearray) -> str:
    """
    CryptoEngine.performTransformation() 的逆变换
    """
    prev = 0
    out = bytearray()
    for i, ob in enumerate(buf):
        delta = 8 if i % 2 == 0 else -8
        temp = (ob - delta - (prev % 4)) & 0xFF
        if 0x20 <= temp <= 0x7E:
            ch = ((temp - 39) % 95) + 32
        else:
            ch = temp
        out.append(ch)
        prev = ob
    return out.decode("ascii")


def main():
    print("[*] Target (custom base64):", TARGET)

    # Step 1: custom base64 decode
    step1 = custom_b64_decode(TARGET)
    print("[*] After base64 decode:", step1.hex())

    # Step 2: reverse Fib XOR
    step2 = fib_xor(step1)
    print("[*] After Fib XOR:", step2.hex())

    # Step 3: reverse Java transform
    inner = inverse_java_transform(step2)
    print("[*] Inner flag content:", inner)

    flag = f"ISCC{{{inner}}}"
    print("[*] FLAG:", flag)

    # === 正向校验 ===
    verify = custom_b64_encode(fib_xor(java_transform(bytearray(inner.encode()))))
    print("[*] Verify (should match target):", verify)
    assert verify == TARGET, "Verification failed!"
    print("[+] Verification passed!")

    # 写入 flag
    with open("flag.txt", "w") as f:
        f.write(flag)
    print("[+] Flag saved to flag.txt")


if __name__ == "__main__":
    main()
