# misc3 数字奥秘 WP

## 题目信息

- 提示：`VTFWT1Fsb3diRVJSVjJSS1VraENWVll4VlRGU1JtZDRWR3RhVldKRk5WRldWM2MwWlZVeFJWTlVSVDA9`

## 最终答案

`ISCC{56KqrBaKqEDsneCWjLuGj935hf1mip1I}`

## 二、附件分析

压缩包里只有一个文件：

```text
challenge.bin
```

但它并不是真正的普通二进制文件。检查文件头后可以看到：

```text
89 50 4E 47 0D 0A 1A 0A
```

这是标准 PNG 文件头，所以 `challenge.bin` 实际上是一张 PNG 图片，只是被改了扩展名。

## 三、题目脚本的核心逻辑

`misc3 数字奥秘.py` 的整体流程如下：

1. 从附件中读取 PNG 数据。
2. 解析 PNG 的 `tEXt` 文本块。
3. 取出隐藏字段 `SYNC_CODE`、`PERIODS`、`SYNC_PAYLOAD`。
4. 用修复后的自定义 VM 执行 `SYNC_CODE`，得到一组余数。
5. 结合 `PERIODS` 用中国剩余定理 CRT 合并出一个整数。
6. 枚举候选密钥材料，计算 `SHA-256`，再对密文做循环异或解密。
7. 如果解出的结果符合 `ISCC{...}` 格式，就输出 flag。

所以这题本质是：

`PNG 隐藏数据 + 自定义 VM + CRT + XOR 解密`

## 四、PNG 中的隐藏内容

从 PNG 的文本块中可以提取出以下关键信息：

```text
SYNC_CODE=++++...++++*#>++++...++++*#...
PERIODS=[128, 1532, 777, 579, 72, 781, 1791, 956]
SYNC_HINT=payload=base64;encryption=xor;key=merged_result;method=crt
SYNC_PAYLOAD=eJbzjUI/JkpcKE26rdIcbG9mmYPlBvKbuAs6HJv3ADBcrMD/cHc=
README=1. Run vm.py to get sensor data
2. If data looks incorrect, check vm.py for bugs
3. Use correct data with PERIODS to solve constraints
4. Decrypt payload with the key
```

这里已经把关键思路提示得很明显了：

- `payload` 需要先 Base64 解码
- 解密方式是 XOR
- 关键参数是 `merged_result`
- `merged_result` 需要用 CRT 计算
- 附件里的 `vm.py` 有坑

## 五、PNG 尾部还藏了一段 VM 源码

这张 PNG 在 `IEND` 之后还有尾随数据，里面藏了一段 `vm.py`。其中关键逻辑如下：

```python
elif cmd == '*':
    self.fp_reg = self.memory[self.ptr] * 0.1
elif cmd == '#':
    val = int(self.fp_reg)
    self.output.append(val)
```

这就是出题人的坑点。

按这段代码理解：

- `*` 是把当前值乘以 `0.1`
- `#` 是直接 `int()` 截断

但题目脚本里的修正版并不是这么处理的。修正版的意思是：

```python
elif cmd == "*":
    fp_tenths = memory[pointer]
elif cmd == "#":
    output.append(round_tenth(fp_tenths))
```

也就是说：

- `*` 保存的是“十分位整数”
- `#` 输出时不是截断，而是按 `/10` 进行四舍五入

因此直接按附件里的假 VM 跑，结果会全部差 1。

## 六、正确结果与错误结果

### 1. 按附件里的错误 VM 运行

得到余数：

```text
[106, 978, 145, 358, 34, 246, 556, 594]
```

再做 CRT：

```text
1952746
```

### 2. 按题目脚本里的修正版 VM 运行

得到正确余数：

```text
[107, 979, 146, 359, 35, 247, 557, 595]
```

模数为：

```text
[128, 1532, 777, 579, 72, 781, 1791, 956]
```

将这两组数据代入 CRT，得到：

```text
merged_result = 1952747
```

这个值才是正确的核心结果。

## 七、提示串的作用

题目额外给了一个提示串：

```text
VTFWT1Fsb3diRVJSVjJSS1VraENWVll4VlRGU1JtZDRWR3RhVldKRk5WRldWM2MwWlZVeFJWTlVSVDA9
```

对它连续做 Base64 解码，可以得到：

```text
U1VOQlowbERRV2RKUkhCVVYxVTFSRmd4VGtaVWJFNVFWV3c0ZVUxRVNURT0=
SUNBZ0lDQWdJRHBUV1U1RFgxTkZUbE5QVWw4eU1ESTE=
ICAgICAgIDpTWU5DX1NFTlNPUl8yMDI1
       :SYNC_SENSOR_2025
```

最终有效信息就是：

```text
:SYNC_SENSOR_2025
```

同时，脚本还会从附件里再提取两部分内容：

- 从 PNG 文本块键名中提取前缀：`SYNC`
- 从尾随文本中提取关键单词：`SENSOR`

最后组合出的密钥材料是：

```text
1952747:SYNC_SENSOR_2025
```

## 八、最终解密

密文字段：

```text
eJbzjUI/JkpcKE26rdIcbG9mmYPlBvKbuAs6HJv3ADBcrMD/cHc=
```

先 Base64 解码得到字节流。

然后计算：

```text
SHA256("1952747:SYNC_SENSOR_2025")
```

得到 32 字节密钥，并对密文进行循环异或解密。

最终明文为：

```text
ISCC{56KqrBaKqEDsneCWjLuGj935hf1mip1I}
```

## 

因为题目给的 `misc3 数字奥秘.py` 已经把完整解题流程写好了：

1. 自动识别 ZIP 和 PNG
2. 自动提取 PNG 文本块与尾随数据
3. 自动用修正版 VM 算出正确余数
4. 自动做 CRT 合并
5. 自动尝试候选密钥材料
6. 自动解密并匹配 `ISCC{...}`

也就是说，这题真正考的不是“自己从零写脚本”，而是“看懂出题人给的脚本，并识别里面修复过的关键逻辑”。

## 十、总结

这题的关键点有三个：

1. `challenge.bin` 实际是 PNG，信息藏在 `tEXt` 和 PNG 尾随数据里。
2. 尾部附带的 `vm.py` 是错误实现，直接跑会让结果少 1。
3. 正确的密钥材料不是单独的 `merged_result`，而是 `1952747:SYNC_SENSOR_2025`。

最终 flag：

```text
ISCC{56KqrBaKqEDsneCWjLuGj935hf1mip1I}
```
