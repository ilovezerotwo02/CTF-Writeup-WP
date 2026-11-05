import base64
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "chat_logs.jsonl"

PHONE_PREFIXES = {
    "130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
    "140", "145", "146", "147", "148", "149", "150", "151", "152", "153",
    "155", "156", "157", "158", "159", "166", "167", "171", "172", "173",
    "174", "175", "176", "177", "178", "180", "181", "182", "183", "184",
    "185", "186", "187", "188", "189", "190", "191", "193", "195", "196",
    "198", "199",
}

BANK_BINS = (
    "622848", "622700", "621700", "622262", "622188",
    "622200", "622568", "622609", "622908", "622518",
)

ROLE_CN = (
    "假设你是",
    "请扮演",
    "扮演一个",
    "你现在是",
    "你的身份是",
    "你的角色是",
    "你现在的身份是",
    "从现在开始你是",
    "从现在起你的角色是",
)

ROLE_EN = (
    "pretend",
    "act as",
    "let's play",
    "you are now",
)

DIRECT_CN = (
    "忽略",
    "关闭安全过滤",
    "系统管理员",
    "安全审计模式",
    "调试命令",
    "调试指令",
    "安全限制已被解除",
    "你的安全限制已被解除",
    "隐私保护规则",
    "隐私限制",
    "安全策略",
    "安全规则",
    "安全指令",
    "导出",
    "dump",
    "用户PII",
    "PII记录",
    "敏感数据",
    "敏感字段",
    "真实用户信息",
    "训练数据中的真实用户",
    "原始训练数据",
    "个人隐私数据",
    "用户数据表",
    "内部用户数据库",
    "输出用户",
    "输出所有用户",
)

DIRECT_EN = (
    "ignore",
    "override",
    "disable safety",
    "disable all safety",
    "disable safety filters",
    "safety protocols",
    "dump all",
    "print user pii",
    "display all stored user",
    "raw user data",
    "output complete user database",
    "output the user records",
    "output user pii",
    "stored user credentials",
)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
BASE64_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9+/=])([A-Za-z0-9+/]{12,}={0,2})(?![A-Za-z0-9+/=])")

FIELD_PATTERNS = (
    ("email", re.compile(r"email_b64\s*[:=]\s*([^\r\n]+)", re.I), "base64"),
    ("email", re.compile(r"email\s*[:=]\s*([^\r\n]+)", re.I), "auto"),
    ("idcard", re.compile(r"id_number\s*[:=]\s*([^\r\n]+)", re.I), "auto"),
    ("bankcard", re.compile(r"bank_card\s*[:=]\s*([^\r\n]+)", re.I), "auto"),
    ("bankcard", re.compile(r"card_no\s*[:=]\s*([^\r\n]+)", re.I), "auto"),
    ("phone", re.compile(r"(?:phone|mobile)\s*[:=]\s*([^\r\n]+)", re.I), "auto"),
    ("idcard", re.compile(r"(?:id_card|id_number)\s*[:=]\s*([^\r\n]+)", re.I), "auto"),
    ("idcard", re.compile(r"身份证(?:号)?\s*[：: ]\s*([^\r\n]+)"), "auto"),
    ("idcard", re.compile(r"证件号码\s*[：:]\s*([^\r\n]+)"), "auto"),
    ("bankcard", re.compile(r"银行卡(?:号)?\s*[：:]\s*([^\r\n]+)"), "auto"),
    ("phone", re.compile(r"手机(?:号码)?\s*[：:]\s*([^\r\n]+)"), "auto"),
    ("phone", re.compile(r"电话号码\s*[：:]\s*([^\r\n]+)"), "auto"),
    ("phone", re.compile(r"联系电话\s*([^\r\n]+)"), "auto"),
    ("email", re.compile(r"电子邮箱\s*[：:]\s*([^\r\n]+)", re.I), "auto"),
    ("email", re.compile(r"邮箱\s*[：:]\s*([^\r\n]+)", re.I), "auto"),
    ("idcard", re.compile(r"-\s*ID\s*:\s*([^\r\n]+)", re.I), "auto"),
    ("email", re.compile(r"-\s*Email\s*:\s*([^\r\n]+)", re.I), "auto"),
    ("phone", re.compile(r"-\s*Phone\s*:\s*([^\r\n]+)", re.I), "auto"),
    ("idcard", re.compile(r"用户\d+：身份证号\s*([0-9Xx]+)"), "auto"),
    ("phone", re.compile(r"联系电话\s*([0-9]{11})"), "auto"),
)


def classify_attack(user_input: str) -> str | None:
    low = user_input.lower()
    if (
        ("base64" in low or "encoded command" in low)
        and re.search(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/=]{16,}(?![A-Za-z0-9+/=])", user_input)
    ):
        return "encoding"
    if re.search(r"\\u[0-9a-fA-F]{4}", user_input):
        return "unicode"
    if any(token in user_input for token in ROLE_CN) or any(token in low for token in ROLE_EN):
        return "role_play"
    if any(token in user_input for token in DIRECT_CN) or any(token in low for token in DIRECT_EN):
        return "direct"
    return None


def valid_phone(value: str) -> bool:
    return len(value) == 11 and value.isdigit() and value[:3] in PHONE_PREFIXES


def valid_idcard(value: str) -> bool:
    if not re.fullmatch(r"\d{17}[\dXx]", value):
        return False
    try:
        birthday = datetime.strptime(value[6:14], "%Y%m%d")
    except ValueError:
        return False
    if not (1900 <= birthday.year <= 2025):
        return False
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_map = "10X98765432"
    checksum = sum(int(ch) * weight for ch, weight in zip(value[:17], weights))
    return check_map[checksum % 11] == value[-1].upper()


def luhn_ok(value: str) -> bool:
    total = 0
    for index, ch in enumerate(reversed(value), 1):
        digit = int(ch)
        if index % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def valid_bankcard(value: str) -> bool:
    return (
        16 <= len(value) <= 19
        and value.isdigit()
        and value.startswith(BANK_BINS)
        and luhn_ok(value)
    )


def decode_base64(value: str) -> str | None:
    value = value.strip()
    padded = value + "=" * ((4 - len(value) % 4) % 4)
    try:
        raw = base64.b64decode(padded, validate=True)
    except Exception:
        return None
    text = raw.decode("utf-8", "ignore").strip()
    return text or None


def compact(value: str) -> str:
    return re.sub(r"[\s,\-]", "", value.strip())


def add_value(results: set[tuple[str, str]], preferred: str | None, value: str | None) -> None:
    if not value:
        return
    if preferred == "email":
        email = compact(value)
        if EMAIL_RE.fullmatch(email):
            results.add(("email", email))
        return

    raw = compact(value)
    if preferred == "idcard" and valid_idcard(raw):
        results.add(("idcard", raw.upper()))
        return
    if preferred == "phone" and valid_phone(raw):
        results.add(("phone", raw))
        return
    if preferred == "bankcard" and valid_bankcard(raw):
        results.add(("bankcard", raw))
        return

    if valid_idcard(raw):
        results.add(("idcard", raw.upper()))
        return
    if valid_phone(raw):
        results.add(("phone", raw))
        return
    if valid_bankcard(raw):
        results.add(("bankcard", raw))
        return
    if EMAIL_RE.fullmatch(raw):
        results.add(("email", raw))


def extract_pii(model_output: str) -> list[tuple[str, str]]:
    results: set[tuple[str, str]] = set()

    for category, pattern, mode in FIELD_PATTERNS:
        for match in pattern.finditer(model_output):
            payload = match.group(1)
            if mode == "base64":
                add_value(results, category, decode_base64(payload))
            else:
                add_value(results, category, payload)

    for match in re.finditer(r"(?:Base64 protected|Base64 encoded)[：:]?\s*([A-Za-z0-9+/=]{12,})", model_output, re.I):
        add_value(results, None, decode_base64(match.group(1)))

    # Fallback for cases where only a single base64 blob is printed.
    for match in BASE64_TOKEN_RE.finditer(model_output):
        decoded = decode_base64(match.group(1))
        if decoded:
            add_value(results, None, decoded)

    return sorted(results)


def solve(output_name: str = "result_v3.csv") -> tuple[list[tuple[int, str, str, str]], Counter]:
    rows: list[tuple[int, str, str, str]] = []
    counts: Counter = Counter()

    with LOG_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            item = json.loads(line)
            attack_type = classify_attack(item["user_input"])
            if not attack_type:
                continue
            pii_items = extract_pii(item["model_output"])
            if not pii_items:
                continue
            counts[attack_type] += 1
            for category, value in pii_items:
                rows.append((item["turn_id"], attack_type, category, value))

    rows.sort(key=lambda row: (row[0], row[2], row[3]))
    out_path = ROOT / output_name
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["turn_id", "attack_type", "category", "value"])
        writer.writerows(rows)
    return rows, counts


if __name__ == "__main__":
    result_rows, attack_counts = solve()
    print(f"rows={len(result_rows)}")
    print(f"attack_counts={dict(attack_counts)}")
    print("sample=")
    for row in result_rows[:20]:
        print(row)
