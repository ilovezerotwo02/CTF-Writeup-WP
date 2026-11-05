#!/usr/bin/env python3
"""
EchoFold - ISCC CTF Exploit
Challenge: 折叠回声 (Folding Echo)

The APK has three "echoes":
  1. First echo: fake flag ISCC{this_is_only_the_first_echo} (decoy)
  2. Second echo: the encrypted data hidden in sleep_loop.webp (clue)
  3. Third echo: the real flag, decrypted below
"""

import struct, hashlib, zipfile

# ========== Helper functions matching Java 32-bit int semantics ==========
def to_int(v):
    v = v & 0xFFFFFFFF
    return v if v < 0x80000000 else v - 0x100000000

def to_uint(v):
    return v & 0xFFFFFFFF

def rot_left(x, d):
    x = to_uint(x); d = d & 31
    return to_int((x << d) | (x >> (32 - d)))

def rot_right(x, d):
    x = to_uint(x); d = d & 31
    return to_int((x >> d) | (x << (32 - d)))

def reverse_bytes(x):
    x = to_uint(x)
    return to_int(((x & 0xFF) << 24) | ((x & 0xFF00) << 8) |
                  ((x & 0xFF0000) >> 8) | ((x & 0xFF000000) >> 24))

def reverse_bits(x):
    x = to_uint(x); r = 0
    for i in range(32):
        if x & (1 << i): r |= (1 << (31 - i))
    return to_int(r)

def sha256(data):
    return hashlib.sha256(data).digest()

def concat(*args):
    return b''.join(args)

# ========== Step 1: Derive environment values ==========

# resourceKey from R.styleable.EchoFoldPulse (32 values: 0x7f010000..0x7f01001f)
pulse = [0x7f010000 + i for i in range(32)]
resourceKey = bytearray(24)
for i in range(24):
    diff = (pulse[(i + 1) % 32] - pulse[i % 32]) & 0xFF
    resourceKey[i] = ((diff ^ ((pulse[i % 32] & 0x7F) << 1)) ^ (i * 13)) & 0xFF
resourceKey = bytes(resourceKey)
print(f'[1] resourceKey: {resourceKey.hex()}')

# dexDigest = SHA256(classes.dex from APK)
with zipfile.ZipFile('EchoFold.apk') as z:
    dex_data = z.read('classes.dex')
dexDigest = sha256(dex_data)
print(f'[2] dexDigest:   {dexDigest.hex()}')

# certDigest = SHA256(signing certificate extracted from PKCS7)
with zipfile.ZipFile('EchoFold.apk') as z:
    rsa_data = z.read('META-INF/ECHOFOLD.RSA')
# Use asn1crypto to extract the DER certificate
from asn1crypto import cms
info = cms.ContentInfo.load(rsa_data)
cert_bytes = info['content']['certificates'][0].dump()
certDigest = sha256(cert_bytes)
print(f'[3] certDigest:  {certDigest.hex()}')

# snapshot = TraceRecorder.TRACE (hardcoded)
snapshot = bytes([17, 35, 122, 66, 81, 102])
print(f'[4] snapshot:    {snapshot.hex()}')

# ========== Step 2: Decrypt ECH0 chunk from webp ==========
with open('resources/assets/sleep_loop.webp', 'rb') as f:
    webp = f.read()

# Parse RIFF chunks to find ECH0
pos = 12
echo_data = None
while pos + 8 <= len(webp):
    cid = webp[pos:pos+4]
    csz = struct.unpack('<I', webp[pos+4:pos+8])[0]
    if cid == b'ECH0':
        echo_data = webp[pos+8:pos+8+csz]
        break
    pos += 8 + csz + (csz & 1)

assert echo_data is not None, 'ECH0 chunk not found'
print(f'[5] ECH0 chunk:  {len(echo_data)} bytes')

# Decrypt with SHA256 stream cipher: key = SHA256("fold-echo" || resourceKey || dexDigest || certDigest || snapshot)
def xor_stream(data, key):
    out = bytearray(); i = 0; ctr = 0
    while i < len(data):
        k = sha256(key + struct.pack('<I', ctr))
        for j in range(len(k)):
            if i >= len(data): break
            out.append(data[i] ^ k[j]); i += 1
        ctr += 1
    return bytes(out)

xor_key = sha256(concat(b'fold-echo', resourceKey, dexDigest, certDigest, snapshot))
decrypted = xor_stream(echo_data, xor_key)
assert decrypted[:4] == b'EFVM', 'Bad decryption - magic mismatch'

# Parse EFVM container
bcode_len = (decrypted[5] << 8) | decrypted[6]
out_len   = (decrypted[7] << 8) | decrypted[8]
bcode = decrypted[9:9 + bcode_len]
enc_output = decrypted[9 + bcode_len:9 + bcode_len + out_len]
print(f'[6] Bytecode:    {len(bcode)} bytes ({len(bcode)//4} instructions)')
print(f'[7] Enc output:  {len(enc_output)} bytes')

# ========== Step 3: Run the custom VM ==========
vm_seed = sha256(concat(b'vm-seed', resourceKey, dexDigest, certDigest, snapshot))

# Initialize 8 registers from seed XORed with TEA delta constants
regs = [0] * 8
for i in range(8):
    off = i * 4
    val = (vm_seed[off] | (vm_seed[off+1] << 8) | (vm_seed[off+2] << 16) | (vm_seed[off+3] << 24))
    val = to_int(val)
    delta = to_int(0x9E3779B9 * i)  # TEA delta constant, 32-bit wrap
    regs[i] = to_int(val ^ delta)

# Execute 48 instructions (4 bytes each)
ip = 0
while ip + 3 < len(bcode):
    op_byte = bcode[ip] & 0xFF
    rx, ry, rz = bcode[ip+1] & 7, bcode[ip+2] & 7, bcode[ip+3] & 7
    i10 = ip // 4

    # Environment mixing: i11 = dexDigest[...] ^ resourceKey[...] ^ certDigest[...] ^ snapshot[...]
    i11 = to_int((dexDigest[(ip // 2) % 32] & 0xFF) ^
                 (resourceKey[i10 % 24] & 0xFF) ^
                 (certDigest[(ip // 3) % 32] & 0xFF) ^
                 (snapshot[i10 % 6] & 0xFF))

    op = op_byte & 7
    if op == 0:
        regs[rx] = to_int(rot_left((regs[ry] + i11) + ip, (rz + i11) & 31) ^ regs[rx])
    elif op == 1:
        regs[rx] = to_int(rot_left(regs[rx] + regs[ry] + (i11 << 1) + rz, (ry + rz + ip) & 31))
    elif op == 2:
        regs[rx] = to_int(regs[rx] ^ ((reverse_bytes(regs[rz]) ^ regs[ry]) + i11))
    elif op == 3:
        tmp = regs[rx]
        regs[rx] = to_int(regs[ry] + i11)
        regs[ry] = to_int(rot_right(regs[rz] + ip, i11 & 31) ^ tmp)
    elif op == 4:
        regs[rx] = to_int(regs[rx] + rot_right((i11 ^ regs[ry]) ^ ip, (rz + rx + 1) & 31))
    elif op == 5:
        regs[rx] = to_int(rot_left((regs[ry] + regs[rz]) + i11, ((ip + rx) + ry) & 31) ^ regs[rx])
    elif op == 6:
        regs[rx] = to_int((i11 ^ (regs[rx] ^ regs[ry])) + reverse_bits(regs[rz] + ip))
    else:  # op == 7
        regs[rx] = to_int(regs[rx] + (i11 ^ (regs[rz] ^ regs[ry])) + ip)
    ip += 4

# Generate VM output key (35 bytes)
vm_key = bytearray()
for i in range(out_len):
    val = (regs[i & 7] ^ rot_left(regs[(i + 3) & 7], i & 31))
    val ^= (resourceKey[i % 24] & 0xFF)
    val ^= (dexDigest[i % 32] & 0xFF)
    val ^= (certDigest[i % 32] & 0xFF)
    val ^= (snapshot[i % 6] & 0xFF)
    vm_key.append(to_int(val) & 0xFF)
vm_key = bytes(vm_key)
print(f'[8] VM key:      {vm_key.hex()}')

# ========== Step 4: Decrypt flag ==========
# KEY INSIGHT: The verify method uses Bytes.xor (simple bytewise XOR),
# NOT xorStream (SHA256 stream cipher). jadx misdecompiled this call.
flag_content = bytes(e ^ k for e, k in zip(enc_output, vm_key))
flag = f'ISCC{{{flag_content.decode("utf-8")}}}'
print(f'\n[9] FLAG:        {flag}')
print(f'    Content:     {flag_content.decode("utf-8")}')
