# PixelMaze WP

## 最终 flag

`ISCC{SSENEEESENNEESWSESSSWNNWWWNWSSSWWSSEENESEENEESWSEEES}`

## 题目分析

样本是 `PixelMaze.exe`，直接用 `objdump -t` 看符号表，可以发现这题几乎没做符号剥离，核心函数名都还在：

- `decryptPixel(int)`
- `getDecryptedPixel(int, int)`
- `isValidMove(int, int, char)`
- `validatePath(std::string const&)`
- `extractPath(std::string const&)`
- `main`

这意味着可以直接顺着函数名恢复程序逻辑。

## 主逻辑

`main` 的流程很简单：

1. 打印 `===PixelMaze===`
2. 输入一整行字符串
3. 调用 `extractPath()` 解析 flag
4. 调用 `validatePath()` 校验路径
5. 成功输出 `Correct!`，否则输出 `Incorrect!`

从 `.rdata` 字符串可以直接看到 flag 前缀是：

```text
ISCC{
```

## extractPath

`extractPath()` 逻辑可以还原为：

1. 输入长度必须大于 6
2. 前 5 个字符必须是 `"ISCC{"`
3. 最后一个字符必须是 `'}'`
4. 中间内容会被截出来作为路径串
5. 路径串中的每个字符必须属于 `E/N/S/W`

也就是 flag 格式为：

```text
ISCC{<path>}
```

其中 `<path>` 只能由 `E N S W` 组成。

## 迷宫数据与方向位

`decryptPixel(int)` 非常简单：

```cpp
int decryptPixel(int x) {
    return x ^ 0x7F;
}
```

`getDecryptedPixel(row, col)` 把 10x10 的迷宫拆成三段保存：

- 第 1 段 `ENCRYPTED_PART1`：前 3 行
- 第 2 段 `ENCRYPTED_PART2`：中间 4 行
- 第 3 段：最后 3 行，直接在栈上初始化

取出对应元素后统一异或 `0x7F` 得到真实像素值。

`isValidMove(row, col, dir)` 则告诉我们每个像素的低 4 位表示四个方向是否可走：

- bit0: `E`
- bit1: `W`
- bit2: `S`
- bit3: `N`

所以某个格子值如果是 `0b0101`，就表示可以向 `E` 和 `S` 走。

## validatePath

`validatePath()` 的起点是 `(0,0)`，终点是 `(9,9)`。

它会逐字符读取路径：

- `N` -> `row - 1`
- `S` -> `row + 1`
- `E` -> `col + 1`
- `W` -> `col - 1`

每走一步前先调用 `isValidMove()` 检查当前格子是否允许该方向移动。

关键点在结尾判断：

- 必须最终走到 `(9,9)`
- 而且走到终点时，当前位置正好是路径串最后一个字符

所以不能提前到终点，也不能到终点后继续乱走。

## 迷宫恢复

把三段密文解出后可得到 10x10 网格。每个值是一个方向位掩码。

我写了一个 BFS，从 `(0,0)` 搜到 `(9,9)`，得到唯一最短路径长度为 `52`，路径为：

```text
SSENEEESENNEESWSESSSWNNWWWNWSSSWWSSEENESEENEESWSEEES
```

因此最终 flag 为：

```text
ISCC{SSENEEESENNEESWSESSSWNNWWWNWSSSWWSSEENESEENEESWSEEES}
```

## 验证

将该 flag 输入程序，输出：

```text
Correct!
```

## 复现脚本

同目录下已经给出 `solve.py`，直接运行：

```powershell
python solve.py
```

会输出路径和最终 flag。
