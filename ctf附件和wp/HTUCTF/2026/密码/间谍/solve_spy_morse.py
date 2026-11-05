
import sys

MORSE = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
    '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
    '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
    '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
    '-.--': 'Y', '--..': 'Z',
    '-----': '0', '.----': '1', '..---': '2', '...--': '3', '....-': '4',
    '.....': '5', '-....': '6', '--...': '7', '---..': '8', '----.': '9',
    '-....-': '-', '..--..': '?', '.-.-.-': '.', '--..--': ',', '---...': ':',
}

RAW = ("1111 0 110 011110 00 000 101 111 1 011110 00000 0011 0010 010")


def decode(raw, one_is_dot=True):
    out = []
    for tok in raw.split():
        code = ''.join('.' if (c == '1') == one_is_dot else '-'
                       for c in tok if c in '01')
        out.append(MORSE.get(code, '[%s]' % code))
    return ''.join(out)


if __name__ == '__main__':
    raw = sys.argv[1] if len(sys.argv) > 1 else RAW
    for guess in (True, False):
        s = decode(raw, guess)
        ok = '[' not in s
        print('1=点 %-5s -> %s   %s' % (guess, s, 'OK' if ok else '(含无法识别的码组)'))
    print()
    print('FLAG :', decode(raw, True))
    print('备选 :', decode(raw, True) + '.txt')
