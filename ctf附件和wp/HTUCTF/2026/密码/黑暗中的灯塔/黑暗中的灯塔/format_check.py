import re
import sys

if len(sys.argv) != 2 or not re.fullmatch(r'HTUCTF\{[A-Z2-9]{7}\}', sys.argv[1]):
    print('format rejected')
    raise SystemExit(1)
print('format accepted')
