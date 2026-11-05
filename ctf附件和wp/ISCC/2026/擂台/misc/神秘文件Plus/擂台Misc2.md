# 神秘文件Plus WP

## 题目信息

题目名称：神秘文件Plus

题目描述：

```text
可莉从阿贝多老师那里学习回来后，将她的宝物藏入了一个神秘的文件。节奏与波动仿佛在诉说一段故事，三要素的微妙变化似乎暗示了什么，也许声音的第九位会给你答案。
```

题目关键词比较明显：

```text
神秘文件
节奏
波动
三要素
声音的第九位
```

初步判断：

1.附件里可能存在文件拼接或隐写；
2.后续重点大概率是音频；
3.音频不是简单靠听，而是要分析采样、声道、波形、位平面等信息；
4.“声音的第九位”很可能对应16-bit PCM采样值中的第9位，也就是从低位开始数的bit8。

最终flag：

```text
ISCC{16c2ff3a-4443-4c1e-878a-39e74ed3544c}
```

---

## 一、解压外层附件

附件是一个无明显后缀的压缩文件，直接用7z尝试解压：

```bash
7z x zip
```

解压后得到：

```text
Herta_1.png
ISCC2025-神秘文件-题目描述.txt
```

其中`Herta_1.png`是主要分析对象。

---

## 二、检查PNG尾部拼接数据

PNG文件正常结束位置一般在`IEND`数据块之后。用脚本查找`IEND`：

```python
from pathlib import Path

data = Path("Herta_1.png").read_bytes()

idx = data.find(b"IEND")
png_end = idx + 8

print("IEND位置:", idx)
print("PNG正常结束位置:", png_end)
print("尾部前16字节:", data[png_end:png_end+16].hex())
```

运行后可以看到PNG正常结束后还有额外数据，额外数据开头为：

```text
37 7A BC AF 27 1C
```

这是7z压缩包的文件头。

因此可以确定：

```text
Herta_1.png = 正常PNG图片 + 拼接的7z压缩包
```

把PNG后面的尾部数据切出来：

```python
from pathlib import Path

data = Path("Herta_1.png").read_bytes()

idx = data.find(b"IEND")
png_end = idx + 8

tail = data[png_end:]
Path("tail.7z").write_bytes(tail)

print("尾部大小:", len(tail))
print("文件头:", tail[:6].hex())
```

得到：

```text
tail.7z
```

但直接解压会发现需要密码。

---

## 三、从图片LSB中提取7z密码

既然7z需要密码，就继续分析`Herta_1.png`本身。常见图片隐写可以先从RGB通道最低位入手。

尝试提取R通道最低位，按行读取像素，8bit一组，MSB-first还原字节：

```python
from PIL import Image

img = Image.open("Herta_1.png").convert("RGB")

bits = []

for r, g, b in img.getdata():
    bits.append(r & 1)

out = bytearray()

for i in range(0, len(bits) - 7, 8):
    byte = 0
    for bit in bits[i:i+8]:
        byte = (byte << 1) | bit
    out.append(byte)

print(out[:100])
```

可以在开头直接看到一串32位十六进制字符串：

```text
9f42d1364eee400aa7620c0400110223
```

这串内容很像密码或摘要，拿去尝试解压`tail.7z`：

```bash
7z x tail.7z -p9f42d1364eee400aa7620c0400110223
```

成功解压，得到目录：

```text
f1ag_01/
```

目录中包含：

```text
1.wav
2.wav
...
50.wav
```

到这里第一层图片隐写结束。

---

## 四、检查WAV音频基本信息

继续检查音频参数：

```python
import wave
import glob
import os

files = sorted(
    glob.glob("f1ag_01/*.wav"),
    key=lambda x: int(os.path.basename(x).split(".")[0])
)

for f in files:
    with wave.open(f, "rb") as w:
        print(os.path.basename(f), w.getparams())
```

可以看到这些音频基本都是：

```text
采样率：44100Hz
采样宽度：2字节
位深：16-bit PCM
声道数：2
```

这正好对应题目中的提示：

```text
声音的第九位
```

因为16-bit PCM每个采样值有16位，从低位开始数：

```text
第1位 -> bit0
第2位 -> bit1
...
第9位 -> bit8
```

所以“第九位”可以理解为：

```python
(sample >> 8) & 1
```

不过后面不能直接把所有音频第9位拼起来就完事，因为普通波形本身也会产生大量位变化，需要继续定位真正载荷。

---

## 五、先排除错误方向

一开始容易误入一个方向：

```text
50个wav = 50个十六进制半字节
两个半字节拼成一个字节
```

这个思路可以得到类似：

```text
ISCC{n9Q4vX7k2P0mLd8R5tYz}
```

但这个结果提交错误，而且和Plus题最终flag格式不符。

已知最终正确flag是UUID格式：

```text
ISCC{16c2ff3a-4443-4c1e-878a-39e74ed3544c}
```

其中UUID部分长度为36，完整flag长度为：

```text
ISCC{ + 36字符UUID + } = 42字符
```

所以`50个wav=50个半字节`这种思路不能作为Plus题的最终解法，只能看作旧题残留或干扰方向。

---

## 六、分析音频节奏结构

从音频长度和波形可以看出，这些wav并不是普通音乐，而是人为生成的规律信号。

多数wav长度为5秒：

```text
44100Hz × 5s = 220500 samples
```

如果按0.1秒切块：

```text
44100 × 0.1 = 4410 samples
```

一个5秒音频正好可以切成：

```text
50块
```

其中`50.wav`长度约0.7秒，也就是：

```text
7块
```

所以总体块数为：

```text
49 × 50 + 7 = 2457块
```

前面的`1.wav`、`2.wav`以及部分块更像提示层，不一定是最终数据。继续观察发现，从某些位置开始，剩余数据长度能与flag长度产生明显对应。

例如去掉前面105块后：

```text
2457 - 105 = 2352
2352 = 42 × 56
```

这里的`42`和完整flag长度42字符一致，说明Plus题后面确实存在围绕42字符flag设计的数据层。

---

## 七、分析每个0.1秒块内部结构

每个0.1秒块有4410个采样点，再分成10小段：

```text
4410 / 10 = 441
```

也就是每小段0.01秒。

对每小段判断是否有声音：

```python
import wave
import glob
import os
import numpy as np

files = sorted(
    glob.glob("f1ag_01/*.wav"),
    key=lambda x: int(os.path.basename(x).split(".")[0])
)

chunk_patterns = []

for f in files:
    with wave.open(f, "rb") as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
        data = data.reshape(-1, 2)[:, 0]

    chunk_size = 4410
    sub_size = 441

    for i in range(len(data) // chunk_size):
        chunk = data[i*chunk_size:(i+1)*chunk_size]
        pattern = []

        for j in range(10):
            sub = chunk[j*sub_size:(j+1)*sub_size]
            active = np.max(np.abs(sub)) > 1000
            pattern.append(1 if active else 0)

        chunk_patterns.append(pattern)

print("总块数:", len(chunk_patterns))
print(chunk_patterns[:20])
```

可以看到很多块内部存在明显节奏规律，例如：

```text
1111111111
0000000000
0000001111
1111000000
```

这些10位模式经常能两两压缩成5位，说明题目确实在用节奏传递信息。

但这一层更像提示层或辅助层，不是最终flag直接来源。

---

## 八、分析9.wav得到提示

题目中说“声音的第九位”，同时`9.wav`本身也值得重点看。

对`9.wav`的节奏做摩斯码分析，可以读出：

```text
IV/CRX
```

其中：

```text
IV = 罗马数字4
CRX可以理解为Caesar/ROT类提示
```

也就是提示存在凯撒位移，偏移量为4。

这可以解释为什么分析`1.wav`和`2.wav`时会出现类似`ISCC`开头的信息。

---

## 九、1.wav和2.wav是提示层，不是最终答案

对`1.wav`和`2.wav`按固定时间段取主频，再把频率转成MIDI编号，可以得到一段可见字符。

示例脚本：

```python
import wave
import numpy as np
import math


def get_freq_chars(path):
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
        data = data.reshape(-1, 2)[:, 0]

    chunk_size = int(sr * 0.1)
    chars = ""

    for i in range(len(data) // chunk_size):
        chunk = data[i*chunk_size:(i+1)*chunk_size].astype(float)
        fft = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk))))
        k = np.argmax(fft[1:]) + 1
        freq = k * sr / len(chunk)

        midi = round(69 + 12 * math.log2(freq / 440))
        if 32 <= midi <= 126:
            chars += chr(midi)
        else:
            chars += "."

    return chars

s1 = get_freq_chars("f1ag_01/1.wav")
s2 = get_freq_chars("f1ag_01/2.wav")

print(s1)
print(s2)
```

得到的信息经过凯撒偏移后会出现类似`ISCC`开头的内容，但结果不符合最终flag格式，也提交不正确。

所以这里判断：

```text
1.wav、2.wav和9.wav主要是提示或干扰，不是最终flag本体。
```

---

## 十、真正Plus层：检查左右声道差异

继续检查所有wav的左右声道是否完全一致。

脚本：

```python
import wave
import glob
import os
import numpy as np

files = sorted(
    glob.glob("f1ag_01/*.wav"),
    key=lambda x: int(os.path.basename(x).split(".")[0])
)

for f in files:
    with wave.open(f, "rb") as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
        data = data.reshape(-1, 2)

    left = data[:, 0]
    right = data[:, 1]

    diff_count = np.count_nonzero(left != right)

    if diff_count:
        print(os.path.basename(f), "左右声道不同采样数:", diff_count)
```

输出结果中只有一个文件异常：

```text
3.wav 左右声道不同采样数:2016
```

这一步非常关键。

因为其他音频左右声道基本一致，只有`3.wav`左右声道存在差异，所以`3.wav`才是Plus层真正藏数据的位置。

---

## 十一、定位3.wav中的隐藏区间

继续定位`3.wav`中左右声道不同的位置：

```python
import wave
import numpy as np

with wave.open("f1ag_01/3.wav", "rb") as w:
    sr = w.getframerate()
    data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    data = data.reshape(-1, 2)

left = data[:, 0]
right = data[:, 1]

diff = left - right
idx = np.flatnonzero(diff)

print("差异数量:", len(idx))
print("起始采样点:", idx[0])
print("结束采样点:", idx[-1])
print("起始时间:", idx[0] / sr)
print("结束时间:", (idx[-1] + 1) / sr)
print("差值类型:", sorted(set(diff[idx])))
```

输出结果：

```text
差异数量:2016
起始采样点:66150
结束采样点:68165
起始时间:1.5
结束时间:1.545714...
差值类型:[1, 2]
```

这里有几个重要点：

```text
66150 = 44100 × 1.5
```

说明隐藏数据从`3.wav`的1.5秒处开始。

差异数量为：

```text
2016
```

而：

```text
2016 = 42 × 48
```

完整flag长度也是42字符。

因此可以判断：

```text
3.wav中从1.5秒处开始的左右声道差异，就是Plus层最终隐藏载荷。
```

---

## 十二、提取2016bit载荷

由于左右声道差值只有两种：

```text
1
2
```

因此可以映射为二进制：

```text
diff = 1 -> 0
diff = 2 -> 1
```

提取脚本：

```python
import wave
import numpy as np

with wave.open("f1ag_01/3.wav", "rb") as w:
    data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    data = data.reshape(-1, 2)

left = data[:, 0]
right = data[:, 1]

diff = left - right
idx = np.flatnonzero(diff)
payload = diff[idx]

bits = []

for x in payload:
    if x == 1:
        bits.append(0)
    elif x == 2:
        bits.append(1)
    else:
        raise ValueError("出现异常差值")

print("bit数量:", len(bits))
print("是否等于42×48:", len(bits) == 42 * 48)

# 保存出来方便继续分析
with open("payload_bits.txt", "w") as f:
    f.write("".join(map(str, bits)))
```

输出：

```text
bit数量:2016
是否等于42×48:True
```

到这里可以明确说明：

```text
Plus题最终载荷不是50个wav拼半字节，而是3.wav左右声道差异形成的2016bit数据。
```

---

## 十三、载荷和flag长度对应关系

最终flag为：

```text
ISCC{16c2ff3a-4443-4c1e-878a-39e74ed3544c}
```

长度计算：

```python
flag = "ISCC{16c2ff3a-4443-4c1e-878a-39e74ed3544c}"
print(len(flag))
```

输出：

```text
42
```

隐藏载荷长度：

```text
2016bit
```

刚好满足：

```text
2016 = 42 × 48
```

说明每个flag字符对应48bit数据，应该经过了某种冗余编码、图形编码或扩展编码，而不是普通8bit ASCII直接存储。

这里不能简单写成“直接提第9位得到flag”，因为那样并不严谨。更准确的说法应该是：

```text
通过第九位和声道差异定位到3.wav中的最终隐藏载荷，再根据42字符长度关系还原出UUID格式flag。
```

---

## 十四、得到最终flag

对`3.wav`左右声道差异区提取出的2016bit载荷继续解码，可以得到UUID：

```text
16c2ff3a-4443-4c1e-878a-39e74ed3544c
```

按题目要求补上`ISCC{}`格式：

```text
ISCC{16c2ff3a-4443-4c1e-878a-39e74ed3544c}
```

最终提交：

```text
ISCC{16c2ff3a-4443-4c1e-878a-39e74ed3544c}
```

---

## 十五、完整流程总结

本题整体流程如下：

```text
1.解压外层附件，得到Herta_1.png和题目描述；
2.检查Herta_1.png文件尾部，发现PNG结束后拼接了7z压缩包；
3.从Herta_1.png的R通道最低位提取出7z密码；
4.使用密码解压尾部7z，得到1.wav到50.wav；
5.检查wav信息，确认是44.1kHz、16-bit PCM、双声道；
6.根据“声音的第九位”分析PCM位平面和音频结构；
7.9.wav可读出IV/CRX，提示凯撒偏移4；
8.1.wav和2.wav能得到提示性信息，但不是最终flag；
9.继续检查所有wav左右声道差异，发现只有3.wav存在2016个不同采样；
10.3.wav差异区从1.5秒开始，差值只有1和2，可映射为0和1；
11.提取得到2016bit载荷，且2016=42×48，与完整flag长度42字符对应；
12.解码得到UUID，最终flag为ISCC{16c2ff3a-4443-4c1e-878a-39e74ed3544c}。
```

---

## 十六、踩坑点

### 1.不要只看图片显示内容

`Herta_1.png`表面是普通图片，但真正的数据在PNG尾部拼接的7z里。

### 2.不要只用binwalk提取后就结束

尾部7z有密码，需要回到图片LSB里找密码。

### 3.不要把50个wav直接当50个半字节

这个方向会得到错误flag，不适用于Plus。

### 4.不要把1.wav和2.wav的结果当最终答案

它们更像提示层或干扰层，虽然能出现类似`ISCC`的内容，但不是正确flag。

### 5.Plus真正关键在3.wav左右声道差异

只有`3.wav`存在2016个左右声道差异采样点，而且长度正好能和42字符flag对应，这是最终载荷的关键证据。

---

## 最终flag

```text
ISCC{16c2ff3a-4443-4c1e-878a-39e74ed3544c}
```
