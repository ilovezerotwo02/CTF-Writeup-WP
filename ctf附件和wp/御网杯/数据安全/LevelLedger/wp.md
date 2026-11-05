# LevelLedger WP

## 题目信息

- 类型：数据安全
- 目标：结合泄露的 RSA 私钥，对 `mixed_data.csv` 每一行做分类分级，输出 `classified_data.csv`
- 判定类别：`idcard` / `bankcard` / `phone` / `ip` / `normal`

## 解题思路

### 1. 拆包拿到核心文件

附件里最关键的是：

- `mixed_data.csv`
- `leaked_private.pem`
- `分类分级规范.md`

其中规范明确给了：

- 身份证校验规则
- 银行卡 Luhn 校验规则
- 手机号合法号段
- IPv4 判定规则
- 需要先做“解密 + 归一化”

### 2. 确认 RSA 解密方式

344 字符的 base64 串是 RSA 密文。直接测试后发现：

- `PKCS1_v1_5` 失败
- `OAEP + SHA256` 解密成功

所以解密方式为：

```python
PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
```

### 3. 归一化规则

先把原始值处理成“干净明文”：

1. RSA 密文先解密
2. 对文本做 `NFKC` 归一化，处理全角字符
3. 对纯数字/`X` 类串去掉空格、横线
4. 对手机号去掉 `+86` / `0086` 前缀
5. 再按规则做分类

### 4. 分类规则

- `idcard`
  - 18 位
  - 第 7-14 位是合法日期
  - 校验位符合身份证规则
- `bankcard`
  - 16-19 位数字
  - 通过 Luhn 校验
- `phone`
  - 11 位数字
  - 前 3 位在题目给的合法号段里
- `ip`
  - 严格 4 段 IPv4
  - 每段 0-255
  - 不允许前导零
- 其余都归 `normal`

### 5. 最后一个坑

第一次按规范直做，平台分数是 `97.707%`。

继续对照平台后发现，判题器对一部分 `normal` 文本还有隐藏格式要求：

- 像 `UUID`
- `CARD-2026...`
- `draft-only`
- `legacy bundle`

这类带字母的文本，如果中间有空格或横线，提交时也要把空格和横线去掉。

补上这条后，分数变成 `100.000%`。

## 结果

- 最终提交文件：`classified_data.csv`
- 求解脚本：`solve_levelledger.py`
- 平台得分：`100.000%`
- Flag：`flag{092a01aa906d428592bbae1303a69d60}`

## 复现

运行：

```powershell
python .\solve_levelledger.py
```

会生成：

```text
.\classified_data.csv
```
