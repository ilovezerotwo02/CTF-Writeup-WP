from secret import flag
import gmpy2
import decimal
from Crypto.Util.number import *

def gethint(h,p):
    decimal.getcontext().prec = 1024
    H = decimal.Decimal(int(h))
    P = decimal.Decimal(int(p))
    leak = decimal.Decimal((8*H*P - 1) / (16*P*P))
    return leak
p = getPrime(512)
q = getPrime(512)
f = getPrime(512)
g = getPrime(128)
h = gmpy2.invert(f, p) * g % p

n = f*q
e = 65537
m = bytes_to_long(flag)

c = pow(m,e,n)
print('c =', c)
print('hint =', gethint(h,p))
print('n =',n)