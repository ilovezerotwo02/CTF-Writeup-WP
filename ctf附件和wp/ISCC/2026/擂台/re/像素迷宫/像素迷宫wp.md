# 像素迷宫 (PixelMaze) WP

**题目来源**: ISCC   
**题目类型**: Reverse / Maze   
**题目分值**: 150   
**题目描述**: 是像素不是0和1

---

## 1. 初步分析

给到一个 Windows PE 文件 `PixelMaze.exe`，先看看基本信息：

```bash
$ file PixelMaze.exe
PixelMaze.exe: PE32+ executable (console) x86-64, for MS Windows
```

用 IDA Pro / objdump 查看符号表，发现程序**几乎没有做符号剥离**，关键函数名全部保留：

| 函数名 | 地址 | 作用 |
|--------|------|------|
| `decryptPixel(int)` | `0x1400016A0` | 解密单个像素值 |
| `getDecryptedPixel(int, int)` | `0x1400016B0` | 获取解密后的迷宫格子值 |
| `isValidMove(int, int, char)` | `0x140001810` | 判断某个方向是否可走 |
| `extractPath(string)` | `0x140001950` | 提取 flag 花括号内的路径 |
| `validatePath(string)` | `0x140001890` | 校验路径是否合法 |
| `main` | `0x1400B8390` | 主函数 |

此外 `.rdata` 段中可直接看到字符串 `"ISCC{"`，确认 flag 以 `ISCC{...}` 格式组织。

---

## 2. main 函数逻辑

main 函数流程（反编译还原）：

1. 输出 `===PixelMaze===`
2. 输出 `Enter flag:` 提示用户输入
3. 读入一整行字符串
4. 调用 `extractPath()` 解析 flag，提取 `{}` 内部的路径字符串
5. 调用 `validatePath()` 校验路径
6. 成功输出 `Correct!`，失败输出 `Incorrect!`

```c
int main() {
    cout << "===PixelMaze===" << endl;
    cout << "Enter flag:" << endl;
    string input;
    getline(cin, input);
    string path = extractPath(input);
    if (path.length() > 0) {
        if (validatePath(path))
            cout << "Correct!" << endl;
        else
            cout << "Incorrect!" << endl;
    } else {
        cout << "Incorrect!" << endl;
    }
    return 0;
}
```

---

## 3. extractPath 解析

`extractPath` 负责验证 flag 格式并提取路径串：

1. 输入长度必须 **> 6**
2. 前 5 个字符必须是 `"ISCC{"`
3. 最后一个字符必须是 `'}'`（ASCII 125）
4. 中间内容被截取出来
5. 对截取出的每个字符做合法性检查：只能是 `E`(69)、`N`(78)、`S`(83)、`W`(87) 四个字母之一

核心合法性校验片段：

```c
v14 = 279041;  // 0x44181 - bitmap for valid chars
do {
    if ((unsigned int)(*v15 - 69) > 0x12u 
        || !_bittest64(&v14, (unsigned int)(unsigned char)*v15 - 69))
        goto INVALID;
    ++v15;
} while (/* end of string */);
```

这里 `279041` 的二进制是 `0x44181 = 0b0000 0000 0000 0100 0100 0001 1000 0001`，从低位到高位对应字符偏移 `(char - 69)`：

| 字符 | ASCII | offset = char-69 | bit 位置 | 是否有权 |
|------|-------|------------------|----------|---------|
| `E`  | 69    | 0                | bit 0    | 1 (0x44181 & 1 = 1) |
| `N`  | 78    | 9                | bit 9    | 1 (0x44181 >> 9 & 1 = 1) |
| `S`  | 83    | 14               | bit 14   | 1 (0x44181 >> 14 & 1 = 1) |
| `W`  | 87    | 18               | bit 18   | 1 (0x44181 >> 18 & 1 = 1) |

因此 flag 格式为：**`ISCC{<只包含E/N/S/W的路径串>}`**。

---

## 4. 迷宫数据解密

### 4.1 decryptPixel —— XOR 解密

```c
int decryptPixel(int x) {
    return x ^ 0x7F;
}
```

加密方式非常简单：每个像素值与 `0x7F` 异或。

### 4.2 getDecryptedPixel —— 迷宫布局

10×10 的迷宫被拆成**三段**存储：

| 部分 | 行号 | 元素数量 | 存储位置 |
|------|------|----------|----------|
| `ENCRYPTED_PART1` | 第 0–2 行 | 30 个 int | `.rdata` 段 (偏移 0xBB980) |
| `ENCRYPTED_PART2` | 第 3–6 行 | 40 个 int | `.rdata` 段 (偏移 0xBB8E0) |
| `PART3` (栈) | 第 7–9 行 | 30 个 int | 栈上数组初始化 |

第三部分直接在 `getDecryptedPixel` 函数的栈上初始化，值可通过反编译直接提取：

```c
_QWORD v3[17];
v3[0]  = 0xBE000000BELL;  // row 7: 0xBE, 0xBE, 0x37, 0x2E, ...
v3[1]  = 0x2E00000037LL;
// ... 共 30 个值
```

所有值取出后统一 XOR `0x7F` 还原真实像素。

解密后得到 10×10 网格（值以十六进制显示，括号内为可走方向）：

```
row 0: 04(S)    01(E)    B1(E)    C3(EW)   52(W)    D1(E)    D1(E)    F4(S)    21(E)    B4(S)
row 1: 64(S)    51(E)    B1(E)    01(E)     F4(S)    B8(N)    24(S)    82(W)     B4(S)    F6(WS)
row 2: A1(E)    78(N)    84(S)    F2(W)     F1(E)    28(N)    E1(E)    84(S)     DC(SN)   C9(EN)
row 3: E5(ES)   F4(S)    24(S)    C8(N)     A2(W)    02(W)    92(W)    14(S)     F8(N)    68(N)
row 4: A9(EN)   FA(WN)   74(S)    35(ES)    A4(S)    86(WS)   E8(N)    84(S)     49(EN)   33(EW)
row 5: 84(S)    D2(W)    62(W)    F8(N)     9C(SN)   DA(WN)   98(N)    A2(W)     71(E)    D2(W)
row 6: 74(S)    76(WS)   81(E)    E4(S)     B8(N)    B1(E)    01(E)    94(S)     25(ES)   C2(W)
row 7: C1(E)    C1(E)    48(N)    51(E)     01(E)    C8(N)    F4(S)    62(W)     19(EN)   E2(W)
row 8: 11(E)    35(ES)   43(EW)   25(ES)    02(W)    D6(WS)   41(E)    91(E)     51(E)    94(S)
row 9: 09(EN)   91(E)    32(W)    73(EW)    18(N)    36(WS)   D2(W)    03(EW)    42(W)    7F(EWSN)
```

---

## 5. isValidMove —— 方向位掩码

`isValidMove(row, col, dir)` 函数通过检查像素值的低 4 位判断方向可行性：

```c
int isValidMove(unsigned int row, unsigned int col, char dir) {
    if (row > 9 || col > 9)
        return 0;
    int pixel = getDecryptedPixel(row, col);
    switch (dir) {
        case 'E': return pixel & 1;         // bit 0
        case 'W': return (pixel >> 1) & 1;  // bit 1
        case 'S': return (pixel >> 2) & 1;  // bit 2
        case 'N': return (pixel >> 3) & 1;  // bit 3
    }
    return 0;
}
```

方向位对应关系：

| 方向 | ASCII | 位 | Shift |
|------|-------|----|-------|
| `E` (East)  | 69 | bit 0（0x01） | `pixel & 1` |
| `W` (West)  | 87 | bit 1（0x02） | `(pixel >> 1) & 1` |
| `S` (South) | 83 | bit 2（0x04） | `(pixel >> 2) & 1` |
| `N` (North) | 78 | bit 3（0x08） | `(pixel >> 3) & 1` |

例如格子值为 `0x04` = `0b0100`，bit2=1 表示可向 **S** 走；
格子值为 `0x7F` = `0b0111 1111`，低 4 位全 1 表示四方向均可走（终点格子）。

---

## 6. validatePath —— 路径校验

`validatePath` 从 `(0, 0)` 出发，逐字符移动：

- `N` → `row -= 1`
- `S` → `row += 1`
- `E` → `col += 1`
- `W` → `col -= 1`

每一步移动前调用 `isValidMove` 检查当前格子是否允许该方向。

关键校验点有两处：

1. **不能越界**：`row > 9` 或 `col > 9` 直接返回 false
2. **必须在路径结束时恰好到达 `(9, 9)`**：走到终点时 `row == 9 && col == 9` 且当前步数索引必须是最后一个字符（即不能提前到达终点，也不能到终点后继续走）

```c
// 核心校验逻辑
result = v3 == 9 && v4 == 9;    // 是否到达 (9,9)
if (result)
    return v1 - 1 == v2;         // 是否正好是最后一个字符
if (++v2 == v1)
    return result;               // 路径走完了还没到终点
```

所以我们必须找到一条从 `(0,0)` 到 `(9,9)` 的路径，且长度必须是**唯一的最短路径长度**（否则会在非末尾位置经过 `(9,9)` 导致提前判定失败）。

---

## 7. BFS 求解

将解密后的 10×10 迷宫建模为有向图，每个格子根据低 4 位的方向掩码连接相邻节点。

因为要求**最短**路径（避免提前经过终点），使用 BFS（广度优先搜索）：

```python
from collections import deque

moves = {'N': (-1,0), 'S': (1,0), 'E': (0,1), 'W': (0,-1)}
bits  = {'E': 0, 'W': 1, 'S': 2, 'N': 3}

q = deque([((0,0), "")])
seen = {(0,0)}

while q:
    (r,c), path = q.popleft()
    if (r,c) == (9,9):
        print(path)  # 找到最短路径
        break
    for d, (dr, dc) in moves.items():
        cell = grid[r][c]
        if (cell >> bits[d]) & 1:  # 该方向可走
            nr, nc = r+dr, c+dc
            if 0 <= nr < 10 and 0 <= nc < 10 and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append(((nr, nc), path + d))
```

---

## 8. 结果

BFS 找到唯一最短路径，长度为 **52 步**：

```
SSENEEESENNEESWSESSSWNNWWWNWSSSWWSSEENESEENEESWSEEES
```

因此最终 flag 为：

```
ISCC{SSENEEESENNEESWSESSSWNNWWWNWSSSWWSSEENESEENEESWSEEES}
```

验证：输入程序，输出 `Correct!`。

---

## 9. 总结

| 步骤 | 操作 |
|------|------|
| 1 | 分析 PE，发现符号未剥离，关键函数名可见 |
| 2 | 还原 `extractPath`：提取 `ISCC{...}` 中的 `E/N/S/W` 路径串 |
| 3 | 还原 `getDecryptedPixel`：三段存储，异或 `0x7F` 解密 |
| 4 | 还原 `isValidMove`：低 4 位为 `E W S N` 方向掩码 |
| 5 | 还原 `validatePath`：从 `(0,0)` 到 `(9,9)`，必须在末尾精确到达 |
| 6 | 提取加密数据 → XOR 解密 → 10×10 网格 → BFS 搜路径 |
| 7 | 拼接得到 flag |
