import struct

data = open('elfstudy', 'rb').read()

# 1) rolling-decrypt 0x7396-0x76c6 (203 dwords, from high addr to low)
blob = bytearray(data[0x7396:0x76c6])
acc = 0
for c in range(203, 0, -1):
    off = c * 4
    v = struct.unpack_from('<I', blob, off)[0] ^ acc
    struct.pack_into('<I', blob, off, v)
    assert v != 0
    acc = (acc + v) & 0xffffffff

M = (1 << 64) - 1
rol = lambda x, n: ((x << (n % 64)) | (x >> (64 - n % 64))) & M
ror = lambda x, n: ((x >> (n % 64)) | (x << (64 - n % 64))) & M
g = lambda off: struct.unpack_from('<Q', blob, off - 0x7396)[0]

KEY_A = g(0x7686) ^ g(0x768e)      # slot[0]
KEY_B = g(0x7696) ^ g(0x769e)      # slot[1]
T0, T1 = g(0x76a6), g(0x76ae)
R = 0x9e3779b97f4a7c15

slot = {0: KEY_A, 1: KEY_B}
for i in range(2, 32):
    slot[i] = (rol((slot[i-1] + slot[i-2]) & M, 13) ^ ror(slot[i-2], 7) ^ (i * R & M)) & M

F = lambda x, k: ((rol((x + k) & M, 13) ^ rol(x, 29)) + rol(x, 47)) & M

r8, r9 = T0, T1
for i in range(31, 1, -1):
    r9, r8 = r8, r9 ^ F(r8, slot[i])
P0, P1 = r8 ^ KEY_A, r9 ^ KEY_B
print('flag{%s}' % struct.pack('<QQ', P0, P1).hex())
