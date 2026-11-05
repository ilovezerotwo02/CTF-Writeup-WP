import sys, os, json, random, string
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_tools"))
import px

BASE = "http://103.163.47.230:34414"
OP = px.opener("http://143.246.138.227:80")
user = "hacker" + "".join(random.choice(string.digits) for _ in range(5))
pwd = "Passw0rd!2026"

s, h, b = px.post(BASE + "/api/register", {"username": user, "password": pwd}, OP)
print("register", s, b[:300])

s, h, b = px.get(BASE + "/api/me", OP)
print("me", s, b[:400])

tok = None
for c in OP.handlers:
    if hasattr(c, "cookiejar"):
        for ck in c.cookiejar:
            print("cookie", ck.name, ck.value[:60])
            if ck.name == "htu_token":
                tok = ck.value
json.dump({"user": user, "pwd": pwd, "token": tok}, open("creds.json", "w"), indent=1)
print("token saved", bool(tok))
