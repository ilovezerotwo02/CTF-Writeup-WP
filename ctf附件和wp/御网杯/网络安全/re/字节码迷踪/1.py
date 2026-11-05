import binascii
import marshal
import re
import types
from pathlib import Path


FLAG_RE = re.compile(r"flag\{[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}\}")


def walk_consts(obj):
    if isinstance(obj, types.CodeType):
        for item in obj.co_consts:
            yield from walk_consts(item)
    else:
        yield obj


def looks_like_b64(s):
    if not isinstance(s, str) or len(s) < 16:
        return False
    return re.fullmatch(r"[A-Za-z0-9+/=]+", s) is not None


def main():
    blob = Path(__file__).with_name("py_obf_08.pyc").read_bytes()
    root = marshal.loads(blob[16:])
    pool = list(walk_consts(root))

    texts = [x for x in pool if looks_like_b64(x)]
    keys = [x for x in pool if isinstance(x, int) and 0 <= x < 256]

    for text in texts:
        try:
            raw = binascii.a2b_base64(text)
        except binascii.Error:
            continue

        for key in keys:
            plain = bytes(c ^ key for c in raw)
            hit = FLAG_RE.search(plain.decode("latin1", errors="ignore"))
            if hit:
                print(hit.group(0))
                return

    raise SystemExit("flag not found")


if __name__ == "__main__":
    main()
