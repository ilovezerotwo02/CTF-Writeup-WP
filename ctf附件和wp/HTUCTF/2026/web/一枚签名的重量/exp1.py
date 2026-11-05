import sys, os, json, urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_tools"))
import px

BASE = "http://103.163.47.230:34414"
tok = json.load(open("admin_token.json"))["token"]
OP = px.opener("http://143.246.138.227:80")
OP.addheaders = [("User-Agent", "Mozilla/5.0"), ("Cookie", "htu_token=" + tok)]

for f in ["monthly.csv", "quarterly.csv", "annual.csv"]:
    s, h, b = px.get(BASE + "/api/admin/export?file=" + urllib.parse.quote(f), OP)
    print("==", f, s, len(b))
    print(b[:400])
