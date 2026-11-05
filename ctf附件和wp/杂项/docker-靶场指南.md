# Docker 靶场 & 靶机 指令速查

---

## 一、靶场（Web 漏洞练习平台）

### 镜像名速查

| 靶场 | 镜像 | 端口 |
|------|------|------|
| DVWA | `vulnerables/web-dvwa` | 8083 |
| sqli-labs | `acgpiano/sqli-labs` | 8081 |
| upload-labs | `c0ny1/upload-labs` | 8082 |
| Pikachu | `area39/pikachu` | 8084 |
| WebGoat | `webgoat/webgoat-8.0` | 自定 |

### 常用命令

```powershell
# === 搜索 & 下载 ===
wsl -d ubuntu-24 docker search 关键字
wsl -d ubuntu-24 docker pull 镜像名
wsl -d ubuntu-24 docker images                    # 查看本地所有镜像

# === 启动 ===
wsl -d ubuntu-24 docker run -d --name 容器名 -p 宿主机端口:80 镜像名
# 加上自动重启（推荐）
wsl -d ubuntu-24 docker run -d --name 容器名 -p 宿主机端口:80 --restart=always 镜像名

# === 启停 ===
wsl -d ubuntu-24 docker stop 容器名               # 停止（数据保留）
wsl -d ubuntu-24 docker start 容器名              # 启动
wsl -d ubuntu-24 docker restart 容器名            # 重启

# === 查看状态 ===
wsl -d ubuntu-24 docker ps                        # 运行中的容器
wsl -d ubuntu-24 docker ps -a                     # 所有容器（含已停止）

# === 进入容器 ===
wsl -d ubuntu-24 docker exec -it 容器名 bash      # 进 shell
wsl -d ubuntu-24 docker logs 容器名               # 看日志

# === 删除 ===
wsl -d ubuntu-24 docker rm 容器名                 # 删除已停止的容器
wsl -d ubuntu-24 docker rm -f 容器名              # 强制删除（运行中也删）
wsl -d ubuntu-24 docker rmi 镜像名                # 删除镜像

# === 本地构建 ===
wsl -d ubuntu-24 docker build -t 镜像名 .         # 在 Dockerfile 所在目录执行
```

### 一个命令部署新靶场

```powershell
wsl -d ubuntu-24 docker run -d --name 名字 -p 端口:80 --restart=always 镜像名
```

---

## 二、靶机（VulnHub / 渗透测试）

### 流程

1. 去 [VulnHub](https://www.vulnhub.com) 下载 `.ova` 靶机
2. 导入 VirtualBox 或 VMware
3. 设置网络为 **桥接模式** 或 **NAT 网络**
4. 靶机和 Kali 在同一网段

### 获取靶机 IP（Kali 中执行）

```bash
sudo netdiscover -r 192.168.x.0/24    # ARP 扫描
# 或
sudo arp-scan -l                      # 快速扫本地网段
# 或
sudo nmap -sn 192.168.x.0/24          # ping 扫描
```

### Docker 跑靶机（部分靶机有 Docker 版）

```powershell
# 下载 vulnhub 靶机镜像后
wsl -d ubuntu-24 docker run -d --name 靶机名 -p 靶机端口:靶机端口 镜像名
# 然后用 Kali 去攻击 localhost:端口 即可
```

---

## 三、快速恢复全部靶场（当前部署）

```powershell
# 启动全部
wsl -d ubuntu-24 docker start dvwa sqli-labs upload-labs

# 停止全部
wsl -d ubuntu-24 docker stop dvwa sqli-labs upload-labs

# 查看全部状态
wsl -d ubuntu-24 docker ps -a --filter name=dvwa --filter name=sqli-labs --filter name=upload-labs
```

---

## 四、端口速查

| 服务 | 端口 |
|------|------|
| MCP Server | 3001 |
| DVWA | 8083 |
| sqli-labs | 8081 |
| upload-labs | 8082 |
| Pikachu | 8084 |

---

## 五、Docker Hub 被墙时配镜像加速

```powershell
# 查看当前配置
wsl -d ubuntu-24 cat /var/snap/docker/3505/config/daemon.json

# 添加加速器
wsl -d ubuntu-24 -u root bash -c 'cat > /var/snap/docker/3505/config/daemon.json << EOF
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://dockerproxy.cn",
    "https://hub.rat.dev"
  ]
}
EOF
snap restart docker'
```
