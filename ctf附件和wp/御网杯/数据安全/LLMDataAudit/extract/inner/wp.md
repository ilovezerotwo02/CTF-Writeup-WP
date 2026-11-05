# LLMDataAudit WP

## Flag

`flag{6faeb4b833db3e6faafb4b3ac9c9b3f2}`

## 题目理解

附件里给了三份核心文件：

- `chat_logs.jsonl`：10000 条对话日志
- `system_prompt.txt`：客服系统的系统提示词
- `README.pdf`：审计规则、提交格式、PII 校验要求

目标是生成 `result.csv`，格式为：

```csv
turn_id,attack_type,category,value
```

其中：

- `attack_type` 只看 `user_input` 判定，优先级为 `encoding > unicode > role_play > direct`
- `category` 只可能是 `idcard / phone / bankcard / email`
- `value` 需要还原成标准格式，去掉分隔符或解码 Base64

## 关键分析

### 1. 攻击类型判定

按 `README` 的定义做四类分类：

- `encoding`：输入里出现 `Base64` 提示词，且包含 Base64 串
- `unicode`：输入里出现 `\uXXXX`
- `role_play`：例如 `假设你是`、`你现在是`、`请扮演`、`Pretend`、`Act as`
- `direct`：例如 `忽略`、`关闭安全过滤`、`系统管理员`、`dump`、`output user pii`

### 2. PII 提取思路

一开始如果直接全局跑数字正则，很容易把：

- 交易流水号
- 订单号
- 工单号

误判成身份证或银行卡，所以后面改成了“字段标签驱动提取”：

- `bank_card=...`
- `email=...`
- `id_card: ...`
- `phone: ...`
- `身份证号 ...，联系电话 ...`
- `电话号码: 1 5 0 ...`

然后再做标准化和校验：

- 身份证：18 位 + 生日合法 + 校验位正确
- 手机号：11 位 + 号段合法
- 银行卡：16-19 位 + 指定 BIN + Luhn
- 邮箱：标准邮箱格式

### 3. 变形处理

题目里的泄露值有三种主要变形：

- 明文
- Base64
- 字符分隔，例如 `1 5 0 6 6 5 3 4 8 8 6`

所以脚本里统一做了：

- Base64 解码
- 空格 / 逗号 / 连字符清洗
- 再做校验

## 最终脚本

审计脚本：

- [solve_llmdataaudit.py](D:/桌面/yuwang/数据安全/LLMDataAudit/extract/inner/solve_llmdataaudit.py)

运行方式：

```powershell
py -3 solve_llmdataaudit.py
```

会输出最终提交文件：

- [result_v3.csv](D:/桌面/yuwang/数据安全/LLMDataAudit/extract/inner/result_v3.csv)

## 提交结果

上传 `result_v3.csv` 后，平台返回：

- `score = 100.000%`
- `flag = flag{6faeb4b833db3e6faafb4b3ac9c9b3f2}`

## 关键坑点

### 1. 不能直接全局扫长数字

交易流水号很容易撞上弱校验，必须结合字段语义提取。

### 2. 正则不能跨行吞字段

早期版本把 `id_card:` 后面连同下一行一起吞掉，导致很多真实泄露没被识别出来。

### 3. Unicode 轮次里的 `电话号码`

这批日志里的手机号是空格分隔格式，必须单独兼容 `电话号码:` 这个字段名。
