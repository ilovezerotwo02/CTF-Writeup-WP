# 结界中的契约 — Writeup

**分类** Reverse / 1000 分 / StaticAttachment
**flag**：`HTUCTF｛S1gn a contract w1th qb!｝`（注意是**全角**括号 `｛｝` U+FF5B/U+FF5D）

---

## 1. 程序结构

MinGW-w64 x64 PE，自定义节：

| 节 | 作用 |
|---|---|
| `.verify` | 3 个哈希函数（可执行）：`VERIFY_A`、splitmix 变体、`CONTRACT` |
| `.vmeta` | 魔数 `RMV1` + CRC32 + `EDOC_CRC`（`CRC_CODE` 反序） |
| `.rdata` | 加密密钥材料 `e4d5bb85...`（16 字节）+ 36 字节密文 + 8 条 decoy 密文 |

## 2. 反调试 / 完整性

- `CheckRemoteDebuggerPresent` / `IsDebuggerPresent` / `NtQueryInformationProcess` / PEB `gs:[0x60]`
- 遍历 PE 节表找 `.verify`，校验 `IMAGE_SCN_MEM_EXECUTE|READ`（`0x60000000`）
- 运行时间差阈值 `0x3d090`（250000µs）：过快视为被 patch
- 签名校验：FNV-1a 64（`offset=0xcbf29ce484222325`，`prime=0x100000001b3`）== `0x8e39c98107229425`
- 回执：`%016llX` 16 位十六进制，与 mix 输出比对

任何不符 → 走 decoy（全角括号假 flag）或「真相已封存…」提示。

## 3. 密钥材料

`.rdata` 16 字节用滚动 XOR 解出：

```
key[i] = enc[i] XOR (0xffffffa7 + 0x13*i)   # 首字节用常量 0xffffffe4
→ b"CovenantKey_2026"
```

`hash(ecx)`（0x401590）：

```
h_base = rol(q1,17) ^ q0 ^ 0xd6e8feb86659fd93
       = 0xc2e22124c9b9feb4
rax = ecx * 0xa24baed4963ee407 + (h_base + GOLDEN)
return splitmix_final(rax)
```

`hash(0) = 0xaf29685c48b140a6`。

## 4. 流密码（0x401660）

```
r10 = splitmix_final(hash(0) ^ sig ^ receipt ^ g427010 ^ 0xa11ce5eed00d5eed + GOLDEN) + GOLDEN
for i in range(len):
    z = splitmix_final((i//8)*GOLDEN + r10)
    pt[i] = ct[i] ^ (z >> ((i%8)*8))
```

splitmix64-finalizer 可逆（xor-shift 逆 + 模逆乘法），因此已知明文可直接恢复 `r10`。

## 5. 已知明文攻击

8 条 decoy（case 0–7）解出后确认明文形态为 `HTUCTF｛...｝`（全角括号）。
真 flag 同样全角：前缀 `HTUCTF｛` 共 9 字节，覆盖整个第一块（8 字节）→

```
z0 = int.from_bytes(ct[0:8] ^ b"HTUCTF｛"[:8], "little")
r10 = inv_splitmix(z0)
```

一次恢复，无需爆破。解密 36 字节得：

```
HTUCTF｛S1gn a contract w1th qb!｝
```

与题面「与 qb 签订契约」「円環の理（小圆/Madoka）」主题吻合。

## 6. Decoy 一览（供对照）

| case | 明文 |
|---|---|
| 0 | `HTUCTF｛SAMIA DOSTA｝` |
| 1 | `HTUCTF｛ARI ADITIDA｝` |
| 2 | `HTUCTF｛TORI ADITO MADORA｝` |
| 3 | `HTUCTF｛ESTIA MORITA NARI AMITIA｝` |
| 4 | `HTUCTF｛SORI ARITO ASORA｝` |
| 5 | `HTUCTF｛SEMARI AISI ISOLA MATOLA｝` |
| 6 | `HTUCTF｛SORIBIA DOLCE IRORA AMITA｝` |
| 7 | `HTUCTF｛SAMARIA DOSE HIA MIO LORA FIA SIA ADORA｝` |

## 7. 复现

```bash
python solve_contract.py
# HTUCTF｛S1gn a contract w1th qb!｝
```
