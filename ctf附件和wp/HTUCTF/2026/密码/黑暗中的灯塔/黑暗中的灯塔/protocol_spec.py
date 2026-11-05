import hashlib
import struct

Q = 2147483647
G = 7919

def rol32(x, n):
    x &= 0xffffffff
    return ((x << n) | (x >> (32 - n))) & 0xffffffff

def digest(mode, message, nonce, sid):
    frame = message + struct.pack('<I', nonce) + bytes([sid & 255])
    if mode == 0:
        return int.from_bytes(hashlib.sha256(frame).digest()[:8], 'little') % Q
    if mode == 1:
        a, b, c, d = 0x243F6A88, 0x85A308D3, 0x13198A2E, 0x03707344
        for i, byte in enumerate(frame):
            a = (a + byte + rol32(d, 7)) & 0xffffffff
            b = (b ^ rol32(a, 11) ^ (i * 0x9E3779B9)) & 0xffffffff
            c = (c + (b ^ (byte * 257))) & 0xffffffff
            d = (d ^ rol32(c, 17) ^ a) & 0xffffffff
            if (i & 3) == 3:
                a, c = c, a
                b, d = d, b
        z = (a ^ rol32(b, 3) ^ c ^ rol32(d, 19)) & 0xffffffff
        return ((z << 32) | (b ^ d)) % Q
    if mode == 2:
        return int.from_bytes(hashlib.sha256(b'LANTERN/2' + frame[::-1]).digest()[8:16], 'big') % Q
    raise ValueError('unknown mode')

def calibration_mode(blob):
    return (blob[4] ^ blob[7] ^ blob[10] ^ blob[15]) % 3

def verify(row, x, mode):
    msg = bytes.fromhex(row['msg'])
    nonce, sid = row['nonce'], row['sid']
    h = digest(mode, msg, nonce, sid)
    r, s = row['r'], row['s']
    k = (r * pow(G, -1, Q)) % Q
    return (s * k - h - x * r) % Q == 0
