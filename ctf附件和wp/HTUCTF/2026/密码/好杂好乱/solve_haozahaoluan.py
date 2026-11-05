
import base64

cipher = ("344435413443353634443336353335323439333534363437353935393541353134393441"
          "35353536353535373433344634393436344435373334333534333537344235413433353734"
          "46353034393344")

# 1) 第一层 hex
s1 = bytes.fromhex(cipher).decode()
print("[1] hex      ->", s1)

# 2) 第二层 hex（解出来的仍是十六进制文本）
s2 = bytes.fromhex(s1).decode()
print("[2] hex      ->", s2)

# 3) base32
s3 = base64.b32decode(s2).decode()
print("[3] base32   ->", s3)

# 4) base64
s4 = base64.b64decode(s3).decode()
print("[4] base64   ->", s4)

# 5) 反转字符串
flag = s4[::-1]
print("[5] reverse  ->", flag)

# 语义还原：@ 代指 a（base x3 的 leet 写法）
print("[*] 语义还原  ->", flag.replace("@", "a"))
