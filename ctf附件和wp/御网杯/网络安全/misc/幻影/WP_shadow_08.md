# 幻影（shadow_08）WP

## 题目信息

- 分类：MISC
- 难度：中级
- 附件：`shadow_08.zip`

## 解题思路

拿到附件后，先看文件结构和头部数据：

1. `shadow_08.zip` 是一个正常的 ZIP。
2. ZIP 里只有一个文件：`data.bin`。
3. `data.bin` 的开头是 `Rar!`，看起来像 RAR，但继续看内容会发现这只是伪装。
4. 文件正文里直接给了提示：

```text
REMEMBER: FLAG IS HIDDEN IN BASE64 PLUS XOR!
FAKE FLAG: flag{00000000-0000-0000-0000-000000000000}
DO NOT TRUST THIS ONE.
GBIfGQVPR0tLTh8dHFMdSxhOU0ocSRpTHEZNTFNJS0ZHThpHSRpIHBsD
```

这里已经非常明确：

- 假 flag 不能信。
- 真 flag 在最后那串 Base64 文本里。
- 处理方式是 `Base64 + XOR`。

## 具体步骤

### 1. 提取最后一行 Base64

最后一行密文为：

```text
GBIfGQVPR0tLTh8dHFMdSxhOU0ocSRpTHEZNTFNJS0ZHThpHSRpIHBsD
```

### 2. 先做 Base64 解码

解码后得到 42 字节原始数据，内容不是可读文本，说明还要继续处理。

### 3. 爆破单字节 XOR

因为题目只说了 XOR，没有给 key，最稳妥的方法就是枚举 `0x00` 到 `0xFF`。

当 key 为 `126`（十六进制 `0x7e`）时，结果还原为标准 flag 格式：

```text
flag{19550acb-c5f0-4b7d-b832-75890d97d6be}
```

## 最终 flag

```text
flag{19550acb-c5f0-4b7d-b832-75890d97d6be}
```

## 复现脚本

目录中已补充批量脚本：

- [extract_shadow_flags.py](D:\桌面\yuwang\misc\2\extract_shadow_flags.py)

运行方式：

```bash
python3 extract_shadow_flags.py /mnt/d/桌面/yuwang/misc/2
```

如果后续把另外 9 个 `shadow_*.zip` 也放进同一目录，脚本会自动逐个提取。

## 逻辑可行性分析

这题的逻辑是可行的，而且从当前附件可以直接出 flag，原因有三点：

1. 文件内部有明确提示 `BASE64 PLUS XOR`，不是盲猜。
2. Base64 解码后的长度和内容都符合“再做一次轻量混淆”的特征。
3. XOR 爆破后能得到完整、规范、闭合的 `flag{...}`，说明解法链路自洽。

## 补充说明

当前目录里只有一份样本：`shadow_08.zip`。

如果题面说总共有 10 个文件，但你现在只拿到这 1 个，那么目前只能确认这一个附件的 flag。其余 9 个如果也采用相同隐藏方式，可以直接用同一脚本批量提取。
