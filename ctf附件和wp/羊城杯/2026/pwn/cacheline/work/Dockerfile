FROM alpine:3.22
RUN apk add --no-cache pcre2 openssl zlib \
 && addgroup -g 1001 broker && adduser -D -u 1001 -G broker -h /home/broker -s /sbin/nologin broker \
 && addgroup -g 1002 vault && adduser -D -u 1002 -G vault -h /home/vault -s /sbin/nologin vault \
 && mkdir -p /opt/cacheline /home/vault
COPY nginx cacheline.so cachebroker cachevault ld-musl-x86_64.so.1 nginx.conf entry.sh /opt/cacheline/
RUN chmod +x /opt/cacheline/entry.sh
EXPOSE 9999
ENTRYPOINT ["/opt/cacheline/entry.sh"]
