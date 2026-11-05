import base64
import functools
import hashlib

def abort():
    print("Incorrect! Keep trying, you're close!")
    exit(1)

print("Welcome to HTUCTF!")
flag = input("Enter the flag: ")

if len(flag) != 56:
    abort()
if len(flag.encode()) != 56:
    abort()
if flag[:7] != "HTUCTF{" or flag[54:] != "!}":
    abort()
if list(map(len, flag.split("_"))) != [13, 2, 4, 1, 9, 11, 10]:
    abort()
if not (flag[0].isalpha() and flag[7].isupper()):
    abort()
if flag.count("@") != 6 or flag.count("1") != 3:
    abort()
if flag[::-4].encode().hex() != "7d40406e407231745f6324305043":
    abort()
if "$".join(["P", flag[8]]) != "P$&":
    abort()
if flag[14].lower() != "i" or not flag[14].isupper():
    abort()
if "".join("_" if c.isdigit() else c for c in flag[9:13]) != "th_n":
    abort()
if "".join(chr(ord(c) + 1) for c in flag[17:21]) != "Tvdi":
    abort()
if flag[22] != chr(2 ** 6):
    abort()
if flag[24:33:4].swapcase() != "F@C":
    abort()
if base64.b64encode(flag[25:28].encode()) != b"QG50":
    abort()
if flag[29:31].encode().hex() != "2474":
    abort()
_t = str.maketrans("abcdefghijklmnopqrstuvwxyz",
                   "nopqrstuvwxyzabcdefghijklm")
if flag[34:39].translate(_t) != "ce0te":
    abort()
if functools.reduce(lambda a, b: a * 256 + ord(b), flag[40:43], 0) != 0x6D6D31:
    abort()
if ord(flag[44]) != ord(flag[36]) + 55:
    abort()
if not flag[31].isnumeric() or chr(ord(flag[31]) + 14) != "?":
    abort()
if not (flag[31] == flag[42] == flag[46]):
    abort()
if flag[26] != flag[43]:
    abort()
if "".join(map(lambda c: chr(ord(c) + 1), flag[52:54])) != "hf":
    abort()
exec(base64.b64decode(b"aWYgZmxhZ1s0Njo1MV0uc3dhcGNhc2UoKSAhPSAiMUBOR1UiOgogICAgYWJvcnQoKQo="))
if sum(map(ord, flag)) != 4887:
    abort()
if hashlib.sha256(flag.encode()).hexdigest() != \
        "1b051ffd05ada83d6e60f8c785aa93c37fa5dec563f211dc962836eb257add3f":
    abort()

print("Amazing! You solved it!")
