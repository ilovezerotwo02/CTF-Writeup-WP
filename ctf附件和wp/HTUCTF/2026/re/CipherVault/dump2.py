import ctypes, ctypes.wintypes as wt, subprocess, time, sys, os, struct

PROCESS_ALL = 0x1F0FFF
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
ntdll = ctypes.WinDLL('ntdll')
psapi = ctypes.WinDLL('psapi')

exe = os.path.abspath('CipherVault.exe')
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(1.5)
h = kernel32.OpenProcess(PROCESS_ALL, False, p.pid)
mods = (ctypes.c_void_p * 256)(); needed = wt.DWORD()
psapi.EnumProcessModules(h, ctypes.byref(mods), ctypes.sizeof(mods), ctypes.byref(needed))
base = mods[0]

hdr = ctypes.create_string_buffer(0x1000)
n = ctypes.c_size_t()
kernel32.ReadProcessMemory(h, ctypes.c_void_p(base), hdr, 0x1000, ctypes.byref(n))
raw = hdr.raw
e_lfanew = struct.unpack_from('<I', raw, 0x3c)[0]
size_of_image = struct.unpack_from('<I', raw, e_lfanew + 24 + 56)[0]
print('base', hex(base), 'SizeOfImage', hex(size_of_image))

buf = ctypes.create_string_buffer(size_of_image)
ok = kernel32.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size_of_image, ctypes.byref(n))
print('read ok', ok, n.value)
open('image.bin', 'wb').write(buf.raw[:n.value])
open('image_base.txt', 'w').write(hex(base))

# 解析节表
nsec = struct.unpack_from('<H', raw, e_lfanew + 6)[0]
opt_size = struct.unpack_from('<H', raw, e_lfanew + 20)[0]
sec_off = e_lfanew + 24 + opt_size
for i in range(nsec):
    o = sec_off + i * 40
    name = raw[o:o+8].rstrip(b'\0').decode(errors='replace')
    vsize, vaddr, rsize, roff = struct.unpack_from('<IIII', raw, o + 8)
    print(f'{name:8s} va={vaddr:#x} vsize={vsize:#x} raw={roff:#x} rsize={rsize:#x}')

p.kill()
