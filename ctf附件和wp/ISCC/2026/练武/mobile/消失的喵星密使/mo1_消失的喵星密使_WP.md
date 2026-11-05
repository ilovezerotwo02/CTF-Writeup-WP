# mo1 消失的喵星密使 WP

## 题目信息

- 附件：`mo1 消失的喵星密使.apk`
- 参考脚本：`消失的喵星密使.py`
- 要求：不能直接运行现成脚本拿答案

## 最终答案

`ISCC{kP7#mZ9!vR2@nQ4*xW}`

## 一、题目整体思路

这题的完整链路可以拆成 4 部分：

1. Java 层检查输入格式。
2. 根据界面上的 6×6 emoji 方阵，点击出正确路径。
3. Native 层从 `hint.png` 中提取隐藏数据，并做反调试检测。
4. 用路径派生密钥，配合图片里提取出的自定义 S 盒，解出真正的 flag。

题面里的两句提示分别对应：

- “看穿布偶猫眼睛里的秘密” -> `hint.png` 图片隐写
- “躲过猫砂盆监控” -> native 里的 `TracerPid` 反调试

## 二、入口分析

APK 包名：

```text
com.example.mobile03
```

关键类只有这几个：

```text
MainActivity
_A
_B
_C
_P
```

对应作用：

- `MainActivity`：主界面逻辑
- `_B`：构造 emoji 方阵并记录点击序列
- `_C`：校验路径字符串的 MD5
- `_A`：native 校验入口
- `_P`：读取 `assets/sys/OBSERVER_PROTOCOL`

`MainActivity` 的按钮点击逻辑很直接：

1. 先取当前点击得到的路径串。
2. 调用 `_C._c(path)` 判断路径是否正确。
3. 再检查用户输入是否满足 `ISCC{...}` 格式。
4. 把花括号里的内容和路径串一起传给 native 方法 `_A._v(...)`。

## 三、输入格式校验

`_B._g()` 里藏了一段异或恢复前缀的逻辑，原始字节为：

```text
0b 11 01 01 39
```

每个字节异或 `0x42` 后得到：

```text
ISCC{
```

所以输入格式被固定为：

```text
ISCC{...}
```

函数最后会把花括号内部内容截出来，因此 native 真正参与校验的是：

```text
kP7#mZ9!vR2@nQ4*xW
```

## 四、emoji 方阵与路径恢复

`_B` 中构造了一个 6×6 方阵，行列标签都是：

```text
A D F G V X
```

本质上就是一个 ADFGVX 风格的坐标表。

### 1. 路径哈希条件

`_C._c()` 对路径字符串做 MD5，要求结果等于：

```text
15f75053b23af442b365f5593d317da4
```

### 2. 界面明文提示

界面上的提示文本为：

```text
密使巡逻日志：雪球在印记的起点打转，它转而扑向那抹舞动的斑斓，在清甜的气息中小憩片刻；它凝视苍穹中央的光源，却为未竟之事而黯然，终没入无光的轮廓里。
```

这句话可以对应出 6 个目标 emoji：

1. 印记的起点 -> `🐾`
2. 舞动的斑斓 -> `🦋`
3. 清甜的气息 -> `🌿`
4. 苍穹中央的光源 -> `☀️`
5. 黯然 -> `😿`
6. 无光的轮廓 -> `🐈‍⬛`

### 3. 隐藏提示 `OBSERVER_PROTOCOL`

`_P._l()` 会读取 `assets/sys/OBSERVER_PROTOCOL`。这个文件表面是十六进制文本，解码后可以看到：

```text
[GLOBAL_SEED]: 0xDEADC0DE
[RUNTIME_STR]: @LOG_TAG_DESCRIPTOR
[CONSTRAINT]: S = { x | 1 ≤ x ≤ 6, x ∈ ℤ }

[[ PHASE_ALPHA: THE_ORIGIN_BIAS ]]
...
P1.r = r_A; P1.c = c_A / λ

[[ PHASE_BETA: THE_FRACTAL_SHIFT ]]
...
r_B = τ + (φ >> 31) + 1
c_B = ((r_B << τ) ^ (T & 0x00)) & 0x07

[[ PHASE_GAMMA: THE_ASYMPTOTIC_GHOST ]]
...
r_C = lim(x→∞) [ (6x² + 5x) / (x² + 1) ]
c_C = ⌈ cos(π) ⌉ + ghost + 2

[[ GLOBAL_PARITY_CHECK ]]
Row_Total ≡ 21
Col_Total ≡ 20
隐藏条件：P2.c > P1.c 且 P6.c < P2.c
```

把这些约束和上面的 6 个目标点结合起来，可以恢复坐标：

- `P1 = (1,1)` -> `🐾`
- `P2 = (2,4)` -> `🦋`
- `P3 = (3,6)` -> `🌿`
- `P4 = (4,2)` -> `☀️`
- `P5 = (5,6)` -> `😿`
- `P6 = (6,1)` -> `🐈‍⬛`

行和：

```text
1 + 2 + 3 + 4 + 5 + 6 = 21
```

列和：

```text
1 + 4 + 6 + 2 + 6 + 1 = 20
```

完全满足协议里的隐藏校验条件。

### 4. 正确路径串

把上述 6 个点映射为 ADFGVX 坐标：

1. `🐾` -> `AA`
2. `🦋` -> `DG`
3. `🌿` -> `FX`
4. `☀️` -> `GD`
5. `😿` -> `VX`
6. `🐈‍⬛` -> `XA`

拼接得到：

```text
AADGFXGDVXXA
```

验证：

```text
MD5("AADGFXGDVXXA") = 15f75053b23af442b365f5593d317da4
```

与 Java 层硬编码常量完全一致。

## 五、native 反调试

`lib/x86_64/libmobile03.so` 在 `JNI_OnLoad` 中会启动一个监控线程：

```text
_Z10_f_monitorPv
```

它会不断读取：

```text
/proc/self/status
```

然后查找：

```text
TracerPid:
```

如果 `TracerPid` 不为 0，就直接调用 `_exit(0)` 结束进程。

所以这题如果走动态调试，要么 patch 掉反调试，要么伪造结果；这里直接走纯静态分析即可。

## 六、`hint.png` 中的隐藏数据

native 校验入口 `_A._v()` 对应 so 里的：

```text
_Z6_f_valP7_JNIEnvP8_jobjectP8_jstringS4_S2_
```

它一上来会调用 `_Z6_f_ext...` 从 `hint.png` 中提取一段隐藏数据。

### 1. 提取方式

`_f_ext` 的逻辑可以概括为：

1. 锁定图片像素。
2. 按行扫描整张图。
3. 取每个像素某个颜色字节的最低位。
4. 连续取前 `0x830 = 2096` 个 bit。
5. 每 8 bit 打包成 1 字节，共得到 `262` 字节。

前 4 字节必须是：

```text
MEOW
```

否则直接失败。

### 2. 实际提取结果

从 `hint.png` 的蓝色通道最低位提取，前 32 字节为：

```text
4d454f57d5bb02d1d3cd4cda5eee3145906f295f1fdf6e428fa02c9c8d2f5abc
```

也就是：

- `4d454f57` -> `MEOW`
- 后面 256 字节 -> 自定义 AES 使用的 S 盒

前 32 字节的 S 盒内容为：

```text
d5bb02d1d3cd4cda5eee3145906f295f1fdf6e428fa02c9c8d2f5abcfe1787e4
```

这就是题面里“布偶猫眼睛里的秘密”。

## 七、路径如何派生出密钥

so 中还有两个关键函数：

```text
_Z3_f1PKcPh
_Z6_f_expPKh
```

分析后可以知道：

- `_f1`：根据路径生成 32 字节初始密钥
- `_f_exp`：使用提取到的自定义 S 盒，做 AES-256 的密钥扩展

### 1. 自定义 6×6 字符表

so 里有一个 36 字符字符串：

```text
ph9z2r7w5kjs1m06u4vdy3i8txqaeobglfc6
```

按 6×6 填表如下：

| 行\列 | A | D | F | G | V | X |
| --- | --- | --- | --- | --- | --- | --- |
| A | p | h | 9 | z | 2 | r |
| D | 7 | w | 5 | k | j | s |
| F | 1 | m | 0 | 6 | u | 4 |
| G | v | d | y | 3 | i | 8 |
| V | t | x | q | a | e | o |
| X | b | g | l | f | c | 6 |

### 2. 路径重排

native 不会直接使用：

```text
AADGFXGDVXXA
```

而是先重排成：

```text
AXXAFVDGXGDA
```

重排规则是按下标分组：

1. 先取 `1 mod 4`
2. 再取 `0 mod 4`
3. 再取 `2 mod 4`
4. 最后取 `3 mod 4`

### 3. 生成 32 字节原始 key

重排后的字符串每两个字符作为一个坐标，到上面的 6×6 表里取出对应字符，然后计算：

```text
key[i] = SBOX[polybius_char] ^ (0x13 * i)
```

最终得到 32 字节 key：

```text
7dc715ce3dae0f51ab5ccf20992339ea41b22bbd4f78d344b50fddf665d64799
```

## 八、native 最终校验本质上是自定义 S 盒版 AES-256

`_f_exp` 中能清楚看出 AES-256 key schedule 的特征：

- 初始 8 个 word
- `RotWord`
- `SubWord`
- `Rcon = 01 02 04 08 10 20 40 80 1b 36`

不同点在于：

- 标准 AES 使用固定 S 盒
- 这里的 S 盒来自 `hint.png`

`_f_enc` 则实现了标准的 AES 轮结构：

1. AddRoundKey
2. SubBytes
3. ShiftRows
4. MixColumns

总共 14 轮，完全符合 AES-256。

所以可以把这题 native 理解为：

```text
自定义 S 盒版 AES-256
```

## 九、从 native 常量逆出 flag

so 中还藏了一段 Base64 字符串：

```text
y1pjBEs2bI0aMxi6qPR3zDfvV/DjSr18MK/4h51Ve64=
```

先做 Base64 解码，得到：

```text
cb5a63044b366c8d1a3318baa8f477cc37ef57f0e34abd7c30aff8879d557bae
```

native 又拿它和 16 字节常量：

```text
ffffffffffffffff
```

分块异或，得到两块目标密文：

```text
ad3c05622d500aeb7c557edcce9211aa
51893196852cdb1a56c99ee1fb331dc8
```

然后使用：

- 从 `hint.png` 中提取的自定义 S 盒
- 由路径派生的 32 字节 key

对这两块做 AES-256 逆运算，得到：

```text
Block1 = kP7#mZ9!vR2@nQ4*
Block2 = xW + 14 个 0x00
```

所以花括号内部的真实内容就是：

```text
kP7#mZ9!vR2@nQ4*xW
```

拼回完整 flag：

```text
ISCC{kP7#mZ9!vR2@nQ4*xW}
```

## 十、完整验证

整个结果可以被完整验证：

1. 路径串 `AADGFXGDVXXA` 的 MD5 正确。
2. `hint.png` 蓝色通道最低位确实能提取出 `MEOW` 和 256 字节 S 盒。
3. 路径串可以稳定派生出 32 字节 key。
4. 使用该 key 和自定义 S 盒解密，得到可读明文：

```text
kP7#mZ9!vR2@nQ4*xW
```

5. 拼回外层格式：

```text
ISCC{kP7#mZ9!vR2@nQ4*xW}
```

## 十一、总结

这题最关键的点有 4 个：

1. emoji 方阵不是装饰，而是真正的路径密码表。
2. `OBSERVER_PROTOCOL` 负责提供路径的数学约束和行列和条件。
3. `hint.png` 藏的不是明文 flag，而是自定义 AES 的 S 盒。
4. native 最终校验是带 `TracerPid` 反调试的自定义 S 盒版 AES-256。

最终答案：

```text
ISCC{kP7#mZ9!vR2@nQ4*xW}
```
