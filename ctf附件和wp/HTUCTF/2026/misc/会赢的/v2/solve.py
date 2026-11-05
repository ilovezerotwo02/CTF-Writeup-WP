# -*- coding: utf-8 -*-
"""会赢的(34) 重新分析：从新下载的 zip 独立提取全部隐藏数据"""
import base64, struct, io, zipfile, os, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(HERE, '会赢的.zip')

z = open(ZIP, 'rb').read()
print('zip len', len(z), 'md5', hashlib.md5(z).hexdigest())

# ---------- 1) 取出 zip 内的 jpeg ----------
zf = zipfile.ZipFile(io.BytesIO(z))
info = zf.infolist()[0]
jpeg = zf.read(info.filename)
print('\n[1] zip 内条目:', info.filename, 'size', info.file_size)

# ---------- 2) JPEG 尾部 (EOI 之后) ----------
i = jpeg.rfind(b'\xff\xd9')
tail = jpeg[i + 2:]
print('[2] EOI at', i, '/', len(jpeg), ' 尾部', len(tail), '字节:', tail)
p1 = base64.b64decode(tail + b'==').decode('utf-8')
print('    p1 = %r' % p1)
print('    p1: %d 字符 / %d 字节' % (len(p1), len(p1.encode())))

# ---------- 3) ZIP EOCD 注释 -> 半字节交换 + 反转 = 7z ----------
e = z.rfind(b'PK\x05\x06')
n = struct.unpack('<H', z[e + 20:e + 22])[0]
C = z[e + 22:e + 22 + n]
print('\n[3] EOCD comment:', n, '字节  注释后多余字节:', len(z) - (e + 22 + n))
W = bytes(((b & 0xF) << 4) | (b >> 4) for b in C)[::-1]
print('    还原后魔数:', W[:6].hex(), '(7z = 377abcaf271c)')
open(os.path.join(HERE, '_7z.7z'), 'wb').write(W)

# 7z: signature header 32B, 之后是 pack streams
off, size = struct.unpack('<QQ', W[12:28])
print('    NextHeaderOffset=%d NextHeaderSize=%d  -> 32+%d+%d = %d' %
      (off, size, off, size, 32 + off + size))

# flag.txt 的 pack stream: LZMA2 未压缩块，直接找 01 xx xx 头
import lzma
d = lzma.LZMADecompressor(format=lzma.FORMAT_RAW,
                          filters=[{'id': lzma.FILTER_LZMA2, 'dict_size': 1 << 22}])
content = d.decompress(W[32:32 + off])
print('    flag.txt: %d 字节, unused=%d' % (len(content), len(d.unused_data)))
print('    CRC32 = %08X' % (__import__('zlib').crc32(content) & 0xffffffff))
print('    raw   =', content)

# 内容反转 -> base64
p2 = base64.b64decode(content[::-1]).decode('utf-8')
print('    p2 = %r' % p2)
print('    p2: %d 字符 / %d 字节' % (len(p2), len(p2.encode())))

# ---------- 4) 汇总 ----------
print('\n==== 汇总 ====')
print('p1 =', repr(p1))
print('p2 =', repr(p2))
print('直接拼接 A(双下划线) =', repr(p1 + p2))
print('拼接 B(单下划线)     =', repr(p1[:-1] + p2))
open(os.path.join(HERE, '_flag_A.txt'), 'w', encoding='utf-8').write('HTUCTF{' + p1 + p2 + '}')
open(os.path.join(HERE, '_flag_B.txt'), 'w', encoding='utf-8').write('HTUCTF{' + p1[:-1] + p2 + '}')
