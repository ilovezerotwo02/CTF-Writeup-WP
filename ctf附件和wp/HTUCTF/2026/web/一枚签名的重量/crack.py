import sys, os, json, hmac, hashlib, base64, itertools, string

tok = json.load(open("creds.json"))["token"]
h, p, sig = tok.split(".")
signing_input = (h + "." + p).encode()
want = base64.urlsafe_b64decode(sig + "=" * (-len(sig) % 4))


def sign(key):
    return hmac.new(key.encode(), signing_input, hashlib.sha256).digest()


bases = """
htu htuctf HTU HTUCTF htu2025 htu2026 htuctf2025 htuctf2026
archive archives jing archive2026 danganshi 档案馆 档案
sign signature signkey weight weightofasignature
admin administrator root superadmin sysadmin manager
password passwd pass pass123 passw0rd password123 Password Password123 P@ssw0rd P@ssword
secret secretkey mysecret supersecret topsecret jwt jwtsecret sqlite flask session
key apikey mykey htuadmin htusecure htu@2026 Htu2026
123456 12345678 1234567890 111111 000000 123123 123321 654321 666666 888888 5201314
qwerty qwerty123 abc123 abcdef admin123 admin888 root123 test test123 demo
iloveyou woaini 520 woaini1314 nihao hello world
changeme letmein welcome default master monkey dragon sunshine princess football baseball
flag flag123 getflag htuflag
"""
words = [w.strip() for w in bases.split() if w.strip()]
suffixes = ["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "12", "123", "1234", "12345", "123456", "2024", "2025", "2026",
            "!", "@", "#", "@123", "!@#", "2026!", "1!", "_2026", "-2026"]
cands = set()
for w in words:
    for s in suffixes:
        cands.add(w + s)
        cands.add(w.upper() + s)
        cands.add(w.capitalize() + s)

print("候选", len(cands))
found = None
for c in cands:
    if hmac.compare_digest(sign(c), want):
        found = c
        break
print("SECRET:", found)
if found:
    json.dump({"secret": found}, open("secret.json", "w"))
