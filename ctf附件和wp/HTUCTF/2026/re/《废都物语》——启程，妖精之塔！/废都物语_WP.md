# 《废都物语》——启程，妖精之塔！ Writeup

## 题目信息
- 分类：Reverse / 1000 分 / StaticAttachment
- 附件：`HTU_NightRoute.exe`（10,291,744 字节）
- flag：`HTUCTF{Welcome Ruina- Fairy Tale of the Forgotten Ruins}`

## 一、样本类型判定

PE 头显示 x64 控制台程序，但 PE 本体（`.text` 约 200KB）只占 ~370KB，剩余 **9.9MB 为 overlay**——典型的 **PyInstaller** 自解压包特征。strings 中可见 `PYZ archive`、`_MEIPASS`、`pyiboot01_bootstrap` 等标志。

```
Python version: 3.14
Entry point: htu_maze_route.pyc   ← 主程序
附带资源: assets/{fail1,fail2,fail3,tower_lower,fairy_king}.jpg
```

用 `pyinstxtractor.py` 解包得到 `htu_maze_route.pyc`（22KB）及 5 张 CG 图。

## 二、反编译思路

pyc 为 **Python 3.14** 字节码（magic `2b0e0d0a`）。3.13 的 `dis` 反汇编 3.14 字节码会段错误，故安装 Python 3.14.4 后用 `marshal.loads` + `dis.dis` 直接还原字节码，逐函数人工还原源码。

游戏本体是 **三重迷宫文字冒险**：W/A/S/D 移动，三层迷宫各有出口 A/B/C，选错出口进"回程通道"，撞墙 5 次或连续 2 次走错出口即失败（触发 fail CG）。走对三层后进入"妖精王"剧情，要求输入"终端密钥"。

## 三、关键逻辑还原

### 3.1 正确出口序列

```python
_CONTINUE_EXIT = (0, 2, 1)          # 各层正确出口在 'ABC' 中的下标
# → 第1层走 A，第2层走 C，第3层走 B
route = ['A', 'C', 'B']
```

程序内 `exit_index = 'ABC'.index(cell)` 与 `_CONTINUE_EXIT[level]` 比对，相等即正确出口，`route.append(cell)`。三层走完后：

```python
credential = _final_credential(route)      # 妖精们的凭证
# 提示: "凭证不是最终的密钥，请通过逆向分析程序得到最终击败他的密钥"
candidate = input("输入终端密钥：")
assert candidate == _derive_console_key(credential)
print(_open_flag(candidate))               # 最终 flag
```

### 3.2 凭证生成 `_final_credential(route)`

自定义 32 位状态机 + xorshift，把出口序列打成 `TRI-XXXX-XXXX-XXXX`：

```python
state = 1831565813
for index, exit_name in enumerate(route, 1):
    state = ((state << 7) | (state >> 25)) & 0xFFFFFFFF
    state ^= (ord(exit_name) * 73244475) ^ (index * 2654435769)
    state = (state + 2712847316 + index * 1267611) & 0xFFFFFFFF

parts = []
for block in range(3):
    state = (state * 1664525 + 1013904223 + block) & 0xFFFFFFFF   # LCG
    word = []
    for _ in range(4):
        state ^= (state << 13) & 0xFFFFFFFF                       # xorshift32
        state ^= state >> 17
        state ^= (state << 5) & 0xFFFFFFFF
        state &= 0xFFFFFFFF
        word.append(_CREDENTIAL_ALPHABET[state % 32])
    parts.append(''.join(word))
return 'TRI-' + '-'.join(parts)
```

`_CREDENTIAL_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"`（去 0/1/I/O/U/V 的 Crockford 风格）。

计算得 **credential = `TRI-KZDT-JPRX-7VHA`**（游戏内展示的"妖精们的凭证"）。

### 3.3 终端密钥派生 `_derive_console_key(credential)`

这是题面所说的"击败妖精王的密钥"，**不能直接用凭证**，需再做一层混淆：

```python
compact = credential.replace('-', '')        # 'TRIKZDTJPRX7VHA'
state = 3237998097
for index, char in enumerate(compact):
    state = (state + (ord(char) ^ _KEY_SALT[index % 8])) & 0xFFFFFFFF
    state = ((state * 33) ^ (state >> 11) ^ (index * 81)) & 0xFFFFFFFF

raw = []
for index in range(12):
    state = (state * 1103515245 + 12345 + _KEY_SALT[index % 8]) & 0xFFFFFFFF  # LCG
    raw.append(_KEY_ALPHABET[state % 32])
return ''.join(raw[i] for i in _KEY_ORDER)   # 位置重排
```

- `_KEY_SALT = (23, 163, 92, 225, 40, 150, 79, 210)`
- `_KEY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"`
- `_KEY_ORDER = (7, 2, 10, 0, 5, 11, 3, 8, 1, 6, 4, 9)`（12 位置换）

计算得 **console_key = `LXDW9BMUA5SG`**。

### 3.4 flag 还原 `_open_flag(console_key)`

flag 被拆散存进 `_FLAG_BOX`（56 个 0~94 的数值），按 `_FLAG_ORDER`（0..55 的置换）回填，每位用密钥+盐做移位反演：

```python
key_bytes = console_key.encode('ascii')      # 12 字节
restored = [' '] * 56
for index, storage_index in enumerate(_FLAG_ORDER):
    shift = (key_bytes[index % 12] + _FLAG_SALT[index % 7]) * (index + 3) % 95
    restored[index] = chr((_FLAG_BOX[storage_index] - shift) % 95 + 32)
return ''.join(restored)
```

- `_FLAG_SALT = (11, 29, 7, 41, 18, 3, 37)`
- 结果为 56 字符可打印 ASCII，模 95 加 32 映射到 `0x20~0x7E`

## 四、解题结果

```
route      = ['A', 'C', 'B']
credential = TRI-KZDT-JPRX-7VHA
console_key= LXDW9BMUA5SG
flag       = HTUCTF{Welcome Ruina- Fairy Tale of the Forgotten Ruins}
```

flag 以 `HTUCTF{` 开头、`}` 结尾，且语义与题面（废都物语 Ruina / 妖精之塔 / 遗忘的废墟）完全吻合，交叉验证正确。

## 五、附：迷宫最短路径（BFS 验证出口可达）

| 层 | 出口 | 最短步数 |
|----|------|---------|
| 1 | A | 106 |
| 2 | C | 92 |
| 3 | B | 120 |

完整路径见 `solve.py` 输出。

## 六、解题脚本

`solve.py` —— 含常量、三个核心函数的忠实还原、BFS 路径验证，直接运行即可得到 flag。

```bash
python3.14 solve.py
```

## 七、备注

- 题面"特殊结局（精美CG）"指通关时可选查看 `tower_lower.jpg`（妖精之塔下层）与 `fairy_king.jpg`（妖精王）两张 CG，不影响 flag。
- 失败 CG（fail1/2/3.jpg）对应三层不同失败剧情，也是干扰项。
- 「请保持你的决心」为剧情 flavor，无密码学含义。
