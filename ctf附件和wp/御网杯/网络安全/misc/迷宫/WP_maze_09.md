# maze_09 WP

## 题目信息

- 题型：MISC
- 目标：逐层解压压缩包，提取最内层数据并还原凭证
- 附件：`maze_09.zip`

## 解题思路

这题本质上是一个多层压缩包套娃，重点在于：

1. 先把压缩链完整梳理出来。
2. 找到最内层文件后，不要被 `.bin` 后缀误导，继续判断它是否还是文本编码数据。

## 解压链

从 `maze_09.zip` 开始逐层查看：

1. `maze_09.zip`
   - 解压得到 `layer1/data2.zip`
2. `data2.zip`
   - 解压得到 `secret3/hidden4.zip`
3. `hidden4.zip`
   - 解压得到 `.config/user/backup5/vault.bin`

到这里压缩层结束，最内层文件是 `vault.bin`。

## 分析 `vault.bin`

直接查看内容可以得到：

```text
NGEzMzU4ZWU5ODdkYzJlODVlYjZhODkxNDUwMzdjYmY=61
```

这个文件虽然叫 `.bin`，但实际是文本。可以看出主体是 Base64，末尾多了一个干扰后缀 `61`。

取前面的有效 Base64 部分：

```text
NGEzMzU4ZWU5ODdkYzJlODVlYjZhODkxNDUwMzdjYmY=
```

Base64 解码后得到：

```text
4a3358ee987dc2e85eb6a89145037cbf
```

这是最终还原出的原始凭证。

## Flag

```text
flag{4a3358ee987dc2e85eb6a89145037cbf}
```

## EXP

题目目录下已经放好自动化脚本：

[`exp_maze_09.py`](D:/桌面/yuwang/misc/迷宫/exp_maze_09.py)

运行方式：

```bash
python exp_maze_09.py
```

脚本会自动：

1. 递归解压 `maze_09.zip`
2. 定位最终的 `vault.bin`
3. 提取有效 Base64
4. 解码出凭证
5. 输出最终 flag
