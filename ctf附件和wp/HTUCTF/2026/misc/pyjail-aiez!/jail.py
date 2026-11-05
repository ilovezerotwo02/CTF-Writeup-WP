import ast
import base64
import io
import importlib.machinery
import os
import shutil
import sys
import tarfile
import tempfile

ALLOWED_CALLS = {"print", "len", "str", "int", "list", "dict", "range"}
ALLOWED_NODES = (ast.Module, ast.FunctionDef, ast.arguments, ast.Return,
                 ast.Expr, ast.Call, ast.Name, ast.Load, ast.Constant)
MAX_ARCHIVE = 512 * 1024
MAX_SOURCE = 64 * 1024


def check(src):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return "syntax error"

    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if len(funcs) != 1:
        return "exactly one function is allowed"
    fn = funcs[0]
    if fn.name != "run":
        return "function must be named run"
    if fn.decorator_list:
        return "decorators are not allowed"
    if fn.returns is not None:
        return "annotations are not allowed"
    args = fn.args
    if (args.posonlyargs or args.args or args.vararg or args.kwonlyargs
            or args.kwarg or args.defaults or args.kw_defaults):
        return "arguments are not allowed"

    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            return "disallowed syntax: " + type(node).__name__
        if isinstance(node, ast.Name):
            if not isinstance(node.ctx, ast.Load):
                return "assignment is not allowed"
            if node.id != "run" and node.id not in ALLOWED_CALLS:
                return "disallowed name: " + node.id
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_CALLS:
                return "disallowed call"
            if node.keywords or any(isinstance(x, ast.Starred) for x in node.args):
                return "star arguments are not allowed"
        if isinstance(node, ast.Constant):
            value = node.value
            if not isinstance(value, (str, bytes, int, float, bool, type(None))):
                return "bad constant"
            if isinstance(value, str) and not value.isascii():
                return "non-ascii string"
    return None


def main():
    print("python %d.%d" % (sys.version_info[0], sys.version_info[1]))
    sys.stdout.flush()
    line = sys.stdin.buffer.readline().strip()
    if not line:
        return
    workdir = tempfile.mkdtemp()
    try:
        try:
            raw = base64.b64decode(line, validate=True)
        except Exception:
            print("bad payload")
            return
        if len(raw) > MAX_ARCHIVE:
            print("payload too large")
            return
        try:
            tf = tarfile.open(fileobj=io.BytesIO(raw))
        except Exception:
            print("bad archive")
            return
        with tf:
            members = tf.getmembers()
            if len(members) > 4:
                print("bad archive")
                return
            for member in members:
                name = member.name.rstrip("/")
                if name.startswith("/") or ".." in name:
                    print("bad archive")
                    return
                if member.issym() or member.islnk():
                    print("bad archive")
                    return
                if not (member.isfile() or member.isdir()):
                    print("bad archive")
                    return
            try:
                tf.extractall(workdir, filter="fully_trusted")
            except TypeError:
                tf.extractall(workdir)

        src_path = os.path.join(workdir, "plugin.py")
        if not os.path.isfile(src_path):
            print("plugin.py not found")
            return
        if os.path.getsize(src_path) > MAX_SOURCE:
            print("source too large")
            return
        spec = importlib.machinery.PathFinder.find_spec("plugin", [workdir])
        if spec is None or not spec.origin:
            print("unexpected module")
            return
        if os.path.realpath(spec.origin) != os.path.realpath(src_path):
            print("unexpected module")
            return
        with open(src_path, "r", encoding="utf-8") as fh:
            source = fh.read()

        problem = check(source)
        if problem:
            print("rejected:", problem)
            return
        print("source check: ok")
        sys.stdout.flush()

        sys.path.insert(0, workdir)
        import plugin

        print("result:", plugin.run())
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


main()
