#!/usr/bin/env python3
"""ShadowMeter solve — 从 error.log 还原被外传的审计数据"""

import re, os, sys, tempfile, subprocess, json

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, "3_ShadowMeter", "extracted", "ShadowMeter附件", "error.log")

if not os.path.exists(LOG):
    print(f"未找到 error.log，预期路径: {LOG}")
    print("请将 error.log 放在脚本同目录下，或修改 LOG 变量路径")
    sys.exit(1)

# ── 1. 行状态机：按 [client:port] 追踪每个 TCP 连接的 POST body ──
connections = {}        # client_port → {"job":"", "seq":"", "note":"", "body_len":0}
collect = []            # 收集到的 SM 条目

with open(LOG, errors="replace") as f:
    for line in f:
        # 提取 client:port  例: [client 172.25.0.1:60118]
        m = re.search(r"\[client ([\d.]+:\d+)\]", line)
        if not m:
            continue
        host = m[1]

        # dumpio_in 标记 HTTP 请求行和请求体
        if "dumpio_in (data-HEAP):" in line:
            # 一个 POST 请求开始了
            if "POST " in line:
                connections[host] = {"body": "", "expect": 0, "job": "", "seq": ""}
            elif "Content-Length:" in line:
                cl = re.search(r"Content-Length: (\d+)", line)
                if cl and host in connections:
                    connections[host]["expect"] = int(cl[1])
            elif host in connections and connections[host]["expect"] > 0:
                # 提取请求体中的数据 (app=... 形式)
                payload = line.split("dumpio_in")[-1]
                payload = re.sub(r".*?\(data-HEAP\):\s*", "", payload).strip()
                payload = payload.replace("\\r\\n", "").replace("\\n", "")
                if payload and "job=SM-20260507-17" in payload:
                    conn = connections[host]
                    conn["body"] += payload
                    # 判断是否收齐 (根据 Content-Length)
                    if len(conn["body"]) >= conn["expect"]:
                        body = conn["body"][:conn["expect"]]
                        # 手工提取 note、seq
                        note_m = re.search(r"note=([^&]+)", body)
                        seq_m  = re.search(r"seq=(\d+)", body)
                        if note_m and seq_m:
                            collect.append({
                                "seq": int(seq_m[1]),
                                "note_enc": note_m[1]   # URL 编码的 base64
                            })
                        del connections[host]

# 合并重复 seq（取第一次出现的）
seen = set()
deduped = []
for e in collect:
    if e["seq"] not in seen:
        seen.add(e["seq"])
        deduped.append(e)
collect = deduped
collect.sort(key=lambda x: x["seq"])
print(f"共收集 {len(collect)} 个分片 (seq {collect[0]['seq']}~{collect[-1]['seq']})")

# ── 3. 还原 ZIP: 逐个 URL 解码 → 去 padding → 拼接 → 加 padding → 一次解码 ──
import urllib.parse

pieces = []
for entry in collect:
    raw = urllib.parse.unquote(entry["note_enc"])
    raw = raw.rstrip("=")         # 去掉本来的 padding
    pieces.append(raw)

big_b64 = "".join(pieces)
# 补回最终的 padding
pad = 4 - len(big_b64) % 4
if pad != 4:
    big_b64 += "=" * pad

import base64
zip_data = base64.b64decode(big_b64)

# 写入临时文件
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
tmp.write(zip_data)
tmp.close()
print(f"ZIP还原完成 ({len(zip_data)} bytes)")

# ── 4. 用 7z 命令行解密 ──
out_dir = tempfile.mkdtemp()
pwd = "SM-20260507-17:meter:report"
_7z = r"C:\Program Files\7-Zip\7z.exe"
rc = subprocess.call([
    _7z, "x", f"-p{pwd}", f"-o{out_dir}",
    tmp.name
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

os.unlink(tmp.name)  # 删除临时 ZIP

# ── 5. 读取 CSV 和 manifest ──
csv_path = os.path.join(out_dir, "export.csv")
mft_path = os.path.join(out_dir, "manifest.json")

if not os.path.exists(csv_path):
    print("失败请检查密码")
    sys.exit(1)

with open(csv_path, encoding="utf-8", errors="replace") as f:
    csv_lines = f.read().strip().split("\n")
with open(mft_path, encoding="utf-8", errors="replace") as f:
    manifest = json.load(f)

# ── 6. 按 manifest.focus.filter 定位 ──
flt = manifest["focus"]["filter"]
print(f"过滤条件: app={flt['app']} metric={flt['metric_name']} user={flt['user_id']}")

# 解析 CSV 列名: trace_id,app,user_id,event_time,metric_name,value,trace_tag
header = csv_lines[0].split(",")
col_idx = {name: i for i, name in enumerate(header)}

for row in csv_lines[1:]:
    cols = row.split(",")
    if len(cols) < len(header):
        continue
    if (cols[col_idx["app"]] == flt["app"]
            and cols[col_idx["user_id"]] == flt["user_id"]
            and cols[col_idx["metric_name"]] == flt["metric_name"]):
        tag = cols[col_idx["trace_tag"]]
        flag = tag.split("flag{")[1].rstrip("}") if "flag{" in tag else tag.replace("tg_", "")
        print(f"\nflag{{{flag}}}")
        break

# 清理
import shutil
shutil.rmtree(out_dir, ignore_errors=True)
