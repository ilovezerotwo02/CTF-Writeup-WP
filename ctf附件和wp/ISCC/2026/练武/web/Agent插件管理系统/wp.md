# ISCC 2026 Web - Agent插件管理系统

**Team:** zerotwo
**Solves:** 2113  
**Flag:** `ISCC{aunXV6waj5Hp8cT35SwVcKK}`

---

## 1. 环境探测

目标 `http://39.105.213.28:9000` 是一个 Spring Boot 应用，提供 Agent 插件管理功能。

关键页面：
- `/plugins` — 可下载 `agent-core.jar` 和 `sample-plugin.zip`
- `/upload` — 上传插件 ZIP
- `/my-plugins` — 配置 update_url
- `/logs` — 查看 Agent 日志

HTML 注释中泄露了以下信息：

```
/upload:     <!-- TODO: remove debug endpoint /api/debug/flag before production -->
/my-plugins: <!-- Hidden admin panel: /api/admin/flag?token=admin_token_here -->
/logs:       <!-- Debug: try accessing /api/logs?team_id=admin for system-level logs -->
```

`/api/logs?team_id=admin` 接口无需认证，后续作为数据回显通道。

---

## 2. 附件逆向

`sample-plugin.zip` 解压得到：
- `manifest.json` — 插件配置 + HMAC 签名
- `metadata.ser` — Java 序列化对象

`agent-core.jar` 使用 jd-gui 反编译，关注 `com.agent.update.deserialization` 包。

### 2.1 PluginLoader — 反序列化入口

```java
public static void loadPlugin(String path) throws Exception {
    byte[] data = Files.readAllBytes(Paths.get(path));
    ByteArrayInputStream bais = new ByteArrayInputStream(data);
    CustomObjectInputStream ois = new CustomObjectInputStream(bais);
    Object obj = ois.readObject();                    // <= 反序列化
    if (obj instanceof ResourceRefresher) {
        ((ResourceRefresher) obj).refresh();           // <= 触发利用链
    }
}
```

`CustomObjectInputStream` 继承 `ObjectInputStream`，`resolveClass()` 直接调 `super.resolveClass()` — **无类白名单**。

### 2.2 ResourceRefresher — 自动触发点

```java
private void readObject(ObjectInputStream ois) {
    ois.defaultReadObject();  // 恢复 targetPath, dataStream
    refresh();                // 自动执行！
}

public void refresh() {
    if (targetPath != null && dataStream != null) {
        dataStream.process(targetPath);
    }
}
```

### 2.3 DataStream — 桥接

```java
public void process(String path) {
    if (exporter != null) {
        exporter.export(path);
    }
}
```

### 2.4 FileExporter — 文件读取 + 日志回显

```java
public void export(String path) {
    try {
        byte[] bytes = Files.readAllBytes(Paths.get(path));
        String content = new String(bytes);
        LogService.log(teamId, "FILE_EXPORT",
            "Exported:" + path + ", Content:" + content);
    } catch (IOException e) {
        LogService.log(teamId, "FILE_EXPORT_ERROR",
            "Failed to export:" + path + ", Error:" + e.getMessage());
    }
}
```

将 `teamId` 设为 `"admin"`，文件内容即写入 admin 队伍日志。

### 2.5 Constants — 硬编码密钥

```java
public static final String HMAC_KEY = "k3y_5A62_X86";
public static final String FLAG_PATH = "/etc/flag";
```

---

## 3. 攻击面分析

### 3.1 上传路径

`POST /api/upload?team_id=x` → `extractPlugin()` 解压 → `validatePlugin()` 校验 HMAC → `loadPluginMetadata()` 反序列化

Zip Slip：`extractDir.resolve(entry.getName())` 无路径过滤。但 Spring Boot 运行在 Docker 容器中，模板目录（`/app/templates/`、`/app/static/`）挂载为只读，无法覆盖。

### 3.2 update_url 路径（绕过 HMAC）

`POST /api/config/update_url?team_id=x&url=x` → `setUpdateUrl()` → `triggerUpdate()` → HTTP 下载文件 → `PluginLoader.loadPlugin()` 直接反序列化

**这条路径不经过 HMAC 校验。** 只需将原始序列化 payload 托管到任意 HTTP 服务器，即可触发。

---

## 4. Payload 构造

### 利用链

```
ResourceRefresher.readObject()
  → defaultReadObject()
  → refresh()
    → dataStream.process(targetPath)
      → exporter.export(targetPath)
        → Files.readAllBytes(path)
        → LogService.log("admin", "FILE_EXPORT", content)
```

### 对象结构

```
FileExporter { teamId = "admin" }
  └── DataStream { exporter = ↑ }
        └── ResourceRefresher { targetPath = "/app/agent-update-system.jar", dataStream = ↑ }
```

---

## 5. Flag 获取过程

1. 读 `/etc/flag` → `ISCC{f4k3_fl4g_d3c0y_d0nt_subm1t}`（诱饵）
2. 读 `/proc/1/cmdline` → `java -jar /app/agent-update-system.jar --server.port=8080`
3. 读 `/proc/1/environ`、`/proc/1/mounts` 确认 Docker 环境
4. 读 `/app/agent-update-system.jar`（约 19MB），在日志中搜索 `ISCC{}` 模式
5. 提取到真 Flag：`ISCC{aunXV6waj5Hp8cT35SwVcKK}`

---

## 6. 漏洞总结

| # | 漏洞类型 | CWE | 说明 |
|---|---------|-----|------|
| 1 | Java 反序列化无白名单 | CWE-502 | CustomObjectInputStream.resolveClass() 直接调父类 |
| 2 | 硬编码密钥 | CWE-798 | HMAC 密钥 k3y_5A62_X86 在 Constants.class 中 |
| 3 | Zip Slip | CWE-22 | extractDir.resolve(name) 无路径过滤 |
| 4 | 信息泄露 | CWE-200 | HTML 注释暴露内部接口 |
| 5 | readObject 设计缺陷 | — | ResourceRefresher 在 readObject 中自动触发 refresh |
