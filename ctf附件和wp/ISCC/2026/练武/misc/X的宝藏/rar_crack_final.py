import rarfile, os, sys, itertools, string

rarfile.UNRAR_TOOL = r'D:/桌面/wp/misc/unrar_w64.exe'

rar_path = None
for f in os.listdir('.'):
    if os.path.isfile(f) and os.path.getsize(f) == 567950:
        rar_path = f
        break

rf = rarfile.RarFile(rar_path)

def try_password(pwd_bytes):
    """Try a password and return True if correct"""
    try:
        rf.setpassword(pwd_bytes)
        files = rf.infolist()
        return len(files) > 0
    except rarfile.RarWrongPassword:
        return False
    except Exception:
        return False

# Test a focused list
passwords_to_try = []

# ASCII printable characters single and repeated
for c in string.printable:
    if c not in string.whitespace or c == ' ':
        passwords_to_try.append(c)
        passwords_to_try.append(c * 2)
        passwords_to_try.append(c * 3)
        passwords_to_try.append(c * 4)
        passwords_to_try.append(c * 5)

# Numbers
for i in range(10000):
    passwords_to_try.append(str(i))

# Common patterns
common = [
    'X', 'x', 'ISCC', 'iscc', 'flag', 'ctf', 'hacker', 'Hacker',
    'admin', 'root', 'test', 'guest', 'password', 'secret', 'key',
    'token', 'treasure', 'talent', 'Talent', 'TALENT',
    '33', '93', '514', '63988', '53771',
    'abc', '123', '1234', '12345', '123456',
    'qwerty', 'asdfgh', 'zxcvbn',
    'hack', 'root', 'pass', 'word',
    'hello', 'world', 'welcome',
    'aaa', 'aaaa', 'aaaaa',
    '111', '1111', '11111', '22222', '33333', '44444',
    '55555', '66666', '77777', '88888', '99999', '00000',
    'cangbaozang', 'baozang', 'xinfu', 'xinwu', 'xingwu',
    'x_treasure', 'X_TREASURE', 'xtreasure',
    'baozang', 'zangbao', 'xbao', 'baozang',
    'hackerx', 'HackerX', 'hacker_x',
    'talisman', 'Talisman', 'TALISMAN',
    'opensesame', 'open_sesame',
    'abracadabra', 'alakazam',
    'iscc2025', 'ISCC2025', 'iscc2026', 'ISCC2026',
    'iscc_ctf', 'isccctf', 'ISCC_CTF', 'ISCCCTF',
    'misc', 'MISC',
    '这货不是NONO',
    'lxh', 'LXH',
    'xman', 'xmen', 'xfiles', 'xfile',
    'nono', 'NONO', 'NonO',
    'zero', 'one', 'two', 'three', 'four', 'five',
    'passw0rd', 'p@ssw0rd', 'P@ssw0rd',
    '1234567', '12345678', '123456789', '1234567890',
    'qwerty123', 'abc123', 'pass123', 'admin123', 'root123',
    'football', 'baseball', 'monkey', 'dragon', 'master',
    'iloveyou', 'sunshine', 'trustno1', 'letmein', 'princess',
    'welcome1', 'password123',
    '!@#$%', '!@#$%^',
    '2025', '2026', '250',
]

passwords_to_try.extend(common)

# Remove duplicates while preserving order
seen = set()
unique = []
for p in passwords_to_try:
    if p not in seen:
        seen.add(p)
        unique.append(p)

print(f"Testing {len(unique)} passwords with RAR5 builtin verification...")

# Test a few first to see if the tool works
for pwd in unique[:20]:
    result = try_password(pwd.encode('utf-8') if isinstance(pwd, str) else pwd)
    print(f"  '{pwd}': {'CORRECT!' if result else 'wrong'}")

# Now test all
for pwd in unique:
    pwd_bytes = pwd.encode('utf-8') if isinstance(pwd, str) else pwd
    result = try_password(pwd_bytes)
    if result:
        print(f"\n*** PASSWORD FOUND: '{pwd}' ***")
        rf.setpassword(pwd_bytes)
        for f in rf.infolist():
            print(f"  File: {f.filename}")
            if not f.isdir():
                data = rf.read(f)
                print(f"  Size: {len(data)} bytes")
                print(f"  Content preview: {data[:500]}")
        sys.exit(0)

print("\nPassword not found in testing list.")
print("The RAR5 password is not in the common password list.")
