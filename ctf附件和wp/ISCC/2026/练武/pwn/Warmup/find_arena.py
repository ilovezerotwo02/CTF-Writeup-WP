from pwn import *

libc = ELF('./libc.so.6')

print('=== Finding main_arena ===')
print(f'__malloc_hook: {libc.symbols["__malloc_hook"]:#018x}')
print(f'_IO_2_1_stdout_: {libc.symbols["_IO_2_1_stdout_"]:#018x}')
print(f'_IO_list_all: {libc.symbols["_IO_list_all"]:#018x}')
print(f'environ: {libc.symbols["environ"]:#018x}')

# main_arena is typically in the .data or .bss section
# Let's look at sections near __malloc_hook
print()
print('=== Sections near __malloc_hook ===')
for sec_name in ['.data', '.bss', '__libc_IO_vtables']:
    sec = libc.get_section_by_name(sec_name)
    if sec:
        print(f'{sec_name}: start={sec.header.sh_addr:#018x} size={sec.header.sh_size:#x}')

# main_arena in GLIBC 2.35 Ubuntu is typically at __malloc_hook + 0x10 or so
# Let's calculate: the unsorted bin fd for a single chunk points to &main_arena.bins[0] - 0x10 = main_arena + 0x60
# Actually, let me search for a pattern
# main_arena starts with mutex (int 0), flags (int 0), have_fastchunks (int 0)
# So first 12 (or 16 with padding) bytes are usually 0x00000000
print()
print('=== main_arena offset calculation ===')
# bins[0] is at main_arena + 0x70 (offsetof bins in malloc_state for x86_64 glibc 2.35)
# When one chunk in unsorted bin: fd = &main_arena.bins[0] - 0x10 = main_arena + 0x70 - 0x10 = main_arena + 0x60
# So: leaked_fd = libc_base + main_arena_offset + 0x60
# libc_base = leaked_fd - main_arena_offset - 0x60

# In typical Ubuntu 22.04 GLIBC 2.35:
main_arena_approx = libc.symbols['__malloc_hook'] + 0x10
print(f'main_arena (approx): {main_arena_approx:#018x}')
print(f'main_arena + 0x60 = {main_arena_approx + 0x60:#018x}')
print(f'This is the value leaked from unsorted bin fd')

# Let's also check for the actual offset by looking at the symbol table
print()
print('=== Checking for main_arena in symbols ===')
try:
    # It might be a local symbol
    for sym in libc.symbols:
        if 'arena' in sym.lower() and 'main' in sym.lower():
            print(f'FOUND: {sym} = {libc.symbols[sym]:#018x}')
except:
    pass
