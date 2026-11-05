# -*- coding: utf-8 -*-
"""会赢的(34) 端到端复现：zip -> p1(前半句) + p2(后半句) -> flag
本脚本不提交任何 flag，只做本地还原。
"""
import base64, struct, io, zipfile, lzma, zlib, os, hashlib, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(HERE, '会赢的.zip')

z = open(ZIP, 'rb').read()
print('zip: %d bytes, md5 %s' % (len(z), hashlib.md5(z).hexdigest()))

# ---------- 1) JPEG 尾部 -> p1 ----------
jpeg = zipfile.ZipFile(io.BytesIO(z)).read('会赢的.jpeg')
tail = jpeg[jpeg.rfind(b'\xff\xd9') + 2:]
p1 = base64.b64decode(tail + b'==').decode('utf-8')
print('\n[1] JPEG 尾部 %d 字节 base64 ->' % len(tail))
print('    p1 = %r   (%d 字符 / %d 字节)' % (p1, len(p1), len(p1.encode())))

# ---------- 2) ZIP 注释 -> 7z -> flag.txt -> p2 ----------
e = z.rfind(b'PK\x05\x06')
n = struct.unpack('<H', z[e + 20:e + 22])[0]
W = bytes(((b & 0xF) << 4) | (b >> 4) for b in z[e + 22:e + 22 + n])[::-1]
assert W[:6] == bytes.fromhex('377abcaf271c'), '不是 7z'

off, size = struct.unpack('<QQ', W[12:28])
print('\n[2] EOCD 注释 %d 字节 -> 半字节交换+反转 -> 7z (魔数 %s)' % (n, W[:6].hex()))
print('    NextHeaderOffset=%d NextHeaderSize=%d, 32+%d+%d=%d' % (off, size, off, size, 32 + off + size))

d = lzma.LZMADecompressor(format=lzma.FORMAT_RAW,
                          filters=[{'id': lzma.FILTER_LZMA2, 'dict_size': 1 << 22}])
# W[32:32+off] 是两个 pack stream 的合体：前 76B 是 flag.txt，后 75B 是 encoded header。
# LZMADecompressor 遇到 LZMA2 terminator 就停，所以 unused=75 是 7z 自己的第二个 stream，不是夹带数据。
content = d.decompress(W[32:32 + off])
crc = zlib.crc32(content) & 0xffffffff
assert crc == 0xDAA05664, 'CRC 不匹配: %08X' % crc
print('    flag.txt: %d 字节, CRC=%08X, unused=%d' % (len(content), crc, len(d.unused_data)))

p2 = base64.b64decode(content[::-1]).decode('utf-8')
print('    p2 = %r   (%d 字符)' % (p2, len(p2)))

# ---------- 3) 拼接（两段共享同一个分隔空格） ----------
body = p1[:-1] + p2
flag = 'HTUCTF{' + body + '}'
print('\n[3] p1(%d) + p2(%d) 共享分隔下划线 -> %d 字符' % (len(p1), len(p2), len(body)))
print('\nFLAG = ' + flag)

open(os.path.join(HERE, 'FLAG.txt'), 'w', encoding='utf-8').write(flag)
print('\n已写入 FLAG.txt')
