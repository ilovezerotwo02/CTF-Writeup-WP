#!/bin/bash
set -e
mkdir -p /tmp/qwb
cp '/mnt/d/桌面/新建强网杯/reverse/license/license' /tmp/qwb/license
python3 - <<'EOF'
d=bytearray(open('/tmp/qwb/license','rb').read())
off=0x402fb9-0x400000
d[off:off+5]=b'\x90'*5
open('/tmp/qwb/licp','wb').write(d)
EOF
chmod +x /tmp/qwb/licp
A=bda7d397b51b7f23911c7a4ddcd32b1ecc2d8b1e7ba0c07d829e8876ba02f5969aedecee589ce258d18a238e45d3e22b
printf '%s\n' "$A" > /tmp/qwb/in_A.txt
printf '%096d\n' 0 > /tmp/qwb/in_B.txt
python3 -c "import random;random.seed(1);print(''.join(random.choice('0123456789abcdef') for _ in range(96)))" > /tmp/qwb/in_C.txt
python3 - <<'EOF'
a=open('/tmp/qwb/in_A.txt').read().strip()
open('/tmp/qwb/in_D.txt','w').write(a[:16]+'00'*40+'\n')
open('/tmp/qwb/in_11.txt','w').write('11'*48+'\n')
EXP='082f54e63c2997605d0679ba143a49d07dcdba76266c79d0'
open('/tmp/qwb/in_E1.txt','w').write(EXP+'00'*24+'\n')
open('/tmp/qwb/in_E2.txt','w').write('00'*24+EXP+'\n')
open('/tmp/qwb/in_E3.txt','w').write(EXP+EXP+'\n')
EOF
cp '/mnt/c/Users/ASUS/Documents/Qoder/2026-10-31/0f67305c/tracer.c' /tmp/qwb/tracer.c
cp '/mnt/c/Users/ASUS/Documents/Qoder/2026-10-31/0f67305c/tracerpid_sanitize.py' /tmp/qwb/tracerpid_sanitize.py
gcc -O2 -o /tmp/qwb/tracer /tmp/qwb/tracer.c
echo setup-ok
