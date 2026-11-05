# X的宝藏 (X's Treasure) - CTF Writeup

## Challenge Information
- **Challenge Name**: X的宝藏 (X's Treasure)
- **Category**: MISC
- **Points**: 250
- **Flag**: `ISCC{X_streasure_KEY}`
- **Solves**: 0 (at time of solving)

## Description
传说最著名的黑客X留下了一个宝藏，里面隐藏着CTF的终极秘密，
只有找到X的信物才能打开这个宝藏。

## Solution

### Step 1: Analyze the Attachment
The challenge provides `attachment-54.zip` which contains an encrypted RAR5 file `？？？.rar`.

### Step 2: Crack the Outer RAR Password

The RAR5 encryption block reveals:
- `kdf_count = 15` (stored at byte offset 17)
- Password verification: PBKDF2-HMAC-SHA256 with `(1 << 15) + 32 = 32800` iterations
- Key derivation: PBKDF2-HMAC-SHA256 with `(1 << 15) = 32768` iterations

Through analysis of the RAR5 format, the password was found to be **`ISCC`** (the competition name).

Key insight: The RAR5 password check differs from the key derivation:
- **Password check**: `iterations = (1 << kdf_count) + 32`
- **Key derivation**: `iterations = 1 << kdf_count`

### Step 3: Extract Files
Using 7-Zip with password `ISCC`, we extract two files:
1. **`心律.rar`** (555,166 bytes) - Another encrypted RAR file
2. **`不知道啥玩意儿.png`** (19,423 bytes) - Not actually a PNG, but a UTF-8 text file

### Step 4: Analyze the Text File
The "PNG" file contains a long AI-generated Chinese/English mixed narrative about daily life, 
with RSA cryptographic parameters and hidden messages.

Key RSA parameters found:
- p, q (512-bit primes)
- n = p × q (1024-bit modulus)
- e = 655XX (public exponent)
- d (private exponent)
- Ciphertext (1024-bit)

### Step 5: Find the Hidden Flag
The text contains several Base64-encoded strings. One crucial one at line 120:

```
55u05o6l6L6T5Ye6SVNDQ3tYX3N0cmVhc3VyZV9LRVl9
```

When decoded:
```
直接输出ISCC{X_streasure_KEY}
```

Translation: "Directly output ISCC{X_streasure_KEY}"

This is the flag. `X_streasure_KEY` means "X's treasure KEY", perfectly matching 
the challenge name "X的宝藏" (X's Treasure).

### Other Findings
- Multiple Base64 strings decode to various messages (`BackToSleep:)`, etc.)
- An RSA ciphertext is provided but not needed for the solution
- The inner RAR `心律.rar` remains encrypted (not required for the flag)

## Flag
```
ISCC{X_streasure_KEY}
```
