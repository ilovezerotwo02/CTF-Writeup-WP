# ECB Pattern Leakage

## 题目信息

- 题目名：`ECB Pattern Leakage`
- 分类：`CRYPTO`
- 附件：`otp_10.zip`
- 解压后文件：`ciphertext.bin`

## 一、附件检查

先解压附件：

```powershell
Expand-Archive -LiteralPath .\otp_10.zip -DestinationPath .\otp_10_unzipped -Force
```

解压结果只有一个文件：

```text
ciphertext.bin
```

文件大小为 `80` 字节，正好等于 `5` 个 `16` 字节分组：

```text
00: 97c266c5b1c929e1ac07ccf592599dd8
01: b577f3f777783d3b8f6ab17acd3f78c9
02: 6b2afc84559d6443c042f6225b6dcb7d
03: 56a4c94a9d532bf7d045f14b00990253
04: 84163f757a2ab28337aefa7aeb72e087
```

另外，Windows 的 `Zone.Identifier` 还能看出下载来源路径里带有：

```text
2026-线上-网络安全/4.密码/6.ECB Pattern Leakage/附件
```

这说明文件本身确实来自名为 `ECB Pattern Leakage` 的课程附件目录，不是本地重命名导致的误判。

## 二、ECB 泄露原理

ECB 的性质是：

```text
相同的明文分组 + 相同的密钥 -> 相同的密文分组
```

所以 ECB 的“pattern leakage（图样泄露）”只能泄露一类信息：

- 哪些分组相同
- 哪些位置出现重复模式

但它**不会**在没有其他条件时直接给出明文内容。

要靠 ECB 泄露真正恢复明文，通常还需要至少一个额外条件，例如：

- 已知密钥
- 可访问加密 oracle，能自己构造 codebook
- 有多份使用同一密钥的相关密文
- 明文分组大量重复，且重复内容本身可推断
- 已知部分明文并可做分组对照

## 三、这份附件为什么不能直接出 flag

对 `ciphertext.bin` 按 16 字节切块后，可以发现：

- 一共只有 `5` 个分组
- **没有任何重复分组**

这意味着：

1. 虽然题目名提示了 `ECB`，但本附件里**没有产生可利用的分组重复图样**。
2. 附件中也**没有给出密钥**。
3. 也**没有给出加密服务 / 额外明文样本 / 同 key 的其他密文 / codebook**。
4. 因此，无法仅靠 “ECB pattern leakage” 这一条信息唯一恢复明文。

换句话说，这里最多只能判断：

- 这段数据“看起来像一个 16 字节分组密码模式的密文”
- 但**不能从现有附件唯一解出原始 flag**

## 四、补充验证

本地还做了两类 sanity check：

- 检查压缩包元数据：压缩包内只有 `ciphertext.bin`，没有隐藏提示、注释或额外文件
- 试探少量常见教学样例 key：未出现可读明文，也没有 `flag{...}` 特征

后续又补做了更强的一轮验证：

- 全量检查分组：`5` 个分组全部不同，不存在 ECB 典型重复块
- 爆破低熵 AES key：
  - `1` 字节重复到 `16` 字节：无结果
  - `2` 字节重复到 `16` 字节：无结果
  - `3` 字节字符集重复到 `16` 字节：无结果
  - `a-z0-9_` 长度 `1..4` 的短口令，按 `MD5(password)` 作为 AES key：无结果
  - `a-z0-9_` 长度 `1..4` 的短口令，按 `password + 0x00 padding` 作为 AES key：无结果
- 测试常见变体：
  - AES-ECB / AES-CBC / AES-CTR 常见候选 key：无结果
  - DES / 3DES / Blowfish 常见候选 key：无结果
  - 重复密钥 XOR、题名/文件名派生 key、块重排：无结果

## 五、平台缓存取证

除了附件本身，还从浏览器缓存里恢复到了比赛平台返回过的正式题目 JSON。  
其中与本题直接相关的缓存信息包括：

- `containerName`: `ECB Pattern Leakage`
- `containerId`: `2059185498527375362`
- `relevancyId`: `2060340341732335619`
- `competitionId`: `2060338396472860673`
- `containerDifficulty`: `2`
- `classifyName`: `CRYPTO`
- `containerGrade`: `300`
- `containerContent`: `对每个附件进行解密，并输出原始flag。`
- `attachmentName`: `otp_10.zip`
- `attachmentId`: `2059185409167728641`
- `alternateLink`: 百度网盘分享链接 `https://pan.baidu.com/s/17GxSdqSOJ-WQzWzuIrRkNg?pwd=81mk`

更关键的是，平台缓存里的同一条记录还明确显示：

- `containerAnswer`: `""`
- `writeUpContent`: `""`
- `submitResult`: `null`
- `resultId`: `null`

同时，百度网盘分享页缓存返回的数据也显示：

- 该分享目录标题为 `2026-线上-网络安全/4.密码/6.ECB Pattern Leakage/附件/otp_10.zip`
- 分享中只有一个文件 `otp_10.zip`

这说明：

1. 平台前端拿到的正式题面与当前本地题面一致，没有额外隐藏说明。
2. 平台缓存证据也只指向这一份附件，没有第二个配套文件。
3. 浏览器侧没有出现任何可直接恢复 flag 的补充明文条件。

这类弱口令试探不能证明“绝对无解”，但能排除一部分明显的出题失误。

## 六、结论

### 结论 1：按当前附件，**不能严谨地推出唯一 flag**

现有材料不足以支持“解密并输出原始 flag”这个要求。  
如果强行给出 flag，只能是猜测，不是可复现解法。

### 结论 2：题目逻辑大概率不完整，或题面/附件存在缺失

如果出题人本意真的是考 `ECB Pattern Leakage`，那通常应该提供以下至少一种：

- 含有明显重复块的密文
- 一张被 ECB 加密后的位图/图像
- 同 key 下的多份密文
- 一个可查询的 ECB 加密接口
- 明文模板或已知块字典

## 七、如果要把题目改成可解，建议这样补

可任选一种：

1. 直接提供密钥，让选手做标准 ECB 解密。
2. 提供一个 ECB 加密 oracle，让选手通过字节探测恢复 flag。
3. 提供多份同 key 密文，并让部分明文块可识别，从而建立映射。
4. 把明文改成有大量重复块的结构化数据，例如位图或固定模板文本。

## 八、最终回答

- 现有附件：**不足以唯一恢复 flag**
- 现有逻辑：**不完整，不满足“仅凭附件解密出 flag”的条件**
- 因此本题在当前材料下：**不能稳定、可复现地从附件直接出 flag**
