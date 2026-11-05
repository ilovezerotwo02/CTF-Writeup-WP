# 12、签到题-损坏的压缩包 WP

## 题目信息

- 分类：MISC
- 难度：初级
- 提交格式：`flag{*****}`
- 附件：
  - `archive_10.zip`
  - `data.txt`

## 解题环境

题目里提到的 `wsl -d ubuntu-24` 环境可直接使用，已确认以下工具存在：

- `unzip`
- `zipinfo`
- `7z`
- `file`
- `xxd`
- `strings`
- `zipdetails`

## 解题过程

### 1. 检查压缩包是否真的损坏

先测试压缩包完整性：

```bash
cd /mnt/d/桌面/yuwang/misc/签到题-损坏的压缩包
unzip -t archive_10.zip
```

结果：

```text
Archive:  archive_10.zip
    testing: data.txt                 OK
No errors detected in compressed data of archive_10.zip.
```

说明这个 ZIP 实际上**没有损坏**，可以正常解压。

### 2. 查看 ZIP 结构

继续看 ZIP 结构：

```bash
zipinfo -v archive_10.zip
zipdetails archive_10.zip
```

关键信息如下：

- ZIP 中只有一个文件：`data.txt`
- 压缩方式：`Stored`
- 压缩包总大小：`122` 字节
- 文件内容直接存放在 ZIP 里，payload 为：

```text
dGFoZw==
```

### 3. 提取并解码内容

解压得到的 `data.txt` 内容也是：

```text
dGFoZw==
```

该串一眼像 Base64，直接解码：

```bash
python3 - <<'PY'
import base64
print(base64.b64decode('dGFoZw=='))
PY
```

输出：

```text
b'tahg'
```

也就是明文：

```text
tahg
```

## 结论

### 可以严格确认的事实

从附件中可以**确定无疑**得到以下信息：

1. `archive_10.zip` 并未损坏。
2. ZIP 内只有一个 `data.txt`。
3. `data.txt` 的内容是 `dGFoZw==`。
4. 该内容做 Base64 解码后得到 `tahg`。

### flag 判断

如果按最常见的签到题出题逻辑：

- 解压
- Base64 解码
- 按题目要求包上 `flag{}`

那么最自然的候选 flag 是：

```text
flag{tahg}
```

## 逻辑可行性分析

这道题目前的附件存在一个问题：**从现有证据无法唯一证明还需要额外变换**。

也就是说：

- 从附件里可以稳定拿到 `tahg`
- 但题目名“损坏的压缩包”和附件实际行为不一致，因为 ZIP 本身是正常的
- 附件里也没有更多线索说明 `tahg` 之后还要继续逆序、移位、异或或其他处理

所以结论应当分两层看：

### 如果只是问“能不能从附件推出一个最合理的 flag 候选”

可以，候选值是：

```text
flag{tahg}
```

### 如果是问“能不能仅凭附件唯一确定最终 flag”

不能完全唯一确定。

原因是：

- 附件没有体现真正的“损坏修复”过程
- `tahg` 不是一个自解释的标准单词
- 没有额外 hint 指向下一步转换

## 最终建议

优先提交：

```text
flag{tahg}
```

如果平台不通过，那么大概率是：

1. 题目附件不完整；
2. 题目标题写错了；
3. 还缺少一个额外提示，用来说明 `tahg` 需要再做一次变换。
