# CrackMe_2_3.apk 题解

## 1. 最终结论

从附件中可以直接恢复出 flag：

```text
flag{2023326077889096380}
```

但需要注意：

- 附件可以出 flag。
- APK 当前的 native 校验逻辑本身有问题，正常通过界面输入并不能和程序里存储的目标值对应上。

## 2. 入口定位

Java 层入口在 `sources/com/cr/test/wide.java`：

```java
public static native boolean verifyFlag(String str);
```

点击按钮后会调用 `verifyFlag(candidate)`，因此真正的校验逻辑在：

```text
resources/lib/x86/libcrackme2.so
```

## 3. so 中的关键信息

查看导出符号后，可以看到这些关键函数：

```text
_Z10verifyFlagP7_JNIEnvP7_jclassP8_jstring
_Z15des_ecb_encryptPKhiS0_Ph
_Z11des_encryptPKhS0_Ph
_Z15des_ecb_decryptPKhiS0_Ph
_Z11des_decryptPKhS0_Ph
```

说明这题的核心确实是 DES，并且校验逻辑在 native 层。

## 4. verifyFlag 逻辑分析

从 `verifyFlag` 的反汇编可以整理出下面的流程：

1. 通过 `GetStringUTFChars` 取出用户输入。
2. 将输入补齐到 8 字节的整数倍。
3. 使用 DES-ECB 对补齐后的数据进行加密。
4. 将加密结果转成 hex 字符串。
5. 把这个 hex 字符串和程序中预置的目标串比较。

关键位置如下：

- `0x241fa`：传入 DES key
- `0x24203`：调用 `des_ecb_encrypt`
- `0x24221`：调用 `bytesToHex`
- `0x24288`：将结果与预置目标串比较

## 5. DES key

在 `.rodata` 中可以直接看到 key 明文：

```text
12345678
```

因此 DES key 为：

```text
12345678
```

## 6. 预置目标串

程序初始化全局字符串时，使用了下面这段内容：

```text
666c61677b323032333332363037373838393039363338307d07070707070707
```

将它按 hex 解码后得到：

```text
66 6c 61 67 7b 32 30 32 33 33 32 36 30 37 37 38
38 39 30 39 36 33 38 30 7d 07 07 07 07 07 07 07
```

转成 ASCII 后就是：

```text
flag{2023326077889096380}\x07\x07\x07\x07\x07\x07\x07
```

去掉末尾的 PKCS#7 padding 后，直接得到：

```text
flag{2023326077889096380}
```

## 7. 为什么说校验逻辑有问题

如果程序逻辑正确，那么它应该比较：

```text
hex(DES-ECB(candidate, key))
```

和：

```text
预先保存的密文 hex
```

但这个 APK 实际保存的并不是“密文 hex”，而是：

```text
明文 flag 加 padding 之后的 hex
```

我用恢复出的 key `12345678` 对：

```text
flag{2023326077889096380}\x07\x07\x07\x07\x07\x07\x07
```

做真正的 DES-ECB 加密，得到的密文是：

```text
b05ee26625e3964694d75a9909293fb4d1b5adb1c3bde558edf967ea6f13b4bc
```

而程序里存储的目标值却是：

```text
666c61677b323032333332363037373838393039363338307d07070707070707
```

二者完全不同。

也就是说，程序实际变成了：

```text
hex(DES(candidate)) == hex(plaintext_flag_with_padding)
```

等价于要求：

```text
DES(candidate) == plaintext_flag_with_padding
```

再把右边这串数据强行做 DES 解密，会得到：

```text
6189cf824b331205318247e73cbcd9f8443bd9f01aa4329dfe9359661462e078
```

这不是合法的 UTF-8 字节流，因此在 Android `EditText -> GetStringUTFChars`
这条正常输入路径下，并不是一个现实可输入、可稳定构造的候选值。

## 8. 可行性判断

结论分成两部分：

1. 能不能从附件直接出 flag？

可以。因为 so 里直接保存了 `flag + padding` 的 hex，解码后即可恢复 flag。

2. 能不能按 APK 当前逻辑正常输入通过校验？

基本不行。因为开发者本应保存“密文 hex”，但实际保存成了“明文 hex”，导致比较逻辑前后不一致。

## 9. 复现脚本

目录中已经放好复现脚本：

[`solve.py`](/D:/桌面/yuwang/re/DES加密验证/solve.py)

脚本会输出：

- 提取出的 DES key
- 程序中存储的目标 hex
- 直接恢复出的 flag
- 正确 DES 密文与存储值不一致的证据
- 反向推导出的字节流不是合法 UTF-8 的证据

在 WSL 中运行：

```bash
cd /mnt/d/桌面/yuwang/re/DES加密验证
python3 solve.py
```

## 10. 最终答案

```text
flag{2023326077889096380}
```
