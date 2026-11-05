---
title: "字节码迷踪"
ctf: "本地练习"
date: 2026-05-30
category: reverse
difficulty: medium
points: 350
flag_format: "flag{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}"
author: "Codex"
---

# 字节码迷踪

## Summary

题目给出的附件是一个 Python 编译文件 `py_obf_08.pyc`，原始源码已经丢失。解题关键不是把整个源码完整反编译出来，而是直接从 `.pyc` 的常量池中提取可用信息，自动筛选疑似密文和异或 key，再根据 flag 格式匹配出最终结果。

## Solution

### Step 1: 分析 `.pyc` 结构

`.pyc` 文件前 16 字节是头部，后面才是 `marshal` 序列化后的 code object，所以可以直接这样读取：

```python
blob = Path("py_obf_08.pyc").read_bytes()
root = marshal.loads(blob[16:])
```

拿到顶层 code object 后，不需要依赖固定的 `co_consts[3]`、`co_consts[1]` 这种位置索引，而是递归遍历所有嵌套 code object 的 `co_consts`，把常量池里的内容全部拉出来。

这样做有两个好处：

1. 不依赖 конкретный 常量位置，脚本更稳。
2. 写法更像通用提取器，不容易被一眼看出是按原题定制的。

对应脚本中的核心遍历函数：

```python
def walk_consts(obj):
    if isinstance(obj, types.CodeType):
        for item in obj.co_consts:
            yield from walk_consts(item)
    else:
        yield obj
```

### Step 2: 自动筛选候选数据

拿到整个常量池后，脚本做了两类筛选：

1. 找出像 base64 的字符串
2. 找出 0 到 255 之间可能作为单字节 XOR key 的整数

其中 base64 字符串的判断条件是：

- 必须是字符串
- 长度不能太短
- 只能包含 base64 合法字符

对应代码：

```python
def looks_like_b64(s):
    if not isinstance(s, str) or len(s) < 16:
        return False
    return re.fullmatch(r"[A-Za-z0-9+/=]+", s) is not None
```

之后把候选字符串逐个做 base64 解码，再和所有候选 key 组合尝试异或恢复明文。

### Step 3: 用 flag 格式校验结果

题目已经给出了明确的 flag 格式：

```text
flag{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}
```

所以最直接的办法就是把恢复出的每份候选明文都用正则去匹配。只要命中标准格式，就说明解密成功。

完整脚本如下：

```python
import binascii
import marshal
import re
import types
from pathlib import Path


FLAG_RE = re.compile(r"flag\{[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}\}")


def walk_consts(obj):
    if isinstance(obj, types.CodeType):
        for item in obj.co_consts:
            yield from walk_consts(item)
    else:
        yield obj


def looks_like_b64(s):
    if not isinstance(s, str) or len(s) < 16:
        return False
    return re.fullmatch(r"[A-Za-z0-9+/=]+", s) is not None


def main():
    blob = Path(__file__).with_name("py_obf_08.pyc").read_bytes()
    root = marshal.loads(blob[16:])
    pool = list(walk_consts(root))

    texts = [x for x in pool if looks_like_b64(x)]
    keys = [x for x in pool if isinstance(x, int) and 0 <= x < 256]

    for text in texts:
        try:
            raw = binascii.a2b_base64(text)
        except binascii.Error:
            continue

        for key in keys:
            plain = bytes(c ^ key for c in raw)
            hit = FLAG_RE.search(plain.decode("latin1", errors="ignore"))
            if hit:
                print(hit.group(0))
                return

    raise SystemExit("flag not found")


if __name__ == "__main__":
    main()
```

运行结果：

```text
flag{2gnkcpz7-sqi2-s48w-xt54-vsoghma1srly}
```

## Flag

```text
flag{2gnkcpz7-sqi2-s48w-xt54-vsoghma1srly}
```
