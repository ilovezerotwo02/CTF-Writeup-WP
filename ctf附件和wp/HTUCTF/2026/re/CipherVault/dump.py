import ctypes, ctypes.wintypes as wt, subprocess, time, sys, re, os

PROCESS_ALL = 0x1F0FFF
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
ntdll = ctypes.WinDLL('ntdll')
psapi = ctypes.WinDLL('psapi')


class MEMORY_BASIC_INFORMATION64(ctypes.Structure):
    _fields_ = [('BaseAddress', ctypes.c_ulonglong), ('AllocationBase', ctypes.c_ulonglong),
                ('AllocationProtect', wt.DWORD), ('__alignment1', wt.DWORD),
                ('RegionSize', ctypes.c_ulonglong), ('State', wt.DWORD),
                ('Protect', wt.DWORD), ('Type', wt.DWORD), ('__alignment2', wt.DWORD)]


exe = os.path.abspath('CipherVault.exe')
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(1.5)
h = kernel32.OpenProcess(PROCESS_ALL, False, p.pid)
print('pid', p.pid, 'handle', h)
if not h:
    print('open failed'); sys.exit(1)

# 主模块基址
mods = (ctypes.c_void_p * 256)()
needed = wt.DWORD()
psapi.EnumProcessModules(h, ctypes.byref(mods), ctypes.sizeof(mods), ctypes.byref(needed))
base = mods[0]
print('image base', hex(base))

PAGE_READABLE = (0x02, 0x04, 0x20, 0x40, 0x80)
regions = []
addr = 0
mbi = MEMORY_BASIC_INFORMATION64()
while addr < 0x7FFFFFFF0000:
    if ntdll.NtQueryVirtualMemory(h, ctypes.c_void_p(addr), 0, ctypes.byref(mbi), ctypes.sizeof(mbi), None) != 0:
        break
    size = mbi.RegionSize
    if size == 0:
        break
    if mbi.State == 0x1000 and mbi.Protect in PAGE_READABLE and size < 100 * 1024 * 1024:
        buf = ctypes.create_string_buffer(size)
        n = ctypes.c_size_t(0)
        if kernel32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, size, ctypes.byref(n)) and n.value:
            regions.append((addr, bytes(buf.raw[:n.value])))
    addr += size

print('regions', len(regions))

# 1) 抓取镜像（前 0x40000 字节）
img = None
for a, b in regions:
    if a <= base < a + len(b):
        off = base - a
        img = b[off:off + 0x40000]
        break
if img:
    open('image.bin', 'wb').write(img)
    print('image dumped', len(img), 'bytes')

# 2) 全内存搜关键字
keys = [b'HTUCTF', b'VAULT', b'ARCHIVE', b'flag', b'unlock']
for a, b in regions:
    if a < 0x10000:
        continue
    for k in keys:
        for m in re.finditer(re.escape(k), b):
            s = max(0, m.start() - 40); e = min(len(b), m.start() + 80)
            seg = b[s:e]
            printable = ''.join(chr(c) if 32 <= c < 127 else '.' for c in seg)
            print(hex(a + m.start()), k.decode(), '|', printable)

p.kill()
print('done')
