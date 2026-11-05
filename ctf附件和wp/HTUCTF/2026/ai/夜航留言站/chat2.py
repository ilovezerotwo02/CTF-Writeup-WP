import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "web", "_tools"))
import px

BASE = "http://103.163.47.230:34432"
OP = px.opener("http://143.246.138.227:80")


def chat(msg, timeout=90, tries=2):
    for i in range(tries):
        s, h, b = px.post(BASE + "/api/chat", raw=json.dumps({"message": msg}).encode(),
                          op=OP, ctype="application/json", timeout=timeout)
        if s == 200:
            try:
                return json.loads(b)
            except Exception:
                return {"raw": b}
        time.sleep(2)
    return {"error": b[:200]}


if __name__ == "__main__":
    print(chat("月色真美"))
    for m in sys.argv[1:]:
        r = chat(m)
        print("\n>>>", m)
        print("<<<", json.dumps(r, ensure_ascii=False)[:1500])
