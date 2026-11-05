alphabet = "zKJUExRaVtM3Ydv5TQIsWD1frnHC78Lckl6euPh9AGoj0SgN4Zp+OwXi2F/ybmBq"
target = "cUdltutGeWWIUm+7OE4ce3wi"


def custom_b64_decode(s: str) -> bytearray:
    table = {c: i for i, c in enumerate(alphabet)}
    vals = [table[c] for c in s]
    out = bytearray()
    for i in range(0, len(vals), 4):
        a, b, c, d = vals[i:i + 4]
        out.append((a << 2) | (b >> 4))
        out.append(((b & 0x0F) << 4) | (c >> 2))
        out.append(((c & 0x03) << 6) | d)
    return out


def fib_xor(buf: bytes) -> bytearray:
    out = bytearray(buf)
    a, b = 1, 1
    for i in range(len(out)):
        out[i] ^= a & 0xFF
        a, b = b, (a + b) & 0xFFFFFFFF
    return out


def inverse_java_transform(buf: bytes) -> str:
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


def java_transform(s: str) -> bytearray:
    data = bytearray(s.encode("ascii"))
    prev = 0
    for i in range(len(data)):
        ch = data[i]
        if 0x20 <= ch <= 0x7E:
            ch = ((ch - 0x19) % 0x5F) + 0x20
        delta = 8 if i % 2 == 0 else -8
        prev = (ch + delta + (prev % 4)) & 0xFF
        data[i] = prev
    return data


def custom_b64_encode(buf: bytes) -> str:
    out = []
    i = 0
    while i < len(buf):
        chunk = buf[i:i + 3]
        if len(chunk) == 3:
            b0, b1, b2 = chunk
            out.append(alphabet[b0 >> 2])
            out.append(alphabet[((b0 << 4) & 0x30) | (b1 >> 4)])
            out.append(alphabet[((b1 & 0x0F) << 2) | (b2 >> 6)])
            out.append(alphabet[b2 & 0x3F])
        else:
            padded = chunk + b"\x00" * (3 - len(chunk))
            b0, b1, b2 = padded
            vals = [
                b0 >> 2,
                ((b0 << 4) & 0x30) | (b1 >> 4),
                ((b1 & 0x0F) << 2) | (b2 >> 6),
            ]
            for j in range(len(chunk) + 1):
                out.append(alphabet[vals[j]])
            out.extend("=" * (3 - len(chunk)))
        i += 3
    return "".join(out)


def main() -> None:
    step1 = custom_b64_decode(target)
    step2 = fib_xor(step1)
    inner = inverse_java_transform(step2)
    flag = f"ISCC{{{inner}}}"

    verify = custom_b64_encode(fib_xor(java_transform(inner)))

    print("inner =", inner)
    print("flag  =", flag)
    print("check =", verify)


if __name__ == "__main__":
    main()
