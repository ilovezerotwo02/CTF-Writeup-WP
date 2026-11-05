# HTUCTF MISC「大杂烩 / Base Stew」Writeup

> 864 pts · 静态附件 `好吃吗.txt`（7 KB 纯文本）· 题面：`做的东西好吃吗😋`

## Flag

```
HTUCTF{15_m1x3d_573w_600d?}
```

谜底就是题面：**is mixed stew good?**（五花八门的 base 乱炖，味道如何）

## 一眼认出：这是 Chef 语言

附件不是 hex、不是 base64，而是一份"菜谱"：

```
Base Stew.
Ingredients.
61 g x 7
61 g w 7
...
Method.
Put x 7 into the mixing bowl.
Put w 7 into the mixing bowl.
...
Liquefy contents of the mixing bowl.
Pour contents of the mixing bowl into the baking dish.
Serves 180.
```

这是 esolang **Chef**（David Morgan-Mar, 2002）。本题只用到最核心的几条语法：

| 菜谱指令 | 语义 |
| --- | --- |
| `Ingredients.` 里的 `61 g x 7` | 声明配料 **x 7**，初始值 **61**（`g` 是干量单位 gram，没有实际作用） |
| `Put <配料> into the mixing bowl` | 把配料值**压栈**（mixing bowl = 栈） |
| `Liquefy contents of the mixing bowl` | 液化（栈操作后无额外影响） |
| `Pour ... into the baking dish` | 把碗里内容倒进烤盘 = **输出** |
| `Serves 180` | 出餐份数 = 输出字符数，这里是 **180** |

关键点：**mixing bowl 是栈，Pour 时从栈顶开始输出**，所以输出顺序 = 入碗顺序的**逆序**。

- 配料 180 个、`Put` 指令 180 条、`Serves 180`，三者对齐，说明每个配料恰好用一次，输出 180 个字符。
- 按**入碗顺序**取字符得到一个以 `==` 开头的乱串（非法 base64）；按**栈顶优先**（逆序）取字符，正好是 180 字符的合法 base64（以 `==` 结尾、180 % 4 == 0）。

```
Q3hjQk9OS2VhcnV2YVZ1TlVIS3lESkZTTDhHM2dUSFZMZldZZzhLelFTdkRHRHJKVHlXTmdmNW11djhDVHExOGNsVzk0WkdhNkxHbXByUXMwbmx3aVpiSXBLNlV3aUZxOVJMajF5R2VUMXFQOXl1VnV2Q1VaaTJkQ0FyekVQR1dKTlJURw==
```

## 五层 base 乱炖

后面就是"大杂烩"的部分了。每一层的**字符集**都能验证下一层是什么编码——这是识别多层 base 最可靠的办法。

| # | 编码 | 输入 | 输出 | 判定依据 |
| --- | --- | --- | --- | --- |
| 1 | **base64** | 180 字符 | 133 字符 | 以 `==` 结尾，长度 % 4 == 0 |
| 2 | **base62**（`0-9A-Za-z`） | 133 字符 | 99 字符 | 全是字母数字，四种字母表里只有 `0-9A-Za-z` 能解出可打印结果 |
| 3 | **base58**（Bitcoin 字母表） | 99 字符 | 72 字符 | 字符串里**完全没有 `0 O I l`**，正是 base58 的排除字符 |
| 4 | **base45**（RFC 9285） | 72 字符 | 48 字符 | 无小写字母，只有大写 + 数字 + `+` `*`，全在 base45 字母表 `0-9A-Z $%*+-./:` 内 |
| 5 | **base32**（RFC 4648） | 48 字符 | 27 字节 | 解出 `JBKF...H56Q====`，大写 + `2-7` + `====` 填充 |

中间值：

```
133: CxcBONKearuvaVuNUHKyDJFSL8G3gTHVLfWYg8KzQSvDGDrJTyWNgf5muv8CTq18clW94ZGa6LGmprQs0nlwiZbIpK6UwiFq9RLj1yGeT1qP9yuVuvCUZi2dCArzEPGWJNRTG
 99: 27T2MkMQPqnkqwbu6PrWK3hVnS6w6UmE37Qaw6NYNcqZ2McbLuhBhZeNUyvEMvordjA8nFmm3v17KpsPgca1PGFrnKP4BYR5CEz
 72: KH9AN9LN9FG6DC9HX6+M8+M9S+9CDBNCAUL6NS9EG661A4M6NS9TL6MB8HS8Z590*6HX7HX7
 48: JBKFKQ2UIZ5TCNK7NUYXQM3EL42TOM3XL43DAMDEH56Q====
 27: HTUCTF{15_m1x3d_573w_600d?}
```

## 复现

```bash
python solve_food.py source.txt
# [0] Chef: 配料 180 个 / 入碗 180 次 / Serves 180
# [1] base64 -> 133 ... [5] base32 -> 27 字节
# FLAG = HTUCTF{15_m1x3d_573w_600d?}
```

纯标准库，无第三方依赖。

## 踩坑记录

1. **栈顶 / 栈底方向**：先按入碗顺序拼串会得到 `==wRUJ...`（`==` 跑到最前面），一眼不对；逆序才是 base64。
2. **base62 的字母表**：`0-9A-Za-z`、`A-Za-z0-9`、`a-zA-Z0-9`、`0-9a-zA-Z` 四种里只有 `0-9A-Za-z`（数字打头）能解出全可打印输出，其余全是乱码字节。
3. **base58 的判据很好用**：`0` `O` `I` `l` 四个字符缺席 ≈ base58（Bitcoin 字母表）；flickr / ripple 字母表解出来是二进制乱码，可排除。
4. **base45 容易被漏**：72 字符、全大写、含 `+` `*`，第一反应会当成 base85。但 ascii85（`!`~`u`）、Z85（需长度 % 5 == 0）、RFC1924 三种 base85 全解成二进制，改用 base45（3 字符→2 字节）一次命中。
5. **不要用"自定义字母表"方向硬解**：我一度怀疑 72 字符串是"自定义字母表的 base32/base64"，用 45 字节全可打印做约束反推字母表——按 `HTUCTF{` 已知明文推导，base32 与 base64 都会出现"同一字符需要映射到两个不同值"的矛盾（ex. base32 第一组 `KH9AN9LN` 要求 `9` 既是 10 又要落在 48~63），从而排除了这条岔路，回头才发现是 base45。
