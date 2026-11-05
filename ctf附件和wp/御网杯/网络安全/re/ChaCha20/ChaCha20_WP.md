# ChaCha20 Writeup

## 1. 题目信息

- 题目：ChaCha20
- 分类：REVERSE
- 难度：初级
- 分值：150
- 附件：CrackMe_1_1.apk

## 2. Java 层分析

JADX 反编译 APK，入口在 `MainActivity`：

```java
public void m128lambda$onCreate$0$comcrmyapplicationMainActivity(View anchor) {
    String candidate = this.inputFlag.getText().toString();
    boolean ok = NativeBridge.c(candidate);
    if (ok) {
        startActivity(new Intent(this, (Class<?>) SuccessActivity.class));
    } else {
        Snackbar.make(anchor, "flag错误", -1).show();
    }
}
```

实际校验函数是 `NativeBridge.c(String)`。

## 3. Native 层分析

`libmyapplication.so` 中通过 `JNI_OnLoad` 动态注册了 3 个 native 方法：

| Java 名 | 签名 | native 地址 |
|---------|------|------------|
| `a` | `([B)[B` | `0x25090` |
| `b` | `([B)[B` | `0x251d0` |
| `c` | `(Ljava/lang/String;)Z` | `0x25310` |

`ab/cd/dc` 等 Java 声明并未注册，属于干扰项。

## 4. `c(String)` 核心逻辑（地址 0x25310）

```
1. GetStringUTFChars → 获取用户输入 UTF-8 字节
2. std::string 构造
3. ReleaseStringUTFChars
4. std::string::data() / size() 获取数据指针和长度
5. 调用 0x25720 → ChaCha20 异或 (IETF 变体)
6. 调用 0x27510 → hex 编码 (查表 "0123456789abcdef")
7. 遍历目标字符串数组 (位于 GOT+0x127c)，逐一比对
```

校验逻辑等价于：

```
hex(ChaCha20(input)) == target
```

## 5. ChaCha20 参数提取

### 5.1 ChaCha20 常量确认

地址 `0x26ca0` 是 ChaCha20 block 函数，硬编码了标准常量：

```
"expand 32-byte k"
```

round 循环次数为 10（20 轮），为标准 ChaCha20。

### 5.2 参数地址计算

在 `0x25720`（ChaCha20 XOR 函数）中，GOT 基址计算：

```
pop ebx                    ; PC = 0x25731
add ebx, 0x3379f           ; ebx = 0x58ed0 (GOT base)
```

Key 加载：

```
lea ecx, [ebx - 0x49c05]   ; key = 0x58ed0 - 0x49c05 = 0xf2cb
call 0x27100                ; 恒等函数, 返回 key 指针
```

Nonce 加载：

```
lea ecx, [ebx - 0x49be5]   ; nonce = 0x58ed0 - 0x49be5 = 0xf2eb
call 0x27110                ; 恒等函数, 返回 nonce 指针
```

Counter 初始值：

```
mov dword ptr [ebp - 0x58], 1   ; counter = 1
```

### 5.3 从 .so 提取参数

| 参数 | 文件偏移 | 字节 |
|------|---------|------|
| key (32 bytes) | 0xf2cb | `149263a16f2d89cbf0375b1ca94e78d3226017ee9abc4d0853e1762a8dc4903f` |
| nonce (12 bytes) | 0xf2eb | `44332211abcdef668899aa55` |
| counter | — | 1 |

### 5.4 目标字符串

.rodata 中 `0xce9c` 处：

```
d097c3f6d23a8577e1
```

## 6. 求解

ChaCha20 是流密码（XOR 对称），因此：

```
plaintext = ChaCha20(key, nonce, counter) XOR unhex(target)
          = ChaCha20(key, nonce, counter) XOR ciphertext
```

目标 hex 解码得到 9 字节密文，ChaCha20 XOR 解密即得明文。

### 运行结果

```
target hex: d097c3f6d23a8577e1
key hex   : 149263a16f2d89cbf0375b1ca94e78d3226017ee9abc4d0853e1762a8dc4903f
nonce hex : 44332211abcdef668899aa55
counter   : 1
plain hex : 666c61677b716a667d
flag      : flag{qjf}
```

## 7. Flag

```
flag{qjf}
```

## 8. 解题脚本

见 [solve_chacha20.py](D:\桌面\yuwang\re\ChaCha20\solve_chacha20.py)
