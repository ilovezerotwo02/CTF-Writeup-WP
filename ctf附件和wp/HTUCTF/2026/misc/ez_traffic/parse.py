import struct, sys, collections

path = sys.argv[1] if len(sys.argv) > 1 else 'q1_attack_v4.pcap'
d = open(path, 'rb').read()
magic = d[:4]
assert magic in (b'\xd4\xc3\xb2\xa1', b'\xa1\xb2\xc3\xd4', b'\x4d\x3c\xb2\xa1', b'\xa1\xb2\x3c\x4d')
endian = '<' if magic in (b'\xd4\xc3\xb2\xa1', b'\x4d\x3c\xb2\xa1') else '>'
# linktype
linktype = struct.unpack_from(endian + 'I', d, 20)[0]
print('linktype', linktype, 'endian', endian)

off = 24
streams = collections.OrderedDict()   # (src,sport,dst,dport) -> [seq->bytes]
packets = 0
while off + 16 <= len(d):
    ts, tu, incl, orig = struct.unpack_from(endian + 'IIII', d, off)
    off += 16
    pkt = d[off:off + incl]
    off += incl
    packets += 1
    # ethernet
    if linktype == 1:
        if len(pkt) < 14:
            continue
        eth_type = struct.unpack_from('>H', pkt, 12)[0]
        p = 14
        while eth_type in (0x8100, 0x88a8):
            eth_type = struct.unpack_from('>H', pkt, p + 2)[0]
            p += 4
        if eth_type != 0x0800:
            continue
    else:
        p = 0
    ip = pkt[p:]
    if len(ip) < 20 or (ip[0] >> 4) != 4:
        continue
    ihl = (ip[0] & 0xf) * 4
    proto = ip[9]
    if proto != 6:
        continue
    src = '.'.join(str(b) for b in ip[12:16])
    dst = '.'.join(str(b) for b in ip[16:20])
    tcp = ip[ihl:]
    sport, dport, seq, ack = struct.unpack_from('>HHII', tcp, 0)
    doff = (tcp[12] >> 4) * 4
    payload = tcp[doff:]
    if not payload:
        continue
    streams.setdefault((src, sport, dst, dport), []).append((seq, payload))

print('packets', packets, 'streams', len(streams))

# 合并每个方向
flows = {}
for k, segs in streams.items():
    segs.sort()
    buf = bytearray()
    base = segs[0][0]
    for seq, pl in segs:
        pos = (seq - base) & 0xffffffff
        if pos > len(buf) + 65535:
            continue
        if pos > len(buf):
            buf.extend(b'\0' * (pos - len(buf)))
        buf[pos:pos + len(pl)] = pl
    flows[k] = bytes(buf)

# 输出所有 HTTP 请求/响应
names = {}
for (s, sp, dd, dp), data in flows.items():
    if b'HTTP/' in data[:8] or b'HTTP/' in data[:16]:
        print('\n==== %s:%d -> %s:%d (%d bytes) ====' % (s, sp, dd, dp, len(data)))
        print(data[:2500].decode('utf-8', 'replace'))
