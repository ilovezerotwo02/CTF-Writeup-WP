# hello酷狗（Misc 1000pt）

- 附件：`卡提西亚.zip` → `卡提西亚.png`（1117×1086，伪装成二次元立绘）
- 脚本：`solve_morse.py`
- flag：`HTUCTF{b1e17d71-df09-2ffa-b9c7-a6e2b63bd3e1}`

## 一句话

`卡提西亚.png` 的 `IEND` 之后追加了一个 ZIP，里面 `flag.txt` 是 **摩斯电码**（A=划、B=点），
解出 32 位十六进制，按 UUID 切开就是 flag。题面「分离与融合」= 文件分离（PNG+ZIP）。

## 步骤

1. PNG 结构正常（IHDR + 一堆 8192 的 IDAT + IEND），但 `IEND` 之后还有 177 字节：

```python
i = d.rfind(b'IEND') + 8
open('appended.zip','wb').write(d[i:])     # PK\x03\x04 ...
```

   注意 `unzip` 会报 `missing 2421534 bytes`（因为 ZIP 里的 offset 是相对整张 PNG 的），
   但 `flag.txt` 照样能正常 inflate。

2. `flag.txt`（160 字节，CRLF 两行）内容是 A/B 分组：

```
ABBB BAAAA B BAAAA AABBB ABB AABBB BAAAA ABB BBAB AAAAA AAAAB BBAAA BBAB BBAB
BA ABBB AAAAB ABAB AABBB BA ABBBB B BBAAA ABBB ABBBB BBBAA ABBB ABB BBBAA B BAAAA
```

3. **一定是摩斯**：A 当划、B 当点，32 组**全部**都能落到合法摩斯码表（没有一格是 `?`），
   结果正好是 32 个十六进制字符——这个"全中 + 合法hex"的组合基本排除巧合：

```
A=dash, B=dot  ->  B1E17D71DF092FFAB9C7A6E2B63BD3E1     ← 正确
A=dot,  B=dash ->  J6T62W26WQ547QQNJ4?2N1T7J18JW8T6     ← 有非法组，排除
```

4. 32 位 hex 按 UUID 切成 `8-4-4-4-12`：

```
b1e17d71-df09-2ffa-b9c7-a6e2b63bd3e1
```

5. 套 `HTUCTF{}` 提交 → Accepted。

## 小结

- PNG/JPG 尾巴后面一段 `PK\x03\x04` 是最高频的文件分离点，`rfind(b'IEND')`、`rfind(b'\xff\xd9')` 一把梭。
- A/B 这种二元字母表先想摩斯（两种映射都试）、再想培根（5 位一组）。这里分组长度不规则
  （1~5 不等），**不是**培根，而是摩斯；判据就是"哪种映射能 100% 命中码表"。
- 解出来是 32 位 hex 时，先按本场比赛的 flag 风格还原成 UUID（带横线、小写）。
