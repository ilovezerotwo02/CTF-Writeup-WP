#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 长虹守卫 - 航班日志解密脚本

import re, hashlib, struct, base64
from datetime import datetime, timedelta, timezone

def parse_flight_log(filepath):
    """解析航班日志，提取事件行"""
    events, lines = [], open(filepath,'r',encoding='utf-8',errors='ignore').readlines()
    for line in lines:
        if not re.match(r'^\d{4},', line):
            continue
        parts = line.strip().split(',', 9)
        if len(parts) < 9: continue
        events.append({'idx':int(parts[0]), 'time_str':parts[1],
                       'lon':float(parts[3]), 'event_type':parts[8], 'detail':parts[9]})
    return events, lines

def extract_key_hint(lines):
    """从日志末尾提取Base64密钥提示"""
    for token in re.findall(r'[A-Za-z0-9+/=]{80,}', ''.join(lines)):
        try:
            d = base64.b64decode(token).decode()
            if 'KEYMAT:' in d: return d
        except: continue
    return None

def calc_utc_candidates(event):
    """推算事件可能的UTC时间戳（尝试所有时区偏移和日期校正组合）"""
    local_dt = datetime.strptime(event['time_str'], '%Y-%m-%d %H:%M:%S')
    lon, tz_set = event['lon'], {round(event['lon'] / 15)}
    if lon > 150:   tz_set.update([12, 13, 14])
    elif lon < -150: tz_set.update([-10, -11, -12])

    candidates = set()
    for offset_h in tz_set:
        for corr in (0, -1):
            dt = local_dt + timedelta(days=corr) - timedelta(hours=offset_h)
            candidates.add(int(dt.replace(tzinfo=timezone.utc).timestamp()))
    return sorted(candidates)

def extract_ciphertext(pcap_path):
    """纯Python解析pcap，提取TCP载荷中的CIPH密文"""
    data = open(pcap_path, 'rb').read()
    if len(data) < 24: raise RuntimeError('pcap文件过小')
    magic = data[:4]
    if magic == b'\xd4\xc3\xb2\xa1': endian = '<'
    elif magic == b'\xa1\xb2\xc3\xd4': endian = '>'
    else: raise RuntimeError('不支持的pcap格式')

    pos = 24
    while pos + 16 <= len(data):
        incl_len = struct.unpack(endian + 'I', data[pos+8:pos+12])[0]
        pos += 16
        pkt = data[pos:pos+incl_len]
        pos += incl_len
        if len(pkt) < 14 or pkt[12:14] != b'\x08\x00': continue
        ip = pkt[14:]
        if len(ip) < 20 or (ip[0] >> 4) != 4 or ip[9] != 6: continue
        ihl, total_len = (ip[0] & 0x0f) * 4, struct.unpack('!H', ip[2:4])[0]
        tcp = ip[ihl:total_len]
        if len(tcp) < 20: continue
        payload = tcp[(tcp[12] >> 4) * 4:]
        m = re.search(rb'CIPH:([0-9a-fA-F]+)', payload)
        if m: return bytes.fromhex(m.group(1).decode())
    raise RuntimeError('未找到CIPH密文')

def decrypt_xor(ct, key_mat):
    """SHA256|XOR|CTR 模式解密"""
    ks = b''.join(hashlib.sha256(key_mat.encode() + struct.pack('>I', i)).digest()
                  for i in range((len(ct) + 31) // 32))
    return bytes(c ^ k for c, k in zip(ct, ks))

def main():
    events, lines = parse_flight_log('./LX517.txt')
    hint = extract_key_hint(lines)
    print('[+] 密钥模板:\n' + hint)
    key_tpl = re.search(r'^KEYMAT:(.+)$', hint, re.MULTILINE).group(1)

    evt_a = [e for e in events if e['event_type'] == 'EVT_A'][0]
    evt_b = [e for e in events if e['event_type'] == 'EVT_B'][0]
    evt_c_list = [e for e in events if e['event_type'] == 'EVT_C'
                  and ('marker=A2' in e['detail'] or 'marker=X9' in e['detail'])]

    syn_ts = calc_utc_candidates(evt_a)
    idl_ts = calc_utc_candidates(evt_b)
    ct = extract_ciphertext('./LX517.pcap')
    print('[+] 密文:', ct.hex())

    tried = 0
    for s in syn_ts:
        for i in idl_ts:
            for ec in evt_c_list:
                for a2 in calc_utc_candidates(ec):
                    key = key_tpl.replace('<EVT_A_UTC>',str(s)).replace('<EVT_B_UTC>',str(i)).replace('<EVT_C_UTC>',str(a2))
                    plain = decrypt_xor(ct, key)
                    tried += 1
                    if re.fullmatch(rb'ISCC\{[0-9a-f]{32}\}', plain):
                        print(f'\n[+] 成功! trials={tried}')
                        print(f'[+] key={key}')
                        print(f'[+] FLAG: {plain.decode()}')
                        return
    print(f'[-] 未找到，共尝试 {tried} 种组合')

if __name__ == '__main__':
    main()

