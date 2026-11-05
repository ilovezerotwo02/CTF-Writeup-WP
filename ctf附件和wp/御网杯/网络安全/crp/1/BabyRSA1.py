from pathlib import Path


DATA_FILE = Path(__file__).with_name("output.txt")


def load_values(path: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = int(value.strip())
    return result


def exact_cuberoot(value: int) -> int:
    guess = 1 << ((value.bit_length() + 2) // 3)
    while True:
        updated = (2 * guess + value // (guess * guess)) // 3
        if updated >= guess:
            break
        guess = updated
    while (guess + 1) ** 3 <= value:
        guess += 1
    while guess**3 > value:
        guess -= 1
    if guess**3 != value:
        raise ValueError("ciphertext is not a perfect cube")
    return guess


def decode_integer(value: int) -> str:
    size = (value.bit_length() + 7) // 8
    return value.to_bytes(size, "big").decode("utf-8")


def recover_flag() -> str:
    values = load_values(DATA_FILE)
    n = values["n"]
    e = values["e"]
    c = values["c"]
    if e != 3:
        raise ValueError(f"unexpected public exponent: {e}")
    message = exact_cuberoot(c)
    if pow(message, e) >= n:
        raise ValueError("small-exponent shortcut does not apply")
    return decode_integer(message)


if __name__ == "__main__":
    print(recover_flag())
