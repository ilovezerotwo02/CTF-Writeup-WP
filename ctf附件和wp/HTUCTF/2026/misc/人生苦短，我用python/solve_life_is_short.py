
flag = list("?" * 56)


def put(i, c):
    assert flag[i] in ("?", c), (i, flag[i], c)
    flag[i] = c


# flag[:7]=="HTUCTF{" , flag[54:]=="!}"
for i, ch in enumerate("HTUCTF{"):
    put(i, ch)
put(54, "!"); put(55, "}")

# flag[::-4].hex() == "7d40406e407231745f6324305043"
# 即 flag[55-4k] = 该 hex 的第 k 个字节
for k, ch in enumerate(bytes.fromhex("7d40406e407231745f6324305043")):
    put(55 - 4 * k, chr(ch))          # 55,51,47,...,3

put(8, "&")                            # "$".join(["P", flag[8]]) == "P$&"
put(14, "I")                           # lower()=="i" 且 isupper()
put(9, "t"); put(10, "h"); put(12, "n")  # "th_n"，flag[11] 是数字
put(17, "S"); put(18, "u"); put(20, "h")  # chr(+1) == "Tvdi"
put(22, chr(2 ** 6))                   # '@'
put(24, "f"); put(28, "@"); put(32, "c")  # flag[24:33:4].swapcase()=="F@C"
put(25, "@"); put(26, "n")             # b64(flag[25:28])=="QG50" -> "@nt"
put(29, "$"); put(30, "t")             # flag[29:31].hex()=="2474"
put(34, "p"); put(36, "0"); put(37, "g"); put(38, "r")   # rot13("ce0te")=="pr0gr"
put(40, "m"); put(41, "m"); put(42, "1")                 # reduce(...)==0x6D6D31
put(44, "g")                           # ord(flag[44])==ord(flag[36])+55
put(46, "1"); put(48, "n"); put(49, "g"); put(50, "u")   # swapcase()=="1@NGU"
put(52, "g"); put(53, "e")             # chr(+1)=="hf"

# split("_") 的长度序列 [13,2,4,1,9,11,10] -> 下划线位置
pos = 0
lens = [13, 2, 4, 1, 9, 11, 10]
for i, L in enumerate(lens):
    pos += L
    if i < len(lens) - 1:
        put(pos, "_")
        pos += 1

f = "".join(flag)
assert "?" not in f, flag
import hashlib
print(f)
print("len", len(f), "sum", sum(map(ord, f)), "sha256", hashlib.sha256(f.encode()).hexdigest())
# HTUCTF{P&th0n_I$_Such_@_f@nt@$t1c_pr0gr@mm1ng_1@ngu@ge!}
