#!/usr/bin/env python3
import os
import random
import socket
import socketserver
import argparse

def load_flag():
    for p in ("/flag", "./flag.txt"):
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read().strip()
    return "flag{test_flag}"

FLAG = load_flag()

class CathylinFourPlus:
    def __init__(self, r, key):
        self.r = r
        self.S = (0xC, 0x5, 0x6, 0xB,
                  0x9, 0x0, 0xA, 0xD,
                  0x3, 0xE, 0xF, 0x8,
                  0x4, 0x7, 0x1, 0x2)
        self.P = (0, 5, 10, 15,
                  4, 9, 14, 3,
                  8, 13, 2, 7,
                  12, 1, 6, 11)
        self.RC = (0x0F0F, 0x3333, 0x55AA)
        self.key = key
        assert len(key) == self.r + 1

    @staticmethod
    def deblock(m):
        return [(m >> 12) & 0xF, (m >> 8) & 0xF, (m >> 4) & 0xF, m & 0xF]

    @staticmethod
    def block(nibbles):
        return (nibbles[0] << 12) | (nibbles[1] << 8) | (nibbles[2] << 4) | nibbles[3]

    def s_layer(self, x):
        n = self.deblock(x)
        n = [self.S[i] for i in n]
        return self.block(n)

    def permute_bits(self, x):
        bits = [(x >> (15 - i)) & 1 for i in range(16)]
        new_bits = [0] * 16
        for i in range(16):
            new_bits[self.P[i]] = bits[i]
        out = 0
        for b in new_bits:
            out = (out << 1) | b
        return out & 0xFFFF

    def encrypt(self, m):
        p = m & 0xFFFF
        for t in range(self.r - 1):
            p ^= self.key[t]
            p ^= self.RC[t]
            p = self.s_layer(p)
            p = self.permute_bits(p)
        p ^= self.key[self.r - 1]
        p ^= self.RC[self.r - 1]
        p = self.s_layer(p)
        c = p ^ self.key[-1]
        return c & 0xFFFF

def parse_hex16(s: str) -> int:
    s = s.strip().lower()
    if s.startswith("0x"):
        s = s[2:]
    if not (1 <= len(s) <= 4) or any(ch not in "0123456789abcdef" for ch in s):
        raise ValueError("bad hex")
    return int(s, 16) & 0xFFFF

def serve_one_client(rfile, wfile):
    # 每连接随机 key / mask
    r = 3
    key = [random.getrandbits(16) for _ in range(r + 1)]
    enc = CathylinFourPlus(r, key)
    mask = random.getrandbits(16)

    def wln(msg=""):
        wfile.write((msg + "\n").encode())
        wfile.flush()

    def write_prompt():
        wfile.write(b"Your input: ")
        wfile.flush()

    wln("=== CathylinFour++ (SPN 16-bit) ===")
    wln("Input: hex (e.g. 0x1234). Commands: h/help, k, q")
    wln(f"mask = 0x{mask:04x}")
    wln("Goal: submit (K3 ^ mask) to get the flag.")
    wln("----------------------------------")

    qcnt = 0
    QMAX = 4096

    while True:
        write_prompt()
        line = rfile.readline()
        if not line:
            break
        x = line.decode(errors="ignore").strip().lower()

        if x in ("q", "quit", "exit"):
            wln("Bye.")
            break

        if x in ("h", "help", "?"):
            wln("Commands:")
            wln("  <hex>   encrypt a 16-bit block, e.g. 0x1234")
            wln("  k       submit key proof (K3 ^ mask)")
            wln("  q       quit")
            continue

        if x == "k":
            wfile.write(b"Your key proof (hex): ")
            wfile.flush()
            ki = rfile.readline()
            if not ki:
                break
            try:
                proof = parse_hex16(ki.decode(errors="ignore"))
            except Exception:
                wln("Bad format. Bye.")
                break

            if proof == (key[-1] ^ mask):
                wln("You can smile: " + FLAG)
            else:
                wln("Wrong. Bye.")
            break

        try:
            a = parse_hex16(x)
        except Exception:
            wln("Bad format. Tips: 0x???? (1~4 hex digits).")
            continue

        qcnt += 1
        if qcnt > QMAX:
            wln("Too many queries. Bye.")
            break

        c = enc.encrypt(a)
        wln("Output: " + f"0x{c:04x}")

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        # 每连接超时：防止挂死占用线程
        self.request.settimeout(60)
        rfile = self.request.makefile("rb", buffering=0)
        wfile = self.request.makefile("wb", buffering=0)
        try:
            serve_one_client(rfile, wfile)
        except (socket.timeout, BrokenPipeError, ConnectionResetError):
            pass
        finally:
            try:
                rfile.close()
            except Exception:
                pass
            try:
                wfile.close()
            except Exception:
                pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen", default=None, help="listen address, e.g. 0.0.0.0")
    ap.add_argument("--port", type=int, default=37344)
    args = ap.parse_args()

    if args.listen:
        with ThreadedTCPServer((args.listen, args.port), Handler) as srv:
            srv.serve_forever()
    else:
        # 本地 stdin/stdout 单机调试模式
        import sys
        serve_one_client(sys.stdin.buffer, sys.stdout.buffer)

if __name__ == "__main__":
    main()
