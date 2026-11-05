#!/usr/bin/env python3
# 北极星混淆 — 解题脚本
# 分两层：第一层逆向splitmix64置换XOR，第二层白盒AES的DFA密钥恢复

S=lambda x:x&0xffffffffffffffff
class R:
    __slots__=("t",)
    def __init__(s,x):s.t=S(x)
    def n(s):
        s.t=S(s.t-0x61C8864680B583EB)
        z=s.t
        z=S(((z>>30)^z)*0xBF58476D1CE4E5B9)
        z=S(((z>>27)^z)*0x94D049BB133111EB)
        return (z>>31)^z

def G(a,b):
    while b:a,b=b,a%b
    return a

def C(m,v):
    v=((v>>17)|1)%m
    if v==0:v=1
    while G(v,m)!=1:v=(v+2)%m
    if v==0:v=1
    return v

def IN(k,L,b):
    v8=S((0x6A09E667F3BCC909*b)^(0xD1342543DE82EF95*L)^k)
    v7=0
    for _ in range(4):
        r=R(v7^v8);o=r.n();v8=r.t;v7=S(v7^o)
    return v7

def DC(src,ns,sz,key):
    K=S(key);V=IN(K,sz,20);stp=C(sz,V)
    of=S(IN(S(V^0xA5A5A5A55A5A5A5A),sz,0)>>19)%sz
    ss=C(ns,K);s0=(K>>23)%ns
    r=R(V);b=bytearray(sz)
    for i in range(sz):
        d=S(of+stp*i)%sz
        ai=S(s0+ss*i)%ns;bi=i//ns
        xk=S((61*i-89*d)&0xFF)^((r.n()>>(8*(i&7)))&0xFF)
        b[d]=src[ai][bi]^xk
    return b

if __name__=="__main__":
    with open("traditional_re","rb") as f:
        elf=f.read()

    # 第一层解密
    p1=[bytearray(elf[a:a+10]) for a in[0x14e0c0,0x14e100,0x14e140,0x14e180,0x14e1c0]]
    s1=DC(p1,5,48,0x61F29C0D87A453B1)
    p2=[bytearray(elf[0x14e200+i*0xec0:0x14e200+i*0xec0+3724]) for i in range(11)]
    s2=DC(p2,11,40960,0xD3B5407C19EA8F26)

    # 验证第一层
    assert s2[54:58]==b"blu{"
    print("sec1:",s1.hex())
    print("blu{",s2[58:79].hex(),"}",sep="")

    # 第二层: DFA恢复的AES密钥解密flag
    K=bytes.fromhex("8f4d2a91c736e05bb8a4f01762de39ac")
    C=bytes.fromhex("c6bae55d0275ac4f4a5da18fda143fa9"
                    "486079b58b82039a59c160821547e384"
                    "25af09ae621b3fe309e45f929f64002c")
    try:
        from Crypto.Cipher import AES
        a=AES.new(K,AES.MODE_ECB);p=a.decrypt(C)
        f=p[:-p[-1]].decode()
        print("FLAG:",f)
    except:
        print("pip install pycryptodome then AES-ECB decrypt")
