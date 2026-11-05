import base64
import dis
import marshal
import sys
import traceback
import types

if sys.version_info[:2] != (3, 10):
    sys.exit("unsupported runtime")

MAX_CODE = 1024
BANNED_OPS = {
    "IMPORT_NAME", "IMPORT_FROM", "IMPORT_STAR",
    "LOAD_NAME", "STORE_NAME", "DELETE_NAME",
    "LOAD_GLOBAL", "STORE_GLOBAL", "DELETE_GLOBAL",
    "LOAD_FAST", "STORE_FAST", "DELETE_FAST", "LOAD_CLOSURE",
    "LOAD_BUILD_CLASS", "LOAD_ASSERTION_ERROR", "LOAD_METHOD", "LOAD_ATTR",
    "MAKE_FUNCTION", "CALL_METHOD",
}


def reject(msg):
    print("reject:", msg)
    raise SystemExit(0)


def check(co):
    if type(co) is not types.CodeType:
        reject("not a code object")
    if len(co.co_code) > MAX_CODE:
        reject("too large")
    if co.co_names:
        reject("names are forbidden")
    if co.co_nlocals != 0 or co.co_varnames:
        reject("locals are forbidden")
    if any(isinstance(c, types.CodeType) for c in co.co_consts):
        reject("nested code objects are forbidden")
    for ins in dis.get_instructions(co):
        if ins.opname in BANNED_OPS:
            reject("banned opcode: " + ins.opname)


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
    except BaseException:
        sys.stdout.write(traceback.format_exc())
        sys.stdout.flush()
        return
    print("no exception")


main()
