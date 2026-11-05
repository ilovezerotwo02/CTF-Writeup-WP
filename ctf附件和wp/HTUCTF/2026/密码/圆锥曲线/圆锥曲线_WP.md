# 圆锥曲线_WP

## 题目
- 分类：Crypto / 1000分 / StaticAttachment
- 描述：重生在高考数学写圆锥曲线的现场。草稿纸上的方程从来没见过：x^2 - D*y^2 = 1 (mod p)
- 附件：圆锥曲线.zip（protocol.py + public.txt）

## 分析
protocol.py 定义了 Pell 型 Diffie-Hellman：
- 群：F_p[√3] 中范数 x²-3y²=1 的元素，运算是环乘法
  `(x1,y1)+(x2,y2) = (x1x2+3y1y2, x1y2+x2y1)`
- G 生成元、公钥 P_A=aG、P_B=bG，共享点 x 坐标 → SHA256 → AESGCM 解密 flag

关键观察：
1. `norm(G)=norm(P_A)=norm(P_B)=1`，确实是范数 1 子群
2. legendre(3,p) = -1（3 是非二次剩余）⇒ F_p[√3]≅F_{p²}，范数 1 子群阶 = **p+1**
3. 分解 p+1 = **2¹⁵ × 7 个 35-bit 素数**（完全光滑！）
   - p-1 方法 / Pollard rho 找出全部 7 个因子（每个约 35 bit）
   - 21880660013, 19386034781, 25626614479, 18117811853, 29077022453, 21613218131, 27786452483

## 解题
Pohlig-Hellman：对每个素数幂 q^e 把 DLP 降到 q^e 阶子群（cofactor 作用），BSGS 解（最大 2¹⁵=32768，秒出），CRT 合并得私钥 a。

脚本：`solve_pell.py`（p-1/rho 分解 + PH + AESGCM 解密）

```
a = 109873721430400459426418166762509644759336450558522226422625390900617963408412
shared = a*P_B
key = sha256(x_shared) → AESGCM 解密
```

## Flag
`HTUCTF{I_hate_conic_section}`（submitId 2737，Accepted）
