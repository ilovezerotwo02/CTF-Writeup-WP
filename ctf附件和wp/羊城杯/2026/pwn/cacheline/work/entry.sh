#!/bin/sh
set -e
echo "flag{local_test_flag_0123456789}" > /home/vault/flag
chown vault:vault /home/vault/flag
chmod 400 /home/vault/flag
chmod +x /opt/cacheline/nginx /opt/cacheline/cachebroker /opt/cacheline/cachevault
mkdir -p /run /var/log/nginx /tmp
echo "[entry] start vault"
/opt/cacheline/cachevault >/tmp/vault.log 2>&1 &
sleep 0.3
echo "[entry] start broker"
/opt/cacheline/cachebroker >/tmp/broker.log 2>&1 &
sleep 0.3
ls -la /run/
echo "[entry] start nginx"
exec /opt/cacheline/nginx -c /opt/cacheline/nginx.conf -p /opt/cacheline/
