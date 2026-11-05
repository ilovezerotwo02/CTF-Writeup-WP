import base64
import hashlib
import re
import struct
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TXT = ROOT / "LX517.txt"
PCAP = ROOT / "LX517.pcap"


def decode_hint(text: str) -> str:
    for token in re.findall(r"[A-Za-z0-9+/=]{80,}", text):
        try:
            decoded = base64.b64decode(token).decode("utf-8")
        except Exception:
            continue
        if "KEYMAT:" in decoded and "ALGO:" in decoded:
            return decoded
    raise RuntimeError("Base64 hint not found")


def parse_rows(text: str):
    rows = []
    for line in text.splitlines():
        if not re.match(r"^\d{4},", line):
            continue
        parts = line.split(",", 9)
        if len(parts) != 10:
            continue
        rows.append(
            {
                "idx": int(parts[0]),
                "local_dt": datetime.strptime(parts[1], "%Y-%m-%d %H:%M:%S"),
                "lat": float(parts[2]),
                "lon": float(parts[3]),
                "event": parts[8],
                "detail": parts[9],
            }
        )
    return rows


def likely_tz_offsets(lon: float):
    """Return plausible UTC offsets for this challenge's IDL route."""
    offsets = {round(lon / 15)}
    if lon > 150:
        offsets.update({12, 13, 14})
    if lon < -150:
        offsets.update({-10, -11, -12})
    return sorted(offsets)


def epoch_candidates(row):
    candidates = set()
    for utc_offset_hours in likely_tz_offsets(row["lon"]):
        # The note mentions a date correction around the IDL.  The released
        # attachment is solved by trying both interpretations.
        for date_corr_days in (0, -1):
            local_dt = row["local_dt"] + timedelta(days=date_corr_days)
            utc_dt = local_dt - timedelta(hours=utc_offset_hours)
            candidates.add(int(utc_dt.replace(tzinfo=timezone.utc).timestamp()))
    return sorted(candidates)


def tcp_payloads_from_pcap(path: Path):
    data = path.read_bytes()
    if len(data) < 24:
        return []

    magic = data[:4]
    if magic == b"\xd4\xc3\xb2\xa1":
        endian = "<"
    elif magic == b"\xa1\xb2\xc3\xd4":
        endian = ">"
    else:
        raise RuntimeError("Unsupported pcap magic")

    payloads = []
    pos = 24
    while pos + 16 <= len(data):
        _ts_sec, _ts_usec, incl_len, _orig_len = struct.unpack(
            endian + "IIII", data[pos : pos + 16]
        )
        pos += 16
        pkt = data[pos : pos + incl_len]
        pos += incl_len

        if len(pkt) < 14:
            continue
        eth_type = struct.unpack("!H", pkt[12:14])[0]
        if eth_type != 0x0800:
            continue

        ip = pkt[14:]
        if len(ip) < 20 or ip[0] >> 4 != 4:
            continue
        ihl = (ip[0] & 0x0F) * 4
        total_len = struct.unpack("!H", ip[2:4])[0]
        if ip[9] != 6 or len(ip) < total_len:
            continue

        tcp = ip[ihl:total_len]
        if len(tcp) < 20:
            continue
        data_offset = (tcp[12] >> 4) * 4
        payload = tcp[data_offset:]
        if payload:
            payloads.append(payload)
    return payloads


def extract_ciphertext(path: Path) -> bytes:
    joined = b"".join(tcp_payloads_from_pcap(path))
    match = re.search(rb"CIPH:([0-9a-fA-F]+)", joined)
    if not match:
        match = re.search(rb"CIPH:([0-9a-fA-F]+)", path.read_bytes())
    if not match:
        raise RuntimeError("CIPH payload not found")
    return bytes.fromhex(match.group(1).decode())


def decrypt(ciphertext: bytes, keymat: str) -> bytes:
    blocks = (len(ciphertext) + 31) // 32
    keystream = b"".join(
        hashlib.sha256(keymat.encode() + struct.pack(">I", i)).digest()
        for i in range(blocks)
    )
    return bytes(c ^ k for c, k in zip(ciphertext, keystream))


def main():
    text = TXT.read_text(encoding="utf-8", errors="ignore")
    hint = decode_hint(text)
    rows = parse_rows(text)
    ciphertext = extract_ciphertext(PCAP)

    key_template = re.search(r"^KEYMAT:(.+)$", hint, re.MULTILINE).group(1).strip()
    evt_a_rows = [r for r in rows if r["event"] == "EVT_A"]
    evt_b_rows = [r for r in rows if r["event"] == "EVT_B"]
    evt_c_rows = [
        r
        for r in rows
        if r["event"] == "EVT_C" and ("marker=A2" in r["detail"] or "marker=X9" in r["detail"])
    ]

    tried = 0
    for evt_a in evt_a_rows:
        for evt_b in evt_b_rows:
            for evt_c in evt_c_rows:
                for syn in epoch_candidates(evt_a):
                    for idl in epoch_candidates(evt_b):
                        for a2 in epoch_candidates(evt_c):
                            keymat = (
                                key_template.replace("<EVT_A_UTC>", str(syn))
                                .replace("<EVT_B_UTC>", str(idl))
                                .replace("<EVT_C_UTC>", str(a2))
                            )
                            tried += 1
                            plain = decrypt(ciphertext, keymat)
                            if re.fullmatch(rb"ISCC\{[0-9a-fA-F]{32}\}", plain):
                                print("hint:")
                                print(hint)
                                print("ciphertext:", ciphertext.hex())
                                print("keymat:", keymat)
                                print("flag:", plain.decode())
                                print("tried:", tried)
                                return

    raise RuntimeError(f"Flag not found, tried {tried} candidates")


if __name__ == "__main__":
    main()
