import struct

dwords = [
    0x697F7E62, 0x5D516C7E, 0x1A494619, 0x5E754F47, 0x1958751A,
    0x5958195C, 0x44197519, 0x19441B4D, 0x441B5819,
]
# mov word ptr [rsp+0x44], 0x574d
word = 0x574D

data = b"".join(struct.pack("<I", d) for d in dwords) + struct.pack("<H", word)
assert len(data) == 38

KEY = b"\x2a" * 16          # 0x140018420
out = bytearray()
for i, b in enumerate(data):
    if i < 32:
        out.append(b ^ KEY[i % 16])
    else:
        out.append(b ^ 0x2A)  # 尾部循环 xor 0x2a

flag = out.decode()
print(len(flag), flag)
