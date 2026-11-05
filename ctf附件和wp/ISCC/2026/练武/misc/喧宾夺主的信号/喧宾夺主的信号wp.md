# 喧宾夺主的信号 — MISC WriteUp

## 题目信息

| 项目 | 内容 |
|------|------|
| **题目** | 喧宾夺主的信号 |
| **类型** | MISC（杂项） |
| **分值** | 200 |
| ** solves** | 1909 |
| **附件** | `attachment-17.pcapng` |

---

## 题目描述

网络管理员抓取到了一段可疑的网络流量，但其中绝大部分都是某台被攻陷的摄像头在持续广播的垃圾组播流量。据说，攻击者的秘密指令就隐藏在这片嘈杂的信号中，但直接分析这些数据包只会让你陷入无限循环的迷宫。

**提示**：或许在那些看似无意义的广播中，藏着打开真正宝藏的钥匙。

**声东击西**——三十六计第一套第六计，是解开本题的关键。

---

## 解题思路

### Step 1：流量分析

使用 Scapy 读取 pcap 文件：

```
from scapy.all import *
packets = rdpcap("attachment-17.pcapng")
print(f"Total packets: {len(packets)}")
# 1509 total: 1500 UDP + 9 TCP
```

流量共 **1509 个包**：
- **1500 个 UDP 包** → 全部发往 `239.255.255.250:1900`（SSDP 组播），每包 payload 固定 28 字节
- **9 个 TCP 包** → `192.168.1.100` 与 `45.78.1.1` 之间的通信

**"声东击西"**：UDP 组播是"东"（噪声），TCP 才是"西"（真正的攻击指令）。

---

### Step 2：从 TCP 中提取加密 ZIP

过滤出带 Raw 载荷的 TCP 包，发现一个 HTTP POST 请求：

```
POST /command HTTP/1.1
Host: 45.78.1.1
Content-Type: application/json
Content-Length: 680

{"instruction": "UEsDBBQAAQBjACBEdFyjQiCBSgEAANkBAAAJAAsAaW1hZ2UucG5nAZkHAAEAQUUD...",
 "note": "This is the real command."}
```

提取 `instruction` 字段（base64 编码），解码后得到一个 **AES 加密的 ZIP 文件**（compress_type=99），内含 `image.png`。

---

### Step 3：从 UDP 组播中提取密码

> **"或许在那些看似无意义的广播中，藏着打开真正宝藏的钥匙。"**

遍历 1500 个 UDP 包，发现其中 **4 个包**的 base64 payload 带有 `=` 填充符（分别位于第 200、500、800、1100 个 UDP 包），内容均为：

```
U2hlbmdEb25nSmlYaUAzNi0xLTY=
```

解码后得到：**`ShengDongJiXi@36-1-6`**

这是极具巧思的密码设计：
- `ShengDongJiXi` → "**声东击西**"的拼音
- `36-1-6` → 三**十六**计**第**一**套**第**六**计

---

### Step 4：解密 ZIP 获取隐写图片

使用密码 `ShengDongJiXi@36-1-6` 解密 ZIP，得到 `image.png`。

图片特征：
- 尺寸：**100 × 100** 像素
- 模式：**RGB**
- 颜色数：仅 **8 种颜色**
- 各通道值相差仅为 **1**（如 72/73、108/109、136/137）

这是典型的 **LSB（Least Significant Bit）隐写**：8 种颜色 = 3 bits/像素，正好对应 R、G、B 三个通道的 LSB。

| 像素值 (R,G,B) | R LSB | G LSB | B LSB |
|---------------|:-----:|:-----:|:-----:|
| (72, 108, 136) | 0 | 0 | 0 |
| (72, 108, 137) | 0 | 0 | 1 |
| (72, 109, 136) | 0 | 1 | 0 |
| (72, 109, 137) | 0 | 1 | 1 |
| (73, 108, 136) | 1 | 0 | 0 |
| (73, 108, 137) | 1 | 0 | 1 |
| (73, 109, 136) | 1 | 1 | 0 |
| (73, 109, 137) | 1 | 1 | 1 |

---

### Step 5：LSB 提取 Flag

遍历每个像素，依次提取 R、G、B 通道的 LSB，每 8 位组成一个字节：

```python
bits = []
for r, g, b in pixels:
    bits.append(str(r & 1))  # R 通道 LSB
    bits.append(str(g & 1))  # G 通道 LSB
    bits.append(str(b & 1))  # B 通道 LSB

# 每 8 bit 转为字节
flag_bytes = bytes(int(''.join(bits[i:i+8]), 2)
                   for i in range(0, len(bits) - 7, 8))
```

最终得到 Flag：

```
ISCC{1d3f1c44t10n_1s4_th3_k3y_t0_v1cmtc0Fry}
```

---

## 总结

| 步骤 | 关键点 | 工具/库 |
|:----:|--------|:-------:|
| 1 | 流量分类，识别"声东击西"模式 | Scapy |
| 2 | TCP 中提取 base64 → AES ZIP | — |
| 3 | UDP 广播中找 `=` 填充，base64 解码得密码 | base64 |
| 4 | AES-256 解密 ZIP → image.png | pyzipper |
| 5 | RGB 三通道 LSB 隐写提取 flag | Pillow |

---

**Flag:** `ISCC{1d3f1c44t10n_1s4_th3_k3y_t0_v1cmtc0Fry}`
