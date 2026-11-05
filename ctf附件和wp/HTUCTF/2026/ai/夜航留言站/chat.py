import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "web", "_tools"))
import px

BASE = "http://103.163.47.230:34432"
OP = px.opener("http://143.246.138.227:80")


def state():
    s, h, b = px.get(BASE + "/api/state", OP)
    return s, b


def chat(msg):
    s, h, b = px.post(BASE + "/api/chat", raw=json.dumps({"message": msg}).encode(), op=OP, ctype="application/json")
    return s, b


if __name__ == "__main__":
    print("state:", state())
    for m in sys.argv[1:]:
        s, b = chat(m)
        print("\n>>>", m)
        print("<<<", s, b[:1200])
