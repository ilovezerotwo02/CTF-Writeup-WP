# 像素中的秘密 (Secrets in Pixels) — Writeup

## 题目信息

- 分类：MISC
- 难度：高级（350分）
- 附件：`image_06.zip` → `image_06.png`

## 一、文件结构分析

### 1.1 ZIP 结构

ZIP 中仅包含一个文件：`image_06.png`，无加密，无额外文件。

### 1.2 PNG 结构分析

使用 `pngcheck` / 手工解析 PNG 块结构：

| 偏移 | 块类型 | 长度 | CRC | 说明 |
|------|--------|------|-----|------|
| 0x00 | PNG Sig | 8 | — | 标准 PNG 签名 |
| 0x08 | IHDR | 13 | 0x250BE689 | 64×64, 8-bit RGB |
| 0x21 | IDAT | 124 | 0x65288373 | zlib 压缩的图像数据 |
| 0xA9 | IEND | 0 | 0xAE426082 | 标准结束标记 |
| 0xB5 | **tail** | **64** | — | **IEND 之后的额外数据** |

**关键发现：IEND 之后存在 64 字节额外数据。** ExifTool 明确指出：
> Warning: [minor] Trailer data after PNG IEND chunk

### 1.3 图像像素数据

- 解压 IDAT → 12352 字节（64 × (1+64×3)）
- 过滤类型：第 0 行使用 Filter 1 (Sub)，第 1-63 行使用 Filter 2 (Up)
- 所有像素均为纯白 (255, 255, 255)
- 过滤后的数据完全是纯白图的正常编码结果
- Adler-32 校验和匹配正常

### 1.4 尾随 64 字节

```
十六进制:
0000000069cb34428ca630e2b4556568f38812932fb5eb592e5e2b53c3f80a8d5e751fb7bf038898bf0231645bb257caa18c7b9e6580dfb269b48306ad28679a

字节分布:
- 信息熵: 5.62 bits/byte (最大值 6.0)
- 前 4 字节: 0x00000000 (全零)
- 唯一字节数: 58/64 个字节值出现
```

**高熵（5.62 bits/byte）表明数据为加密或随机数据，非明文文本。**

## 二、已尝试的提取方法

### 2.1 标准隐写工具

| 工具 | 结果 |
|------|------|
| `zsteg -a` | 未发现任何 LSB 隐写数据 |
| `steghide` | 图片格式不支持（64×64 太小） |
| `binwalk` | 工具故障，未完成 |
| `exiftool` | 仅报告尾随数据警告 |
| `strings` | 只有块类型名称和少量随机字符 |

### 2.2 XOR 解密尝试

- **单字节 XOR**（256 个密钥）：无一产生 `flag{...}` 可读文本
- **多字节重复 XOR**：尝试了 `flag{`、`image_06`、`pixel`、`secret`、`PNG`、`IHDR`、`IDAT`、`IEND` 等密钥
- **CRC 派生密钥 XOR**：使用 IHDR/IDAT/IEND 的 CRC 值（0x250BE689, 0x65288373, 0xAE426082）
- **图像数据派生密钥**：使用过滤字节模式 `[1,2,2,...,2]` 和纯白像素的 SHA-256
- **位置相关 XOR**：`tail[i] XOR i`、`tail[i] XOR (63-i)`

### 2.3 AES 解密尝试

- 模式：ECB、CBC、CTR
- 密钥来源：
  - PNG CRC 值
  - SHA-256(图像像素数据)
  - SHA-256(解压 IDAT)
  - SHA-256(challenge_name)
  - PBKDF2(password) + 零 salt
- 密文配置：全 64 字节 / 后 32 字节 / 前 32 字节
- IV 配置：全零 / 尾数据前 16 字节

### 2.4 图像渲染尝试

| 渲染方式 | 结果 |
|----------|------|
| 8×8 灰度图 | 随机噪声 |
| 32×16 / 16×32 位图 | 随机噪声 |
| 64×8 / 8×64 位图 | 随机噪声 |
| 64×64 重复 XOR | 均匀条纹（无文字） |
| 坐标散点图 | 分散点，无图案 |
| 柱状图（行/列） | 无可见文字 |
| 极坐标图 | 无可见图案 |
| LSB 嵌入图 | 无明显变化 |
| 绘图指令模拟 | 随机路径 |

### 2.5 其他技术

- **字节变换**：ROL/ROT/ADD/SUB/MUL/255-complement
- **差分分析**：前后差值
- **哈希匹配**：常见 flag 候选的 SHA-512 与尾数据对比
- **Base64/Base32/Ascii85 范围检测**：不符合
- **PNG 过滤反演**：Sub/Up 逆过滤 (bpp=1,2,3,4,8)
- **矩阵置换**：行列主序、Zigzag 序
- **zlib 结构分析**：动态 Huffman，无异常存储块

## 三、结论

### 3.1 确认的事实

1. `image_06.png` 在 IEND 之后**确实隐藏了 64 字节数据**
2. 可以**稳定且完整地提取**这 64 字节
3. 图像本身为**纯白 64×64 RGB PNG**，像素中不含隐写信息
4. 尾随 64 字节具有**高熵特征**，呈现加密/随机数据特征
5. 所有常见的隐写解码方法（XOR、AES、位图渲染、坐标映射等）**均无法产生可读的 flag{...} 文本**

### 3.2 无法确定 flag 的可能原因

| 原因 | 可能性 | 说明 |
|------|--------|------|
| 缺少其他图片 | **高** | 文件名是 `image_06`，题面说"每张图"，可能需要 image_01-05 组成完整 flag |
| 缺少解密密钥 | **高** | 64 字节是加密数据，密钥可能来自其他图片或题目提示 |
| 自定义编码 | **中** | 可能使用了非标准的自定义编码方案，需要额外信息 |
| 需要特定工具 | **低** | 某些商业/专用隐写工具可能有特定解码能力 |

### 3.3 建议

1. **确认是否有其他附件**（image_01~05）需要联合解密
2. **查看 CTF 平台是否有提示**（hint 功能）
3. **检查题目描述**中是否有遗漏的密码/密钥信息
4. 如果确有密钥，使用 `cryptography` 库进行 AES-256-CBC 解密，密钥为 SHA-256(密钥字符串)

## 四、提取脚本

```python
# extract_tail.py - 提取 IEND 之后的隐藏数据
import struct

def extract_png_tail(path):
    data = open(path, 'rb').read()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError("Not a valid PNG")
    
    offset = 8
    while offset + 8 <= len(data):
        length = struct.unpack('>I', data[offset:offset+4])[0]
        chunk_type = data[offset+4:offset+8]
        offset += 12 + length
        if chunk_type == b'IEND':
            break
    
    tail = data[offset:]
    print(f"Extracted {len(tail)} bytes after IEND")
    print(f"Hex: {tail.hex()}")
    return tail

tail = extract_png_tail('image_06.png')
# 64 bytes: 0000000069cb34428ca630e2b4556568f38812932fb5eb592e5e2b53c3f80a8d5e751fb7bf038898bf0231645bb257caa18c7b9e6580dfb269b48306ad28679a
```

## 五、文件清单

| 文件 | 说明 |
|------|------|
| `image_06.png` | 原始 PNG (245 bytes) |
| `image_06.zip` | 原始压缩包 |
| `image_06_end.txt` | 尾随 64 字节的十六进制 |
| `extract_image_06_overlay.py` | 尾随数据提取脚本 |
| `analysis/` | 各种分析生成的图像和中间数据 |
| `*_scaled.png` | 各种渲染图像的放大版本 |

---

**最终判断：在当前仅有 image_06.png 的条件下，无法唯一确定最终 flag{...}。** 最可能缺少的条件是：（1）同系列的其他图片（image_01-05），或（2）解密所需的密钥/密码。
