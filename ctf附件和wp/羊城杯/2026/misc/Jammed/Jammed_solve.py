#!/usr/bin/env python3
"""Jammed CTF solution: reconstruct two-character fragments from two noisy Selectric pages.

Usage: put this file next to Jammed.zip, install `cryptography`, run python Jammed_solve.py.
The source rows below are manually transcribed from the provided images.
"""
import hashlib
import hmac
import io
from pathlib import Path
import struct
import zipfile

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# The first page has its *original* row numbers restored from the glyph remapping.
PAGE_A = """\
01/l;tb-/-g
02/h//;g/,x
03/ckbnq/-x
04/cdbbx/hu
05/qeghg/xb
06/hdjdu/xq
07/bxkgl/ek
08/eyhef/ef
09/cqlxy/qc
10//qpb-/cb
11//ck/g/xq
12/y;fcg/,p
13/htybl/ju
14/xbxey//-
15/puygc/hu
16/yxfgd/ke
17/jxty-/qn
18/ny-nn/;h
19/fxnh//n,
20/clntx/px
21/g;cxj/uu
22/fl,uf/ln
23/ppyhg/cd
24/x;hxp/cl
"""
PAGE_B = """\
01/17z99/91
02/0447x/81
03/ckbnk/91
04/8db9l/03
05/6exhx/x9
06/hdt7u/16
07/91k1l/ek
08/e0h5u/5u
09/c6l1h/k8
10/46e99/89
11/4c64x/16
12/07ucl/8e
13/hthb4/t3
14/19xeh/49
15/e3018/03
16/013x7/k5
17/t1zh9/62
18/2h92n/70
19/3x204/28
20/clntx/e1
21/x78xt/3u
22/u483u/12
23/ee0hl/8d
24/x70xe/c4
"""
# 4 tilt rows x 11 rotate columns, used to reverse the two control-bit losses.
ROWS = [
    "90652z48731",
    "bhkentlcdux",
    "wsi'.!oarvm",
    "-yqp=j/,;fg",
]
LOOKUP = {ch: (tilt, rotation) for tilt, line in enumerate(ROWS) for rotation, ch in enumerate(line)}


def snippets(text):
    d = {}
    for line in text.strip().splitlines():
        num, serial, fragment = line[:2], line[3:8], line[9:11]
        assert len(line) == 11 and line[2] == "/" and line[8] == "/", line
        d[int(num)] = fragment
    assert set(d) == set(range(1, 25))
    return d


def password():
    a, b = snippets(PAGE_A), snippets(PAGE_B)
    recovered = []
    print("num   A    B   original")
    for n in range(1, 25):
        decoded = ""
        for col, (ca, cb) in enumerate(zip(a[n], b[n])):
            # In the scan, lowercase 'l' and digit '1' look almost identical.
            # The row/rotation consistency check resolves this ambiguous glyph.
            if n == 22 and col == 0:
                assert cb == "1"
                cb = "l"
            ta, ra = LOOKUP[ca]
            tb, rb = LOOKUP[cb]
            assert ra == rb, (n, col, ca, cb)
            decoded += ROWS[2 * (ta // 2) + (tb % 2)][ra]
        print(f"{n:02d}    {a[n]}   {b[n]}    {decoded}")
        recovered.append(decoded)
    pw = "".join(recovered)
    assert len(pw) == 48
    return pw


def decrypt_aes_zip(raw_zip, password_bytes):
    """WinZip AES-256, uncompressed method 0 (this specific challenge archive)."""
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        info = archive.infolist()[0]
        assert info.filename == "flag.txt" and info.compress_type == 99
        # Vendor AE / AES-256 strength 3, original method 0 (stored).
        # AES extra-field value: version[2], vendor[2], strength[1], method[2].
        aes_extra = None
        extra = info.extra
        while extra:
            tag_id, size = struct.unpack_from("<HH", extra, 0)
            payload, extra = extra[4:4+size], extra[4+size:]
            if tag_id == 0x9901:
                aes_extra = payload
        assert aes_extra and aes_extra[4] == 3 and struct.unpack_from("<H", aes_extra, 5)[0] == 0
        local_head_offset = info.header_offset
        fn_len, ex_len = struct.unpack_from("<HH", raw_zip, local_head_offset + 26)
        start = local_head_offset + 30 + fn_len + ex_len
        body = raw_zip[start:start + info.compress_size]
    salt, verifier, ciphertext, auth = body[:16], body[16:18], body[18:-10], body[-10:]
    keys = hashlib.pbkdf2_hmac("sha1", password_bytes, salt, 1000, 66)
    assert hmac.compare_digest(verifier, keys[64:66]), "password verifier failed"
    expected_mac = hmac.new(keys[32:64], ciphertext, hashlib.sha1).digest()[:10]
    assert hmac.compare_digest(expected_mac, auth), "AES HMAC integrity check failed"
    ecb_encryptor = Cipher(algorithms.AES(keys[:32]), modes.ECB()).encryptor()
    plaintext = bytearray()
    for offset in range(0, len(ciphertext), 16):
        counter = (offset // 16 + 1).to_bytes(16, "little")
        keystream = ecb_encryptor.update(counter)
        plaintext.extend(x ^ y for x, y in zip(ciphertext[offset:offset+16], keystream))
    ecb_encryptor.finalize()
    return bytes(plaintext)


def main():
    pw = password()
    target = "cfde9ebf5fb607b0c8d54abd707fa622fd8a246032d8b06d528e684f6238dcab"
    digest = hashlib.sha256(pw.encode()).hexdigest()
    print("\npassword:", pw)
    print("SHA256    :", digest)
    print("attachment:", target)
    print("SHA256 match:", digest == target)
    with zipfile.ZipFile(Path(__file__).with_name("Jammed.zip")) as attachment:
        inner = attachment.read("treasure.zip")
    flag_data = decrypt_aes_zip(inner, pw.encode())
    print("AES password verifier & HMAC: PASS")
    print("FLAG:", flag_data.decode())
    Path(__file__).with_name("Jammed_flag.txt").write_bytes(flag_data)


if __name__ == "__main__":
    main()
