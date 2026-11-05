import base64
import dis
import marshal
import sys
import types

if sys.version_info[:2] != (3, 13):
    sys.exit("unsupported runtime")

MAX_CODE = 2048
BANNED_OPS = {
    "LOAD_NAME", "STORE_NAME", "DELETE_NAME",
    "LOAD_GLOBAL", "STORE_GLOBAL", "DELETE_GLOBAL",
    "LOAD_FROM_DICT_OR_GLOBALS", "LOAD_FROM_DICT_OR_DEREF",
    "IMPORT_NAME", "IMPORT_FROM", "IMPORT_STAR",
    "LOAD_BUILD_CLASS", "LOAD_LOCALS", "LOAD_ASSERTION_ERROR",
    "LOAD_FAST", "LOAD_FAST_CHECK", "LOAD_FAST_AND_CLEAR", "LOAD_FAST_BORROW",
    "LOAD_FAST_BORROW_LOAD_FAST_BORROW", "LOAD_FAST_LOAD_FAST",
    "STORE_FAST", "STORE_FAST_LOAD_FAST", "STORE_FAST_STORE_FAST", "DELETE_FAST",
    "MAKE_FUNCTION", "SET_FUNCTION_ATTRIBUTE",
}


def reject(msg):
    print("reject:", msg)
    raise SystemExit(0)


def check(co):
    if type(co) is not types.CodeType:
        reject("not a code object")
    if len(co.co_code) > MAX_CODE:
        reject("too large")
    if co.co_nlocals != 0 or co.co_varnames:
        reject("locals are forbidden")
    if any(isinstance(c, types.CodeType) for c in co.co_consts):
        reject("nested code objects are forbidden")
    for ins in dis.get_instructions(co):
        if ins.opname in BANNED_OPS:
            reject("banned opcode: " + ins.opname)
        if ins.opname == "LOAD_CONST" and isinstance(ins.argval, types.CodeType):
            reject("nested code objects are forbidden")


def main():
    sys.stdout.write("payload(base64 marshal) > ")
    sys.stdout.flush()
    line = sys.stdin.buffer.readline().strip()
    if not line:
        return
    try:
        co = marshal.loads(base64.b64decode(line, validate=True))
    except Exception as e:
        print("bad payload:", type(e).__name__)
        return
    try:
        check(co)
    except SystemExit:
        return
    except Exception as e:
        print("bad payload:", type(e).__name__)
        return

    try:
        eval(co, {"__builtins__": None})
    except BaseException as e:
        print("runtime:", type(e).__name__)
        return
    print("ok")


main()
