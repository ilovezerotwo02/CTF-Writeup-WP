import struct, sys, itertools

d=open('license','rb').read()
def rd(va,n): return d[va-0x400000:va-0x400000+n]
TTraw=rd(0x50e3c0,262144)
TT=list(struct.unpack('<65536I', TTraw))
G4=rd(0x5563c0,16384); ET=rd(0x55a3c0,73728); DT=rd(0x56c3c0,73728)
PI=list(rd(0x57e490,16))
NS=rd(0x57e470,16); PAD=rd(0x57e480,16); RCON=rd(0x57e4a0,64)
TGT=list(rd(0x57e3c0,48))

ETI=[None]*288
for row in range(288):
    t=bytearray(256)
    base=row*256
    for v in range(256): t[ET[base+v]]=v
    ETI[row]=t
DTI=[None]*288
for row in range(288):
    t=bytearray(256)
    base=row*256
    for v in range(256): t[DT[base+v]]=v
    DTI[row]=t

def fwd_round(S,r):
    out=[0]*16
    for g in range(4):
        base=(r*4+g)*1024
        w=0
        for i in range(4): w ^= TT[base+i*256+S[4*g+i]]
        for k in range(4):
            ob=0
            for j in range(4): ob ^= G4[(16*g+4*k+j)*256 + ((w>>(8*j))&0xff)]
            p=PI[4*g+k]
            out[p]=ET[((r+1)*16+p)*256+ob]
    return out

_cache={}
def Ginv(r,g):
    key=(r,g)
    if key in _cache: return _cache[key]
    cols=[]
    for b in range(32):
        w=1<<b; t=0
        for k in range(4):
            ob=0
            for j in range(4): ob ^= G4[(16*g+4*k+j)*256 + ((w>>(8*j))&0xff)]
            t |= ob<<(8*k)
        cols.append(t)
    M=[[0]*32 for _ in range(32)]
    for b in range(32):
        for i in range(32):
            if (cols[b]>>i)&1: M[i][b]=1
    A=[row[:] + [1 if i==j else 0 for j in range(32)] for i,row in enumerate(M)]
    rk=0
    for c in range(32):
        p=None
        for i in range(rk,32):
            if A[i][c]: p=i; break
        if p is None: continue
        A[rk],A[p]=A[p],A[rk]
        for i in range(32):
            if i!=rk and A[i][c]: A[i]=[x^y for x,y in zip(A[i],A[rk])]
        rk+=1
    inv=[row[32:] for row in A]
    # precompute table: for each possible t byte? build map w->(b0..b3) lazily via mitm dict
    base=(r*4+g)*1024
    T0=TT[base:base+256]; T1=TT[base+256:base+512]; T2=TT[base+512:base+768]; T3=TT[base+768:base+1024]
    dd={}
    for a in range(256):
        ta=T0[a]
        for b in range(256):
            dd[ta^T1[b]]=(a<<8)|b
    _cache.clear()   # keep only one
    _cache[key]=(inv,dd,T2,T3)
    return _cache[key]

def apply_mat(mat,x):
    out=0
    for i,row in enumerate(mat):
        s=0
        for b in range(32):
            if row[b]: s ^= (x>>b)&1
        out |= s<<i
    return out

def inv_round(S,r):
    out=[0]*16
    for g in range(4):
        inv,dd,T2,T3=Ginv(r,g)
        t=0
        for k in range(4):
            p=PI[4*g+k]
            t |= ETI[(r+1)*16+p][S[p]]<<(8*k)
        w=apply_mat(inv,t)
        found=None
        for c in range(256):
            T2c=T2[c]
            for e in range(256):
                got=dd.get(w ^ T2c ^ T3[e])
                if got is not None:
                    found=(got>>8,got&0xff,c,e); break
            if found: break
        if not found: raise RuntimeError("no solution r=%d g=%d"%(r,g))
        for i in range(4): out[4*g+i]=found[i]
    return out

def inv_block(ct,prev):
    S=list(ct)
    for r in range(15,-1,-1):
        S=inv_round(S,r)
    K=[0]*16
    for j in range(16):
        val=ETI[j][S[j]]
        K[j]=DTI[j][ val ^ DT[0x10000+256*j+prev[j]] ]
    return K

def rcon(v18,i): return RCON[16*v18 + (i&15)]

def keysched_fwd(B0,sels):
    B=list(B0)
    for k in range(4):
        v18=sels[k]; row=32+k+4*v18
        if v18==0:
            B=[B[i]^rcon(v18,i) for i in range(48)]
        elif v18==1:
            tmp=[B[i]^rcon(v18,i) for i in range(48)]
            B=[tmp[(x+5)%48] for x in range(48)]
        elif v18==2:
            B=[((x^rcon(v18,i))&0xff) for i,x in enumerate(B)]
            B=[((x>>4)|((x&15)<<4)) for x in B]
        else:
            tmp=[B[i]^rcon(v18,i) for i in range(48)]
            B=[tmp[47-x] for x in range(48)]
        B=[ET[(row<<8)+x] for x in B]
    return B

def keysched_inv(K,sels):
    B=list(K)
    for k in range(3,-1,-1):
        v18=sels[k]; row=32+k+4*v18
        B=[ETI[row][x] for x in B]
        if v18==0:
            B=[B[i]^rcon(v18,i) for i in range(48)]
        elif v18==1:
            tmp=[0]*48
            for i in range(48): tmp[i]=B[(i-5)%48]
            B=[tmp[i]^rcon(v18,i) for i in range(48)]
        elif v18==2:
            B=[((x>>4)|((x&15)<<4)) for x in B]
            B=[(x^rcon(v18,i)) for i,x in enumerate(B)]
        else:
            tmp=[0]*48
            for x in range(48): tmp[47-x]=B[x]
            B=[tmp[i]^rcon(v18,i) for i in range(48)]
    return B

def decode_B(B,t):
    P=[0]*48
    for i in range(48):
        P[i]=ETI[i&15][B[i]] ^ t ^ PAD[i&15]
    return P

def fnv(P):
    h=0x811c9dc5
    for b in P:
        h=((h^b)*0x1000193)&0xffffffff
    return h

def invert_all(ct48,label=""):
    blocks=[ct48[0:16],ct48[16:32],ct48[32:48]]
    K=[]
    prev=[0]*16
    for b in blocks:
        Ki=inv_block(b,prev)
        K+=Ki
        prev=b
    return K

if __name__=="__main__":
    ct=bytes.fromhex(sys.argv[1]) if len(sys.argv)>1 else bytes(TGT)
    print("ct:", ct.hex(), file=sys.stderr)
    K=invert_all(ct)
    print("K:", bytes(K).hex(), file=sys.stderr)
    hits=0
    for sels in itertools.product(range(4),repeat=4):
        B=keysched_inv(K,sels)
        for t in range(256):
            P=decode_B(B,t)
            if fnv(P)&0xff==t:
                hits+=1
                print("sels",sels,"t=%02x"%t,"P=",bytes(P))
    print("hits",hits, file=sys.stderr)
