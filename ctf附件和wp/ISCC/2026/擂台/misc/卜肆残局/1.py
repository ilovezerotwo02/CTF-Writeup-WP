import base64
import csv
import hashlib
import io
import re
import tarfile
import tempfile
import zipfile
from pathlib import Path

import py7zr
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
FUXI_ORDER = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
SEASON_PICK = {
    "春": ("立春", "春分"),
    "夏": ("立夏", "夏至"),
    "秋": ("立秋", "秋分"),
    "冬": ("立冬", "冬至"),
}


def find_single(base: Path, pattern: str) -> Path:
    matches = list(base.rglob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(f"expected exactly one {pattern}, got {len(matches)}")
    return matches[0]


def find_named(base: Path, filename: str) -> Path:
    matches = [path for path in base.rglob("*") if path.is_file() and path.name == filename]
    if len(matches) != 1:
        raise FileNotFoundError(f"expected exactly one {filename}, got {len(matches)}")
    return matches[0]


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-16", "gbk"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("read_text", b"", 0, 1, f"cannot decode {path}")


def decode_attachment_zip(base: Path) -> dict[str, str]:
    note_zip = find_named(base, "夹页录.zip")
    decoded: dict[str, str] = {}
    with zipfile.ZipFile(note_zip, "r") as zf:
        for name in zf.namelist():
            content = zf.read(name).decode("utf-8")
            decoded[name] = content
    return decoded


def solve_heaven(svg_path: Path) -> tuple[str, str]:
    svg = svg_path.read_text(encoding="utf-8")
    coins: dict[str, dict[str, str]] = {}
    pattern = re.compile(r'<g class="coin [^"]+" id="(outer|inner)-([^"]+)">(.*?)</g>', re.S)
    for ring, seat, body in pattern.findall(svg):
        levels = sorted(set(float(y) for y in re.findall(r'y1="([0-9.]+)"', body)))
        bits = []
        for y in levels:
            hits = len(re.findall(fr'y1="{y}"', body))
            bits.append("0" if hits == 2 else "1")
        coins.setdefault(seat, {})[ring] = "".join(bits)

    heaven_b64 = "".join(coins[seat]["outer"] + coins[seat]["inner"] for seat in FUXI_ORDER)
    heaven_b64 = "".join(B64[int(bits, 2)] for bits in re.findall(r".{6}", heaven_b64))
    return heaven_b64, base64.b64decode(heaven_b64).decode("utf-8")


def solve_human(text_path: Path, attachment_notes: dict[str, str]) -> tuple[str, str]:
    text = text_path.read_text(encoding="utf-8").split("旁注数条：")[0]
    parts = re.split(r"【([^】]+)】\n", text)[1:]
    gates = {}
    for i in range(0, len(parts), 2):
        name = parts[i].replace("门", "")
        body = parts[i + 1].strip()
        note = re.search(r"批注：([A-Za-z0-9+/=]+)", body)
        if note is None:
            continue
        rule = base64.b64decode(note.group(1)).decode("utf-8")
        lines = re.sub(r"批注：[A-Za-z0-9+/=]+", "", body).strip().splitlines()
        gates[name] = {
            "drop": [CN_NUM[ch] for ch in rule if ch in CN_NUM],
            "lines": [line.strip() for line in lines if line.strip()],
        }

    gate_note = attachment_notes["门位札记.txt"]
    gate_order_b64 = re.search(r"唱门旧次：([A-Za-z0-9+/=]+)", gate_note)
    if gate_order_b64 is None:
        raise ValueError("missing gate order")
    gate_order = list(base64.b64decode(gate_order_b64.group(1)).decode("utf-8"))

    human_b64_chars = []
    for gate in gate_order:
        remaining = [
            line for idx, line in enumerate(gates[gate]["lines"], start=1) if idx not in gates[gate]["drop"]
        ]
        bits = "".join("0" if line.endswith("。") else "1" for line in remaining)
        human_b64_chars.append(B64[int(bits, 2)])

    human_b64 = "".join(human_b64_chars)
    return human_b64, base64.b64decode(human_b64).decode("utf-8")


def solve_earth(bmp_path: Path) -> tuple[str, str]:
    data = bmp_path.read_bytes()
    start = data.find(b"PK\x03\x04")
    if start == -1:
        raise ValueError("no appended zip found in bmp")

    with zipfile.ZipFile(io.BytesIO(data[start:]), "r") as outer_zip:
        inner_zip_name = next(name for name in outer_zip.namelist() if name.endswith(".zip"))
        inner_zip_bytes = outer_zip.read(inner_zip_name)

    with zipfile.ZipFile(io.BytesIO(inner_zip_bytes), "r") as middle_zip:
        gz_name = next(name for name in middle_zip.namelist() if name.endswith(".gz"))
        gz_bytes = middle_zip.read(gz_name)

    with tarfile.open(fileobj=io.BytesIO(gz_bytes), mode="r:gz") as tar:
        palace_text = tar.extractfile("覆土匣/后天九宫.txt").read().decode("utf-8")
        tar.extractfile("覆土匣/圆图别录.txt").read().decode("utf-8")
        book_text = tar.extractfile("覆土匣/字契簿.txt").read().decode("utf-8")

    palace_to_token = {}
    for palace, _, token in re.findall(r"([坎坤震巽中乾兑艮离])([一二三四五六七八九])：(\S+)", palace_text):
        palace_to_token[palace] = token
    token_to_char = dict(re.findall(r"(\S)：(\S)", book_text))
    order = [palace for palace, _ in re.findall(r"([坎坤震巽中乾兑艮离])([一二三四五六七八九])", palace_text.splitlines()[3])]

    earth_b64 = "".join(token_to_char[palace_to_token[palace]] for palace in order if palace != "中")
    return earth_b64, base64.b64decode(earth_b64).decode("utf-8")


def solve_season(csv_path: Path, attachment_notes: dict[str, str]) -> tuple[str, str]:
    raw = csv_path.read_text(encoding="utf-16")
    rows = list(csv.DictReader(io.StringIO("\n".join(raw.splitlines()[6:]))))
    row_by_name = {row["节气"]: row for row in rows}

    clue_text = attachment_notes["候气骨谜.txt"]
    picks = []
    for season in ("春", "夏", "秋", "冬"):
        if f"{season}骨" not in clue_text:
            raise ValueError(f"missing {season} clue")
        picks.extend(SEASON_PICK[season])

    season_b64_chars = []
    for name in picks:
        row = row_by_name[name]
        bits = "".join("0" if piece.strip() == "忌" else "1" for piece in row["六断"].split("/"))
        season_b64_chars.append(B64[int(bits, 2)])

    season_b64 = "".join(season_b64_chars)
    return season_b64, base64.b64decode(season_b64).decode("utf-8")


def load_outer_payloads(base: Path) -> tuple[bytes, bytes]:
    outer = base / ".zip"
    with zipfile.ZipFile(outer, "r") as zf:
        root_files = [info.filename for info in zf.infolist() if "/" not in info.filename.rstrip("/")]
        peek_name = next(name for name in root_files if name.endswith(".zip"))
        final_name = next(name for name in root_files if name.endswith(".7z"))
        return zf.read(peek_name), zf.read(final_name)


def derive_stage_two(peek_zip_bytes: bytes, mid: str) -> tuple[str, str]:
    password = hashlib.md5(mid.encode("utf-8")).hexdigest()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        with zipfile.ZipFile(io.BytesIO(peek_zip_bytes), "r") as zf:
            zf.extractall(out_dir, pwd=password.encode("utf-8"))
            comment = zf.comment.decode("utf-8")

        txt_files = sorted(
            out_dir.rglob("*.txt"),
            key=lambda path: int(re.search(r"\d+", path.stem).group()) if re.search(r"\d+", path.stem) else path.stem,
        )
        if len(txt_files) != 64:
            raise ValueError(f"expected 64 txt files, got {len(txt_files)}")

        chars = []
        for index, marker in enumerate(comment):
            char_index = B64.index(marker)
            content = txt_files[index].read_text(encoding="utf-8", errors="ignore")
            chars.append(content[char_index])

    return comment, "".join(chars)


def derive_flag(final_7z_bytes: bytes, mid: str, seven_pwd: str) -> tuple[str, str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        with py7zr.SevenZipFile(io.BytesIO(final_7z_bytes), mode="r", password=seven_pwd) as archive:
            archive.extractall(path=out_dir)
        final_txt = next(out_dir.rglob("*.txt"))
        ciphertext_b64 = final_txt.read_text(encoding="utf-8").strip()

    cipher = AES.new(mid.encode("utf-8")[:16], AES.MODE_CBC, seven_pwd.encode("utf-8")[:16])
    plaintext = unpad(cipher.decrypt(base64.b64decode(ciphertext_b64)), AES.block_size).decode("utf-8")
    return ciphertext_b64, plaintext


def main() -> None:
    base = Path.cwd()
    challenge_dir = next(
        path
        for path in base.iterdir()
        if path.is_dir()
        and any(path.glob("*.svg"))
        and any(path.glob("*.bmp"))
        and any(path.glob("*.csv"))
        and any(path.glob("*.txt"))
    )
    notes = decode_attachment_zip(challenge_dir)

    heaven_b64, heaven = solve_heaven(find_single(challenge_dir, "*.svg"))
    human_b64, human = solve_human(find_named(challenge_dir, "人言-签筒残册.txt"), notes)
    earth_b64, earth = solve_earth(find_single(challenge_dir, "*.bmp"))
    season_b64, season = solve_season(find_single(challenge_dir, "*.csv"), notes)

    mid = heaven + human + earth + season
    peek_zip_bytes, final_7z_bytes = load_outer_payloads(base)
    comment, seven_pwd = derive_stage_two(peek_zip_bytes, mid)
    ciphertext_b64, flag = derive_flag(final_7z_bytes, mid, seven_pwd)

    print("[stage1] heaven  :", heaven_b64, "->", heaven)
    print("[stage1] human   :", human_b64, "->", human)
    print("[stage1] earth   :", earth_b64, "->", earth)
    print("[stage1] season  :", season_b64, "->", season)
    print("[stage1] mid     :", mid)
    print("[stage1] zip md5 :", hashlib.md5(mid.encode('utf-8')).hexdigest())
    print("[stage2] comment :", comment)
    print("[stage2] seven   :", seven_pwd)
    print("[stage3] cipher  :", ciphertext_b64)
    print("[final] flag     :", flag)


if __name__ == "__main__":
    main()
