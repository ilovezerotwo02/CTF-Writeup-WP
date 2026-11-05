"""按实测机制搜索一条 17 回合内把夜族王气力磨到 0 的行动序列。"""
import sys
from functools import lru_cache

PM, EM = 105, 105          # 初始气力
PHP, EHP = 100, 145        # 初始氧气
PMPMAX, EMPMAX = 130, 135
LIMIT = 17


def enemy_action(turn):
    tab = [0, 1, 2, 0, 2, 1, 0, 2, 1, 0]     # 0 攻击 1 恢复 2 夺取
    return tab[(turn - 1) % 10]


def drain_amount(turn):
    return 17 + (turn % 5)


best = []


def dfs(turn, php, pmp, ehp, emp, will, path):
    if ehp <= 0 or emp <= 0:
        return path
    if php <= 0 or pmp <= 0:
        return None
    if turn > LIMIT:
        return None
    if len(path) > 24:
        return None
    for act in '1234':
        n_php, n_pmp, n_ehp, n_emp = php, pmp, ehp, emp
        if act == '1':                       # 吸：偷 6~10 氧气（取最差 6）
            n_ehp -= 6
        elif act == '2':                     # 塞舌头：自己 -23 气力
            if pmp <= 22:
                continue
            n_pmp -= 23
            n_emp -= 34 if emp <= 70 else 22
        elif act == '3':                     # 忍耐：+24 气力
            n_pmp = min(PMPMAX, pmp + 24)
        elif act == '4':
            pass
        if n_emp <= 0 or n_ehp <= 0:
            return path + act
        # 敌方行动
        ea = enemy_action(turn)
        if ea == 0:
            n_php -= 16
        elif ea == 1:
            n_emp = min(EMPMax := 135, n_emp + 18)
        else:
            n_pmp -= drain_amount(turn)
            if not will and ehp > 49 and n_emp <= 49:
                n_pmp -= 35
                will = True
        if n_php <= 0 or n_pmp <= 0:
            continue
        r = dfs(turn + 1, n_php, n_pmp, n_ehp, n_emp, will, path + act)
        if r:
            return r
    return None


r = dfs(1, PHP, PM, EHP, EM, False, '')
print('worst-case:', r)
