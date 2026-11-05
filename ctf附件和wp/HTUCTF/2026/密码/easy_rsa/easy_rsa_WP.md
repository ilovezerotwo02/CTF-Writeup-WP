# easy_rsa_WP

## 题目
Crypto / 1000分 / StaticAttachment。Ez_rsa.py 里 RSA 加密脚本，参数直接注释给出。

## 解题
p、q 都给了，直接算 d = inv(e, (p-1)(q-1))，m = c^d mod n。

```python
phi = (p-1)*(q-1)
d = pow(e, -1, phi)
m = pow(c, d, p*q)  # → b'HTU{now!you_know_rsa}'
```

## Flag
`HTU{now!you_know_rsa}`（submitId 2739，Accepted）
