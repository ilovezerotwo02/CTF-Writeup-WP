M = 0xFFFFFFFF


def _init(seed):
    r = [0] * 400
    seed &= 0xFFFFFFFF
    if seed == 0:
        seed = 1
    r[0] = seed
    for i in range(1, 31):
        # r[i] = (16807 * r[i-1]) % 2147483647  with signed 32-bit semantics
        hi = r[i - 1] // 127773
        lo = r[i - 1] % 127773
        word = 16807 * lo - 2836 * hi
        if word < 0:
            word += 2147483647
        r[i] = word & M
    for i in range(31, 34):
        r[i] = r[i - 31]
    for i in range(34, 344):
        r[i] = (r[i - 31] + r[i - 3]) & M
    return r


class GlibcRand:
    def __init__(self, seed):
        self.r = _init(seed)
        self.i = 344

    def next(self):
        i = self.i
        r = self.r
        val = (r[i - 31] + r[i - 3]) & M
        r[i] = val
        self.i = i + 1
        return val >> 1


if __name__ == '__main__':
    g = GlibcRand(1)
    print([g.next() for _ in range(5)])
    print('expect 1804289383 846930886 1681692777 1714636915 1957747793')
