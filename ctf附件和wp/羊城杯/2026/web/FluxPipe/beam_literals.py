import struct, zlib, sys, os

def parse_beam(path):
    d = open(path, "rb").read()
    assert d[:4] == b"FOR1"
    i = 12
    chunks = {}
    while i + 8 <= len(d):
        tag = d[i:i+4].decode("latin1")
        size = struct.unpack(">I", d[i+4:i+8])[0]
        data = d[i+8:i+8+size]
        chunks[tag] = data
        i += 8 + size
        i += (4 - size % 4) % 4
    return chunks

def parse_atoms(chunk):
    n = struct.unpack(">I", chunk[:4])[0]
    atoms = []
    p = 4
    for _ in range(n):
        ln = chunk[p]; p += 1
        atoms.append(chunk[p:p+ln].decode("latin1", "replace")); p += ln
    return atoms

# minimal ETF decoder for literals
def decode_etf(b, p=0):
    def u8():
        nonlocal p; v = b[p]; p += 1; return v
    def u32():
        nonlocal p; v = struct.unpack(">I", b[p:p+4])[0]; p += 4; return v
    def u16():
        nonlocal p; v = struct.unpack(">H", b[p:p+2])[0]; p += 2; return v
    tag = u8()
    if tag == 97: return u8()
    if tag == 98: return u32() - 0x80000000 if False else struct.unpack(">i", b[p-4:p])[0]
    if tag == 100:  # atom
        n = u16(); s = b[p:p+n]; p += n; return s.decode("latin1")
    if tag == 119:  # small atom utf8
        n = u8(); s = b[p:p+n]; p += n; return s.decode("utf-8", "replace")
    if tag == 118:  # atom utf8
        n = u16(); s = b[p:p+n]; p += n; return s.decode("utf-8", "replace")
    if tag == 104:  # small tuple
        n = u8(); return tuple(decode_etf(b, p) if False else None for _ in range(0))  # placeholder
    raise ValueError("unhandled ETF tag %d at %d" % (tag, p-1))

chunks = parse_beam(sys.argv[1])
print("chunks:", list(chunks))
if "AtU8" in chunks:
    atoms = parse_atoms(chunks["AtU8"])
    print("=== ATOMS (%d) ===" % len(atoms))
    for a in atoms:
        print(" ", a)
if "LitT" in chunks:
    lit = chunks["LitT"]
    sz = struct.unpack(">I", lit[:4])[0]
    raw = zlib.decompress(lit[4:4+sz])
    print("=== LITERALS raw %d bytes ===" % len(raw))
    # dump as text-ish
    txt = raw.decode("latin1", "replace")
    import re
    for m in re.finditer(r"[ -~]{4,}", txt):
        print("  STR:", m.group(0))
