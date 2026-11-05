import time
import random
from Crypto.Cipher import AES

def pad(string):
    if type(string) == str:
        string = string.encode()
    length = len(string)
    if length % 16 == 0:
        return string
    result = string + b"\x00" * (16 - length % 16)
    return result


rand = random.Random()
rand.seed(int(time.time()))
data = [rand.getrandbits(12) for _ in range(1664)]
secret_key = rand.getrandbits(32)
aes = AES.new(pad(str(secret_key)) ,AES.MODE_ECB)
msg = aes.encrypt(pad(flag))

print(f"{data=}")
print(f"{msg=}")