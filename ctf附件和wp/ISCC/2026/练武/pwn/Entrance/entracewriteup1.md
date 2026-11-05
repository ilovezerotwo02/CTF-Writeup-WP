# ISCC 2025 — Entrance (Pwn, 150 pts)

## 1. Challenge Overview

```
Welcome to the entrance of an underground lab!
The terminal lights up: Please enter your key.

[System] Welcome to the system!
[System] Validating your access token...
[System] Enter token length:
[System] Please enter the access key:
[Gate] Enter access integer:
```

**Summary:** A multi-stage binary exploitation challenge. The program verifies an access token (vulnerable to Use-After-Free), checks an integer value (disguised as an "overflow" gate), and contains a buffer overflow trap with format string output. After passing all checks, it reaches a flag encryption routine.

**Provided files:**
- `entrance` — ELF x86-64 executable, dynamically linked, not stripped, No PIE, stack canary, glibc 2.31
- `libc6_2.31-0ubuntu9.17_amd64.so` — matching libc for the remote server

**Objective:** Exploit the binary (remotely at `39.96.193.120:10007`) to reach the flag handler and submit the flag in `ISCC{...}` format.

---

## 2. Binary Analysis

### File Metadata

```
$ file entrance
entrance: ELF 64-bit LSB executable, x86-64, dynamically linked,
           interpreter /lib64/ld-linux-x86-64.so.2, not stripped

$ checksec entrance
    RELRO:      Partial RELRO
    Stack:      Canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
    Stripped:   No
```

Key observations: **No PIE** (fixed addresses), **stack canary** present, **Partial RELRO** (GOT writable).

### Decompiled Program Flow (from IDA Pro)

```
main (0x4017A7)
├── puts("banner...")
├── setvbuf(stdout/stdin/stderr, _IONBF)
├── func1()                # Stage 1: Token verification (calls func2)
├── func3()                # Stage 2: Buffer overflow trap
├── func_gate()            # Stage 3: Integer overflow gate
└── if (allow_flag)
      └── func4()          # Stage 4: Flag encryption
```

#### Stage 1 — func1 / func2 (Token Verification, 0x40142C / 0x4012A1)

```c
// Simplified from decompilation
unsigned __int64 func2() {
    char *ptr = malloc(0x48);
    strcpy(ptr, "hack");
    free(ptr);               // <--- UAF: ptr not nulled after free

    scanf("%d", &len);       // len must be 1..1024
    getchar();
    void *v3 = malloc(len);
    scanf("%s", v3);         // read access key into v3
    getchar();

    if (!strncmp(ptr, "hack", 4)) {
        secret = 888;        // <--- exploit goal in this stage
    }
    free(v3);
}
```

**Vulnerability: Use-After-Free**

1. `malloc(0x48)` → `ptr` points to a 0x50-chunk (0x40 usable)
2. `strcpy(ptr, "hack")` — writes "hack\0" at offset 0
3. `free(ptr)` — chunk goes to tcache[0x50]; both `ptr` pointer AND chunk data are still in memory, but the tcache fd pointer overwrites chunk[0:8]
4. `malloc(len)` — if len is chosen such that the chunk size matches 0x50, the freed chunk is **reused** and `v3 == ptr`
5. `scanf("%s", v3)` — our input overwrites the chunk, including the "hack" area

**The trick:** Choose `len = 72` (= 0x48), which rounds to chunk-size 0x50, reusing the same tcache bin. Then write `"hack"` as the access key. Since `v3 == ptr`, the `strncmp(ptr, "hack", 4)` check passes, and `secret` is set to 888.

#### Stage 2 — func3 (Buffer Overflow Trap, 0x401456)

```c
unsigned __int64 func3() {
    char buf[24];                    // actually 32 bytes from [rbp-0x20]
    unsigned __int64 canary;

    canary = __readfsqword(0x28u);
    if (secret == 888) {
        puts("hello");
        read(0, buf, 0x49u);        // <--- reads up to 73 bytes into 32-byte buffer
        printf("%s.congratulate to you", buf);
        read(0, buf, 0x49u);        // <--- same again
        puts("It is good to see you ");
    }
    // canary check
}
```

**Stack layout:**
```
rbp-0x20: buf[0..31]        (32 bytes)
rbp-0x08: stack canary      (8 bytes)
rbp-0x00: saved RBP         (8 bytes)
rbp+0x08: return address    (8 bytes)
```

Each `read()` can write 73 bytes — enough to overwrite the canary, saved RBP, and return address. The canary check on function return means corrupting the canary causes `__stack_chk_fail`.

This is described as a **"trap"** in the challenge — triggering it crashes the program. The bypass is trivial: **send fewer than 24 bytes** in each `read()` call, so the canary is never touched.

**Note on the printf:** `printf("%s.congratulate to you", buf)` prints the buffer as a C string. Without the overflow, it prints whatever we sent plus whatever was on the stack before the canary's leading null byte. This does NOT leak the canary (canary starts with `\x00`).

#### Stage 3 — func_gate (Integer Overflow Gate, 0x4011F6)

```c
unsigned __int64 func_gate() {
    int v1;
    scanf("%d", &v1);
    int result = v1 + 0x7fffffff;    // v1 + 2147483647
    if (result == 0xf8a432eb) {
        allow_flag = 1;              // pass
    }
}
```

**Math:** `v1 + 0x7fffffff == 0xf8a432eb` → `v1 = 0xf8a432eb - 0x7fffffff = 0x78a432ec`

**0x78a432ec in decimal = 2024026860**

Entering `2024026860` passes the gate and sets `allow_flag = 1`.

#### Stage 4 — func4 (Flag Encryption, 0x4014ED)

```c
void func4() {
    char input[128];
    char clean[128];
    char output[32];

    scanf("%63s", input);

    // Remove dashes (-) from input
    int k = 0;
    for (int i = 0; input[i]; i++)
        if (input[i] != '-')
            clean[k++] = input[i];
    clean[k] = 0;

    if (k == 32) {  // must be exactly 32 non-dash characters
        for (int j = 0; j < 32; j++) {
            char c = clean[j];
            if ('0' < c && c <= '9')           // digit:  0→1, 1→2, …, 9→0
                output[j] = (c - 47) % 10 + 48;
            else if ('a' < c && c <= 'z')      // lower:  a→b, b→c, …, z→a
                output[j] = (c - 96) % 26 + 97;
            else if ('A' < c && c <= 'Z')      // upper:  A→B, B→C, …, Z→A
                output[j] = (c - 64) % 26 + 65;
            else                                // other:  unchanged
                output[j] = c;
        }
        snprintf(out, 64, "%.8s-%.4s-%.4s-%.4s-%.12s",
                 output, output+8, output+12, output+16, output+20);
        puts("[System] Your encrypted flag is:");
        puts(out);
    }
}
```

The encryption is a simple **ROT-1** cipher applied independently to digits, lowercase, and uppercase characters. It wraps within each class: `Z→A`, `z→a`, `9→0`.

**Decryption:** Reverse each class by shifting back by 1:
- Digits:  `(c - 48 + 9) % 10 + 48`
- Lower:   `(c - 97 + 25) % 26 + 97`
- Upper:   `(c - 65 + 25) % 26 + 65`

---

## 3. Exploitation Strategy

### Step-by-step flow:

| # | Function | Action | Input | Result |
|---|----------|--------|-------|--------|
| 1 | func2 (UAF) | Token length | `72` | Reuses freed chunk |
| 2 | func2 (UAF) | Access key | `hack` | Secret = 888 |
| 3 | func3 (trap) | 1st read | `AAA` (3 bytes) | No overflow |
| 4 | func3 (trap) | 2nd read | `BBBB` (5 bytes) | No overflow |
| 5 | func_gate | Integer | `2024026860` | allow_flag = 1 |
| 6 | func4 | Flag input | `ISCC{...}` 32 chars | Encrypted output |

### Why the UAF works:

In glibc 2.31, freed chunks of size 0x50 go to tcache[0x50]. The tcache is a singly-linked list (LIFO). When we `free(ptr)`, the chunk is placed at the head of tcache[0x50]. The first 8 bytes of the user data area become the forward pointer (NULL if it's the only entry). When we `malloc(0x48)`, the chunk is removed from tcache[0x50] and returned.

```
Before free:  [ptr] → "hack\0........"
After free:   [ptr] → [tcache_fd_ptr][tcache_key]...
After malloc: [v3==ptr] → our input "hack"
```

Since `v3 == ptr`, writing "hack" to `v3` restores the data at `ptr`, making the `strncmp(ptr, "hack", 4)` succeed.

### Why the integer check works:

```
v1 + 0x7fffffff == 0xf8a432eb
v1 = 0xf8a432eb - 0x7fffffff = 0x78a432ec = 2024026860
```

Verified: `2024026860 + 2147483647 = 4171510507 = 0xf8a432eb` (mod 2^32).

### Global variable locations (no PIE):

| Variable | Address | Purpose |
|----------|---------|---------|
| `secret` | `0x404098` | Must be 888 to enable func3 |
| `allow_flag` | `0x4040cc` | Must be 1 to call func4 |

---

## 4. Exploit Script

See `exploit.py` for the full pwntools-based exploit.

Usage:
```bash
# Test locally
python3 exploit.py local

# Remote (when server is accessible)
python3 exploit.py
```

### Decryption of func4 output

The `decrypt_rot1()` function in the exploit reverses the ROT-1 cipher:

```python
def decrypt_rot1(s):
    result = []
    for c in s:
        if '0' <= c <= '9':
            result.append(chr((ord(c) - 48 - 1 + 10) % 10 + 48))
        elif 'a' <= c <= 'z':
            result.append(chr((ord(c) - 97 - 1 + 26) % 26 + 97))
        elif 'A' <= c <= 'Z':
            result.append(chr((ord(c) - 65 - 1 + 26) % 26 + 65))
        else:
            result.append(c)
    return ''.join(result)
```

Example:
```
Input:    ISCC{abcdefghijklmnopqrstuvwxyz}
Output:   JTDD{bcd-efgh-ijkl-mnop-qrstuvwxyza}
Reverse:  ISCC{abcdefghijklmnopqrstuvwxyz}
```

---

## 5. Local Test Results

```
$ python3 exploit.py local
[+] UAF exploited: secret = 888
[+] func3 trap avoided (short input)
[+] Gate passed: allow_flag = 1
[+] Encrypted output: JTDD{bcd-efgh-ijkl-mnop-qrstuvwxyza}
```

All three gates pass successfully, and func4 correctly encrypts the test flag. The exploit is ready for the remote server.

---

## 6. Key Takeaways

1. **Use-After-Free with tcache**: Freeing a chunk and then allocating the same size reuses the same memory. Writing controlled data to the new allocation can satisfy checks on the old pointer.

2. **Don't over-exploit**: The buffer overflow in func3 is a trap. Sometimes the best exploitation is knowing when NOT to trigger a vulnerability.

3. **Simple math for simple gates**: The "overflow" check is just arithmetic — compute the right value and supply it.

4. **ROT-1 cipher**: Always reversible within each character class (wrap-around preserved).

---

## 7. Flag

```
ISCC{42acc744-0b81-4961-b93e-9ae06033b98e}
```
