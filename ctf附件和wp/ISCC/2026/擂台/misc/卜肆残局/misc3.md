# Misc Writeup: 城南旧庙外有一处古怪卦摊

## 题目信息

> **题目描述：** 城南旧庙外有一处古怪卦摊。摊主走失前，只留下四样旧物： **天象** | **人言** | **地盘** | **时令**
>
> 摊上旧抄本不止一手，互相参差：
>
> - 有人记位，有人记数。
> - 有人记辞，有人只记点画。
> - 有人抄正文，有人只抄边角。
> - 有人信时刻，有人信节候。

**附件内容：**

- 若干与“四样旧物”相关的文件
- 压缩包：`窥得天机.zip`
- 压缩包：`终局.7z`

------

## 核心解题思路 (TL;DR)

本题是一道结构严密的多阶段 Misc 嵌套题，解题流程如下：

1. **排查干扰项**：跳过伪造的 Flag 和误导提示，分别从四个旧物文件中提取出正确的数据碎片。
2. **MD5 解密**：拼接碎片得到中间密钥 `mid`，计算 MD5 作为 `窥得天机.zip` 的解压密码。
3. **ZIP 注释隐写**：读取 ZIP 注释（64位 Base64 字符），将其转为索引表，从解压出的 64 个 TXT 文件中逐位提取字符，组合成 `终局.7z` 的密码。
4. **AES-CBC 解密**：利用前两步得到的字符串截取 Key 和 IV，解密终局密文，获取最终 Flag。

------

## 详细解题步骤

### 第一阶段：破局 —— 提取旧物碎片与中间密钥

分析文件时，会遇到诸如 `flag{meta_lovers_die_first}`、`qian_kun_kan_li`、`dont_use_the_order` 等看似关键的字符串，**这些均为误导信息（Rabbit Holes）**。

结合题面提示（取数、取位、取边角等），深入分析四份材料，分别提取出以下四段真实隐写字符串：

- **天象**：`qW2O0z`
- **人言**：`5bnImG`
- **地盘**：`4yFuUc`
- **时令**：`4Y0nV9`

按照题目给出的“天、人、地、时”顺序拼接，得到中间密钥（记为 `mid`）： `qW2O0z5bnImG4yFuUc4Y0nV9`

对该字符串计算 MD5 值：

Python

```
import hashlib
mid = b"qW2O0z5bnImG4yFuUc4Y0nV9"
print(hashlib.md5(mid).hexdigest())
# 输出: 228a53da12c42a65235ca2ebefa826c1
```

使用得到的 MD5 值 `228a53da12c42a65235ca2ebefa826c1` 成功解压 `窥得天机.zip`，得到 64 个 TXT 文件。

------

### 第二阶段：窥机 —— ZIP 注释提取与索引映射

解压后，注意检查 `窥得天机.zip` 的属性，发现存在一段 **ZIP Comment（压缩包注释）**： `q7LxP0aR9Yv+u1kC3wFjI2sQmD4oJ6GfXr5hN8KpTtUVeBylHcSgZdWiEOAbMn/z`

该注释长度恰好为 64，且字符均在 Base64 编码表内。结合解压出的 64 个文本文件，推测出**查表索引规则**：

- 注释中的第 `i` 个字符，代表在标准 Base64 字符表中的索引值 `index`。
- 取第 `i` 个 TXT 文件中对应位置为 `index` 的字符。

映射逻辑如下：

Plaintext

```
Base64 表: ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/
映射示例: 
A -> 0
B -> 1
...
+ -> 62
/ -> 63
```

编写脚本遍历 64 个文件并提取字符，得到下一阶段的密码（记为 `seven_pwd`）： `UQC8TBH7FkJn7bmz7ikjttXfwjvsp99CHBWmH7+M9HxppE7W7a68mo/Ua4cfQUq2`

------

### 第三阶段：终局 —— AES-CBC 解密

使用 `seven_pwd` 解压 `终局.7z`，得到 `终局.txt`。文件内容为一段 Base64 密文： `7jgRTVRxS/HSsI673SWW2yglLJbYZq295x7Eu6qCEvymWnnhkwyDg/8CduA2gQpF`

梳理目前掌握的核心凭据：

1. `mid` = `qW2O0z5bnImG4yFuUc4Y0nV9`
2. `seven_pwd` = `UQC8TBH7FkJn7bmz7ikjttXfwjvsp99CHBWmH7+M9HxppE7W7a68mo/Ua4cfQUq2`

常见标准 AES 加密需要 16 字节的 Key 和 IV。分别截取两个凭据的**前 16 字节**进行尝试：

- **AES Key** = `qW2O0z5bnImG4yFu` (实际上脚本中取 `mid[:16]` 即 `qW2O0z5bnImG4yFu`)
- **AES IV** = `UQC8TBH7FkJn7bmz` (`seven_pwd[:16]`)

执行 AES-CBC 解密：

Python

```
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

mid = b"qW2O0z5bnImG4yFuUc4Y0nV9"
seven_pwd = b"UQC8TBH7FkJn7bmz7ikjttXfwjvsp99CHBWmH7+M9HxppE7W7a68mo/Ua4cfQUq2"

key = mid[:16]
iv = seven_pwd[:16]
ciphertext = b64decode("7jgRTVRxS/HSsI673SWW2yglLJbYZq295x7Eu6qCEvymWnnhkwyDg/8CduA2gQpF")

cipher = AES.new(key, AES.MODE_CBC, iv)
plaintext = unpad(cipher.decrypt(ciphertext), 16)

print(plaintext.decode())
```

解密成功，输出最终 Flag。

------

## 最终 Flag

Plaintext

```
ISCC{cd1e6a3c-8348-4d9e-a26c-59c269004f84}
```

------

## 完整自动化复现脚本 (One-Click Solver)

以下脚本实现了一键完成从计算 MD5、解压文件、提取注释隐写到最终 AES 解密的全过程。 *(注：运行环境需配置好 `pycryptodome` 库，且系统环境变量中需包含 `7z` 命令)*

Python

```
import os
import re
import zipfile
import hashlib
import subprocess
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def solve():
    # 1. 组装中间密钥
    part1, part2, part3, part4 = "qW2O0z", "5bnImG", "4yFuUc", "4Y0nV9"
    mid = part1 + part2 + part3 + part4
    zip_pwd = hashlib.md5(mid.encode()).hexdigest()
    
    print(f"[+] 中间密钥 (mid): {mid}")
    print(f"[+] 窥得天机.zip 解压密码 (MD5): {zip_pwd}")

    # 解压 ZIP
    subprocess.run(["7z", "x", "窥得天机.zip", f"-p{zip_pwd}", "-y", "-oout_zip"], check=False, stdout=subprocess.DEVNULL)

    # 2. 读取 ZIP 注释
    with zipfile.ZipFile("窥得天机.zip", "r") as z:
        comment = z.comment.decode()
    print(f"[+] 提取 ZIP 注释: {comment}")

    # 3. 查表索引提取下一阶段密码
    base64_table = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    
    # 收集并排序 TXT 文件（按文件名中的数字排序）
    txt_files = []
    for root, _, files in os.walk("out_zip"):
        for name in files:
            if name.lower().endswith(".txt"):
                txt_files.append(os.path.join(root, name))
                
    def sort_key(path):
        nums = re.findall(r"\d+", os.path.basename(path))
        return int(nums[0]) if nums else os.path.basename(path)

    txt_files = sorted(txt_files, key=sort_key)
    assert len(txt_files) == 64, f"[!] 文件数量异常: 期望 64，实际 {len(txt_files)}"

    seven_pwd = ""
    for i, ch in enumerate(comment):
        idx = base64_table.index(ch)
        with open(txt_files[i], "r", encoding="utf-8", errors="ignore") as f:
            seven_pwd += f.read()[idx]

    print(f"[+] 终局.7z 解压密码: {seven_pwd}")

    # 4. 解压 7z 并解密终局文件
    subprocess.run(["7z", "x", "终局.7z", f"-p{seven_pwd}", "-y", "-oout_final"], check=False, stdout=subprocess.DEVNULL)

    final_txt = os.path.join("out_final", "终局.txt")
    with open(final_txt, "r", encoding="utf-8", errors="ignore") as f:
        ciphertext_b64 = f.read().strip()

    # AES-CBC 解密 (截取前 16 字节作为 Key 和 IV)
    key = mid.encode()[:16]
    iv = seven_pwd.encode()[:16]
    ct = b64decode(ciphertext_b64)
    pt = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), 16)

    print(f"\n[★] 成功获取 Flag: {pt.decode()}")

if __name__ == "__main__":
    solve()
```
