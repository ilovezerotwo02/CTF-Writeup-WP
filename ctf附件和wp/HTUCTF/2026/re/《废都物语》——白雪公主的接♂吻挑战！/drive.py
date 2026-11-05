"""驱动 duel_arena（可指定 exe 与输入序列），用于观察剧情分支。"""
import subprocess, sys, time, os

exe = sys.argv[1] if len(sys.argv) > 1 else 'duel_arena.exe'
lines = sys.argv[2:]
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, bufsize=0)
os.set_blocking(p.stdout.fileno(), False)


def drain(tag):
    time.sleep(0.8)
    try:
        d = p.stdout.read() or b''
    except Exception:
        d = b''
    txt = d.decode('utf-8', 'replace')
    if txt.strip():
        print('--- [%s]' % tag)
        print(txt)
    return txt


drain('banner')
for i, ln in enumerate(lines):
    p.stdin.write((ln + '\n').encode())
    p.stdin.flush()
    drain('after %r' % ln)
time.sleep(1.0)
drain('tail')
p.kill()
