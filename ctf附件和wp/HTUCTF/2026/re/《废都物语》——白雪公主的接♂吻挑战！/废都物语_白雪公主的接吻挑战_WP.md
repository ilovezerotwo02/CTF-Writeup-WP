# 《废都物语》——白雪公主的接♂吻挑战！ — WriteUp

| 项目 | 内容 |
|---|---|
| 分类 | Reverse / 控制台文字冒险（剧情状态机 + 隐藏选项 + 连招判定） |
| 分值 | 864（动态分值） |
| 附件 | `duel_arena.exe`（MinGW-w64 x64，GCC 编译，2.79MB，无壳无混淆，`.rsrc` 塞了 3 张 JPG） |
| Flag | `HTUCTF{YOU ARE AINNER！！！}`（注意 **AINNER**，三个感叹号是**全角 ！** U+FF01） |
| 复现 | `python solve.py duel_arena.exe`（原版 exe，不 patch，全自动到出 flag） |

---

## 0. 先看结论：完整正路（照这个按就能出 flag）

```
启动
 ├─ 1 给公主献上热吻
 ├─ 2 由同伴献吻
 ├─ n 不看 CG
 ├─ Enter
 ├─ 1 查看挑战规则   ← 不看过规则，选项 4 会被七个小矮人拦住
 ├─ Enter
 ├─ 3 调查石棺 → 1 Search the wall        ← 解锁选项 5（纸条）
 ├─ Enter
 ├─ 3 调查石棺 → 2 Inspect the surroundings ← 解锁选项 6（壁中凹痕）
 ├─ Enter
 ├─ 5 查看纸条（**这一步是必须的**，不是可选的背景故事）
 ├─ Enter
 ├─ 6 壁中凹痕 → 输入密钥 7391            ← 连招的四个前提之一（`0x1400E121089`）
 ├─ Enter
 ├─ 4 开始接吻挑战
 └─ 战斗里依次按 2 3 1 4                  ← 连招：塞舌头 → 忍耐 → 吸 → 观察
       → "You unleashed a move beyond the rules!" 秒杀 → y 看 CG → Enter
       → 终端打印 HTUCTF{YOU ARE AINNER！！！}
```

四个「必须」缺一不可：**看过规则**、**搜过墙（拿纸条）**、**读过纸条**、**输入过 7391**。

---

## 1. 环境

`wsl.exe` 在本机被安全策略拉黑，进不去 pwn 环境。全程用 Windows 版 Python 3.13 + `pwntools`(含 capstone) + `pefile`。

```bash
pip install pwntools pefile
python solve.py duel_arena.exe
```

---

## 2. 静态定位：从字符串反向找代码

`.rsrc` 里 3 个 RCDATA（101/102/103）都是 JPEG，导出看是废都物语风 CG + 一张 Panty&Stocking 海报，题面说的「塞了张好的（真的！）」就是它。**图里没有 flag，纯干扰。**

在 `.text` 里全量搜 `HTU`/`flag` 无结果 → flag 是运行时拼的。于是改用「字符串 → rip 相对引用 → 反汇编」的套路：

```python
# 用 capstone 扫 .text，凡是 op 是 [rip+disp] 就 tgt = ins.address+ins.size+op.mem.disp
# 命中 .rdata 里的目标字符串即打印引用点
```

先用 `pefile` 把文件偏移换成 VA，再把 `.pdata` 里的 (begin, end) 当函数边界，从函数头开始反汇编（比从字符串附近硬切可靠，capstone 中途遇到半条指令会直接吐出 0 条）。

关键全局变量全部落在 `.bss` 一块里，整理成表：

| 地址 | 含义 | 置 1 的地方 |
|---|---|---|
| `0x1400E12108A` | 凹痕（选项 6）可见 | 石棺 → `2 Inspect the surroundings` |
| `0x1400E12108C` | 纸条（选项 5）可见 | 石棺 → `1 Search the wall` |
| `0x1400E12108B` | 已经读过纸条 | 主菜单 `5` |
| `0x1400E12108D` | 纸条「触发过」——连招开关 | 打印纸条内容时（一次性） |
| `0x1400E121089` | 隐藏路线（密钥正确） | 密钥 `7391` 校验通过 |
| `0x1400E12108E` | 看过挑战规则（选项 4 的闸门） | 主菜单 `1` |
| `0x1400E121090` | 回合数 | 每次有效输入 +1 |
| `0x1400E121080` | **连招计数器** | 连招命中 +1，非法输入清零 |

---

## 3. 剧情状态机

主菜单实际接受：

```
1 查看挑战规则   2 向七个矮人抗议   3 调查石棺   4 开始接吻挑战   0 离开   （+ 满足条件时出现的 5 / 6）
```

石棺子菜单：`1 Search the wall` / `2 Inspect the surroundings`，分别解锁 5 和 6。石棺铭文本身就是提示：

> "Do not trust the visible menu. The true kiss is hidden outside the rules."

---

## 4. 隐藏选项 6 的密钥：`7391`（**不是 8 字节**）

`0x1400E08E0` 起是 `'6'` 的分发：

```
0x1400E08E0  cmp  al, 0x36              ; '6'
0x1400E08E8  cmp  byte [0x1400E12108A], 0
0x1400E08EF  je   0x1400E0390           ; 没搜过墙就当无效选项
0x1400E0905  ...  "The recess is shaped for a small key."
0x1400E092F  ...  "Enter the key for the hidden route > "
             getline(cin, in)
```

然后是「拼期望密钥」的循环（`0x1400E09DC` 起）：

```
r15 = 0x1400ED9AC                      ; .rdata
i   = built.length  (=0)
while (i != 4) {
    built[i] = *(0x1400ED9AC + i) ^ 0x5A;
    i++;
}
0x1400E0B18  cmp  rax(=4), in.length   ; 长度必须 = 4
0x1400E1755  call memcmp(in, built, 4) ; 内容必须相等
0x1400E175C  jne  "The key is incorrect. The recess remains silent."
```

`.rdata:0x1400ED9AC` 起始字节是 `6D 69 63 6B` = `"mick"`：

```
'm' ^ 0x5A = 0x37 '7'
'i' ^ 0x5A = 0x33 '3'
'c' ^ 0x5A = 0x39 '9'
'k' ^ 0x5A = 0x31 '1'
```

**密钥 = `7391`**（4 字节）。注意这里没有第二段、也没有 8 字节：`cmp rax, [输入长度]` 里的 `rax` 就是 `0 + 4`。实测输入 `7391` 直接过：

```
Enter the key for the hidden route > 7391
The recess glows. A mechanism turns inside the wall.
A path outside the rules has been unlocked.
```

> 顺带一个易踩的坑：`0x1400ED9AC` 之后紧跟 `qdb\r\x11\x1a...`，那是**另一张表**（flag 的密文），不要和密钥混在一起算。

---

## 5. 战斗机制（反汇编 + 实测互相验证）

```
你      氧气(HP) 100   气力(MP) 105/130
夜族王  氧气(HP) 145   气力(MP) 105/135
任一方 HP 或 MP 归零即分胜负；第 17 回合后仍未结束 → 判负
```

| 行动 | 精确效果 |
|---|---|
| 1 吸 | 对方 HP −6~10（随机），自己不掉 MP |
| 2 把舌头塞进去 | 自己 MP −23；对方 MP −22，若**对方 MP ≤ 70 则 −34** |
| 3 忍耐 | 自己 MP +24（上限 130） |
| 4 观察 | 打印对方下一步的「征兆」，自己不额外受损 |

夜族王的行动表在 `.rdata:0x1400ED980`（10 个 int），索引 `(回合-1) % 10`：

```
0,1,2,0,2,1,0,2,1,0        ; 0 攻击 / 1 恢复 / 2 夺取
```

- 攻击：打掉你 `13 + 回合%4` 点 HP（13~16，**确定性**）
- 恢复：自己 MP +18（上限 135）
- 夺取：打掉你 `17 + 回合%5` 点 MP（17~21，**确定性**）
- 【夜族王的决心】：**一次性**，当它的 HP ≤ 49 **或** MP ≤ 49 时，在你行动 + 它行动之后结算，扣你 **35** 点 MP

17 回合硬上限（`0x1400E0C99: cmp dword [0x1400E121090], 0x11` → `jg` 判负）让"正常磨 MP"几乎不可能：它 17 回合内会恢复 5 次共 +90 MP，而你每回合光是被夺取就要吐 17~21 点，还要吃一次 −35。**这就是为什么作者把正解做成连招。**

---

## 6. 真正的正解：`2 3 1 4` 连招（"beyond the rules"）

`.rdata:0x1400ED9A8` 有 4 个字节：`02 03 01 04`。战斗里每次行动都会拿「连招计数器 `0x1400E121080`」当索引去比这张表：

```
0x1400E187C  cmp  byte [0x1400ED9A8 + counter], 1   ; 吸  命中？
0x1400E1909  cmp  byte [0x1400ED9A8 + counter], 2   ; 塞舌头 命中？
0x1400E188F  counter++ ；counter == 4 且 [0x1400E12108D] != 0 → 跳 0x1400E11D2
```

也就是按顺序打出 **塞舌头(2) → 忍耐(3) → 吸(1) → 观察(4)**，计数器走满 4，进入秘密分支：

```
0x1400E11D2  cmp byte [0x1400E12108C], 0   je 失败   ; 搜过墙（拿到纸条）
0x1400E11DF  cmp byte [0x1400E12108B], 0   je 失败   ; 读过纸条
0x1400E11EC  cmp byte [0x1400E8010], 0x65  jne 失败  ; .data 那个字节必须变成 'e'
0x1400E11F9  cmp byte [0x1400E121089], 0   je 失败   ; 密钥 7391 已通过
0x1400E1206  cmp r12d(自己的MP), 0x1E      jle 失败  ; MP 必须 > 30
   → "You unleashed a move beyond the rules!"
   → "This kiss took the Night King's last oxygen and energy."
   → 对方 HP = 0, MP = 0（直接判负）
```

那个 `'e'` 是本题最阴的一点：`.data:0x1400E8010` 出厂值是 `'m'`，只有**打印纸条**那段代码会顺手做一次

```
0x1400E075E  eax = byte [0x1400E8010]        ; 'm'
0x1400E076C  eax ^= 0x23                      ; 0x4E
0x1400E076F  eax += 0x17                      ; 0x65 = 'e'
0x1400E0772  byte [0x1400E8010] = al
0x1400E0765  byte [0x1400E12108D] = 1
```

**所以不读纸条（菜单 5），连招虽然计数照样走满，但一定不触发。** 负向验证过：跳过 5，同样按 `2 3 1 4`，只有"征兆"文本，战斗照常继续，最后因 17 回合超时判负。

纸条的 9 条提示其实就是这套规则的说明（"观察可以看见征兆"、"恢复之后下一次通常不会立刻恢复"、"奖励只认最后一次真正的胜利"）。

---

## 7. flag 是运行时异或出来的

胜利分支（`0x1400E12F7` 起）现场拼字符串，31 字节：

```
r14 = 0x1400ED9B0            ; 密文表，紧跟 "mick" 那 4 字节之后
state = '1' (0x31)
for (i = 0; ; i++) {
    out[i] = table[i] ^ state ^ 8;
    state += 7;                       // mod 256
    if (state == 0x0A) break;         // 31 次后正好收住
}
```

密文表（`0x1400ED9B0`，31 字节）：

```
71 64 62 0D 11 1A 28 33 2E 2D 5F 37 DF C1 BB D3
E0 EE E9 FB E7 23 7F 5B 3E 54 6E 09 41 75 76
```

复算：

```python
t = bytes.fromhex('7164620d111a28332e2d5f37dfc1bbd3e0eee9fbe7237f5b3e546e09417576')
st, out = 0x31, bytearray()
for b in t:
    out.append(b ^ st ^ 8); st = (st + 7) & 0xFF
print(out.decode())      # HTUCTF{YOU ARE AINNER！！！}
```

字节确认：

```
48 54 55 43 54 46 7B  59 4F 55 20 41 52 45 20 41 49 4E 4E 45 52  EF BC 81 EF BC 81 EF BC 81  7D
H  T  U  C  T  F  {   Y  O  U  ' 'A  R  E  ' 'A  I  N  N  E  R    ！        ！        ！      }
```

提交时两个坑：
1. 是 `AINNER` 不是 `WINNER`（作者原样就这么写的，别手滑"纠正"）；
2. 三个感叹号是**全角 `！`**（U+FF01 / UTF-8 `EF BC 81`），不是 ASCII `!`。

---

## 8. 复现脚本

`solve.py`（本目录）就是第 0 节那条操作序列的自动化，靠 `recvuntil` 卡提示符，不 sleep 硬等：

```bash
python solve.py duel_arena.exe
# ...
# 石棺发出微光。
# HTUCTF{YOU ARE AINNER！！！}
```

同目录其它脚本：
- `xr.py`：给文件偏移/VA 找 rip 相对引用，或 `xr.py -d <va> <len>` 直接反汇编一段
- `probe.py`：按顺序喂答案，逐步打印程序输出（探路 / 做负向验证用）
- `search.py`：早期"正常磨 MP"路线的 DFS 搜索器（用于证明 17 回合内磨不死，结论见第 5 节）

---

## 9. 踩坑清单

1. **密钥不是 8 字节**。只看 `memcmp(..., 8)` 之类的印象会走偏；实际 `cmp rax,[len]` 里 `rax = 0 + 4`，密钥是 4 字节 `7391`。
2. **不读纸条 = 连招永远不触发**（`.data:0x1400E8010` 还停在 `'m'`）。这条只能靠动态验证发现，静态看表很容易漏掉那个单向改写。
3. **选项 4 需要先看过规则**（`0x1400E12108E`，否则小矮人拦人）；密钥 `7391` 不拦开战，但它是连招的四个前提之一（`0x1400E121089`），不输入就打不出秒杀。
4. **17 回合硬上限 + 一次 −35 的【决心】**，正常磨 MP 路线基本死路。
5. 胜利后必须回 `y` 看 CG，程序才会继续走到 `公主【呜呜…】→【拿走你们的奖励吧】→ 石棺发出微光 → flag`；回 `n` 会直接回主菜单，看不到 flag。
6. CG 是三张纯干扰图，flag 只在终端里。
