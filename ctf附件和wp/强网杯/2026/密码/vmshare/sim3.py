import struct

M32 = 0xffffffff
M16 = 0xffff
T_BYTES = bytes.fromhex("571368249c36ad48e15bf26c037d148e259f36a047b158c269d37ae48bf59c06")
P_BYTES = b"SIMD_TINY_BLOCK_IS_A_NIGHTMARE!!"
T = list(struct.unpack("<16H", T_BYTES))
CR = None

def stream(seed, salt):
    eax = ((seed & 0xffffff) ^ salt) & M32
    eax ^= eax >> 13
    eax = (eax * 0x45d9f3b) & M32
    eax ^= eax >> 16
    esi = 0
    out = []
    while True:
        eax = (eax + esi - 0x61c88647) & M32
        esi = (esi + 0x7f4a7c15) & M32
        ecx = ((eax >> 13) ^ eax) & M32
        ecx = (ecx * 0x85ebca6b) & M32
        eax = (ecx ^ (ecx >> 16)) & M32
        out.append((eax ^ (eax >> 16)) & 0xffff)
        if esi == 0xfa53e0a8:
            break
    return struct.pack("<8H", *out)

def transform(state, key_words):
    """8 rounds; last round omits final xor-shift."""
    x = [(s ^ (s >> 5)) & M16 for s in state]
    for r in range(8):
        y = [((s << 3) | (s >> 13)) & M16 for s in x]
        y = [(key_words[r] + T[i] + y[i]) & M16 for i in range(16)]
        y = [(s ^ (s >> 7)) & M16 for s in y]
        y = [((s << 9) | (s >> 7)) & M16 for s in y]
        if r < 7:
            y = [(s ^ (s >> 5)) & M16 for s in y]
        x = y
    return x

def enc(flag):
    X = int(flag[5:12], 16)
    Y = int(flag[13:20], 16)
    k1 = struct.unpack("<8H", stream(X, 0x31415926))
    k2 = struct.unpack("<8H", stream(Y, 0x27182818))
    st = transform(list(struct.unpack("<16H", P_BYTES)), k1)
    st = transform(st, k2)
    return struct.pack("<16H", *st)

if __name__ == "__main__":
    tests = {
        "flag{0123456_ABCDEF0}": "6aa54f7ccba94ec8f9274331a6129dc78eb90c097b5eeec1aac160c05ab69021",
        "flag{0000000_0000000}": "1a4d526d4ce7022ee20b91f9a5db31585ad905ee231e8e99dd8c492291e40274",
        "flag{0000001_0000002}": "0da17ab5f39a39036cd1e691b786a6d2dde01738da1290ae466ad6cf49648001",
        "flag{1234567_89ABCDE}": "6c17261f1bb632b50ad29c2d8bde236cf3c81967ec9622e9110f6a44b62aa4b6",
        "flag{FFFFFFF_FFFFFFF}": "a8828959fa2f505da8b8b5c3489869f72474b13fbcca2e43412f18de6d92249d",
    }
    for f, expect in tests.items():
        got = enc(f).hex()
        print(f, "OK" if got == expect else "FAIL %s" % got)
    print("cipher.bin:", open("cipher.bin", "rb").read().hex())
