FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ARG LIBC_REV=2.39-0ubuntu8.9

RUN apt-get update \
    && apt-get install -y --no-install-recommends xinetd \
    && apt-get install -y --no-install-recommends "libc6=${LIBC_REV}" "libc-bin=${LIBC_REV}" \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/xinetd.d/* \
    && useradd -m -u 1000 ctf

RUN printf '%s\n' \
    'service babel' \
    '{' \
    '    disable         = no' \
    '    socket_type     = stream' \
    '    protocol        = tcp' \
    '    wait            = no' \
    '    user            = ctf' \
    '    type            = UNLISTED' \
    '    port            = 8888' \
    '    bind            = 0.0.0.0' \
    '    server          = /app/babel' \
    '    per_source      = 10' \
    '    rlimit_cpu      = 60' \
    '    rlimit_as       = 1024M' \
    '}' \
    > /etc/xinetd.d/babel

RUN printf '%s\n' \
    '#!/bin/sh' \
    'set -eu' \
    'if [ ! -s /flag ]; then' \
    '    if [ -n "${FLAG:-}" ]; then' \
    '        printf "%s" "$FLAG" > /flag' \
    '    elif [ "${FLAG_RANDOM:-0}" = "1" ]; then' \
    '        r=$(od -An -tx1 -N16 /dev/urandom | tr -d " \n")' \
    '        printf "%s" "flag{$r}" > /flag' \
    '    else' \
    '        printf "%s" "flag{set_FLAG_env_or_mount_/flag}" > /flag' \
    '    fi' \
    'fi' \
    'unset FLAG FLAG_RANDOM' \
    'chmod 444 /flag 2>/dev/null || true' \
    'mkdir -p /var/log/xinetd' \
    'exec /usr/sbin/xinetd -dontfork -stayalive -filelog /var/log/xinetd/ctf.log' \
    > /entrypoint.sh \
    && chmod 755 /entrypoint.sh

WORKDIR /app
COPY babel /app/babel
RUN chmod 755 /app/babel

EXPOSE 8888
ENTRYPOINT ["/entrypoint.sh"]
