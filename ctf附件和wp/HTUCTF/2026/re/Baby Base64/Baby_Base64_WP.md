# Baby Base64 — Writeup

**题目类别：** Reverse / 逆向  
**题目名称：** Baby Base64  
**附件：** `Base64_Baby.exe`  
**Flag 格式：** `HTUCTF{...}`

## 题目描述

程序运行后打印如下 banner：

```text
=============================
    HTUCTF - Baby Base64
=============================
Find the correct flag!
Input flag:
```

输入正确 flag 后提示 `Correct! Nice reverse!`，错误则提示 `Wrong flag! Try again.`。从名字就能看出考点是 Base64。

## 解题思路

这是一道典型的“编码比较型” crackme：程序把**输入做 Base64 编码**后与硬编码字符串比较。因此解题方向要**反过来**——对硬编码的目标串做 Base64 解码，而不是对输入解码。这个方向一旦搞反，就会得出错误结论。

## 解题过程

### 1. 文件特征

```bash
$ ls -la Base64_Baby.exe
-rwxr-xr-x 3584 Base64_Baby.exe
```

x86-64 PE，仅 3584 字节，无壳、无混淆。导入表只有 4 个函数：

```text
ExitProcess / GetStdHandle / ReadFile / WriteFile / KERNEL32.dll
```

说明它不用 CRT 的 printf/scanf，而是自己用 `ReadFile`/`WriteFile` 做控制台 IO，属于纯手写逻辑的小 crackme。

### 2. 字符串一步到位

```bash
$ strings -a Base64_Baby.exe
...
SFRVQ1RGe0I0c2U2NF8xc19FYXN5fQ==
ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/
Input flag:
=============================
    HTUCTF - Baby Base64
No input.
Wrong flag! Try again.
Find the correct flag!
Correct! Nice reverse!
```

两个关键点：

1. 出现了**标准 Base64 字母表** `A-Za-z0-9+/`，说明没有自定义置换，直接用标准 Base64 处理即可；
2. 紧挨着字母表的那串 `SFRVQ1RGe0I0c2U2NF8xc19FYXN5fQ==` 明显是编码后的目标串。

### 3. 反汇编确认校验方向

主流程（`main` @ `0x140001020`）：

```asm
140001063: lea  rcx, [rsp+0x20]      ; 输入缓冲区
140001068: mov  edx, 0x80            ; 最多读 0x80 字节
14000106d: call 0x140001140          ; ReadFile 读入 + 去掉末尾 \r\n
140001090: lea  rcx, [rsp+0x20]
140001095: call 0x140001250          ; 校验函数
14000109a: cmp  eax, 0x0
14000109d: je   0x1400010b8          ; eax==0 判为正确
```

- `0x140001140`：`GetStdHandle(-10)` + `ReadFile` 读入输入，随后依次 `cmp ecx, 0xd`（回车）、`cmp eax, 0xa`（换行）把行尾换行剥掉；
- `0x140001250`：`strlen` 取输入长度 → **对输入做标准 Base64 编码**写入栈上缓冲 → 与 `.rdata` 中的硬编码串逐字节比较，相同则返回 0；
- `0x1400010E0`：`GetStdHandle(-11)` + `WriteFile` 的输出封装。

也就是说校验等式是：

```text
base64(输入) == "SFRVQ1RGe0I0c2U2NF8xc19FYXN5fQ=="
```

因此：

```text
输入 == base64_decode("SFRVQ1RGe0I0c2U2NF8xc19FYXN5fQ==")
```

### 4. 解码

```python
import base64
print(base64.b64decode(b"SFRVQ1RGe0I0c2U2NF8xc19FYXN5fQ=="))
# b'HTUCTF{B4se64_1s_Easy}'
```

### 5. 实机验证

```bash
$ printf 'HTUCTF{B4se64_1s_Easy}' | ./Base64_Baby.exe
=============================
    HTUCTF - Baby Base64
=============================
Find the correct flag!
Input flag: Correct! Nice reverse!        # exit 0

$ printf 'wrongflag' | ./Base64_Baby.exe
Input flag: Wrong flag! Try again.        # exit 1
```

正确输入返回 `Correct! Nice reverse!` 且退出码为 0，错误输入返回 `Wrong flag! Try again.` 且退出码为 1，可以排除假 flag。

## Flag

```text
HTUCTF{B4se64_1s_Easy}
```

## 小结

这题的全部难度在于**认清比较方向**：程序是“把输入编码后比较”，不是“把目标解码后比较”。识别出标准 Base64 字母表后，直接对目标串解码即可，全程不到一分钟。配套的实机验证（正确/错误输入各跑一次）可以有效防止把干扰串当成 flag。

> 注：Flag 已通过运行程序实机验证（正确/错误双路径）。
