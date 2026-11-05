// vmshare solver: MITM over X (first transform key) and Y (second transform key)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <immintrin.h>
#include <time.h>
#include <omp.h>

static const uint8_t P_BYTES[32] = "SIMD_TINY_BLOCK_IS_A_NIGHTMARE!!";

// ciphertext
static uint8_t CT[32] = {0};

static inline void stream8(uint32_t seed, uint32_t salt, uint16_t *k) {
    uint32_t eax = ((seed & 0xffffffu) ^ salt);
    eax ^= eax >> 13;
    eax *= 0x45d9f3bu;
    eax ^= eax >> 16;
    uint32_t esi = 0;
    for (int i = 0; i < 8; i++) {
        eax = eax + esi + 0x9e3779b9u;
        esi += 0x7f4a7c15u;
        uint32_t ecx = (eax >> 13) ^ eax;
        ecx *= 0x85ebca6bu;
        eax = ecx ^ (ecx >> 16);
        k[i] = (uint16_t)(eax ^ (eax >> 16));
    }
}

static inline __m256i Tvec(void) {
    return _mm256_setr_epi16(0x1357,0x2468,0x369c,0x48ad,0x5be1,0x6cf2,0x7d03,0x8e14,
                             0x9f25,0xa036,0xb147,0xc258,0xd369,0xe47a,0xf58b,0x069c);
}

static inline __m256i fwd_transform(__m256i st, const uint16_t *k) {
    const __m256i T = Tvec();
    st = _mm256_xor_si256(st, _mm256_srli_epi16(st, 5));
    for (int r = 0; r < 8; r++) {
        __m256i a = _mm256_or_si256(_mm256_slli_epi16(st, 3), _mm256_srli_epi16(st, 13));
        a = _mm256_add_epi16(a, _mm256_set1_epi16((short)k[r]));
        a = _mm256_add_epi16(a, T);
        a = _mm256_xor_si256(a, _mm256_srli_epi16(a, 7));
        a = _mm256_or_si256(_mm256_slli_epi16(a, 9), _mm256_srli_epi16(a, 7));
        if (r < 7) a = _mm256_xor_si256(a, _mm256_srli_epi16(a, 5));
        st = a;
    }
    return st;
}

static inline __m256i unx(__m256i y, int s) {
    for (int sh = s; sh < 16; sh *= 2)
        y = _mm256_xor_si256(y, _mm256_srli_epi16(y, sh));
    return y;
}

static inline __m256i rotl(__m256i x, int n) {
    return _mm256_or_si256(_mm256_slli_epi16(x, n), _mm256_srli_epi16(x, 16 - n));
}

static inline __m256i inv_transform(__m256i st, const uint16_t *k) {
    const __m256i T = Tvec();
    for (int r = 7; r >= 0; r--) {
        if (r < 7) st = unx(st, 5);
        st = rotl(st, 7);                 // inverse of rotl9
        st = unx(st, 7);
        st = _mm256_sub_epi16(st, _mm256_set1_epi16((short)k[r]));
        st = _mm256_sub_epi16(st, T);
        st = rotl(st, 13);                // inverse of rotl3
    }
    st = unx(st, 5);                      // inverse of pre xor-shift
    return st;
}

// ---------- bloom filter ----------
#define BLOOM_BYTES (1u << 29)   // 2^32 bits
#define BLOOM_BITS  (1ull << 32)
static uint8_t *bloom;

static inline uint64_t mix64(uint64_t z) {
    z += 0x9e3779b97f4a7c15ull;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ull;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebull;
    return z ^ (z >> 31);
}

static const uint64_t SALT[4] = {0x1234567ull, 0x89abcdefull, 0xdeadbeefull, 0xfeedfaceull};

static inline void bloom_add(uint64_t sig) {
    for (int i = 0; i < 4; i++) {
        uint64_t b = mix64(sig ^ SALT[i]) & (BLOOM_BITS - 1);
        __atomic_fetch_or(&bloom[b >> 3], (uint8_t)(1u << (b & 7)), __ATOMIC_RELAXED);
    }
}
static inline int bloom_test(uint64_t sig) {
    for (int i = 0; i < 4; i++) {
        uint64_t b = mix64(sig ^ SALT[i]) & (BLOOM_BITS - 1);
        if (!(bloom[b >> 3] & (1u << (b & 7)))) return 0;
    }
    return 1;
}

// ---------- helpers ----------
static inline uint64_t sig_of(__m256i st) {
    uint16_t w[16];
    _mm256_storeu_si256((__m256i *)w, st);
    return (uint64_t)w[0] | ((uint64_t)w[1] << 16) | ((uint64_t)w[2] << 32);
}

static void encrypt_flag(const char *flag, uint8_t out[32]) {
    uint32_t X = (uint32_t)strtoul((char[]){flag[5],flag[6],flag[7],flag[8],flag[9],flag[10],flag[11],0}, NULL, 16);
    uint32_t Y = (uint32_t)strtoul((char[]){flag[13],flag[14],flag[15],flag[16],flag[17],flag[18],flag[19],0}, NULL, 16);
    uint16_t k[8];
    stream8(X, 0x31415926u, k);
    __m256i st = _mm256_loadu_si256((const __m256i *)P_BYTES);
    st = fwd_transform(st, k);
    stream8(Y, 0x27182818u, k);
    st = fwd_transform(st, k);
    _mm256_storeu_si256((__m256i *)out, st);
}

// candidate storage
#define MAXCAND 8000000
static uint64_t *cand_sig;
static uint32_t *cand_y;
static long cand_n = 0;

// open addressing set for pass3
static uint64_t *hs_key;   // sig48 or EMPTY
static uint32_t *hs_val;
static uint32_t hs_mask;
#define EMPTY 0xffffffffffffffffull

static inline uint64_t hs_hash(uint64_t k) { return mix64(k ^ 0x5bf03635ull); }

static void hs_build(long n) {
    uint32_t cap = 1;
    while (cap < (uint32_t)n * 4) cap <<= 1;
    hs_mask = cap - 1;
    hs_key = malloc(sizeof(uint64_t) * (size_t)cap);
    hs_val = malloc(sizeof(uint32_t) * (size_t)cap);
    for (uint32_t i = 0; i < cap; i++) hs_key[i] = EMPTY;
    for (long i = 0; i < n; i++) {
        uint64_t k = cand_sig[i];
        uint32_t p = (uint32_t)hs_hash(k) & hs_mask;
        while (hs_key[p] != EMPTY && hs_key[p] != k) p = (p + 1) & hs_mask;
        hs_key[p] = k;
        hs_val[p] = (uint32_t)i;
    }
}

static inline long hs_find(uint64_t k) {
    uint32_t p = (uint32_t)hs_hash(k) & hs_mask;
    while (hs_key[p] != EMPTY) {
        if (hs_key[p] == k) return (long)hs_val[p];
        p = (p + 1) & hs_mask;
    }
    return -1;
}

int main(int argc, char **argv) {
    FILE *f = fopen(argv[1] ? argv[1] : "cipher.bin", "rb");
    if (!f) { perror("cipher.bin"); return 1; }
    if (fread(CT, 1, 32, f) != 32) { fprintf(stderr, "short read\n"); return 1; }
    fclose(f);
    printf("CT: ");
    for (int i = 0; i < 32; i++) printf("%02x", CT[i]);
    printf("\n");

    // self test
    {
        uint8_t o[32];
        encrypt_flag("flag{FFFFFFF_FFFFFFF}", o);
        const uint8_t exp[32] = {0xa8,0x82,0x89,0x59,0xfa,0x2f,0x50,0x5d,0xa8,0xb8,0xb5,0xc3,0x48,0x98,0x69,0xf7,
                                 0x24,0x74,0xb1,0x3f,0xbc,0xca,0x2e,0x43,0x41,0x2f,0x18,0xde,0x6d,0x92,0x24,0x9d};
        printf("selftest enc: %s\n", memcmp(o, exp, 32) == 0 ? "OK" : "FAIL");
        if (memcmp(o, exp, 32) != 0) return 1;
        uint8_t o2[32];
        encrypt_flag("flag{0123456_ABCDEF0}", o2);
        const uint8_t exp2[32] = {0x6a,0xa5,0x4f,0x7c,0xcb,0xa9,0x4e,0xc8,0xf9,0x27,0x43,0x31,0xa6,0x12,0x9d,0xc7,
                                  0x8e,0xb9,0x0c,0x09,0x7b,0x5e,0xee,0xc1,0xaa,0xc1,0x60,0xc0,0x5a,0xb6,0x90,0x21};
        printf("selftest enc2: %s\n", memcmp(o2, exp2, 32) == 0 ? "OK" : "FAIL");
        if (memcmp(o2, exp2, 32) != 0) return 1;
    }


    if (argc > 3 && argv[3][0] == 'd') {
        uint32_t X = (uint32_t)strtoul(argv[4], NULL, 16);
        uint32_t Y = (uint32_t)strtoul(argv[5], NULL, 16);
        uint16_t kk[8];
        __m256i pst = _mm256_loadu_si256((const __m256i *)P_BYTES);
        __m256i ctv = _mm256_loadu_si256((const __m256i *)CT);
        stream8(X, 0x31415926u, kk);
        __m256i f1 = fwd_transform(pst, kk);
        stream8(Y, 0x27182818u, kk);
        __m256i b1 = inv_transform(ctv, kk);
        uint16_t w1[16], w2[16];
        _mm256_storeu_si256((__m256i *)w1, f1);
        _mm256_storeu_si256((__m256i *)w2, b1);
        printf("fwd sig=%012llx  inv sig=%012llx  equal=%d\n", (unsigned long long)sig_of(f1), (unsigned long long)sig_of(b1), memcmp(w1,w2,32)==0);
        for (int i=0;i<16;i++) printf("%04x ", w1[i]); printf("\n");
        for (int i=0;i<16;i++) printf("%04x ", w2[i]); printf("\n");
        uint8_t o[32];
        _mm256_storeu_si256((__m256i *)o, f1);
        __m256i chk = fwd_transform(f1, ({ static uint16_t z[8]; stream8(Y,0x27182818u,z); z; }));
        uint8_t o3[32];
        _mm256_storeu_si256((__m256i *)o3, chk);
        printf("reenc=%d\n", memcmp(o3, CT, 32)==0);
    }

    double t0 = omp_get_wtime();
    bloom = calloc(BLOOM_BYTES, 1);
    if (!bloom) { perror("calloc bloom"); return 1; }
    memset(bloom, 0, BLOOM_BYTES);

    // pass 1: forward over X
    const uint32_t N = (argc > 2) ? (1u << atoi(argv[2])) : (1u << 28);
#pragma omp parallel
    {
        __m256i pst = _mm256_loadu_si256((const __m256i *)P_BYTES);
        uint16_t k[8];
#pragma omp for schedule(static)
        for (uint32_t x = 0; x < N; x++) {
            stream8(x, 0x31415926u, k);
            __m256i st = fwd_transform(pst, k);
            bloom_add(sig_of(st));
        }
    }
    printf("[pass1] forward bloom done, %.2fs\n", omp_get_wtime() - t0);
    fflush(stdout);

    // pass 2: backward over Y
    cand_sig = malloc(sizeof(uint64_t) * MAXCAND);
    cand_y = malloc(sizeof(uint32_t) * MAXCAND);
    cand_n = 0;
    __m256i ct = _mm256_loadu_si256((const __m256i *)CT);
#pragma omp parallel
    {
        uint16_t k[8];
        long local_n = 0;
        uint64_t lbuf[4096];
        uint32_t ybuf[4096];
#pragma omp for schedule(static)
        for (uint32_t y = 0; y < N; y++) {
            stream8(y, 0x27182818u, k);
            __m256i st = inv_transform(ct, k);
            uint64_t s = sig_of(st);
            if (bloom_test(s)) {
                lbuf[local_n] = s;
                ybuf[local_n] = y;
                local_n++;
                if (local_n == 4096) {
                    long base;
#pragma omp atomic capture
                    { base = cand_n; cand_n += local_n; }
                    memcpy(&cand_sig[base], lbuf, sizeof(uint64_t) * local_n);
                    memcpy(&cand_y[base], ybuf, sizeof(uint32_t) * local_n);
                    local_n = 0;
                }
            }
        }
        if (local_n) {
            long base;
#pragma omp atomic capture
            { base = cand_n; cand_n += local_n; }
            memcpy(&cand_sig[base], lbuf, sizeof(uint64_t) * local_n);
            memcpy(&cand_y[base], ybuf, sizeof(uint32_t) * local_n);
        }
    }
    printf("[pass2] backward candidates: %ld, %.2fs\n", cand_n, omp_get_wtime() - t0);
    fflush(stdout);

    // pass 3: forward, look up candidate sigs
    hs_build(cand_n);
    printf("[pass3] hashset built, %.2fs\n", omp_get_wtime() - t0);
    fflush(stdout);

    long found = 0;
#pragma omp parallel
    {
        uint16_t k[8];
        __m256i pst = _mm256_loadu_si256((const __m256i *)P_BYTES);
#pragma omp for schedule(static)
        for (uint32_t x = 0; x < N; x++) {
            stream8(x, 0x31415926u, k);
            __m256i f1 = fwd_transform(pst, k);
            uint64_t s = sig_of(f1);
            long idx = hs_find(s);
            if (idx >= 0) {
                uint32_t y = cand_y[idx];
                uint16_t k2[8];
                stream8(y, 0x27182818u, k2);
                __m256i b1 = inv_transform(ct, k2);
                if (memcmp(&f1, &b1, 32) == 0) {
#pragma omp critical
                    {
                        printf("*** MATCH flag{%07X_%07X}\n", x, y);
                        fflush(stdout);
                        found++;
                    }
                }
            }
        }
    }
    printf("[done] %ld match(es), total %.2fs\n", found, omp_get_wtime() - t0);
    return 0;
}
