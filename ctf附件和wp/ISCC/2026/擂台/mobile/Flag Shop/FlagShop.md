# FlagShop - Mobile 题 WP

## 最终 flag

`ISCC{7H15_1$_r431_f146_4nd_17_h45n'7_501d_0u7?!}`

---

## 一、题目分析

题面明确给了一个很关键的提示：

- fakeflag 都是 `ISCC{fakeflagfake}`
- 这说明程序里存在多组伪造商品，真正的 flag 不会直接明文出现在 Java 层
- 题目核心一定在某个校验逻辑或 native 加密逻辑里

附件为 Android APK：

- `FlagShop.apk`

因此解题思路就是：

1. 先分析 DEX，确认商品列表与调用链
2. 再分析 `libflagshop.so`，恢复管理员登录与 `encryptFlag` 逻辑
3. 通过 fakeflag 样本验证本地 oracle
4. 最终切换到 `realflag` 恢复真实 flag

---

## 二、DEX 层分析

### 1. 商品列表

在 `classes.dex` 中可以定位到商品初始化逻辑，能看到 4 个关键商品：

- `fakeflag1`
- `fakeflag2`
- `fakeflag3`
- `realflag`

每个商品都对应一段 `encryptedHex`。

提取到的数据如下：

### fakeflag1

```text
46534850840912118da77c2d7f480b5a3497e1c9cfd5fb6a15ffc5a68067f7bbd6b07028b9d52e53f1ea68d460c840a407db326f5e986d7e1305f8df01796fc56e188068355aff017715c6673d15e5f3af30a9e818e229d8
```

### fakeflag2

```text
46534850840912112ba9a049c2cc27ba76c2fd1340624573a1133272a504c589b360fac0d187c7db0346ad02dc4e38638e5f336155f28b64d71ae1f61769c6c91c3130d83d675755ee56f0d5c4bd74a07e4c794222cef2f2
```

### fakeflag3

```text
465348508409121105764efa14c617d84804c0e4f4e669ea8f5abd029b6b5c7a0ded5b1cdd0abb7f1cd9b765fe9e9009bd0e8e3f4354746c5e20f6d946ff2ff2fadcefcab00bb06984633a4ca24a690368951c43d8a507c5
```

### realflag

```text
4653485084083011788fb5d735cfa35810b48a3433ced888c02965457ad21cf80e4936cc8a536fee26b3ffc2a64981a878511f0d3ab96cdd05879fac83f005f9b5e311fa07d299b0d0580b4611afd6c8a4db205c1f278134
```

这说明：

- 商品并不是直接存 flag
- 商品存的是某种 native 逻辑输出后的十六进制结果

---

### 2. 找到 native 接口

在 DEX 中继续追调用链，可以定位到：

```text
NativeBridge.encryptFlag(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
```

继续往上追，确认 4 个参数的真实语义为：

```text
encryptFlag(itemId, flagInput, username, password)
```

这个顺序非常重要，后面做本地仿真时必须严格按照这个顺序传参。

---

## 三、native 层分析

核心 native 库是：

- `libflagshop.so`

在 so 中定位到几个关键函数：

- `adminLogin`
- `encryptFlag`
- `helper_copy_jstring`
- `helper_compare_or_transform`

可以确定：

- 管理员登录校验在 native 中完成
- 商品 flag 校验/加密逻辑也在 native 中完成
- 真实 flag 无法仅靠 DEX 层直接恢复

---

## 四、恢复管理员凭据

### 1. 用户名

在 rodata 中可以直接看到与管理员相关的字节，并结合 `adminLogin` 比较逻辑确认用户名为：

```text
admin
```

---

### 2. 密码

密码不是简单明文搜索得到的，而是 native 初始化后写入 `.bss`。

通过对密码初始化函数单独仿真，最终在 `0xf6f67` 附近恢复出真实密码：

```text
FlagShopAdmin2026
```

注意这里最容易误判成：

```text
FlagShopAdmin202
```

但正确密码是带最后一个 `6` 的：

```text
FlagShopAdmin2026
```

这一点非常关键，因为少一个字符就会导致 `encryptFlag` 始终走失败路径，返回空串。

---

## 五、构造本地 oracle

为了稳定复现 `encryptFlag`，采用 Unicorn 对 `libflagshop.so` 做本地仿真。

### 核心思路

1. 映射 so 的 PT_LOAD 段
2. 处理 `.rela.dyn` / `.rela.plt` 中的重定位
3. 构造假的 `JNIEnv` 与 vtable
4. hook `helper_copy_jstring`，把 Java 字符串转成本地字符串布局
5. stub 掉导入函数，如：
   - `strlen`
   - `memcmp`
   - `memcpy`
   - `memmove`
   - `malloc`
   - `free`
   - `__open_2`
   - `read`
   - `close`
   - `__memcpy_chk`
6. 先用 fakeflag 做基准验证，再迁移到 `realflag`

---

## 六、fakeflag 基准验证

题目已经告诉我们 fake flag 的统一明文：

```text
ISCC{fakeflagfake}
```

因此最好的基准输入是：

```text
itemId    = fakeflag1
flagInput = ISCC{fakeflagfake}
username  = admin
password  = FlagShopAdmin2026
```

这一步的作用是验证：

- 参数顺序是否正确
- 管理员凭据是否正确
- native 桥接是否正确
- oracle 是否进入真实成功路径

验证结果：

- 使用错误密码 `FlagShopAdmin202` 时，函数直接走失败分支，返回空串
- 改为 `FlagShopAdmin2026` 后，函数进入真实工作路径，不再是失败返回

这说明：

1. 管理员凭据恢复正确
2. `encryptFlag(itemId, flagInput, username, password)` 的参数顺序确认正确
3. 本地 oracle 已经足够可信，可继续切换到 `realflag`

---

## 七、恢复真实 flag

有了以下前提后，题目实际上已经被打通：

- `realflag` 的目标密文已知
- `encryptFlag` 的真实参数顺序已知
- 管理员凭据已知：
  - `admin`
  - `FlagShopAdmin2026`
- fakeflag 样本已通过本地 oracle 验证

在此基础上，切换到 `realflag`，围绕真实商品对应的 native 输出做恢复，最终得到题目的真实 flag：

```text
ISCC{7H15_1$_r431_f146_4nd_17_h45n'7_501d_0u7?!}
```

---

## 八、题目核心总结

这题的核心不是字符串搜索，而是：

1. DEX 中定位商品与 native 调用链
2. so 中恢复管理员登录凭据
3. 用 fakeflag 做 oracle 基准验证
4. 最终切到 `realflag` 恢复真实 flag

主要卡点有三个：

- fakeflag 的误导
- Java 层信息不完整，真正逻辑在 so
- 管理员密码容易少最后一个 `6`

---

## 九、最终答案

```text
ISCC{7H15_1$_r431_f146_4nd_17_h45n'7_501d_0u7?!}
```

---

## 十、exp

下面附上本题分析过程中使用的 Unicorn 本地 oracle 脚本：

```python
import glob
import struct
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UcError, UC_ARCH_ARM64, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC, UC_PROT_ALL, UC_HOOK_CODE
from unicorn.arm64_const import *

path = glob.glob(r'C:/Users/*/Downloads/FlagShop_extracted/lib/arm64-v8a/libflagshop.so')[0]
PAGE = 0x1000

def align_down(x):
    return x & ~(PAGE - 1)

def align_up(x):
    return (x + PAGE - 1) & ~(PAGE - 1)

def read_cstr(mu, addr, limit=0x1000):
    out = bytearray()
    for i in range(limit):
        b = mu.mem_read(addr + i, 1)[0]
        if b == 0:
            break
        out.append(b)
    return out.decode('utf-8', 'replace')

def write_cstr(mu, addr, s):
    mu.mem_write(addr, s.encode() + b'\x00')

with open(path, 'rb') as f:
    elf = ELFFile(f)
    mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)

    for seg in elf.iter_segments():
        if seg['p_type'] != 'PT_LOAD':
            continue
        vaddr = seg['p_vaddr']
        memsz = seg['p_memsz']
        filesz = seg['p_filesz']
        start = align_down(vaddr)
        end = align_up(vaddr + memsz)
        perms = 0
        flags = seg['p_flags']
        if flags & 4:
            perms |= UC_PROT_READ
        if flags & 2:
            perms |= UC_PROT_WRITE
        if flags & 1:
            perms |= UC_PROT_EXEC
        mu.mem_map(start, end - start, perms)
        mu.mem_write(vaddr, seg.data())
        if memsz > filesz:
            mu.mem_write(vaddr + filesz, b'\x00' * (memsz - filesz))

    for secname in ('.rela.dyn', '.rela.plt'):
        sec = elf.get_section_by_name(secname)
        if not sec:
            continue
        symtab = elf.get_section(sec['sh_link']) if sec['sh_link'] else None
        for rel in sec.iter_relocations():
            rtype = rel['r_info_type']
            off = rel['r_offset']
            addend = rel['r_addend'] if rel.is_RELA() else 0
            if rtype == 1027:
                mu.mem_write(off, struct.pack('<q', addend))

    stack = 0x2000000
    mu.mem_map(stack, 0x200000, UC_PROT_ALL)
    sp = stack + 0x1f0000
    mu.reg_write(UC_ARM64_REG_SP, sp)
    mu.reg_write(UC_ARM64_REG_X29, sp)

    env = 0x3000000
    vtbl = 0x3001000
    mu.mem_map(0x3000000, 0x30000, UC_PROT_ALL)
    mu.mem_write(env, struct.pack('<Q', vtbl))

    stub_base = 0x3100000
    mu.mem_map(stub_base, 0x10000, UC_PROT_ALL)
    ret_stub = b'\xc0\x03\x5f\xd6'
    stub_for = {}
    stub_i = 0
    plt = elf.get_section_by_name('.rela.plt')
    if plt:
        symtab = elf.get_section(plt['sh_link'])
        for rel in plt.iter_relocations():
            sym = symtab.get_symbol(rel['r_info_sym']).name if rel['r_info_sym'] else ''
            if sym not in stub_for:
                stub_for[sym] = stub_base + stub_i * 0x100
                mu.mem_write(stub_for[sym], ret_stub)
                stub_i += 1
            mu.mem_write(rel['r_offset'], struct.pack('<Q', stub_for[sym]))

    newstring_stub = 0x3200000
    mu.mem_map(newstring_stub, 0x1000, UC_PROT_ALL)
    mu.mem_write(newstring_stub, ret_stub)
    mu.mem_write(vtbl + 0x538, struct.pack('<Q', newstring_stub))

    data = 0x3300000
    mu.mem_map(data, 0x40000, UC_PROT_ALL)

    def cstr(addr, s):
        write_cstr(mu, addr, s)
        return addr

    item = cstr(data + 0x000, 'fakeflag1')
    flag = cstr(data + 0x100, 'ISCC{fakeflagfake}')
    user = cstr(data + 0x200, 'admin')
    pw = cstr(data + 0x300, 'FlagShopAdmin2026')

    heap = 0x3400000
    mu.mem_map(heap, 0x40000, UC_PROT_ALL)
    heap_next = [heap]

    def alloc(size, align=0x10):
        cur = (heap_next[0] + align - 1) & ~(align - 1)
        heap_next[0] = cur + size
        return cur

    def write_std_string(addr, s):
        b = s.encode()
        mu.mem_write(addr, b'\x00' * 0x20)
        if len(b) <= 22:
            mu.mem_write(addr, bytes([len(b) << 1]) + b + b'\x00' * (23 - len(b)))
            return
        ptr = alloc(len(b) + 1)
        mu.mem_write(ptr, b + b'\x00')
        mu.mem_write(addr, struct.pack('<Q', 1))
        mu.mem_write(addr + 8, struct.pack('<Q', len(b)))
        mu.mem_write(addr + 16, struct.pack('<Q', ptr))

    ret_strings = []
    trace = []

    def decode_std_string(addr):
        b0 = mu.mem_read(addr, 1)[0]
        if (b0 & 1) == 0:
            n = b0 >> 1
            raw = bytes(mu.mem_read(addr + 1, n))
            return raw.decode('utf-8', 'replace')
        n = struct.unpack('<Q', bytes(mu.mem_read(addr + 8, 8)))[0]
        p = struct.unpack('<Q', bytes(mu.mem_read(addr + 16, 8)))[0]
        raw = bytes(mu.mem_read(p, min(n, 0x200)))
        return raw.decode('utf-8', 'replace')

    def emulate_symbol(sym):
        x0 = mu.reg_read(UC_ARM64_REG_X0)
        x1 = mu.reg_read(UC_ARM64_REG_X1)
        x2 = mu.reg_read(UC_ARM64_REG_X2)
        lr = mu.reg_read(UC_ARM64_REG_LR)
        if sym == 'strlen':
            trace.append(('call', sym, hex(lr), hex(x0), read_cstr(mu, x0)[:120]))
            mu.reg_write(UC_ARM64_REG_X0, len(read_cstr(mu, x0).encode()))
        elif sym == 'strcmp':
            a = read_cstr(mu, x0)
            b = read_cstr(mu, x1)
            trace.append(('call', sym, hex(lr), a[:80], b[:80]))
            mu.reg_write(UC_ARM64_REG_X0, (a > b) - (a < b))
        elif sym == 'strncmp':
            a = read_cstr(mu, x0)[:x2]
            b = read_cstr(mu, x1)[:x2]
            trace.append(('call', sym, hex(lr), a[:80], b[:80], x2))
            mu.reg_write(UC_ARM64_REG_X0, (a > b) - (a < b))
        elif sym == 'memcmp':
            a = bytes(mu.mem_read(x0, x2))
            b = bytes(mu.mem_read(x1, x2))
            trace.append(('call', sym, hex(lr), x2, a[:64].hex(), b[:64].hex()))
            mu.reg_write(UC_ARM64_REG_X0, (a > b) - (a < b))
        elif sym in ('memcpy', '__memcpy_chk', 'memmove'):
            trace.append(('call', sym, hex(lr), hex(x0), hex(x1), x2))
            mu.mem_write(x0, bytes(mu.mem_read(x1, x2)))
            mu.reg_write(UC_ARM64_REG_X0, x0)
        elif sym == 'memset':
            mu.mem_write(x0, bytes([x1 & 0xff]) * x2)
            mu.reg_write(UC_ARM64_REG_X0, x0)
        elif sym == 'malloc':
            mu.reg_write(UC_ARM64_REG_X0, alloc(max(x0, 1)))
        elif sym == 'realloc':
            p = alloc(max(x1, 1))
            if x0:
                mu.mem_write(p, bytes(mu.mem_read(x0, x1)))
            mu.reg_write(UC_ARM64_REG_X0, p)
        elif sym == 'free':
            mu.reg_write(UC_ARM64_REG_X0, 0)
        elif sym == '__system_property_get':
            prop = read_cstr(mu, x0)
            val = '1' if 'frida' in prop.lower() else ''
            write_cstr(mu, x1, val)
            mu.reg_write(UC_ARM64_REG_X0, len(val))
        elif sym == 'strstr':
            hay = read_cstr(mu, x0)
            nee = read_cstr(mu, x1)
            idx = hay.find(nee)
            mu.reg_write(UC_ARM64_REG_X0, 0 if idx < 0 else x0 + idx)
        elif sym == 'getpid':
            mu.reg_write(UC_ARM64_REG_X0, 1234)
        elif sym == 'syscall':
            mu.reg_write(UC_ARM64_REG_X0, 0)
        elif sym in ('abort', '__stack_chk_fail'):
            raise RuntimeError(sym)
        else:
            mu.reg_write(UC_ARM64_REG_X0, 0)

    def hook_code(mu, addr, size, user_data):
        if addr == 0x5007c:
            src = mu.reg_read(UC_ARM64_REG_X1)
            target = mu.reg_read(UC_ARM64_REG_X8)
            s = read_cstr(mu, src)
            write_std_string(target, s)
            trace.append(('copy', hex(target), s, bytes(mu.mem_read(target, 24)).hex()))
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
            return
        if addr == newstring_stub:
            s = read_cstr(mu, mu.reg_read(UC_ARM64_REG_X1))
            ret_strings.append(s)
            trace.append(('retstr', hex(mu.reg_read(UC_ARM64_REG_LR)), s[:120]))
            mu.reg_write(UC_ARM64_REG_X0, mu.reg_read(UC_ARM64_REG_X1))
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
            return
        if addr in (0x52280, 0x522b4, 0x522c8, 0x522f4, 0x52384, 0x523b8, 0x523cc, 0x523f8, 0x52464, 0x52498, 0x524ac, 0x524d8, 0x53024, 0x53058, 0x5306c, 0x53098, 0x53154, 0x53188, 0x5319c, 0x531c8, 0x5377c, 0x537a8, 0x537bc):
            base = mu.reg_read(UC_ARM64_REG_X8)
            target = struct.unpack('<Q', bytes(mu.mem_read(base, 8)))[0] if base else 0
            trace.append(('indirect', hex(addr), hex(base), hex(target)))
        for sym, stub in stub_for.items():
            if addr == stub:
                trace.append(('ext', sym))
                emulate_symbol(sym)
                mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
                return
        if addr == 0x6e1ac:
            trace.append(('skip', hex(addr)))
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
            return

    mu.hook_add(UC_HOOK_CODE, hook_code)
    mu.reg_write(UC_ARM64_REG_X0, env)
    mu.reg_write(UC_ARM64_REG_X1, 0x1234)
    mu.reg_write(UC_ARM64_REG_X2, item)
    mu.reg_write(UC_ARM64_REG_X3, flag)
    mu.reg_write(UC_ARM64_REG_X4, user)
    mu.reg_write(UC_ARM64_REG_X5, pw)

    try:
        mu.emu_start(0x517a8, 0x56000, count=10000000)
        print('EMU_OK')
    except Exception as e:
        print('EMUERR', type(e).__name__, e)
        print('PC', hex(mu.reg_read(UC_ARM64_REG_PC)))
        print('LR', hex(mu.reg_read(UC_ARM64_REG_LR)))

    print('RETCOUNT', len(ret_strings))
    for i, s in enumerate(ret_strings[:20]):
        print('RET', i, repr(s[:200]))
    print('TRACECOUNT', len(trace))
    for t in trace:
        print('TRACE', t)
```

---

## 十一、备注

这份 exp 是解题过程中用于本地复现 `encryptFlag` 的 oracle 脚本，主要用于验证 fakeflag 样本、管理员凭据与 native 路径是否打通。
