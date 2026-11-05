PW = b"9kmidaaa"
TOPIC_NEWS = b"QWB2026_News"

def varint(n):
    out = b""
    while True:
        d = n & 0x7f; n >>= 7
        out += bytes([d | 0x80]) if n else bytes([d])
        if not n: break
    return out

def connect_pkt(pw=PW, user=b"QWB2026_Admin", cid=b"QWB_Client"):
    body = b"\x00\x04MQTT\x04\xc2\x43\x21"
    body += bytes([0, len(cid)]) + cid
    body += bytes([0, len(user)]) + user
    body += bytes([0, len(pw)]) + pw
    return b"\x10" + varint(len(body)) + body

def subscribe_pkt(topic, msgid=1):
    body = msgid.to_bytes(2, 'big') + len(topic).to_bytes(2, 'big') + topic
    return b"\x82" + varint(len(body)) + body

def unsubscribe_pkt(topic, msgid=1):
    body = msgid.to_bytes(2, 'big') + len(topic).to_bytes(2, 'big') + topic
    return b"\xa2" + varint(len(body)) + body

def publish_pkt(topic, payload=b"", msgid=2, qos=1):
    body = len(topic).to_bytes(2, 'big') + topic
    if qos: body += msgid.to_bytes(2, 'big')
    body += payload
    return bytes([0x30 | (qos << 1)]) + varint(len(body)) + body

def pingreq_pkt():
    return b"\xc0\x00"
