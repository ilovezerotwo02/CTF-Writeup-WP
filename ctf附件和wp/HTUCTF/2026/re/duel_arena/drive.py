import subprocess, sys, time, threading, queue

choices = sys.argv[1].split(',') if len(sys.argv) > 1 else []
q = queue.Queue()
p = subprocess.Popen(['duel_arena.exe'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, bufsize=0)


def reader():
    while True:
        b = p.stdout.read(1)
        if not b:
            break
        q.put(b)


threading.Thread(target=reader, daemon=True).start()

ci = 0
sent = []
buf = b''
last_send = 0.0
start = time.time()
while time.time() - start < 30:
    try:
        b = q.get(timeout=0.2)
    except queue.Empty:
        continue
    buf += b
    sys.stdout.buffer.write(b); sys.stdout.flush()
    if time.time() - last_send < 0.25:
        continue
    t = buf.decode('utf-8', errors='ignore')
    if t.endswith('选择 > '):
        if ci < len(choices):
            p.stdin.write((choices[ci] + '\n').encode())
            sent.append(choices[ci]); ci += 1
        else:
            p.stdin.write(b'0\n')
        p.stdin.flush(); buf = b''; last_send = time.time()
    elif t.endswith('（y/n）') or t.endswith('(y/n)'):
        p.stdin.write(b'n\n'); p.stdin.flush(); buf = b''; last_send = time.time()
    elif t.endswith('按回车继续。'):
        p.stdin.write(b'\n'); p.stdin.flush(); buf = b''; last_send = time.time()
p.kill()
print('\n[driver] sent:', sent)
