# mobile 题解 WP

## 题目附件

- `app-release-01.apk`

## 最终 Flag

`ISCC{n2R#7_pQ!9vL*5mWnp}`

## 解题思路

这题的核心不是直接点击按钮，而是先绕过 Java 层的假逻辑，再进入真正的 native 校验。

### 1. 入口定位

先解包 APK，重点看几个类：

- `com.example.mobile02.MainActivity`
- `com.example.mobile02.FlagValidator`
- `com.example.mobile02.CryptoEngine`
- `com.example.mobile02.SecurityCoreProcessor`
- `com.example.mobile02.SystemEnvironmentManager`
- `libsecure_verify.so`

`MainActivity` 在静态初始化里加载了 native 库：

```java
System.loadLibrary("secure_verify");
```

同时声明了 native 方法：

```java
public native boolean nativeVerify(byte[] data);
```

### 2. 按钮点击是烟雾弹

`MainActivity` 里普通点击按钮后，只会：

1. `SystemEnvironmentManager.updateState()` 计数加一
2. Toast 提示 `Initializing Secure Handshake...`
3. 1 秒后对输入做 `SecurityProvider.computeSecureHash()`
4. 弹出假提示：

```text
Signature Error: [xxxxxxxx] Mismatch
```

也就是说正常点击路径根本不会校验 flag。

### 3. 真正触发校验的条件

`SystemEnvironmentManager.prepareContext()` 的逻辑是：

- 不能挂调试器：`!Debug.isDebuggerConnected()`
- 点击计数 `CLICK_TRIGGER >= 3`

满足后，`CoreProtocolDelegate.dispatchConfiguration()` 会通过反射调用：

```java
setOnLongClickListener(...)
```

反射拼出来的方法名是：

```text
setOnLongClickListener
```

所以真实操作链是：

1. 先点按钮 3 次
2. 再长按按钮

长按后进入 `SecurityCoreProcessor.onLongClick()`，这里才会真正调用：

```java
FlagValidator.doFinalCheck(activity, input)
```

### 4. flag 格式校验

`FlagValidator.isFormatValid()` 要求：

```text
以 ISCC{ 开头
以 } 结尾
```

所以 flag 形如：

```text
ISCC{...}
```

`doFinalCheck()` 会取出花括号中的内容：

```java
input.substring(5, input.length() - 1)
```

然后送入：

```java
CryptoEngine.performTransformation(...)
```

得到字节数组后再喂给：

```java
nativeVerify(...)
```

### 5. Java 层变换

`CryptoEngine.performTransformation()` 的逻辑可以还原为：

```python
for i, ch in enumerate(data):
    if 0x20 <= ch <= 0x7e:
        ch = ((ch - 0x19) % 0x5f) + 0x20

    delta = 8 if i % 2 == 0 else -8
    ch = (ch + delta + (prev % 4)) & 0xff
    prev = ch
```

这一步得到中间字节流，随后交给 native。

### 6. native 校验逻辑

在 `libsecure_verify.so` 中，`nativeVerify()` 最终会调用：

```cpp
SV::v(unsigned char const*, int)
```

`SV::v` 做了两件事：

#### 6.1 Fibonacci 异或

调用 `process_fib_stream(buf, len)`，按斐波那契序列异或：

```python
a, b = 1, 1
for i in range(len(buf)):
    buf[i] ^= (a & 0xff)
    a, b = b, a + b
```

前几个异或值为：

```text
1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...
```

#### 6.2 自定义 Base64 编码并比较

随后调用 `encode_b64()`，其字母表不是标准 Base64，而是：

```text
zKJUExRaVtM3Ydv5TQIsWD1frnHC78Lckl6euPh9AGoj0SgN4Zp+OwXi2F/ybmBq
```

编码后结果会和常量字符串比较：

```text
cUdltutGeWWIUm+7OE4ce3wi
```

所以 native 校验条件等价于：

```text
custom_b64(process_fib_stream(CryptoEngine(inner_flag))) == "cUdltutGeWWIUm+7OE4ce3wi"
```

### 7. 反推输入

把目标串先用自定义 Base64 解码，得到：

```text
7c33612642698d45120fdcdcd04c1f8cbd77
```

再逆一次 Fibonacci 异或，得到 Java 层输出：

```text
7d326325476180503038854c39357d57806f
```

最后逆 `CryptoEngine.performTransformation()`，恢复出花括号内内容：

```text
n2R#7_pQ!9vL*5mWnp
```

因此完整 flag 为：

```text
ISCC{n2R#7_pQ!9vL*5mWnp}
```

## 复现脚本

本目录下提供了 `solve.py`，运行即可输出 flag 并做一次正向校验。

## 总结

这题的关键点有三个：

1. 普通点击路径是假的，只负责制造“校验失败”的错觉
2. 真正校验入口藏在“点 3 次后长按”的反射绑定里
3. native 没有特别重的混淆，本质是 `Fibonacci XOR + 自定义 Base64` 的常量比对
