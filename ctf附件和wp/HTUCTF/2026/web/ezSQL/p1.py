import sys, os, re, urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_tools"))
import px

B = 'http://103.163.47.230:34413/?id='
for i, t in enumerate(["999", "abc", "2", "3", "0"]):
    s, h, b = px.get(B + urllib.parse.quote(t) + "&_=%d" % (i * 7919))
    body = re.sub(r'\s+', ' ', b)
    m = re.findall(r'<td>(.*?)</td>', body)
    print(repr(t), s, len(b), m[:9] if m else body[-200:])
