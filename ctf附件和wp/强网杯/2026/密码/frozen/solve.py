#!/usr/bin/env python3
# frozen (强网杯) solve script: recover D from cold-boot corrupted Falcon tree and decrypt flag
import numpy as np, hashlib, json, re, sys, struct

N = 128
LOG2 = np.log(2.0)

# ---------- parse the memory blob ----------
def parse_blob(cblob):
    d = np.frombuffer(cblob, dtype='<f8')
    Ltop = d[0:128] + 1j*d[128:256]
    def sizes(n):
        if n == 1: return []
        h = n//2
        return [h] + sizes(h) + sizes(h)
    sl = sizes(128)
    pos = 256
    def read_nodes():
        nonlocal pos
        out = []
        for m in sl:
            re = d[pos:pos+m]; im = d[pos+m:pos+2*m]; pos += 2*m
            out.append(re + 1j*im)
        return out
    nodes1 = read_nodes(); nodes2 = read_nodes()
    leaves1 = d[pos:pos+128]; pos += 128
    leaves2 = d[pos:pos+128]; pos += 128
    assert pos == len(d), (pos, len(d))
    def build(nodes, leaves):
        it = iter(nodes); lit = iter(leaves)
        def rec(n):
            if n == 1: return {"leaf": float(next(lit))}
            h = n//2
            L = next(it)
            c1 = rec(h); c2 = rec(h)
            return {"L": L, "c1": c1, "c2": c2, "n": n}
        return rec(128)
    return Ltop, build(nodes1, leaves1), build(nodes2, leaves2)

# ---------- observations in log2 domain ----------
def build_obs(t):
    obs = []
    def rec(nd):
        if "leaf" in nd:
            obs.append(("leaf", float(np.log2(abs(nd["leaf"]))))); return
        L = nd["L"]; m = len(L)
        th = np.pi*(2*np.arange(m)+1)/(2*m)
        cs = np.cos(th); sn = np.sin(th)
        obs.append(("node", (np.log2(np.abs(L.real)) - np.log2(np.abs(cs)),
                             np.log2(np.abs(L.imag)) - np.log2(np.abs(sn)))))
        rec(nd["c1"]); rec(nd["c2"])
    rec(t)
    return obs

def pack_obs(obs):
    vals = []
    for kind, v in obs:
        if kind == "leaf": vals.append(np.array([v]))
        else: vals.append(np.asarray(v[0])); vals.append(np.asarray(v[1]))
    return np.concatenate(vals)

def pred_log(s64):
    logE = np.concatenate([s64, s64[::-1]])   # symmetry of G00
    flat = []
    def rec(a):
        n = len(a)
        if n == 1:
            flat.append(np.array([a[0]])); return
        h = n//2
        x = a[:h]; y = a[h:]
        mx = np.maximum(x, y); mn = np.minimum(x, y)
        Ee = mx + np.log2(1.0 + 2.0**(mn-mx)) - 1.0          # arithmetic mean
        D = np.tanh((x-y)*LOG2/2.0)                          # (x-y)/(x+y)
        ld = np.log2(np.maximum(np.abs(D), 1e-300))
        flat.append(ld); flat.append(ld)
        rec(Ee)
        rec(Ee + np.log2(np.maximum(np.abs(1.0 - D*D), 1e-300)))   # harmonic mean
    rec(logE)
    return np.concatenate(flat)

def jac(u, f0, h=1e-6):
    J = np.zeros((len(f0), len(u)))
    for i in range(len(u)):
        up = u.copy(); up[i] += h
        J[:, i] = (pred_log(up) - f0)/h
    return J

# ---------- consensus reconstruction (error correction) ----------
def _grp(logs, rtol):
    best = []
    for i in range(len(logs)):
        if not np.isfinite(logs[i]): continue
        g = [k for k in range(len(logs)) if np.isfinite(logs[k]) and abs(logs[i]-logs[k]) < rtol]
        if len(g) > len(best): best = g
    return best

def consensus(t, rtol=1e-9, smallD=1e-12, p_pos=0.001, p_neg=0.01):
    def build(nd, n):
        if n == 1:
            return np.array([np.log2(abs(nd["leaf"]))])
        h = n//2
        E1 = build(nd["c1"], h)
        E2 = build(nd["c2"], h)
        Lx = nd["L"]
        th = np.pi*(2*np.arange(h)+1)/(2*h)
        cs = np.cos(th); sn = np.sin(th)
        re = np.real(Lx); im = np.imag(Lx)
        d_re = re/cs; d_im = im/sn
        val = np.clip(1.0 - 2.0**(E2-E1), 0.0, 1.0)
        ad = np.sqrt(val)
        D = np.zeros(h)
        if h == 1:
            D[0] = 0.0          # structurally zero (antisymmetry); stored L is float noise
        else:
            for j in range(h):
                p = h-1-j       # antisymmetry: D_p = -D_j
                cand = []
                if abs(cs[j]) > 1e-8: cand.append((abs(d_re[j]), np.sign(d_re[j]), abs(re[j])))
                if abs(sn[j]) > 1e-8: cand.append((abs(d_im[j]), np.sign(d_im[j]), abs(im[j])))
                if p != j:
                    if abs(cs[p]) > 1e-8: cand.append((abs(d_re[p]), -np.sign(d_re[p]), abs(re[p])))
                    if abs(sn[p]) > 1e-8: cand.append((abs(d_im[p]), -np.sign(d_im[p]), abs(im[p])))
                logs = np.array([np.log2(c[0]) if c[0] > 0 else -np.inf for c in cand])
                g = _grp(logs, rtol)
                if len(g) >= 2:
                    mag = float(2.0**np.mean([logs[k] for k in g]))
                else:
                    g2 = _grp(logs, 1e-2)
                    if len(g2) >= 2:
                        mag = float(2.0**np.mean([logs[k] for k in g2]))
                    else:
                        r1 = abs(ad[j]); r2 = abs(ad[p]) if p != j else r1
                        rl = np.array([np.log2(r1) if r1 > 0 else -np.inf,
                                       np.log2(r2) if r2 > 0 else -np.inf])
                        gr = _grp(rl, rtol)
                        if len(gr) >= 2 and cand:
                            mag = float(2.0**np.mean([rl[k] for k in gr]))
                        else:
                            dirs = [c[0] for c in cand if c[0] > 0]
                            mag = float(np.median(dirs)) if dirs else 0.0
                # sign: weighted majority over raw direct estimates (sign bit flips are rare)
                lp = ln = 0.0
                for (v, sg, sv) in cand:
                    if sg == 0: continue
                    pi = p_pos if sv > 0 else p_neg
                    lp += np.log(1-pi) if sg > 0 else np.log(pi)
                    ln += np.log(1-pi) if sg < 0 else np.log(pi)
                s = 1 if lp >= ln else -1
                if mag < smallD: mag = 0.0
                D[j] = s*mag
        D = np.clip(D, -0.999999, 0.999999)
        return np.concatenate([E1 + np.log2(1+D), E1 + np.log2(1-D)])
    return build(t, 128)[:64]

# ---------- log-domain annealing Gauss-Newton ----------
def fit_gn(t, u0, o, rounds=((3e-2,6),(1e-2,6),(3e-3,6),(1e-3,8),(3e-4,8),(1e-4,8)),
           kthr=0.2, lam=1e-8):
    u = u0.copy()
    for scale, iters in rounds:
        for _ in range(iters):
            f = pred_log(u)
            valid = (f > -25.0) & np.isfinite(f)
            r = o - f; r = np.where(np.isfinite(r), r, 0.0)
            k = np.where(np.abs(r - np.round(r)) < kthr, np.round(r), 0.0)
            e = np.where(np.isfinite(r-k), r-k, 0.0)
            w = np.where(valid, 1.0/(1.0 + (e/scale)**2), 0.0)
            J = jac(u, f)
            A = (J*w[:, None]).T@J + lam*np.eye(len(u))
            b = (J*w[:, None]).T@e
            du = np.linalg.solve(A, b)
            def cost(uu):
                ff = pred_log(uu); rr = o-ff; rr = np.where(np.isfinite(rr), rr, 0.0)
                kk = np.where(np.abs(rr-np.round(rr)) < kthr, np.round(rr), 0.0)
                ee = np.where(np.isfinite(rr-kk), rr-kk, 0.0)
                ww = np.where((ff > -25) & np.isfinite(ff), 1.0/(1.0+(ee/scale)**2), 0.0)
                return np.sum(ww*np.log1p((ee/scale)**2))
            base = cost(u); step = 1.0
            ok = False
            for _ in range(30):
                if cost(u+step*du) < base:
                    u = u + step*du; ok = True; break
                step *= 0.5
            if not ok: break
    return u

# ---------- tight-consistency linear polish ----------
def refine(t, u, o, schedule=(3e-3,1e-3,3e-4,1e-4,3e-5,1e-5,3e-6,1e-6,3e-7,1e-7,
                              3e-8,1e-8,3e-9,1e-9,1e-10), lam=1e-12):
    for thr in schedule:
        for _ in range(3):
            f = pred_log(u)
            valid = (f > -25.0) & np.isfinite(f)
            r = o - f; r = np.where(np.isfinite(r), r, 0.0)
            e = r - np.round(r)
            m = valid & (np.abs(e) < thr)
            if m.sum() < 2*len(u): continue
            J = jac(u, f); A = J[m].T@J[m] + lam*np.eye(len(u)); b = J[m].T@e[m]
            du = np.linalg.solve(A, b)
            u = u + du
            if np.abs(du).max() < 1e-13: break
    return u

# ---------- D and decryption ----------
def inv_fft_D(G00):
    M = np.exp(1j*np.pi*np.outer(np.arange(N), 2*np.arange(N)+1)/N)
    return np.real((G00 @ M.T.conj())/N)

def canon(D): return ",".join(str(int(c)) for c in D)

def keystream(key, length):
    out = b""; ctr = 0
    while len(out) < length:
        out += hashlib.sha256(key + ctr.to_bytes(4, "big")).digest(); ctr += 1
    return out[:length]

def decrypt(D, ct):
    fk = hashlib.sha256(b"frozen:" + canon(D).encode()).digest()
    return bytes(a ^ b for a, b in zip(ct, keystream(fk, len(ct))))

def solve(cblob, ct):
    Ltop, t1, t2 = parse_blob(cblob)
    obs = build_obs(t1); o = pack_obs(obs)
    u = consensus(t1)
    u = fit_gn(t1, u, o)
    u = refine(t1, u, o)
    G = 2.0**np.concatenate([u, u[::-1]])
    Dr = inv_fft_D(G); D = np.round(Dr).astype(np.int64)
    return list(int(x) for x in D), float(np.max(np.abs(Dr - D))), decrypt(D, ct)

if __name__ == "__main__":
    txt = open(sys.argv[1]).read()
    cblob = bytes.fromhex(re.search(r'memory\s*=\s*([0-9a-fA-F]+)', txt).group(1))
    ct = bytes.fromhex(re.search(r'flag\s*=\s*([0-9a-fA-F]+)', txt).group(1))
    D, ierr, pt = solve(cblob, ct)
    print("integrality_err=%.3e" % ierr)
    print("flag =", pt.decode())
