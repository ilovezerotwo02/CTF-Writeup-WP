"""在 _s5.txt 里筛出能真正访问「任意 host:port」的 HTTP 正向代理。

两阶段：
 1) 先打 http://example.com/ 验证代理本身活着
 2) 再打靶机 /?id=1 与 /?id=2，两次响应必须不同（排除缓存型代理）

结果写入 _proxy_ok.txt
"""
import concurrent.futures as cf
import urllib.request, urllib.error, hashlib, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIST = os.path.join(ROOT, "_s5.txt")
TARGET = "http://103.163.47.230:34413"
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 300


def fetch(proxy, url, timeout=6):
    op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy}))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    try:
        r = op.open(url, timeout=timeout)
        return r.status, r.read()
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read()
        except Exception:
            return e.code, b""
    except Exception:
        return -1, b""


def stage1(hp):
    s, b = fetch("http://" + hp, "http://example.com/", 6)
    if s == 200 and b"Example" in b:
        return hp
    return None


def stage2(hp):
    p = "http://" + hp
    s1, b1 = fetch(p, TARGET + "/?id=1&x=1", 8)
    s2, b2 = fetch(p, TARGET + "/?id=2&x=1", 8)
    if s1 == 200 and s2 == 200 and b1 != b2:
        return hp, hashlib.md5(b1).hexdigest()[:6], hashlib.md5(b2).hexdigest()[:6], len(b1), len(b2)
    return None


cands = [l.strip() for l in open(LIST) if l.strip() and ":" in l][:LIMIT]
print("候选 %d 个" % len(cands), flush=True)
alive = []
with cf.ThreadPoolExecutor(60) as ex:
    for r in ex.map(stage1, cands):
        if r:
            alive.append(r)
print("阶段1 存活 %d: %s" % (len(alive), alive[:20]), flush=True)

with cf.ThreadPoolExecutor(20) as ex:
    for r in ex.map(stage2, alive):
        if r:
            print("HIT", r, flush=True)
            open(os.path.join(ROOT, "_proxy_ok.txt"), "a").write(r[0] + "\n")
print("done", flush=True)
