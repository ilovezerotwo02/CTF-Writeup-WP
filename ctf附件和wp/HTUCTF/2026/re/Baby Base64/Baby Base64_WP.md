# Baby Base64 — Writeup

**题目类别：** Reverse  
**附件：** `Base64_Baby.exe`（x86-64 PE，仅 3584 字节）  
**Flag：** `HTUCTF{B4se64_1s_Easy}`

## 题目分析

无壳、无混淆，导入表只有 `ReadFile` / `WriteFile` / `GetStdHandle` / `ExitProcess`——典型的"读输入、比字符串、输出结果"结构。

- `main` @ `0x140001020`：打印 banner → `ReadFile` 读入最多 `0x80` 字节到栈 `[rsp+0x20]` → 调用判定函数
- `sub_140001250`：`strlen` 后把输入做**标准 base64 编码**到栈缓冲，再与 `.rdata` 里的硬编码串比对
- `sub_140001140`：读输入后去掉尾部 `\r` / `\n`
- `sub_1400010E0`：printf 风格输出封装（`GetStdHandle` + `WriteFile`）

## 关键点：程序做的是"编码"而不是"解码"

判定逻辑是 `base64(你的输入) == 目标串`，所以**不能**去 base64 解密码——要解的 flag 本身，就得**反向 base64 解码那个目标串**。

## 硬编码目标串

`strings` 直接可见（字母表是标准的 `A-Za-z0-9+/`，无自定义置换）：

```
SFRVQ1RGe0I0c2U2NF8xc19FYXN5fQ==
```

解码：

```bash
echo -n 'SFRVQ1RGe0I0c2U2NF8xc19FYXN5fQ==' | base64 -d
# HTUCTF{B4se64_1s_Easy}
```

## 实跑验证

```bash
printf 'HTUCTF{B4se64_1s_Easy}' | ./Base64_Baby.exe
# Correct! Nice reverse!   (exit 0)
```

错误输入返回 `Wrong flag! Try again.`（exit 1），可用来排除假 flag。

## 经验

这类"baby"RE 优先 `strings -a` 找长 base64 串直接解码，几秒钟出结果；再用程序本身跑一遍验证，避免踩假 flag。
