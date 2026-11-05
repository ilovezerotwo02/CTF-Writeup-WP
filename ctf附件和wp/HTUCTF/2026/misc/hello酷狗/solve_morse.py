#!/usr/bin/env python3
# hello酷狗：PNG 尾部追加 ZIP -> flag.txt 是 Morse 码（A=划  B=点）
import re

d = open('flag.txt', 'rb').read().decode()
groups = d.split()

MORSE = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
    '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
    '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
    '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
    '-.--': 'Y', '--..': 'Z',
    '-----': '0', '.----': '1', '..---': '2', '...--': '3', '....-': '4',
    '.....': '5', '-....': '6', '--...': '7', '---..': '8', '----.': '9',
}

# A 当"划"、B 当"点"才解得出干净结果
s = ''.join(MORSE[g.replace('A', '-').replace('B', '.')] for g in groups)
print("morse ->", s)          # 32 位 hex
body = s.lower()
uuid = f"{body[:8]}-{body[8:12]}-{body[12:16]}-{body[16:20]}-{body[20:]}"
print("flag ->", "HTUCTF{" + uuid + "}")
# HTUCTF{b1e17d71-df09-2ffa-b9c7-a6e2b63bd3e1}
