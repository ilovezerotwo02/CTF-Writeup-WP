# 人生苦短，我用python（Misc 864pt）

- 附件：`life_is_short.zip` → `life_is_short.py`（1.9 KB）
- 脚本：`solve_life_is_short.py`
- flag：`HTUCTF{P&th0n_I$_Such_@_f@nt@$t1c_pr0gr@mm1ng_1@ngu@ge!}`

## 题目

一个 56 字符的输入校验脚本，20 多条 `if`，满足全部就打印 `Amazing! You solved it!`。
没有任何加密，**纯约束**，逐条反解即可。

```python
if len(flag) != 56: abort()
if flag[:7] != "HTUCTF{" or flag[54:] != "!}": abort()
if list(map(len, flag.split("_"))) != [13, 2, 4, 1, 9, 11, 10]: abort()
if flag.count("@") != 6 or flag.count("1") != 3: abort()
if flag[::-4].encode().hex() != "7d40406e407231745f6324305043": abort()   # 反向取模 4
...
if sum(map(ord, flag)) != 4887: abort()
if sha256(flag) != "1b051f...": abort()
```

## 逐条拆解（关键在几个"反向"的约束）

| 约束 | 反解结果 |
| --- | --- |
| `flag[::-4].hex() == 7d4040...` | 它是**倒序步长 4**，即 `flag[55-4k]`，14 个字节直接钉死下标 55,51,47,…,3 |
| `"$".join(["P", flag[8]]) == "P$&"` | `flag[8]='&'` |
| `flag[14].lower()=="i" and flag[14].isupper()` | 只能是 `'I'`（大写且小写是 i） |
| `"".join("_" if c.isdigit() else c for c in flag[9:13]) == "th_n"` | `flag[9:13]="th0n"` |
| `chr(ord(c)+1) for flag[17:21] == "Tvdi"` | `"Such"` |
| `flag[22] == chr(2**6)` | `'@'` |
| `base64.b64encode(flag[25:28]) == b"QG50"` | `flag[25:28]="@nt"` |
| `flag[29:31].hex() == "2474"` | `"$t"` |
| `flag[34:39].translate(rot13) == "ce0te"` | rot13 自逆 → `"pr0gr"` |
| `reduce(lambda a,b: a*256+ord(b), flag[40:43]) == 0x6D6D31` | `"mm1"` |
| `ord(flag[44]) == ord(flag[36]) + 55` | `'g'`（flag[36]='0'） |
| `chr(ord(flag[31])+14) == "?"` | `'1'` |
| `exec(base64)` 里是 `flag[46:51].swapcase() != "1@NGU"` | `"1@ngu"` |
| `chr(ord(c)+1) for flag[52:54] == "hf"` | `"ge"` |
| 分组长 `[13,2,4,1,9,11,10]` | 定出 6 个下划线位置：13,16,21,23,33,45 |

拼起来：

```
HTUCTF{P&th0n_I$_Such_@_f@nt@$t1c_pr0gr@mm1ng_1@ngu@ge!}
```

校验：`@`×6、`1`×3、`sum(ord)==4887`、`sha256` 全对（脚本里有断言），
并且把 flag 喂给原脚本能打印 `Amazing! You solved it!`。

## 小结

这类题不要手撸——把每条 `if` 翻译成 `put(index, char)`，遇到 `[::-4]`、`translate(rot13)`、
`reduce(...*256+ord)`、`swapcase()` 这种"反向"操作，先想清楚它到底固定了哪些下标/字符，
剩下的自然就唯一了。最后的 `sha256` 只是校验，不需要爆破。
