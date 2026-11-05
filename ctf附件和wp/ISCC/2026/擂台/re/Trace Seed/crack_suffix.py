import struct, sys

def ROL64(v, s):
    s &= 0x3F; v &= 0xFFFFFFFFFFFFFFFF
    return ((v << s) | (v >> (64 - s))) & 0xFFFFFFFFFFFFFFFF

def ROR64(v, s):
    s &= 0x3F; v &= 0xFFFFFFFFFFFFFFFF
    return ((v >> s) | (v << (64 - s))) & 0xFFFFFFFFFFFFFFFF

def sub_1DE72(a1):
    a1 &= 0xFFFFFFFFFFFFFFFF
    x = (a1 - 0x61C8864680B583EB) & 0xFFFFFFFFFFFFFFFF
    x = (0xBF58476D1CE4E5B9 * x) & 0xFFFFFFFFFFFFFFFF
    x ^= (x >> 30)
    x = (0xBF58476D1CE4E5B9 * x) & 0xFFFFFFFFFFFFFFFF
    x ^= (x >> 27)
    x = (0x94D049BB133111EB * x) & 0xFFFFFFFFFFFFFFFF
    x ^= (x >> 31)
    return x

with open("/mnt/d/桌面/wp/擂台/re/Trace Seed/trace", "rb") as f:
    data = f.read()

unk_C0E8 = struct.unpack_from("<4Q", data, 0xC0E8)
v0 = 0x243F6A8885A308D3; v2 = 13; v3 = 0
for idx in range(4):
    v0 = sub_1DE72(v0 ^ ROL64(v3 ^ unk_C0E8[idx], v2))
    v3 = (v3 - 0x2E4AB5CD2E6D12FD) & 0xFFFFFFFFFFFFFFFF
    v2 += 11
SEED = v0 ^ 0xC0DEC0FFEEBADF00

v20 = [sub_1DE72(SEED ^ c) for c in [0x6A09E667F3BCC909, 0xBB67AE8584CAA73B, 0x3C6EF372FE94F82B, 0xA54FF53A5F1D36F1]]
qword_C088 = struct.unpack_from("<4Q", data, 0xC088)

T_E = ROR64(0x9044F5CB87AFD3AF ^ SEED, 7)
T_C = 0x83C43F18D6EB1975
E0 = SEED ^ 0x736F6D657468696E

REM = [(9 + i * 7) & 0x3F for i in range(40)]
MUL = [(i * 256) ^ 0x1000000001B3 for i in range(40)]
CAD = [(i * 40503) ^ v20[i & 3] for i in range(40)]
REM_c = [(17 + i * 13) & 0x3F for i in range(40)]

def inv_mod_2_64(x):
    inv = x
    for _ in range(6):
        inv = (inv * (2 - x * inv)) & 0xFFFFFFFFFFFFFFFF
    return inv

INV_MUL = [inv_mod_2_64(MUL[i]) for i in range(40)]

def ROR64(v, s):
    s &= 0x3F; v &= 0xFFFFFFFFFFFFFFFF
    return ((v >> s) | (v << (64 - s))) & 0xFFFFFFFFFFFFFFFF

# Try different prefixes from the E5B5 solution space
# Use the ISCC{} prefix and search inner bytes

# First, let me try a different approach entirely.
# Instead of fixing the prefix, let me generate ALL possible suffixes
# that satisfy E5B5 and check CFE6

v3_40_target = (T_E ^ v20[3] ^ v20[2] ^ ROL64(v20[0], 17) ^ ROL64(v20[1], 29)) & 0xFFFFFFFFFFFFFFFF

print("v3_40_target = 0x%016x" % v3_40_target)
print("T_E = 0x%016x" % T_E)
print("T_C = 0x%016x" % T_C)

# For each (b39, b38, b37) in printable range, compute b36
# Then check if b36 is also printable, and the full CFE6 matches

# Precompute CFE6 update for each byte at each position
cfe6_table = []
for pos in range(36, 40):
    tbl = {}
    for b in range(256):
        term = ROL64(qword_C088[pos & 3], pos) + pos*256 + b
        v9 = ROL64(0xD6E8FEB86659FD93 * term, REM_c[pos])
        tbl[b] = v9 ^ (v9 >> 29)
    cfe6_table.append(tbl)

# Since we want CFE6 to match T_C, and we know vc_36 (partial CFE6 after 36 bytes),
# we can compute what vc_36 needs to be given suffix bytes and T_C
# And check if the resulting vc_36 is compatible with the prefix

# Actually, let me instead iterate b39,b38,b37,b36 in the printable range
# and check both hashes directly

# But 95^4 = 81M is too many iterations.
# Instead, iterate b39,b38,b37 and compute b36 uniquely.
# 95^3 = 857K iterations - feasible!

print("Searching for E5B5+CFE6 match using printable suffixes...")

# For each prefix, we need v3_36 and vc_36
# Let me collect several E5B5-compatible prefixes to try

# First, try the known E5B5 prefix
prefixes_to_try = [
    # First 36 bytes of various E5B5 solutions
    list(b"ISCC{jMJyHq_NmQ6GJUPuBJDzqXdJy80jOx"),
    list(b"ISCC{K)=Cnj-7v@e*ld-\\6(Y5~@f;JpZ-<n"),
]

for prefix_idx, prefix in enumerate(prefixes_to_try):
    if len(prefix) != 36:
        continue

    # Compute v3_36 and vc_36
    v3 = E0
    vc = 0x3141592653589793
    ok = True
    for i in range(36):
        b = prefix[i]
        v3 = (ROL64(v3 ^ (b * MUL[i]), REM[i]) + CAD[i]) & 0xFFFFFFFFFFFFFFFF
        term = ROL64(qword_C088[i & 3], i) + i*256 + b
        v9 = ROL64(0xD6E8FEB86659FD93 * (vc ^ term), REM_c[i])
        vc = v9 ^ (v9 >> 29)

    v3_36 = v3
    vc_36 = vc

    print("\nPrefix %d: v3_36=0x%016x vc_36=0x%016x" % (prefix_idx, v3_36, vc_36))

    found = False
    count = 0
    for b39 in range(32, 127):
        # Backward: determine v3_39 from v3_40_target and b39
        raw39 = ROR64((v3_40_target - CAD[39]) & 0xFFFFFFFFFFFFFFFF, REM[39])
        v3_39 = (raw39 ^ (b39 * MUL[39])) & 0xFFFFFFFFFFFFFFFF

        for b38 in range(32, 127):
            raw38 = ROR64((v3_39 - CAD[38]) & 0xFFFFFFFFFFFFFFFF, REM[38])
            v3_38 = (raw38 ^ (b38 * MUL[38])) & 0xFFFFFFFFFFFFFFFF

            for b37 in range(32, 127):
                raw37 = ROR64((v3_38 - CAD[37]) & 0xFFFFFFFFFFFFFFFF, REM[37])
                v3_37 = (raw37 ^ (b37 * MUL[37])) & 0xFFFFFFFFFFFFFFFF

                # Compute b36 from v3_36 and v3_37
                # v3_37 = ROL64(v3_36 ^ (b36 * MUL[36]), REM[36]) + CAD[36]
                # ROR64(v3_37 - CAD[36], REM[36]) = v3_36 ^ (b36 * MUL[36])
                # b36 = (ROR64(v3_37 - CAD[36], REM[36]) ^ v3_36) * INV_MUL[36]

                raw36_needed = ROR64((v3_37 - CAD[36]) & 0xFFFFFFFFFFFFFFFF, REM[36])
                b36_raw = ((raw36_needed ^ v3_36) * INV_MUL[36]) & 0xFFFFFFFFFFFFFFFF

                if 32 <= b36_raw <= 126:
                    b36 = b36_raw

                    # Verify E5B5 (forward check)
                    v3_check = v3_36
                    for j, b in enumerate([b36, b37, b38, b39]):
                        pos = 36 + j
                        v3_check = (ROL64(v3_check ^ (b * MUL[pos]), REM[pos]) + CAD[pos]) & 0xFFFFFFFFFFFFFFFF
                    h_e = v3_check ^ v20[3] ^ v20[2] ^ ROL64(v20[0], 17) ^ ROL64(v20[1], 29)

                    if h_e == T_E:
                        # Check CFE6
                        vc_check = vc_36
                        for j, b in enumerate([b36, b37, b38, b39]):
                            pos = 36 + j
                            v9 = cfe6_table[j][b]
                            vc_check ^= v9  # WRONG: it's v9 = f(vc), then vc = v9 ^ (v9 >> 29)

                        # Actually, CFE6 step is: vc_new = v9 ^ (v9 >> 29) where v9 = ROL64(A*(vc_old^term),R)
                        vc_check = vc_36
                        for j, b in enumerate([b36, b37, b38, b39]):
                            pos = 36 + j
                            v9 = ROL64(0xD6E8FEB86659FD93 * (vc_check ^ (ROL64(qword_C088[pos & 3], pos) + pos*256 + b)), REM_c[pos])
                            vc_check = v9 ^ (v9 >> 29)

                        if vc_check == T_C:
                            flag = bytes(prefix + [b36, b37, b38, b39])
                            print("FOUND! Flag: %s" % repr(flag))
                            print("String: %s" % flag.decode())
                            found = True
                            break

                count += 1
                if count % 100000 == 0:
                    pass  # progress tracking
        if found:
            break
    if found:
        break

if not found:
    print("Not found with these prefixes")
    print("Last v3_37 = 0x%016x" % v3_37)
    print("Need v3_check = v3_36...")
    print("b36_raw = %d" % b36_raw if b36_raw else 0)
