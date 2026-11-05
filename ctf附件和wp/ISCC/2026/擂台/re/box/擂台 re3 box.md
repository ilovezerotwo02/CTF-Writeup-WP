# sixSixSix 题解 WP

## 题目信息

- 题型：Reverse / Crypto 交叉
- 附件：[Box.bin](E:\CTFstudy\这是ISCC区域赛\擂台赛\RE\RE3\Box.bin)
- 解题脚本：[solve_sixsixsix.py](E:\CTFstudy\这是ISCC区域赛\擂台赛\RE\RE3\solve_sixsixsix.py)
- 最终 flag：`flag{92cd335ab10f78e4296cd58a11f04b9e}`

---

## 一、题目初看

拿到附件后，第一步先看文件类型和大小。

`Box.bin` 并不是常规可执行文件，而是一个纯数据文件。它的大小为：

```text
48016 bytes
```

观察这个数字可以发现：

```text
48016 = 3001 * 16
```

这非常可疑，因为 `16` 字节正好对应 AES 的一个分组大小。所以第一反应就是：

1. 文件可能由很多个 `16` 字节块组成。
2. 每个块可能都是某种密文输出。
3. 题目很可能和分组密码、故障注入或者差分分析有关。

因此先把整个文件按 `16` 字节切块：

```python
blocks = [data[i:i+16] for i in range(0, len(data), 16)]
```

切完之后一共有：

```text
3001 blocks
```

记第一个块为正确密文：

```python
C0 = blocks[0]
```

实测第一个块为：

```text
23d9a3b3456525a3f8f6f795d7ed1271
```

---

## 二、为什么想到 AES DFA

接下来，将其它 `3000` 个块分别和第一个块比较，统计每个块和 `C0` 的不同字节位置。

如果这是普通随机数据，那么差异通常会很多；但这题里可以找到一批很特别的块：

- 它们和 `C0` 的差异恰好只有 `4` 个字节；
- 并且这 4 个字节的位置落在 AES 状态矩阵某一列经过最后一轮 `ShiftRows` 后对应的位置上。

筛选后得到的有效 fault 分组如下：

```text
column 0: [5, 90, 275, 560]
column 1: [44, 65, 230, 495]
column 2: [27, 152, 189, 434]
column 3: [14, 119, 324, 377]
```

这正是 **AES 差分故障分析（Differential Fault Analysis, DFA）** 的经典特征。

### 原理直观解释

如果在 AES 倒数第二轮附近，对某一列注入一个单字节故障，那么：

1. 故障先经过 `MixColumns` 扩散到整列 4 个字节；
2. 再经过最后一轮 `ShiftRows` 重新打乱位置；
3. 最终在密文中表现为恰好 4 个字节变化。

也就是说：

- “只差 4 字节”
- “4 字节位置符合 AES 列结构”

这两个现象几乎就可以直接判断这题是 **AES DFA**。

---

## 三、AES 最后一轮关系

对于 AES 最后一轮，有如下关系：

```text
C[i] = Sbox(state[i]) ^ K10[i]
```

其中：

- `C[i]` 是最终密文的第 `i` 个字节；
- `state[i]` 是最后一轮 SubBytes 之前的状态字节；
- `K10[i]` 是最后一轮轮密钥对应字节。

对于正确密文 `C` 和故障密文 `Cf`，如果枚举某个最后一轮 key byte `k`，就可以反推：

```text
InvSbox(C[i]  ^ k)
InvSbox(Cf[i] ^ k)
```

两者异或后的差值为：

```python
delta = InvSbox(C[i] ^ k) ^ InvSbox(Cf[i] ^ k)
```

如果这个 `k` 是正确的，那么该列的 4 个 `delta` 会满足单字节故障经过 `MixColumns` 后的扩散模式。

---

## 四、故障模式如何构造

单字节故障在某一列进入 `MixColumns` 后，输出差分一定满足以下 4 类模式之一：

```text
(2e, e,  e,  3e)
(3e, 2e, e,  e )
(e,  3e, 2e, e )
(e,  e,  3e, 2e)
```

其中 `e` 为 `GF(2^8)` 中的任意非零字节。

因此，我们可以枚举：

1. 所有 `e in [1,255]`
2. 上面 4 种模式

从而得到所有合法的故障差分模板。

脚本里的实现是：

```python
for e in range(1, 256):
    patterns.extend([
        (gmul(2, e), e, e, gmul(3, e)),
        (gmul(3, e), gmul(2, e), e, e),
        (e, gmul(3, e), gmul(2, e), e),
        (e, e, gmul(3, e), gmul(2, e)),
    ])
```

---

## 五、如何恢复 round10 key

### 1. 建立单字节候选映射

对于正确密文和故障密文的某个字节位置，枚举 `k`：

```python
for k in range(256):
    delta = InvSbox[c ^ k] ^ InvSbox[f ^ k]
```

把“某个 delta 对应哪些可能的 k”记录下来。

这样，某一列的 4 个字节就分别有 4 张映射表。

### 2. 套合法故障模式

对于同一列的一个 fault 样本：

1. 遍历所有合法模式 `(d0, d1, d2, d3)`；
2. 分别检查 4 个位置上是否有对应候选 key；
3. 如果四个位置都存在候选，则把笛卡尔积加入候选集合。

### 3. 多组 fault 取交集

单组 fault 往往还会留下多个候选；但同一列有多组 fault 时，可以把候选集合不断取交集。

最终每一列只会剩下唯一一组 4 字节 key。

四列全部恢复后，拼出完整的最后一轮轮密钥：

```text
round10 key = 4fd5879336564c0df9e84e812bf94bb8
```

---

## 六、由 round10 key 逆推出主密钥

AES-128 一共有 11 轮轮密钥（`K0 ~ K10`），题目里我们恢复出来的是最后一轮轮密钥 `K10`。

由于 AES key schedule 是可逆的，所以可以从 `K10` 一路逆推回 `K0`，也就是主密钥。

逆推后得到：

```text
master key = 92cd335ab10f78e4296cd58a11f04b9e
```

脚本中通过 `invert_round10_key()` 完成这一过程。

---

## 七、结果验证

恢复出主密钥后，最好不要直接交 flag，而是先做一次验证。

将第一个正确密文 `C0` 用恢复出的主密钥做 AES-128 解密：

```text
C0 = 23d9a3b3456525a3f8f6f795d7ed1271
AES-128-ECB.decrypt(C0) = 11111111111111111111111111111111
```

解密结果是 16 字节的 `0x11`，说明恢复出的密钥完全正确。

因此可以确定最终答案为：

```text
flag{92cd335ab10f78e4296cd58a11f04b9e}
```

---

## 八、完整解题流程总结

1. 观察 `Box.bin` 大小为 `48016 = 3001 * 16`，怀疑是 AES 分组数据。
2. 将文件按 `16` 字节切块，取第一块作为正确密文。
3. 将其它块和第一块逐个比较，筛出只差 `4` 个字节的 fault 块。
4. 发现这些差异位置符合 AES 某一列经过 `ShiftRows` 后的分布规律，判断为 AES DFA。
5. 枚举最后一轮 key byte，利用 `InvSbox` 差分构造候选。
6. 用单字节故障经过 `MixColumns` 的合法模式筛选候选。
7. 多组 fault 取交集，恢复 16 字节的 round10 key。
8. 逆 AES key schedule 得到 master key。
9. 解密正确密文验证，确认结果无误。
10. 提交 `flag{master_key}`。

---

## 九、脚本运行方式

题目目录下直接运行：

```bash
python solve_sixsixsix.py Box.bin
```

如果当前目录不是题目目录，也可以指定绝对路径：

```bash
python solve_sixsixsix.py E:\\CTFstudy\\这是ISCC区域赛\\擂台赛\\RE\\RE3\\Box.bin
```

运行输出：

```text
[+] blocks: 3001
[+] correct ciphertext: 23d9a3b3456525a3f8f6f795d7ed1271
[+] useful single-byte fault groups:
    column 0: [5, 90, 275, 560]
    column 1: [44, 65, 230, 495]
    column 2: [27, 152, 189, 434]
    column 3: [14, 119, 324, 377]
[+] round10 key: 4fd5879336564c0df9e84e812bf94bb8
[+] master key: 92cd335ab10f78e4296cd58a11f04b9e
[+] decrypt(correct): 11111111111111111111111111111111
[+] flag: flag{92cd335ab10f78e4296cd58a11f04b9e}
```

---

## 十、最终答案

```text
flag{92cd335ab10f78e4296cd58a11f04b9e}
```
