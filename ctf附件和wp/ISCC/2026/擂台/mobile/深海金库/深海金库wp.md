# 深海金库 (Deep Sea Gold Vault)

| 项目 | 内容 |
|------|------|
| 题目 | 深海金库 |
| 分值 | 150 |
| 作者 | admin |
| 分类 | Mobile |
| 来自 | ISCC |

> 你在马里亚纳海沟的一艘废弃潜水器中发现了一个密封的金库。金库的显示屏上只有一行跳动的乱码和一张磨损的海螺照片。潜水器的操作指南上写着："秘密深藏于耐心之中，而开启的旋律会随深度起伏。"

---

## 最终 Flag

```
ISCC{n2R#7_pQ!9vL*5mWnp}
```

---

## 解题思路

本题的核心链条分为四层：

1. **入口触发条件** — 点击 3 次按钮后长按，绕过"烟雾弹"逻辑
2. **Java 层字符变换** — `CryptoEngine.performTransformation()`
3. **Native 层 Fibonacci XOR** — `process_fib_stream()`
4. **Native 层自定义 Base64 编码校验** — 与常量 `"cUdltutGeWWIUm+7OE4ce3wi"` 比较

逆向过程就是逐层反解。

---

### 1. APK 解包与入口分析

使用 `apktool` 或 `jadx` 解包 `app-release-01.apk`，主要类位于 `com.example.mobile02`：

```
com.example.mobile02
├── MainActivity              — 主 Activity，加载 native 库
├── FlagValidator             — 格式校验 & 最终校验入口
├── CryptoEngine              — Java 层字符变换
├── SecurityCoreProcessor     — 长按监听器，触发真正校验
├── SystemEnvironmentManager  — 点击计数 & 调试器检测
├── CoreProtocolDelegate      — 反射绑定长按事件
└── SecurityProvider          — 假的 "安全哈希"（烟雾弹）
```

`MainActivity` 在静态代码块中加载 native 库：

```java
static {
    System.loadLibrary("secure_verify");
}
```

并声明 native 方法：

```java
public native boolean nativeVerify(byte[] data);
```

---

### 2. 绕过假逻辑：点击 → 长按的触发链

#### 2.1 按钮点击是烟雾弹

按钮的 `OnClickListener` 绑定在 `MainActivity$ExternalSyntheticLambda1`，点击后：

1. `SystemEnvironmentManager.updateState()` — 原子计数器 +1
2. `SystemEnvironmentManager.prepareContext(button, longClickListener)` — 条件触发入口
3. Toast 显示 `"Initializing Secure Handshake..."`
4. 延迟 1 秒后调用 `SecurityProvider.computeSecureHash(input)`，无论输入什么，都弹出：
   ```
   Signature Error: [xxxxxxxx] Mismatch
   ```

**注意**：`SecurityProvider` 只是做 SHA-256 截断，这个 Toast 完全是烟雾弹，根本不会进入 flag 校验。

#### 2.2 真正校验的条件

`SystemEnvironmentManager.prepareContext()` 有两个条件：

```java
public static void prepareContext(View view, OnLongClickListener listener) {
    if (!Debug.isDebuggerConnected()          // 条件1：不能挂调试器
        && CLICK_TRIGGER.get() >= 3) {        // 条件2：点击次数 >= 3
        CoreProtocolDelegate.dispatchConfiguration(view, listener);
    }
}
```

#### 2.3 反射绑定长按

`CoreProtocolDelegate.dispatchConfiguration()` 通过 char 数组拼接出方法名：

```java
char[] name = {
    's','e','t','O','n','L','o','n','g','C','l','i','c','k','L','i','s','t','e','n','e','r'
};
// => "setOnLongClickListener"
```

然后通过反射调用 `button.setOnLongClickListener(listener)`，将 `SecurityCoreProcessor` 绑定为长按监听器。

#### 2.4 长按触发真正校验

`SecurityCoreProcessor.onLongClick()`：

1. 获取 `EditText` 输入
2. `FlagValidator.isFormatValid()` 检查格式：必须以 `"ISCC{"` 开头、以 `"}"` 结尾
3. `FlagValidator.doFinalCheck(activity, input)` 提取花括号内内容，送入 `CryptoEngine` 变换后，再交给 `native nativeVerify()`

---

### 3. Java 层变换：CryptoEngine.performTransformation()

Smali 代码还原为 Java：

```java
public static byte[] performTransformation(String input) {
    byte[] data = input.getBytes(StandardCharsets.US_ASCII);
    int prev = 0;
    for (int i = 0; i < data.length; i++) {
        int ch = data[i] & 0xFF;
        if (ch >= 0x20 && ch <= 0x7E) {
            ch = ((ch - 0x19) % 0x5F) + 0x20;  // 可打印字符做循环移位
        }
        int delta = (i % 2 == 0) ? 8 : -8;
        ch = (ch + delta + (prev % 4)) & 0xFF;
        prev = ch;
        data[i] = (byte) ch;
    }
    return data;
}
```

变换两步：

- **可打印字符轮换**：在 ASCII 0x20~0x7E 范围内做 `((ch - 0x19) % 0x5F) + 0x20`
- **增量累加**：加上位置决定的 delta（偶数位 +8，奇数位 -8）和上一个输出字节的低 2 位

Python 正向变换：

```python
def java_transform(data):
    out = bytearray(data)
    prev = 0
    for i in range(len(out)):
        ch = out[i]
        if 0x20 <= ch <= 0x7E:
            ch = ((ch - 0x19) % 0x5F) + 0x20
        delta = 8 if i % 2 == 0 else -8
        prev = (ch + delta + (prev % 4)) & 0xFF
        out[i] = prev
    return out
```

---

### 4. Native 层分析

`libsecure_verify.so` 中 `SV::v()` 函数做了两步：

#### 4.1 Fibonacci XOR

```cpp
void process_fib_stream(unsigned char* buf, int len) {
    int a = 1, b = 1;
    for (int i = 0; i < len; i++) {
        buf[i] ^= (a & 0xFF);
        int next = a + b;
        a = b;
        b = next;
    }
}
```

斐波那契序列起始 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233...，取低 8 位与字节异或。

因为 XOR 是自逆运算，所以正向函数可以直接用于逆向：

```python
def fib_xor(buf):
    out = bytearray(buf)
    a, b = 1, 1
    for i in range(len(out)):
        out[i] ^= a & 0xFF
        a, b = b, (a + b) & 0xFFFFFFFF
    return out
```

#### 4.2 自定义 Base64

字母表（从 `.so` 中 `0x14e96` 偏移处提取）：

```
zKJUExRaVtM3Ydv5TQIsWD1frnHC78Lckl6euPh9AGoj0SgN4Zp+OwXi2F/ybmBq
```

标准 Base64 字母表是 `A-Za-z0-9+/`，这里完全不同。编码后的目标常量：

```
cUdltutGeWWIUm+7OE4ce3wi
```

### 5. 逆向计算

逆向流程就是正向的三步依次逆回：

```
 target (custom base64)
      ↓ custom_b64_decode()
 bytearray
      ↓ fib_xor()            ← XOR 自逆
 bytearray
      ↓ inverse_java_transform()
 inner string
      ↓ 加 ISCC{}
 flag
```

**Step 1：自定义 Base64 解码**

```python
# alphabet 查表
"cUdltutGeWWIUm+7OE4ce3wi"
→ bytes: 7c 33 61 26 42 69 8d 45 12 0f dc dc d0 4c 1f 8c bd 77
```

**Step 2：逆 Fibonacci XOR**

用同一函数再做一次 XOR（自逆）：

```python
fib_xor(step1)
→ bytes: 7d 32 63 25 47 61 50 30 38 85 4c 39 35 7d 57 80 6f
```

**Step 3：逆 Java 变换**

```python
def inverse_java_transform(buf):
    prev = 0
    out = bytearray()
    for i, ob in enumerate(buf):
        delta = 8 if i % 2 == 0 else -8
        temp = (ob - delta - (prev % 4)) & 0xFF
        if 0x20 <= temp <= 0x7E:
            ch = ((temp - 39) % 95) + 32
        else:
            ch = temp
        out.append(ch)
        prev = ob
    return out.decode("ascii")
```

得到花括号内内容：

```
n2R#7_pQ!9vL*5mWnp
```

**最终 Flag：**

```
ISCC{n2R#7_pQ!9vL*5mWnp}
```

---

### 6. 校验确认

将得到的 flag 内层重新执行正向流程：

```
inner = "n2R#7_pQ!9vL*5mWnp"
  → java_transform() → fib_xor() → custom_b64_encode()
  → "cUdltutGeWWIUm+7OE4ce3wi"  ✅ 匹配
```

---

## 总结

本题的有趣之处在于：

| 要点 | 说明 |
|------|------|
| **反调 & 触发隐藏** | 需要点击 3 次 + 长按，普通点击只会触发假错误提示 |
| **反射绑定** | `setOnLongClickListener` 通过 char 数组拼接，避免静态分析直接看到 |
| **双层校验** | Java 层做字符变换，Native 层做 Fib XOR + 自定义 Base64 |
| **自定义 Base64** | 字母表完全替换，不能直接用标准库解码 |

---

## 参考

- 完整 exp 见同目录下 `深海金库exp.py`
- 运行 `python 深海金库exp.py` 可直接输出 flag
