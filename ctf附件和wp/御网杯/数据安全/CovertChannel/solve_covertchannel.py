from __future__ import annotations

from base64 import b64decode
from pathlib import Path

from Crypto.Cipher import AES
from scapy.all import DNS, ICMP, IP, UDP, rdpcap


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PCAP = (
    BASE_DIR / "extracted" / "tempdir" / "MISC附件" / "suspicious_traffic.pcapng"
)
TXT_DOMAIN = b"secret.exfil-cdn.com."
SRC_HOST = "10.10.20.33"
ICMP_EXFIL_DST = "45.76.188.23"


def load_packets(pcap_path: Path):
    return rdpcap(str(pcap_path))


def extract_dns_txt_key(packets) -> bytes:
    for pkt in packets:
        if (
            IP in pkt
            and UDP in pkt
            and DNS in pkt
            and pkt[IP].src == "10.10.20.1"
            and pkt[DNS].qr == 1
            and pkt[DNS].qd
            and pkt[DNS].qd.qname == TXT_DOMAIN
        ):
            return b64decode(pkt[DNS].an.rdata[0])
    raise ValueError("DNS TXT key not found")


def extract_icmp_ttl_message(packets) -> str:
    bits = []
    for pkt in packets:
        if (
            IP in pkt
            and ICMP in pkt
            and pkt[IP].src == SRC_HOST
            and pkt[IP].dst == ICMP_EXFIL_DST
            and pkt[ICMP].type == 8
        ):
            bits.append(str(pkt[IP].ttl))

    if not bits:
        raise ValueError("ICMP covert channel not found")

    bitstream = "".join(bits)
    data = bytes(int(bitstream[i : i + 8], 2) for i in range(0, len(bitstream), 8))
    return data.decode()


def decrypt_flag(ciphertext_hex: str, key: bytes) -> str:
    ciphertext = bytes.fromhex(ciphertext_hex)
    plaintext = AES.new(key, AES.MODE_ECB).decrypt(ciphertext)
    return plaintext.rstrip(b"\n").decode()


def solve(pcap_path: Path = DEFAULT_PCAP) -> str:
    packets = load_packets(pcap_path)
    key = extract_dns_txt_key(packets)
    ttl_message = extract_icmp_ttl_message(packets)

    ciphertext_hex, hint = ttl_message.split("|", 1)
    if hint.strip() != "AES-ECB, key is in DNS TXT":
        raise ValueError(f"Unexpected hint: {hint}")

    flag = decrypt_flag(ciphertext_hex, key)
    print(f"DNS TXT key: {key.decode()}")
    print(f"ICMP hint: {hint}")
    print(flag)
    return flag


if __name__ == "__main__":
    solve()
