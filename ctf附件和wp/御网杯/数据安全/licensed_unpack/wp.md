# licensed_unpack 题解

## 一、拿到文件后的第一判断

附件里真正的目标只有一个：[licensed.exe](/D:/桌面/yuwang/数据安全/licensed_unpack/tempdir/REVERSE附件/licensed.exe)。

先做最基础的 PE 结构检查，可以看到几个很扎眼的点：

- 节名是 `.UPX0 / .UPX1`
- 文件内存在 `FPX!`
- 程序体积极小，只有 `2048` 字节
- 导入表几乎是空的

第一眼非常像 UPX，但这里有个反常识的地方：正常 UPX 会留下 `UPX!`，这里故意变成了 `FPX!`。  
如果只是“改一个字节防止工具识别”，那把它改回去应该能直接脱壳；但实际测试并不是这样。

## 二、为什么说这是“假壳”

我分别拿了多版 UPX 做验证：

- `upx-ucl 4.2.2`
- 官方 `upx 4.2.4`
- 更老的 `upx 1.24 / 1.25`

把 `FPX!` 修回 `UPX!` 之后继续测试，结论一致：

```text
file is possibly modified/hacked/protected; take care!
```

也就是说，这个程序不是“普通的 UPX 加壳样本”，而是**故意伪装成 UPX 外形的假壳**。

再跟一下入口点，会发现它确实会先把一段数据复制到 `.UPX0` 再跳转执行，但跳过去之后并不会进入正常的 UPX 解压流程，而是立刻落入一段被篡改过的伪逻辑里。

所以这题真正要做的事情不是“硬脱壳”，而是：

1. 识别伪装
2. 放弃标准 UPX 解包思路
3. 转而恢复壳里隐藏的真实数据

## 三、核心思路转向：恢复隐藏数据

既然正常脱壳走不通，那就把注意力从“壳”转移到“数据”本身。

题目描述里有一句很关键：

> 关键校验逻辑和敏感数据都没有以明文形式暴露

这说明最终 flag 很可能不是运行时交互求出来的，而是**程序里藏着一段固定密文**，只不过经过了伪装。

继续还原后，可以定位出两段关键数据：

```text
key = d1db19c8a2e38c60c1518b0301c8d7ea
ct  = bdd6d58928d8b2427410d6a9a41f5ad63c1ad4bfd555cc714d1615bb8931b48f7ff81240b075048ae644fe513b1120d7
```

长度也很规整：

- `key` 为 `16` 字节
- `ct` 为 `48` 字节

这非常像一个典型的分组密码场景。

## 四、算法确认

接下来对常见对称算法做快速验证，最终命中的是：

- 算法：`Blowfish`
- 模式：`ECB`

把上面的 `key` 和 `ct` 代入后，解出来的明文就是：

```text
flag{b301cd43-2918-4c96-bc1e-0e6addbe3ef3}
```

## 五、exp

我把可直接运行的脚本整理成了：

- [exp.py](/D:/桌面/yuwang/数据安全/licensed_unpack/exp.py)

代码如下：

```python
from Crypto.Cipher import Blowfish


def main() -> None:
    key = bytes.fromhex("d1db19c8a2e38c60c1518b0301c8d7ea")
    ciphertext = bytes.fromhex(
        "bdd6d58928d8b2427410d6a9a41f5ad6"
        "3c1ad4bfd555cc714d1615bb8931b48f"
        "7ff81240b075048ae644fe513b1120d7"
    )

    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    plaintext = cipher.decrypt(ciphertext)
    print(plaintext.rstrip(b\"\\x00\").decode())


if __name__ == \"__main__\":
    main()
```

运行结果：

```text
flag{b301cd43-2918-4c96-bc1e-0e6addbe3ef3}
```

## 六、最终结论

这道题的关键不在于“真的把 UPX 脱掉”，而在于先识别出它是**假壳**：

- 外形故意模仿 UPX
- 但内部不是标准可解包结构
- 真正的考点是恢复出隐藏的密钥与密文
- 最后通过 `Blowfish-ECB` 解出固定 flag

## 七、flag

```text
flag{b301cd43-2918-4c96-bc1e-0e6addbe3ef3}
```
