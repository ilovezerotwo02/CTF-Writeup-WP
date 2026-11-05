import base64
import marshal
from pathlib import Path


def extract_flag(pyc_path: Path) -> str:
    data = pyc_path.read_bytes()
    code = marshal.loads(data[16:])
    main_code = code.co_consts[3]
    encoded_flag = main_code.co_consts[1]
    xor_key = main_code.co_consts[2]
    decoded = base64.b64decode(encoded_flag)
    return "".join(chr(byte ^ xor_key) for byte in decoded)


if __name__ == "__main__":
    pyc_file = Path(__file__).with_name("py_obf_08.pyc")
    print(extract_flag(pyc_file))
