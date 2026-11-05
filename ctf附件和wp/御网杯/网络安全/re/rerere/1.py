target = bytes.fromhex(
    "A3 5B 4C 0A 0E 49 E3 60 "
    "B1 0B 67 D3 DF C2 F4 B6 "
    "A9 E7 43 D3 14 83 2D A1 "
    "C6 E7 4C D3 7C B8 2D 95 "
    "D7 62 43 97 8A 6C"
)

key = bytes.fromhex("B9 CD CE 30 B8 61 4E AA")

sbox = bytes.fromhex(
    "C2 23 97 49 83 F6 D3 A7 EB BF 78 C3 29 56 D2 1A "
    "13 BC 21 6A 37 8E 5F 0C B4 46 DE E4 6C A2 66 30 "
    "0F A4 BB 8C 09 4B 3D 32 42 55 2D 4F F9 77 1B 74 "
    "1F 71 7B 9D 73 C4 AB D0 F3 C1 88 07 DC CE EF C0 "
    "72 4A 27 81 9B EE C7 28 26 5A 94 54 70 D1 E9 C8 "
    "98 36 91 41 B8 3A 79 0A 08 E5 AF 80 24 AE 00 19 "
    "CC 7A F7 51 7D 69 EC 03 65 25 1C 01 F5 E6 BD D9 "
    "59 FE 92 B0 10 6F F0 E3 9F AD 84 F4 A5 33 35 48 "
    "53 B1 E0 D8 05 38 18 68 A9 14 C6 3F 61 8A 31 3B "
    "BA 2B 4E E2 57 9A F1 EA 64 7E A0 93 B6 DA 60 2E "
    "1D 5B 82 34 6D FC CF 7F E7 96 67 43 06 44 C9 4C "
    "40 DB FD 4D B5 ED 39 2C B3 17 9E CD FA 6B CA 87 "
    "8F 9C 89 0E 63 45 86 AA 5E 95 16 C5 D5 2F A1 F8 "
    "99 FF 3C 0D 3E D4 04 76 D7 47 20 8D DF 5C 7C A3 "
    "1E 8B 15 B9 A8 CB 22 A6 52 D6 FB 5D DD B2 6E E8 "
    "F2 E1 2A 58 62 12 11 50 75 B7 AC 90 0B 85 02 BE"
)

inverse_sbox = {value: index for index, value in enumerate(sbox)}
flag = bytes(inverse_sbox[value] ^ key[index & 7] for index, value in enumerate(target))

print(flag.decode())
