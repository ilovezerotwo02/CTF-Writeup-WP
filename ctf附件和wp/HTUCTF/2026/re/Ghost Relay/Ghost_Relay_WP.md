# Ghost Relay_WP

## 题目
Reverse / 1000分 / StaticAttachment。7.6KB 的控制台小游戏（GhostRelay.exe），9 个扇区收集 shard/charge，避开 trap，攒够能量后 P=claim 取档案。

## 分析
- 字符串里有 3 张 22x11 地图、规则（$=+125, +=+60, ^=-90, 连续4 shard +75, 扇区跳 +200, 上限 /4300）
- 反汇编（capstone）：
  - `0x140001000`：`mov rax,[data+0]; xor rax,[data+8]; ret`——运行时状态 XOR
  - `0x140001ef0`：能量校验 `state = 0x35c*5 = 4300`，`setae` 要求 ≥4300 才继续
  - **`0x1400019c7`：flag 解码循环**（校验通过后执行）——静态 XOR，与游戏分数无关
    ```
    cl = 0x1d
    for i in 0..0x24:
        al = (cl * (i&0xff) + (i&3)*17 + 0x79) & 0xff
        out[i] = al ^ cipher[i]
        cl += 3
    ```
  - cipher 在 `.rdata+0x2360`（37 字节）

## 关键
flag 是**硬编码加密串**，能量校验只是显示门槛。直接离线解码即可，不用通关游戏（题目也提示"从 CPU 的角度寻找捷径"）。

```python
cipher = bytes.fromhex("31feb45d...4a1b5b48")  # .rdata 0x140002360
cl = 0x1d
for i in range(0x25):
    al = ((cl * (i & 0xff)) + (i & 3) * 17 + 0x79) & 0xff
    out.append(al ^ cipher[i]); cl = (cl + 3) & 0xff
# → HTUCTF{V4ult_Guard_One_Register_Away}
```

## Flag
`HTUCTF{V4ult_Guard_One_Register_Away}`
