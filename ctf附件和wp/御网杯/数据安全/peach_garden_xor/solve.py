import codecs
import io
import re
import zipfile
from pathlib import Path


ZIP_HEADER = b"PK\x03\x04"


def find_task_zip(base: Path) -> Path:
    matches = sorted(base.rglob("task.zip"))
    if not matches:
        raise FileNotFoundError("task.zip not found under challenge directory")
    return matches[0]


def decrypt_docx(enc_data: bytes) -> tuple[bytes, bytes]:
    key = bytes(c ^ p for c, p in zip(enc_data[:4], ZIP_HEADER))
    dec = bytes(b ^ key[i % len(key)] for i, b in enumerate(enc_data))
    return key, dec


def recover_flag(docx_data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(docx_data)) as docx:
        document_xml = docx.read("word/document.xml").decode("utf-8", errors="ignore")

    match = re.search(r"synt\{[a-z0-9\-]+\}", document_xml, re.IGNORECASE)
    if not match:
        raise ValueError("flag candidate not found in word/document.xml")

    return codecs.decode(match.group(0), "rot_13")


def main() -> None:
    base = Path(__file__).resolve().parent
    task_zip = find_task_zip(base)

    with zipfile.ZipFile(task_zip) as archive:
        enc_name = next(name for name in archive.namelist() if name.endswith(".enc"))
        enc_data = archive.read(enc_name)

    key, docx_data = decrypt_docx(enc_data)
    flag = recover_flag(docx_data)

    print(f"task.zip: {task_zip}")
    print(f"xor key: {key.hex()}")
    print(f"flag: {flag}")


if __name__ == "__main__":
    main()
