#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <windows.h>
#include <timeapi.h>
#include <ctype.h>

#include <array>
#include <vector>
#include <string>
#include <unordered_map>
#include <stdexcept>
#include <cstdint>
#include <cctype>

// ========================================
//  2x2x2 ħ�����ܣ����� mofang.cpp �ļ����߼���
//  ˵������ÿ�� 8 �ֽڿ�ִ�У�����������(mod256) + �ǿ��û������ Base64 ���
// ========================================
namespace g3 {

    using Perm8 = std::array<uint8_t, 8>;

    struct MoveSpec {
        Perm8 perm;                 // old_index -> new_index
        std::array<uint8_t, 8> add;  // ����ʱ�� old λ�üӶ��٣�mod 256��
    };

    // ---------- Base64(�������õ� encode) ----------
    static const char* ahr2 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

    static std::string fafe2(const std::vector<uint8_t>& data) {
        std::string out;
        out.reserve(((data.size() + 2) / 3) * 4);

        size_t i = 0;
        while (i + 3 <= data.size()) {
            uint32_t n = (uint32_t(data[i]) << 16) | (uint32_t(data[i + 1]) << 8) | uint32_t(data[i + 2]);
            out.push_back(ahr2[(n >> 18) & 63]);
            out.push_back(ahr2[(n >> 12) & 63]);
            out.push_back(ahr2[(n >> 6) & 63]);
            out.push_back(ahr2[n & 63]);
            i += 3;
        }

        size_t rem = data.size() - i;
        if (rem == 1) {
            uint32_t n = (uint32_t(data[i]) << 16);
            out.push_back(ahr2[(n >> 18) & 63]);
            out.push_back(ahr2[(n >> 12) & 63]);
            out.push_back('=');
            out.push_back('=');
        }
        else if (rem == 2) {
            uint32_t n = (uint32_t(data[i]) << 16) | (uint32_t(data[i + 1]) << 8);
            out.push_back(ahr2[(n >> 18) & 63]);
            out.push_back(ahr2[(n >> 12) & 63]);
            out.push_back(ahr2[(n >> 6) & 63]);
            out.push_back('=');
        }

        return out;
    }

    // ---------- PKCS#7 padding (block=8) ----------
    static std::vector<uint8_t> pkcs7_pad(const std::vector<uint8_t>& data, size_t block = 8) {
        if (block == 0) throw std::runtime_error("block size must be > 0");
        size_t pad = block - (data.size() % block);
        if (pad == 0) pad = block;

        std::vector<uint8_t> out = data;
        out.insert(out.end(), pad, uint8_t(pad));
        return out;
    }

    // ---------- �û�/���û���Ӽ� ----------
    static Perm8 invert_perm(const Perm8& p_old_to_new) {
        Perm8 inv{};
        for (uint8_t old = 0; old < 8; ++old) {
            uint8_t nw = p_old_to_new[old];
            inv[nw] = old;
        }
        return inv;
    }

    static std::array<uint8_t, 8> hsg32(const std::array<uint8_t, 8>& block, const Perm8& p_old_to_new) {
        std::array<uint8_t, 8> out{};
        for (uint8_t old = 0; old < 8; ++old) {
            out[p_old_to_new[old]] = block[old];
        }
        return out;
    }

    static inline uint8_t h3a(uint8_t v, uint8_t a) {
        return uint8_t((uint16_t(v) + uint16_t(a)) & 0xFF);
    }

    // һ�����ܣ��ȼӣ����û�
    static std::array<uint8_t, 8> bbb4532(const std::array<uint8_t, 8>& block, const MoveSpec& ms) {
        std::array<uint8_t, 8> tmp{};
        for (int i = 0; i < 8; ++i) tmp[i] = h3a(block[i], ms.add[i]);
        return hsg32(tmp, ms.perm);
    }

    static std::array<uint8_t, 8> knw345(const std::vector<int>& idxs, uint8_t k) {
        std::array<uint8_t, 8> a{};
        for (int id : idxs) a[id] = k;
        return a;
    }

    // ���������� mofang.cpp ����һ�£�
    static std::unordered_map<std::string, MoveSpec> vs35z() {
        std::unordered_map<std::string, MoveSpec> mv;

        mv["R"].perm = Perm8{ 0,5,2,1,4,7,6,3 };
        mv["L"].perm = Perm8{ 2,1,6,3,0,5,4,7 };
        mv["U"].perm = Perm8{ 0,1,6,2,4,5,7,3 };
        mv["D"].perm = Perm8{ 1,5,2,3,0,4,6,7 };
        mv["F"].perm = Perm8{ 0,1,2,3,6,4,7,5 };
        mv["B"].perm = Perm8{ 1,3,0,2,4,5,6,7 };

        mv["R"].add = knw345({ 1,3,5,7 }, 1);
        mv["L"].add = knw345({ 0,2,4,6 }, 2);
        mv["U"].add = knw345({ 2,3,6,7 }, 3);
        mv["D"].add = knw345({ 0,1,4,5 }, 4);
        mv["F"].add = knw345({ 4,5,6,7 }, 5);
        mv["B"].add = knw345({ 0,1,2,3 }, 6);

        mv["R'"].perm = invert_perm(mv["R"].perm); mv["R'"].add = knw345({ 1,3,5,7 }, 7);
        mv["L'"].perm = invert_perm(mv["L"].perm); mv["L'"].add = knw345({ 0,2,4,6 }, 8);
        mv["U'"].perm = invert_perm(mv["U"].perm); mv["U'"].add = knw345({ 2,3,6,7 }, 9);
        mv["D'"].perm = invert_perm(mv["D"].perm); mv["D'"].add = knw345({ 0,1,4,5 }, 10);
        mv["F'"].perm = invert_perm(mv["F"].perm); mv["F'"].add = knw345({ 4,5,6,7 }, 11);
        mv["B'"].perm = invert_perm(mv["B"].perm); mv["B'"].add = knw345({ 0,1,2,3 }, 12);

        return mv;
    }

    static std::vector<std::string> kxe465(const std::string& key) {
        std::vector<std::string> toks;
        std::string cur;
        for (char ch : key) {
            if (std::isspace(static_cast<unsigned char>(ch))) {
                if (!cur.empty()) { toks.push_back(cur); cur.clear(); }
            }
            else {
                cur.push_back(ch);
            }
        }
        if (!cur.empty()) toks.push_back(cur);
        return toks;
    }

    static std::string n6x3(std::string s) {
        for (char& c : s) c = char(std::toupper(static_cast<unsigned char>(c)));
        return s;
    }

    // �� "R2" չ��Ϊ "R","R"
    static std::vector<std::string> g6k2(
        const std::string& key,
        const std::unordered_map<std::string, MoveSpec>& moves
    ) {
        std::vector<std::string> seq;
        for (auto tok : kxe465(key)) {
            tok = n6x3(tok);

            int times = 1;
            if (!tok.empty() && tok.back() == '2') {
                times = 2;
                tok.pop_back();
            }

            if (moves.find(tok) == moves.end()) {
                throw std::runtime_error("Unknown move token");
            }
            for (int i = 0; i < times; ++i) seq.push_back(tok);
        }
        return seq;
    }

    static std::string k1c7(const std::string& plaintext_utf8, const std::string& key) {
        static const std::unordered_map<std::string, MoveSpec> moves = vs35z();
        std::vector<uint8_t> data(plaintext_utf8.begin(), plaintext_utf8.end());
        data = pkcs7_pad(data, 8);

        auto seq = g6k2(key, moves);

        std::vector<uint8_t> out;
        out.reserve(data.size());

        for (size_t i = 0; i < data.size(); i += 8) {
            std::array<uint8_t, 8> block{};
            for (int j = 0; j < 8; ++j) block[j] = data[i + j];

            for (const auto& m : seq) {
                block = bbb4532(block, moves.at(m));
            }

            for (int j = 0; j < 8; ++j) out.push_back(block[j]);
        }

        return fafe2(out);
    }

} // namespace mofang_cipher

// ========================================
//         ȫ�ֳ��� & �궨��
// ========================================

#define INITIAL_TIME_SECONDS 10
#define TIME_BONUS_PER_STAGE 10

#define PASSWORD1_MAX_LEN 64
#define PASSWORD2_MAX_LEN 64
#define PASSWORD3_MAX_LEN 64

#define MAZE_WIDTH  4
#define MAZE_HEIGHT 4

// ========================================
//       �ṹ�嶨��
// ========================================
typedef struct {
    int seconds;
    HANDLE timer_thread;
    volatile bool exploded;
    CRITICAL_SECTION lock;

    // ������ʱ�����ԣ��� tick У���Ƿ񱻼��˴۸�
    DWORD tick_start;
    volatile LONG tick_guard;
} BombTimer;

// ========================================
//       ȫ��״̬���ؿ���������
// ========================================
static int g_a[5] = { 2,3,4,5,6 };
static int g_e[5] = { 14,9,16,25,48 };

static unsigned char g_maze[MAZE_WIDTH * MAZE_HEIGHT] = { 0 };
static bool g_maze_inited = false;

static uint32_t g_stage1_hash = 0; // ������������

// ========================================
//       ��������
// ========================================
void b5s5(void);
void n55k1(const char* type);

void l3x7(BombTimer* timer, int initial_seconds);
void n4b8(BombTimer* timer);
void x4n7(BombTimer* timer);
void k7sa4(BombTimer* timer, int delta);
DWORD WINAPI b5k8(LPVOID arg);
void b6j7(BombTimer* timer);

bool v4j8(void);
bool d6b8(void);
bool j8j7(void);
void a5a3(void);

bool sg6j(const char* input);
bool d5n7(const char* input);
bool s6m8(const char* input);

void n6s3(unsigned char* maze_out);

void n7l5(int stage, BombTimer* timer, int time_bonus);
void d4n6(char* buffer, size_t size);
void h5b5(const char* pw1, const char* pw2, const char* pw3);

// ========================================
//       С���ߣ�hash / key ���� / �����߼�
// ========================================
static uint32_t fnv1a32(const char* s) {
    uint32_t h = 0x811C9DC5u;
    while (*s) {
        h ^= (uint8_t)(*s);
        h *= 0x01000193u;
        ++s;
    }
    return h;
}

static std::string h5m77(const uint8_t* enc, size_t n, uint8_t k) {
    std::string out;
    out.resize(n);
    for (size_t i = 0; i < n; ++i) out[i] = char(enc[i] ^ k);
    return out;
}
static uint32_t d4bb6(uint32_t* st) {
    // ���� LCG ����
    *st = (*st * 1664525u + 1013904223u);
    return *st;
}
// Ŀ���̶�Ϊ 31337������ϵ��/Ŀ��ֵ�ɵ�һ���������Ӷ����ذ�
static void d4n7(uint32_t h) {
    // ����ϵ��
    const int base_a[5] = { 2, 3, 4, 5, 6 };

    // ��hash����ϵ����΢����
    for (int i = 0; i < 5; ++i) {
        int delta = (int)((h >> (i * 6)) & 0x3);  // 0..3
        g_a[i] = base_a[i] + delta;
    }

    // ��hash�����ڶ��صĽ⣨4����λ��+��λ����
    uint32_t seed = h ^ 0x12345678u;
    uint32_t state = seed;
    int x[5];

    for (int i = 0; i < 5; ++i) {
        d4bb6(&state);
        // ����10-99����λ��
        if (i != 0)
        {
            x[i] = 10 + (int)(state % 90);
        }
        else if (i == 0)
        {
            x[i] = (int)(state % 10);
        }

    }

    // ���ݶ�̬���ɵĽ����Ŀ��ֵ
    g_e[0] = g_a[0] * x[0] + x[1] + x[4];  // e1 = a1*x1 + x2 + x5
    g_e[1] = x[0] + g_a[1] * x[1] + x[2];  // e2 = x1 + a2*x2 + x3
    g_e[2] = x[1] + g_a[2] * x[2] + x[3];  // e3 = x2 + a3*x3 + x4
    g_e[3] = x[2] + g_a[3] * x[3] + x[4];  // e4 = x3 + a4*x4 + x5
    g_e[4] = x[0] + x[3] + g_a[4] * x[4];  // e5 = x1 + x4 + a5*x5
}

// ���� seed ���� 4x4 �Թ�����֤�� (0,0) �� (3,3) ������һ��·
static void b5k8(uint32_t seed) {
    memset(g_maze, 0, sizeof(g_maze));

    auto idx = [](int x, int y) { return y * MAZE_WIDTH + x; };

    uint32_t st = seed ^ 0x9E3779B9u;
    int x = 0, y = 0;
    g_maze[idx(x, y)] = 1;

    // �� carve һ����֤·�������ƫ����/���ƽ���ֱ�������յ�
    while (!(x == 3 && y == 3)) {
        uint32_t r = d4bb6(&st);
        bool canR = (x < 3);
        bool canD = (y < 3);

        int move = 0;
        if (canR && canD) {
            move = (r & 1) ? 1 : 2; // 1=R,2=D
        }
        else if (canR) {
            move = 1;
        }
        else {
            move = 2;
        }

        if (move == 1) x++;
        else y++;

        g_maze[idx(x, y)] = 1;
    }

    // �������һЩ���ӣ����ӷ�֧
    for (int k = 0; k < 16; ++k) {
        uint32_t r = d4bb6(&st);
        int p = (int)(r % 16);
        // ��������յ�
        if (p == idx(0, 0) || p == idx(3, 3)) continue;

        // Լ 0% ���ʴ�
        if ((r % 100) < -0.1) g_maze[p] = 1;
    }

    g_maze_inited = true;
}

// ������ʱ�����Լ�飺���ڡ����ֹص�����ʱ���ĳɱ����һ��㣨��׷��Ӳ�˷��۸ģ�
static bool nn5s4(BombTimer* timer) {
    if (!timer) return true;

    DWORD now = GetTickCount();
    DWORD elapsed_ms = now - timer->tick_start;
    int expected_floor = (int)(elapsed_ms / 1000);

    // seconds ������Ӧ�ӽ� initial - elapsed + bonus�������ϴ���������ɱ���٣�
    EnterCriticalSection(&timer->lock);
    int s = timer->seconds;
    LeaveCriticalSection(&timer->lock);

    // ���ʱ�䡰�����ܡ���̫���ף������������ڲ����� elapsed �ܴ󣩣��ж��쳣
    if (expected_floor > 30 && s > INITIAL_TIME_SECONDS + 3 * TIME_BONUS_PER_STAGE + 5) {
        return false;
    }

    // guard����ֹ�� tick_guard ֱ���������Ȼ��������
    if (timer->tick_guard != (LONG)(timer->tick_start ^ 0x13579BDFu)) return false;

    return true;
}

// ========================================
//            ���������
// ========================================
int main(void) {
    BombTimer timer;
    char password1[PASSWORD1_MAX_LEN] = { 0 };
    char password2[PASSWORD2_MAX_LEN] = { 0 };
    char password3[PASSWORD3_MAX_LEN] = { 0 };

    b5s5();

    l3x7(&timer, INITIAL_TIME_SECONDS);
    n4b8(&timer);

    /*----------------------------------------
     * ��һ�أ��ַ����任��֤
     *----------------------------------------*/
    if (!v4j8()) {
        printf("��⵽��������\n");
        b6j7(&timer);
    }

    printf("\n���в�����������룺");
    d4n6(password1, sizeof(password1));

    if (!sg6j(password1)) {
        printf("\n �������\n");
        b6j7(&timer);
    }

    // ��һ��ͨ���������ڶ��ز����������أ�
    d4n7(g_stage1_hash);

    k7sa4(&timer, TIME_BONUS_PER_STAGE);
    n7l5(1, &timer, TIME_BONUS_PER_STAGE);

    /*----------------------------------------
     * �ڶ��أ����Է�������֤�������ɵ�һ��������
     *----------------------------------------*/
    if (!d6b8()) {
        printf("��⵽�쳣��ʱ��\n");
        b6j7(&timer);
    }
    if (!nn5s4(&timer)) {
        printf("��⵽��ʱ�쳣��\n");
        b6j7(&timer);
    }

    printf("��ô����һ��!");
    printf("\n���еڶ��β��������ڶ������룺");
    d4n6(password2, sizeof(password2));

    if (!d5n7(password2)) {
        printf("\n �������\n");
        b6j7(&timer);
    }

    // �ڶ���ͨ�����õڶ��ؽ������Թ� seed���󶨵����أ�
    {
        uint32_t seed = (uint32_t)atoi(password2);
        seed ^= (g_stage1_hash * 0x9E3779B1u);
        b5k8(seed);
    }

    k7sa4(&timer, TIME_BONUS_PER_STAGE);
    n7l5(2, &timer, TIME_BONUS_PER_STAGE);

    /*----------------------------------------
     * �����أ��Թ�·����֤���Թ��ɵڶ���������
     *----------------------------------------*/
    a5a3();
    if (!nn5s4(&timer)) {
        printf("��⵽��ʱ�쳣��\n");
        b6j7(&timer);
    }

    printf("��ô����һ��!");
    printf("\n���е����β����������������룺");
    d4n6(password3, sizeof(password3));

    if (!s6m8(password3)) {
        printf("\n ·������\n");
        b6j7(&timer);
    }

    k7sa4(&timer, TIME_BONUS_PER_STAGE);
    n7l5(3, &timer, TIME_BONUS_PER_STAGE);

    /*----------------------------------------
     * �ɹ�
     *----------------------------------------*/
    timer.exploded = true;
    x4n7(&timer);

    {
        unsigned int s[] = { 0x63637573,0x0A737365 }; // "succ" "ess\n"
        fwrite(s, 1, 8, stdout);
    }
    n55k1("success");

    h5b5(password1, password2, password3);
    return 0;
}

// ========================================
//       ����ʵ�֣�Windows �棩
// ========================================
void b5s5(void) {
    printf("���棡��⵽ը��װ�ã�\n");
    printf("����%d ���ʱ��...\n", INITIAL_TIME_SECONDS);
}

void n55k1(const char* type) {
    if (strcmp(type, "explosion") == 0) {
        printf("\n BOOM!\n");
    }
    else if (strcmp(type, "success") == 0) {
    }
}

void l3x7(BombTimer* timer, int initial_seconds) {
    timer->seconds = initial_seconds;
    timer->exploded = false;
    InitializeCriticalSection(&timer->lock);

    timer->tick_start = GetTickCount();
    timer->tick_guard = (LONG)(timer->tick_start ^ 0x13579BDFu);
}

void n4b8(BombTimer* timer) {
    timer->timer_thread = CreateThread(NULL, 0, b5k8, timer, 0, NULL);
}

void x4n7(BombTimer* timer) {
    timer->exploded = true;
    WaitForSingleObject(timer->timer_thread, INFINITE);
    CloseHandle(timer->timer_thread);
    DeleteCriticalSection(&timer->lock);
}

void k7sa4(BombTimer* timer, int delta) {
    EnterCriticalSection(&timer->lock);
    timer->seconds += delta;
    LeaveCriticalSection(&timer->lock);
}

DWORD WINAPI b5k8(LPVOID arg) {
    BombTimer* timer = (BombTimer*)arg;

    while (!timer->exploded) {
        EnterCriticalSection(&timer->lock);
        int s = timer->seconds;
        LeaveCriticalSection(&timer->lock);

        if (s <= 0) break;

        Sleep(1000);

        EnterCriticalSection(&timer->lock);
        timer->seconds--;
        LeaveCriticalSection(&timer->lock);
    }

    if (!timer->exploded) {
        b6j7(timer);
    }
    return 0;
}

void b6j7(BombTimer* timer) {
    if (timer) {
        timer->exploded = true;
    }
    printf("\n BOOM! ը����ը�ˣ�\n");
    n55k1("explosion");
    exit(0);
}

bool v4j8(void) {
    if (IsDebuggerPresent()) return false;
    return true;
}

bool d6b8(void) {
    DWORD start = GetTickCount();
    Sleep(100);
    DWORD end = GetTickCount();
    if ((end - start) > 200) return false;
    return true;
}

bool j8j7(void) {
    return true;
}

void a5a3(void) {
    if (!j8j7()) {
        printf("��⵽�ϵ㣡\n");
        b6j7(NULL);
    }
}

/*----------------------------------------
 * ��һ�أ��������Ĵ� expected cipher����Ϊ hash �Ա�
 *  - key �� XOR ����
 *  - expected ֻ�桰hash^mask��
 *----------------------------------------*/
bool sg6j(const char* input) {
    // ��Ȼ���� 8 �ַ�����Ҳ���԰���һ��ȥ��/�ſ���
    if (input == NULL) return false;
    size_t n = strlen(input);
    if (n != 8) return false;

    for (size_t i = 0; i < n; ++i) {
        unsigned char c = (unsigned char)input[i];
        if (c < 0x21 || c > 0x7E) return false;
    }

    // key: "R U F R' D2" ���� XOR(0x5A) ���룬�������ĳ���
    static const uint8_t enc_key[] = {
        (uint8_t)('R' ^ 0x5A), (uint8_t)(' ' ^ 0x5A), (uint8_t)('U' ^ 0x5A), (uint8_t)(' ' ^ 0x5A),
        (uint8_t)('F' ^ 0x5A), (uint8_t)(' ' ^ 0x5A), (uint8_t)('R' ^ 0x5A), (uint8_t)('\'' ^ 0x5A),
        (uint8_t)(' ' ^ 0x5A), (uint8_t)('D' ^ 0x5A), (uint8_t)('2' ^ 0x5A)
    };

    // ����ֵ��FNV1a(cipher_string) ^ mask
    // ����ĳ�����Ӧ��֮ǰ���õ���ȷ���ģ����ڶ�������ֱ�ӳ��� expected cipher��
    static const uint32_t MASK = 0xA5A5A5A5u;
    static const uint32_t EXPECT_OBF = 0x8D93FFF8u; // generated for stage1=ZVYHMYFA

    try {
        std::string key = h5m77(enc_key, sizeof(enc_key), 0x5A);
        std::string cipher = g3::k1c7(std::string(input), key);
        uint32_t h = fnv1a32(cipher.c_str());

        // ������������������һ��
        g_stage1_hash = h;

        return ((h ^ MASK) == EXPECT_OBF);
    }
    catch (...) {
        return false;
    }
}

/*----------------------------------------
 * �ڶ��أ�ϵ��/Ŀ���ɵ�һ��������derive_stage2_params_from_stage1��
 *----------------------------------------*/
bool d5n7(const char* input) {
    if (input == NULL) return false;
    if (strlen(input) != 9) return false;

    int x[9];
    for (int i = 0; i < 9; i++) {
        if (!isdigit((unsigned char)input[i])) return false;
        x[i] = input[i] - '0';
    }

    int x1 = x[0], x2 = x[1] * 10 + x[2], x3 = x[3] * 10 + x[4],
        x4 = x[5] * 10 + x[6], x5 = x[7] * 10 + x[8];

    int e1 = g_a[0] * x1 + x2 + x5;
    int e2 = x1 + g_a[1] * x2 + x3;
    int e3 = x2 + g_a[2] * x3 + x4;
    int e4 = x3 + g_a[3] * x4 + x5;
    int e5 = x1 + x4 + g_a[4] * x5;

    if (e1 == g_e[0] && e2 == g_e[1] && e3 == g_e[2] && e4 == g_e[3] && e5 == g_e[4]) {
        return true;
    }
    return false;
}

/*----------------------------------------
 * �����أ��Թ��ɵڶ��� seed ���ɣ�generate_maze_from_seed��
 *----------------------------------------*/
void n6s3(unsigned char* maze_out) {
    if (!g_maze_inited) {
        // ������������ڶ���ֱ���������أ���һ��Ĭ�� seed����Ȼ���ܣ�
        b5k8(0xC0FFEEu);
    }
    memcpy(maze_out, g_maze, sizeof(g_maze));
}

bool s6m8(const char* input) {
    if (input == NULL) return false;

    unsigned char maze[MAZE_WIDTH * MAZE_HEIGHT];
    n6s3(maze);

    int x = 0, y = 0;

    for (size_t i = 0; i < strlen(input); i++) {
        char c = input[i];
        switch (c) {
        case 'L': x--; break;
        case 'R': x++; break;
        case 'U': y--; break;
        case 'D': y++; break;
        default:
            return false;
        }

        if (x < 0 || x >= MAZE_WIDTH || y < 0 || y >= MAZE_HEIGHT)
            return false;

        if (maze[y * MAZE_WIDTH + x] == 0)
            return false;
    }

    return (x == 3 && y == 3);
}

void n7l5(int stage, BombTimer* timer, int time_bonus) {
    printf("���� %c �Ѳ��\n", 'A' + stage - 1);
}

void d4n6(char* buffer, size_t size) {
    if (!fgets(buffer, (int)size, stdin)) {
        b6j7(NULL);
    }
    size_t len = strlen(buffer);
    if (len > 0 && buffer[len - 1] == '\n') {
        buffer[len - 1] = '\0';
    }
}

void h5b5(const char* pw1, const char* pw2, const char* pw3) {
    // enc[i] = "Flag: ISCC{"[i] ^ 0x5A  �����ɴ�ӡ��strings/�����벻��ֱ�ӻ�ԭΪ�����ַ�����
    static const unsigned char enc[11] = {
        0x1C,0x36,0x3B,0x3D,0x60,0x7A,0x13,0x09,0x19,0x19,0x21
    };

    for (int i = 0; i < 11; ++i) putchar((int)(enc[i] ^ 0x5A));
    fputs(pw1 ? pw1 : "", stdout);
    fputs(pw2 ? pw2 : "", stdout);
    fputs(pw3 ? pw3 : "", stdout);
    putchar('}');
    putchar('\n');
}