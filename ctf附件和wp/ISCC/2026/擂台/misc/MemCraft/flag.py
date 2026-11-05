import hashlib

def generate_flag(*answers):
    # 将所有答案使用英文逗号连接
    combined_answers = ','.join(answers)
    # 生成flag
    initial_flag = f"ISCC{{{hashlib.md5(combined_answers.encode()).hexdigest()}}}"
    return initial_flag

# 示例用法
if __name__ == "__main__":
    answers = [
        # n0o0b师傅在自己刚买的国产电脑上本地搭建了一个Minecraft服务器和wxm学姐等人进行游戏，可是不小心被蛤客zym获取到了shell，
        # 你能帮助n0o0b师傅找回被锁在无字天书中的照片并帮助他寻找zym是如何入侵的吗？
        # 本题使用的Minecraft服务器使用Frp进行穿透，连接的IP与题目无关，题目中需要分割的部分注意使用英文逗号分割
        # 题目一：蛤客zym在Minecraft游戏中的id是什么?
        "游戏ID",
        # 题目二：蛤客zym进入了与Minecraft相关的什么程序? 蛤客zym进入与Minecraft相关的程序使用的用户名和密码是什么?
        "程序名,用户名,密码",
        # 题目三：请从蛤客zym的入侵痕迹找出他通过上传了什么程序得到了shell?
        "上传文件完整名称",
        # 题目四：蛤客zym从主机中开启了服务并通过此服务获取了密码文件，请分析出他获取的nOo0b-PC中用户n0的密码?
        "系统中用户密码",
        # 题目五：请从蛤客zym的入侵痕迹中恢复出他的密码，解密wXm.vera中找回被删除的照片和其中的隐藏信息?
        "隐藏的字符串"
    ]
    # 生成MD5加密后的flag
    final_flag = generate_flag(*answers)
    # 输出最终的MD5加密字符串
    print(final_flag)