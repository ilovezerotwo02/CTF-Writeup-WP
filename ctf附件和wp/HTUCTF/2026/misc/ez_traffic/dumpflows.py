import struct, collections, sys

d = open('q1_attack_v4.pcap', 'rb').read()
endian = '<'
off = 24
segs_by_flow = collections.OrderedDict()
first_ts = {}
while off + 16 <= len(d):
    ts, tu, incl, orig = struct.unpack_from(endian + 'IIII', d, off)
    off += 16
    pkt = d[off:off + incl]
    off += incl
    if len(pkt) < 14:
        continue
    if struct.unpack_from('>H', pkt, 12)[0] != 0x0800:
        continue
    ip = pkt[14:]
    if len(ip) < 20 or (ip[0] >> 4) != 4:
        continue
    ihl = (ip[0] & 0xf) * 4
    if ip[9] != 6:
        continue
    src = '.'.join(map(str, ip[12:16]))
    dst = '.'.join(map(str, ip[16:20]))
    tcp = ip[ihl:]
    sport, dport, seq, ack = struct.unpack_from('>HHII', tcp, 0)
    doff = (tcp[12] >> 4) * 4
    pl = tcp[doff:]
    if not pl:
        continue
    k = (src, sport, dst, dport)
    segs_by_flow.setdefault(k, []).append((seq, pl))
    first_ts.setdefault(k, ts + tu / 1e6)

flows = {}
for k, segs in segs_by_flow.items():
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

order = sorted(flows, key=lambda k: first_ts[k])
out = open('flows.txt', 'w', encoding='utf-8')
for k in order:
    v = flows[k]
    out.write('\n' + '=' * 70 + '\n')
    out.write('%s:%d -> %s:%d  t=%.3f  %d bytes\n' % (k[0], k[1], k[2], k[3], first_ts[k], len(v)))
    out.write('-' * 70 + '\n')
    out.write(v[:4000].decode('utf-8', 'replace'))
out.close()
print('flows', len(flows), 'written')
