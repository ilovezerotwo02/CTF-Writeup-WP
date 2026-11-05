# 14、像素中的秘密 WP

## 题目信息

- 分类：MISC
- 难度：高级
- 附件：`image_06.zip`

## 解题思路

这题的关键不在像素本身，而在 **PNG 的 `IEND` 之后追加的数据**。

拿到附件后先做结构分析：

1. `image_06.zip` 里只有一个文件：`image_06.png`
2. `image_06.png` 是一张 `64 x 64` 的纯白 PNG
3. PNG 标准块只有：
   - `IHDR`
   - `IDAT`
   - `IEND`
4. 但在 `IEND` 之后还有 **64 字节尾随数据**

脚本 [`misc4.py`](D:/桌面/yuwang/misc/像素中的秘密/misc4.py) 的正确做法就是：

1. 从 ZIP 中取出 PNG
2. 解析 PNG 块，定位 `IEND`
3. 提取 `IEND` 之后的 trailer
4. 用 trailer 前 8 字节作为种子
5. 用线性同余生成器 `LCG` 逐字节生成密钥流
6. 对后面的密文做 XOR 解密
7. 解密结果是一串 **Base62**
8. 再做 Base62 解码得到最终 flag

## 关键数据

提取出的 PNG 尾随数据：

```text
0000000069cb34428ca630e2b4556568f38812932fb5eb592e5e2b53c3f80a8d5e751fb7bf038898bf0231645bb257caa18c7b9e6580dfb269b48306ad28679a
```

前 8 字节作为种子：

```text
0000000069cb3442
```

转成整数：

```text
1774924866
```

## LCG 参数

脚本中使用的 LCG 为：

```python
a = 1664525
c = 1013904223
m = 2 ** 32
```

状态更新公式：

```text
state = (a * state + c) % m
key = state & 0xff
```

然后逐字节执行：

```text
plaintext_byte = ciphertext_byte XOR key
```

## 解密结果

LCG XOR 解密后得到：

```text
5bctImRBrdImjUTKgJH5NpMwOItyj3GzffBRFj
```

这串内容不是最终 flag，而是 **Base62 编码后的数据**。

再做 Base62 解码后得到：

```text
flag{custom_protocol_hiding}
```

## 最终 flag

```text
flag{custom_protocol_hiding}
```

## 复现方法

直接在题目目录运行：

```bash
python misc4.py
```

实际输出为：

```text
[+] png name: image_06.png
[chunk] IHDR length=13 offset=8
[chunk] IDAT length=124 offset=33
[chunk] IEND length=0 offset=169
[+] trailer length: 64
[+] trailer hex: 0000000069cb34428ca630e2b4556568f38812932fb5eb592e5e2b53c3f80a8d5e751fb7bf038898bf0231645bb257caa18c7b9e6580dfb269b48306ad28679a
[+] seed hex: 0000000069cb3442
[+] seed int: 1774924866
[+] ciphertext length: 56
[+] base62: 5bctImRBrdImjUTKgJH5NpMwOItyj3GzffBRFj
[+] flag: flag{custom_protocol_hiding}
```

## 题目总结

这题本质是三层：

1. `PNG trailer` 隐藏数据
2. `LCG + XOR` 还原中间层
3. `Base62` 解码得到 flag

题目名字虽然叫“像素中的秘密”，但真正藏东西的位置并不在像素里，而是在 **PNG 文件尾部结构** 中。
