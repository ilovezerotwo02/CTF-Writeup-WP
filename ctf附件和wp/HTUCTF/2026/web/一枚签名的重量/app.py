# -*- coding: utf-8 -*-
"""
HTU 档案库 · 档案资源管理平台
====================================
HTUCTF 2026 · Web 题目「档案库」

表面：一个功能完整的校内档案管理平台（注册 / 登录 / 档案 / 检索 / 通知 / 系统管理）。
考点：
  1. 登录态使用 HS256 签名的 JWT，密钥为弱口令 -> 爆破后伪造 role=admin
  2. /api/admin/export 存在任意文件读取（os.path.join 未做路径约束）
  3. 前置 WAF 只对原始 query string 做明文黑名单（不解码），
     而 Web 框架会 URL 解码一次 -> %2e%2e / %66lag 等单步绕过
"""

import functools
import hashlib
import os
import re
import secrets
import threading
import time

import jwt
from flask import Flask, Response, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# 基础配置
# ---------------------------------------------------------------------------

# JWT 签名密钥（考点①：人类可猜 + 字典可爆）
SECRET_KEY = "HTU@2026"
TOKEN_TTL = 86400 * 7          # 7 天
COOKIE_NAME = "htu_token"

# 档案目录（考点②的拼接前缀）
ARCHIVE_DIR = os.environ.get("HTU_ARCHIVE_DIR", "/var/htu/archives")
if not os.path.isdir(ARCHIVE_DIR):
    # 本地开发兜底目录；容器内 /var/htu/archives 由 Dockerfile 预先建好
    ARCHIVE_DIR = os.path.join(BASE_DIR, "_runtime_archives")

app = Flask(__name__)
app.json.ensure_ascii = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


# ---------------------------------------------------------------------------
# 通用返回与鉴权
# ---------------------------------------------------------------------------

def _ok(**extra):
    body = {"ok": True}
    body.update(extra)
    return jsonify(body)


def _fail(message, status=400):
    return jsonify({"ok": False, "error": message}), status


def issue_token(user):
    now = int(time.time())
    payload = {
        "sub": str(user["uid"]),   # PyJWT decode 端要求 sub 必须是字符串
        "name": user["username"],
        "role": user["role"],
        "iat": now,
        "exp": now + TOKEN_TTL,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def current_user():
    """从 cookie 解出 JWT，验签通过返回 payload，否则 None。"""
    token = request.cookies.get(COOKIE_NAME, "")
    if not token:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def login_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        payload = current_user()
        if payload is None:
            return _fail("未登录或会话已过期", 401)
        return view(payload, *args, **kwargs)
    return wrapper


def admin_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        payload = current_user()
        if payload is None:
            return _fail("未登录或会话已过期", 401)
        if payload.get("role") != "admin":
            return _fail("只有管理员才能使用", 403)
        return view(payload, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# 自研 WAF（考点③）
# ---------------------------------------------------------------------------

_WAF_BLOCK = ["..", "flag", "etc", "proc", "passwd", "shadow", "root", "%00"]
_WAF_MAX_QS = 200


@app.before_request
def waf():
    """对所有请求先做关键字过滤，命中即拦截。"""
    # 管理接口先鉴权、后进 WAF，避免普通用户通过 403 文案差异探测 WAF 规则
    if request.path.startswith("/api/admin/"):
        payload = current_user()
        if payload is None:
            return _fail("未登录或会话已过期", 401)
        if payload.get("role") != "admin":
            return _fail("只有管理员才能使用", 403)

    # 只对【原始 query string】做明文匹配：不解码、不做路径归一化、不解析参数名
    qs = request.query_string.decode("latin-1").lower()
    if len(qs) > _WAF_MAX_QS:
        return _fail("请求被安全策略拦截", 403)
    for token in _WAF_BLOCK:
        if token in qs:
            return _fail("请求被安全策略拦截", 403)
    return None


# ---------------------------------------------------------------------------
# 用户（内存态：每队独立容器实例，重启即重置；注意 gunicorn 必须单 worker）
# ---------------------------------------------------------------------------

_users = {}
_users_lock = threading.Lock()
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


def _hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _add_user(username, password, role="user", nickname="", bio="", created_at=None):
    with _users_lock:
        uid = len(_users) + 1
        _users[username] = {
            "uid": uid,
            "username": username,
            "password_hash": _hash(password),
            "role": role,
            "nickname": nickname or username,
            "bio": bio,
            "created_at": created_at or time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return _users[username]


def _public_user(user):
    return {
        "uid": user["uid"],
        "username": user["username"],
        "role": user["role"],
        "nickname": user["nickname"],
        "bio": user["bio"],
        "created_at": user["created_at"],
    }


def _seed_users():
    # 内置账号的口令每次启动随机生成，无法猜测，只能走 JWT 路线
    _add_user("admin", secrets.token_hex(16), role="admin",
              nickname="档案馆管理员", bio="档案库平台运维负责人", created_at="2026-08-11 09:12:40")
    _add_user("bob", secrets.token_hex(16),
              nickname="Bob", bio="档案馆借阅室", created_at="2026-09-02 14:26:03")
    _add_user("carol", secrets.token_hex(16),
              nickname="Carol", bio="档案馆办公室", created_at="2026-09-27 11:48:19")


# ---------------------------------------------------------------------------
# 预置业务数据（档案目录 + 通知）
# ---------------------------------------------------------------------------

REPORTS = [
    {
        "id": "r1",
        "name": "monthly.csv",
        "title": "月度归档汇总（2026-09）",
        "updated_at": "2026-10-08 18:22",
        "body": (
            "指标,本月,上月,环比\n"
            "新增归档(件),1284,1197,+7.3%\n"
            "调阅申请(次),862,845,+1.9%\n"
            "超期未还(件),12,18,-33.3%\n"
            "调阅完结率,93.4%,91.8%,+1.6pp\n"
        ),
    },
    {
        "id": "r2",
        "name": "quarterly.csv",
        "title": "季度调阅汇总（2026-Q3）",
        "updated_at": "2026-10-09 09:41",
        "body": (
            "库房,调阅准时率,异常告警,平均处置时长(min)\n"
            "文书档案库,99.96%,17,23\n"
            "科技档案库,99.91%,9,31\n"
            "声像档案库,99.99%,4,12\n"
            "基建档案库,99.87%,21,35\n"
        ),
    },
    {
        "id": "r3",
        "name": "annual.csv",
        "title": "年度档案盘点底稿（2025）",
        "updated_at": "2026-01-15 16:03",
        "body": (
            "盘点项,结论,整改期限\n"
            "账实相符率,部分通过,2026-03-31\n"
            "借阅流程合规,通过,-\n"
            "离线备份完整性,不通过,2026-02-28\n"
            "库房环境巡检,通过,-\n"
        ),
    },
]

NOTICES = [
    {
        "id": 1,
        "kind": "系统",
        "title": "欢迎使用 HTU 档案库",
        "body": "平台已开通档案中心、档案检索、消息通知等模块。首次登录后请到「档案中心」完善个人信息；如有使用问题请联系档案馆运维组。",
        "time": "2026-10-12 09:30",
    },
    {
        "id": 2,
        "kind": "运维",
        "title": "安全提醒：下月将接受上级安全检查",
        "body": "各部门注意：11 月起学校将接受上级安全检查，请大家在系统内不要保存任何明文口令。\n另外，登录态用的 JWT 签名密钥是我手动设置的，还是老规矩——平台名 + 年份 + 一个特殊符号，好记。有疑问当面问，别再发消息问我了。",
        "time": "2026-10-14 17:02",
    },
    {
        "id": 3,
        "kind": "公告",
        "title": "9 月归档汇总已发布",
        "body": "2026 年 9 月归档汇总已发布至「档案检索」，可在线查阅。如有异议请在 10 月 20 日前联系档案馆办公室。",
        "time": "2026-10-15 10:14",
    },
]


def _seed_archives():
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    for item in REPORTS:
        path = os.path.join(ARCHIVE_DIR, item["name"])
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(item["body"])


_seed_users()
_seed_archives()


# ---------------------------------------------------------------------------
# 页面路由：统一交给前端 SPA 渲染
# ---------------------------------------------------------------------------

@app.get("/")
@app.get("/login")
@app.get("/dashboard")
@app.get("/profile")
@app.get("/reports")
@app.get("/notifications")
@app.get("/admin")
def page():
    return render_template("index.html")


@app.get("/healthz")
def healthz():
    return _ok()


# ---------------------------------------------------------------------------
# 认证接口
# ---------------------------------------------------------------------------

@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    # 显式忽略 role 字段：注册出来的永远是普通用户
    if not _USERNAME_RE.match(username):
        return _fail("用户名需为 3-20 位字母、数字或下划线")
    if len(password) < 6:
        return _fail("密码至少 6 位")
    with _users_lock:
        if username in _users:
            return _fail("用户名已被注册", 409)
    user = _add_user(username, password)
    resp = _ok(user=_public_user(user))
    # 刻意不设 HttpOnly：本题要求选手能直接从浏览器读到 JWT 去爆破，
    # 真实生产环境应当加上 httponly=True
    resp.set_cookie(COOKIE_NAME, issue_token(user),
                    max_age=TOKEN_TTL, samesite="Lax", path="/")
    resp.delete_cookie("ez_token", path="/")   # 清理旧版（EzHelp）遗留的 cookie
    # 清理本机调试时其它应用/旧版遗留的 Flask session cookie。
    # 线上每队独立容器、选手浏览器是干净的，这两行都是无操作；只为本地调试时
    # devtools 里不出现无关 cookie 造成困惑。
    resp.delete_cookie("session", path="/")
    return resp


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    with _users_lock:
        user = _users.get(username)
    if user is None or user["password_hash"] != _hash(password):
        return _fail("用户名或密码错误", 401)
    resp = _ok(user=_public_user(user))
    # 刻意不设 HttpOnly：本题要求选手能直接从浏览器读到 JWT 去爆破，
    # 真实生产环境应当加上 httponly=True
    resp.set_cookie(COOKIE_NAME, issue_token(user),
                    max_age=TOKEN_TTL, samesite="Lax", path="/")
    resp.delete_cookie("ez_token", path="/")   # 清理旧版（EzHelp）遗留的 cookie
    # 清理本机调试时其它应用/旧版遗留的 Flask session cookie。
    # 线上每队独立容器、选手浏览器是干净的，这两行都是无操作；只为本地调试时
    # devtools 里不出现无关 cookie 造成困惑。
    resp.delete_cookie("session", path="/")
    return resp


@app.post("/api/logout")
def logout():
    resp = _ok()
    resp.set_cookie(COOKIE_NAME, "", max_age=0, path="/")
    return resp


@app.get("/api/me")
@login_required
def me(payload):
    with _users_lock:
        user = _users.get(payload.get("name"))
    if user is None:
        return _fail("账号不存在", 404)
    return _ok(
        user=_public_user(user),
        session={"cookie": COOKIE_NAME, "jwt_alg": "HS256", "expires_in": TOKEN_TTL},
    )


# ---------------------------------------------------------------------------
# 业务接口
# ---------------------------------------------------------------------------

@app.post("/api/profile")
@login_required
def update_profile(payload):
    data = request.get_json(silent=True) or {}
    nickname = str(data.get("nickname", "")).strip()[:20]
    bio = str(data.get("bio", "")).strip()[:120]
    with _users_lock:
        user = _users.get(payload.get("name"))
        if user is None:
            return _fail("账号不存在", 404)
        if nickname:
            user["nickname"] = nickname
        user["bio"] = bio
    return _ok(user=_public_user(user))


@app.get("/api/reports")
@login_required
def report_list(payload):
    items = []
    for meta in REPORTS:
        path = os.path.join(ARCHIVE_DIR, meta["name"])
        items.append({
            "id": meta["id"],
            "name": meta["name"],
            "title": meta["title"],
            "size": os.path.getsize(path) if os.path.exists(path) else 0,
            "updated_at": meta["updated_at"],
        })
    return _ok(reports=items)


@app.get("/api/reports/download")
@login_required
def report_download(payload):
    rid = request.args.get("id", "")
    meta = next((r for r in REPORTS if r["id"] == rid), None)
    if meta is None:
        return _fail("档案不存在", 404)
    path = os.path.join(ARCHIVE_DIR, meta["name"])
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return _fail("档案读取失败", 500)
    return Response(
        content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="%s"' % meta["name"]},
    )


@app.get("/api/notifications")
@login_required
def notification_list(payload):
    return _ok(notices=NOTICES)


# ---------------------------------------------------------------------------
# 管理接口（admin only）
# ---------------------------------------------------------------------------

@app.get("/api/admin/users")
@admin_required
def admin_users(payload):
    with _users_lock:
        users = [_public_user(u) for u in _users.values()]
    return _ok(users=users, total=len(users))


@app.get("/api/admin/export")
@admin_required
def admin_export(payload):
    """调阅日志 / 档案目录导出。仅导出 archives 目录下的文件。"""
    fname = request.args.get("file", "monthly.csv")
    path = os.path.join(ARCHIVE_DIR, fname)   # 考点②：相对穿越 / 绝对路径均可达
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(65536)
    except (FileNotFoundError, IsADirectoryError, PermissionError, OSError):
        return _fail("文件不存在或无法读取", 404)
    return Response(content, mimetype="text/plain; charset=utf-8")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "80")))
