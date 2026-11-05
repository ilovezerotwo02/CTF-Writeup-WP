exec(open("cl.py").read().split("if __name__")[0])
from broker import TAG_SHARD, TAG_STAMP, TAG_PERMIT, TAG_MAND, TAG_PROBE, TAG_APERT
import broker, time, sys
h=Http("127.0.0.1",19999); so=SoLayer(h, verbose=False)
assert so.run() and so.run_chain()
b=broker.Broker(so.relay, verbose=False)
assert b.leak_tokens()
# duplicate run() but stop before C
K1,K2,K0,base = b.K1,b.K2,b.K0,b.base
import struct
from cl import q, put
b.send(b"G"+bytes([0]), b"PERMIT"); b.send(b"H"+bytes([0,0]), b"HELD")
body=b.send(b"I"+bytes([0])); permit_ptr=struct.unpack_from("<Q",body,0x10)[0]^K1
b.send(b"M"+bytes([0]), b"MANDATE"); b.send(b"O"+bytes([0,0]), b"HELD")
body=b.send(b"Q"+bytes([0])); mand_ptr=struct.unpack_from("<Q",body,0x10)[0]^K1
shp=[];stp=[]
for i in range(4):
    b.send(b"S"+bytes([i,i])); b.send(b"T"+bytes([i,i]))
    shp.append(struct.unpack_from("<Q",b.send(b"U"+bytes([i])),0x18)[0]^K1)
    b.send(b"s"+bytes([i,i])); b.send(b"t"+bytes([i,i]))
    stp.append(struct.unpack_from("<Q",b.send(b"u"+bytes([i])),0x18)[0]^K1)
fsh=[];fst=[]
for i in range(4):
    sh=bytearray(0xf0); st=bytearray(0x130); sseed=0x1000+i; tseed=0x2000+i
    payload=bytes([0x40+i])*0xa8; sh[0x48:0xf0]=payload
    hh=H(K0,sseed,[i],1)
    for j in range(21):
        w=struct.unpack_from("<Q",payload,8*j)[0]; hh=H(K0^sseed,K1,[hh,w,j],3)
    put(sh,0,TAG_SHARD); put(sh,8,i); put(sh,0x10,sseed); put(sh,0x18,K1^shp[i]); put(sh,0x20,K1^stp[i]); put(sh,0x28,tseed); put(sh,0x30,hh); put(sh,0x38,1)
    put(sh,0x40,H(K1,K0,[q(sh,k) for k in range(0,0x40,8)],8))
    put(st,0,TAG_STAMP); put(st,8,i); put(st,0x10,tseed); put(st,0x18,K1^stp[i]); put(st,0x20,K1^shp[i]); put(st,0x28,sseed); put(st,0x30,hh); put(st,0x38,1)
    put(st,0x40,H(K1^0x3c6ef372fe94f82b,K0,[q(st,k) for k in range(0,0x40,8)],8))
    fsh.append(sh); fst.append(st)
for i in range(4):
    b.send(b"F"+bytes([i])+bytes(fsh[i])); b.send(b"f"+bytes([i])+bytes(fst[i]))
h4=K0
for i in range(4):
    h4=H(K0^i,K1,[h4,q(fsh[i],0x30),q(fsh[i],0x10),q(fst[i],0x10),shp[i],stp[i]],6)
permit=bytearray(0x160)
put(permit,0,TAG_PERMIT); put(permit,8,0); put(permit,0x10,K1^permit_ptr); put(permit,0x18,K1^mand_ptr); put(permit,0x20,0); put(permit,0x28,h4); put(permit,0x30,1)
put(permit,0x38,H(K2,K1,[q(permit,k) for k in range(0,0x38,8)],7))
mand=bytearray(0xb0)
put(mand,0,TAG_MAND); put(mand,8,0); put(mand,0x10,K1^mand_ptr); put(mand,0x18,K1^permit_ptr); put(mand,0x20,0)
put(mand,0x28, rol(q(permit,8)^mand_ptr^K2^(base+0x4000),0x13))
put(mand,0x30, H(K2^K1,K0,[h4,permit_ptr,mand_ptr,q(permit,8),q(mand,8)],5)); put(mand,0x38,1)
put(mand,0x40, H(K2^0x13198a2e03707344,K1,[q(mand,k) for k in range(0,0x40,8)],8))
b.send(b"K"+bytes([0])+bytes(permit)); b.send(b"Y"+bytes([0])+bytes(mand))
print("READY permit=%#x mand=%#x base=%#x"%(permit_ptr,mand_ptr,base), flush=True)
time.sleep(int(sys.argv[1]) if len(sys.argv)>1 else 12)
st,body=b.relay(b"C"+bytes([0,0])+bytes([0,0,1,1,2,2,3,3]))
print("C ->",body, flush=True)
time.sleep(3)
