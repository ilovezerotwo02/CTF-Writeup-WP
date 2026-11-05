import struct


class ELF:
    def __init__(self, path):
        self.d = open(path, 'rb').read()
        d = self.d
        assert d[:4] == b'\x7fELF'
        self.is64 = d[4] == 2
        self.e_shoff = struct.unpack_from('<Q', d, 0x28)[0]
        self.e_shentsize = struct.unpack_from('<H', d, 0x3a)[0]
        self.e_shnum = struct.unpack_from('<H', d, 0x3c)[0]
        self.e_shstrndx = struct.unpack_from('<H', d, 0x3e)[0]
        self.sections = []
        for i in range(self.e_shnum):
            o = self.e_shoff + i * self.e_shentsize
            name, typ, flags, addr, off, size, link, info, align, entsize = struct.unpack_from('<IIQQQQIIQQ', d, o)
            self.sections.append(dict(name=name, type=typ, flags=flags, addr=addr, off=off,
                                      size=size, link=link, entsize=entsize))

    def shstr(self, idx):
        st = self.sections[self.e_shstrndx]
        base = st['off']
        s = self.d[base + idx:]
        return s.split(b'\0')[0].decode()

    def find_section(self, name):
        for s in self.sections:
            if self.shstr(s['name']) == name:
                return s
        return None

    def symbols(self, sect='.dynsym'):
        s = self.find_section(sect)
        if not s:
            return {}
        strtab = self.sections[s['link']]
        strend = strtab['off'] + strtab['size']
        out = {}
        n = s['size'] // 24
        for i in range(n):
            o = s['off'] + i * 24
            nameoff, info, other, shndx, value, size = struct.unpack_from('<IBBHQQ', self.d, o)
            if nameoff == 0:
                continue
            p = strtab['off'] + nameoff
            name = self.d[p:self.d.index(b'\0', p)].decode(errors='replace')
            if value:
                out[name] = value
        return out


if __name__ == '__main__':
    e = ELF('libc_cache/libc6_2.39-0ubuntu8.8_amd64.so')
    syms = e.symbols()
    for k in ('puts', 'system', '__libc_start_main', 'str_bin_sh', 'exit', 'read'):
        print(k, hex(syms[k]) if k in syms else 'N/A')
