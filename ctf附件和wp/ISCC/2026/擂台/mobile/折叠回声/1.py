#!/usr/bin/env python3
"""折叠回声 — 求解脚本"""
import struct, hashlib, zipfile
from asn1crypto import cms

def sha256(d): return hashlib.sha256(d).digest()
def cat(*a): return b"".join(a)

# 32-bit helpers
def u32(x): return x & 0xFFFFFFFF
def i32(x): return u32(x) if u32(x) < 0x80000000 else u32(x) - 0x100000000
def rol(x, d): x, d = u32(x), d & 31; return i32((x << d) | (x >> (32 - d)))
def ror(x, d): x, d = u32(x), d & 31; return i32((x >> d) | (x << (32 - d)))
def revb(x): return i32(((u32(x) & 0xFF) << 24) | ((u32(x) & 0xFF00) << 8) | ((u32(x) & 0xFF0000) >> 8) | ((u32(x) & 0xFF000000) >> 24))
def revbit(x):
    x, r = u32(x), 0
    for i in range(32):
        if x & (1 << i): r |= (1 << (31 - i))
    return i32(r)

# Step 1: Derive resourceKey from R.styleable.EchoFoldPulse
pulse = [0x7f010000 + i for i in range(32)]
rk = bytes(((pulse[(i+1)%32] - pulse[i%32]) & 0xFF ^ ((pulse[i%32] & 0x7F) << 1) ^ (i*13)) & 0xFF for i in range(24))
print(f"[1] resourceKey: {rk.hex()}")

# Step 2: dexDigest and certDigest from APK
with zipfile.ZipFile("EchoFold.apk") as z:
    dd = sha256(z.read("classes.dex"))
print(f"[2] dexDigest:   {dd.hex()}")

with zipfile.ZipFile("EchoFold.apk") as z:
    info = cms.ContentInfo.load(z.read("META-INF/ECHOFOLD.RSA"))
    cd = sha256(info["content"]["certificates"][0].dump())
print(f"[3] certDigest:  {cd.hex()}")

snap = bytes([17, 35, 122, 66, 81, 102])
print(f"[4] snapshot:    {snap.hex()}")

# Step 3: Decrypt ECH0 chunk
with open("resources/assets/sleep_loop.webp", "rb") as f:
    webp = f.read()
pos = 12
while pos + 8 <= len(webp):
    cid, csz = webp[pos:pos+4], struct.unpack("<I", webp[pos+4:pos+8])[0]
    if cid == b"ECH0":
        echo = webp[pos+8:pos+8+csz]
        break
    pos += 8 + csz + (csz & 1)

def xor_stream(data, key):
    out, i, ctr = bytearray(), 0, 0
    while i < len(data):
        k = sha256(key + struct.pack("<I", ctr))
        for j in range(len(k)):
            if i >= len(data): break
            out.append(data[i] ^ k[j]); i += 1
        ctr += 1
    return bytes(out)

dec_key = sha256(cat(b"fold-echo", rk, dd, cd, snap))
decrypted = xor_stream(echo, dec_key)
assert decrypted[:4] == b"EFVM", "Decryption failed"
blen = (decrypted[5] << 8) | decrypted[6]
olen = (decrypted[7] << 8) | decrypted[8]
bcode = decrypted[9:9+blen]
enc_out = decrypted[9+blen:9+blen+olen]

# Step 4: Run the custom VM
seed = sha256(cat(b"vm-seed", rk, dd, cd, snap))
regs = [0]*8
for i in range(8):
    v = seed[i*4] | (seed[i*4+1]<<8) | (seed[i*4+2]<<16) | (seed[i*4+3]<<24)
    regs[i] = i32(u32(v) ^ u32(0x9E3779B9 * i))

ip = 0
while ip + 3 < len(bcode):
    op, rx, ry, rz = bcode[ip] & 7, bcode[ip+1] & 7, bcode[ip+2] & 7, bcode[ip+3] & 7
    i10 = ip // 4
    i11 = (dd[(ip//2)%32] ^ rk[i10%24] ^ cd[(ip//3)%32] ^ snap[i10%6]) & 0xFF
    if op == 0:
        regs[rx] = i32(rol(u32(regs[ry]+i11)+ip, (rz+i11)&31) ^ u32(regs[rx]))
    elif op == 1:
        regs[rx] = i32(rol(u32(regs[rx]+regs[ry]+(i11<<1)+rz), (ry+rz+ip)&31))
    elif op == 2:
        regs[rx] = i32(u32(regs[rx]) ^ (u32(revb(regs[rz]) ^ regs[ry]) + i11))
    elif op == 3:
        t = regs[rx]; regs[rx] = i32(regs[ry] + i11)
        regs[ry] = i32(ror(u32(regs[rz]+ip), i11&31) ^ u32(t))
    elif op == 4:
        regs[rx] = i32(u32(regs[rx]) + ror(u32(i11^regs[ry])^ip, (rz+rx+1)&31))
    elif op == 5:
        regs[rx] = i32(rol(u32(regs[ry]+regs[rz])+i11, ((ip+rx)+ry)&31) ^ u32(regs[rx]))
    elif op == 6:
        regs[rx] = i32((i11^(u32(regs[rx])^u32(regs[ry]))) + revbit(regs[rz]+ip))
    else:
        regs[rx] = i32(u32(regs[rx]) + (i11^(u32(regs[rz])^u32(regs[ry]))) + ip)
    ip += 4

vm_key = bytes(
    (u32(regs[i&7]) ^ rol(regs[(i+3)&7], i&31)
     ^ rk[i%24] ^ dd[i%32] ^ cd[i%32] ^ snap[i%6]) & 0xFF
    for i in range(olen))

# Step 5: Decrypt flag using Bytes.xor (NOT xorStream!)
inner = bytes(e ^ k for e, k in zip(enc_out, vm_key)).decode()
flag = f"ISCC{{{inner}}}"
print(f"[9] FLAG: {flag}")
print(f"    Inner: {inner}")

with open("flag.txt", "w") as f:
    f.write(flag)
print("[+] Flag saved")

