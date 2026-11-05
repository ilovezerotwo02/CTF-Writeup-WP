import os, re, sys

data = open(sys.argv[1] if len(sys.argv) > 1 else "Conway's Trap.exe", "rb").read()

# ---- locate seed final state ----
found = None
for h in re.finditer(rb'(?<![0-9A-Fa-f])([0-9A-Fa-f]{32})\x00', data):
    x = bytes.fromhex(h.group(1).decode())
    if len(x) == 16:
        found = x
        break
if found is None:
    print("cannot locate seed"); exit(1)

print("最终的种子:", found.hex())

# ---- revert 5 rounds ----
cur = found
for _ in range(5):
    # shift right (opposite of original shift-left)
    r = bytearray(16)
    r[0] = cur[15]
    r[1:] = cur[:15]
    nxt = bytearray(16)
    j = 0
    while j < 16:
  
        aa = r[j]
        bb = r[j + 1]
        # rotl((a+b)^b, 1) = bb → (a+b)^b = rotr(bb, 1)
        # let s = a+b = aa → b = aa ^ rotr(bb, 1)
        # a = aa - b
        rev_b = aa ^ (((bb << 7) | (bb >> 1)) & 0xFF)
        rev_a = (aa - rev_b) & 0xFF
        nxt[j] = rev_a
        nxt[j + 1] = rev_b
        j += 2
    cur = bytes(nxt)

seed = cur
print("seed orig:", seed.hex())

# ---- verify ----
v = seed
for _ in range(5):
    t = list(v)
    k = 0
    while k < 16:
        sm = (t[k] + t[k + 1]) & 0xFF
        t[k] = sm
        t[k + 1] = ((sm ^ t[k + 1]) * 2 + ((sm ^ t[k + 1]) >> 7)) & 0xFF
        # same as rotl((sm ^ t[k+1]), 1) but avoids function call
        k += 2
    v = bytes(t[1:] + t[:1])
if v != found:
    print("verify failed"); exit(1)

# ---- extract hidden constants ----
pat = re.compile(
    b'\xc7\x45\xe4(....)'
    b'\xc7\x45\xe8(....)'
    b'\xc7\x45\xec(....)'
    b'\xc7\x45\xf0(....)'
    b'\xc7\x45\xf4(....)'
    b'\x66\xc7\x45\xf8(..)'
    b'\xc6\x45\xfa(.)', re.S)
m = pat.search(data)
if m is None:
    print("check table not found"); exit(1)

raw_tbl = b''.join(m.groups())
tbl = bytes([b ^ 0xCC for b in raw_tbl])
print("check tbl:", tbl.hex(), f"(len={len(tbl)})")

# ---- decode flag ----
nn = len(tbl)
res = []
for p in range(nn):
    vv = tbl[p]
    # ROR3 = (vv ^ 0xAA) >> 3 | (vv ^ 0xAA) << 5
    xored = vv ^ 0xAA
    ror3 = ((xored >> 3) | (xored << 5)) & 0xFF
    subbed = (ror3 - (p * nn)) & 0xFF
    res.append(seed[p & 0x0F] ^ subbed)

body = bytes(res).decode()
print("flag body:", body)
print("ISCC{" + body + "}")
