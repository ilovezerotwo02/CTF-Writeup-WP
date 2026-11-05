from scapy.all import *
packets = rdpcap("attachment-17.pcapng")
print(packets)
udp_packets = [p for p in packets if UDP in p]
tcp_with_data = [p for p in packets if TCP in p and Raw in p]
print(f"UDP: {len(udp_packets)}, TCP(with data): {len(tcp_with_data)}")
tcp_raw = tcp_with_data[0][Raw].load
print(tcp_raw)
import json, base64
body = tcp_raw.split(b'\r\n\r\n')[1]
data = json.loads(body)
zip_b64 = data['instruction']
zip_data = base64.b64decode(zip_b64)
print(f"ZIP大小: {len(zip_data)} bytes")
print(f"文件头: {zip_data[:4].hex()}")
for i, p in enumerate(udp_packets):
    if Raw in p and b'=' in p[Raw].load:
        print(f"UDP包 #{i}: {p[Raw].load}")
import base64
print(base64.b64decode("U2hlbmdEb25nSmlYaUAzNi0xLTY=").decode())
import pyzipper, io, os
os.makedirs("extracted", exist_ok=True)
with pyzipper.AESZipFile(io.BytesIO(zip_data)) as zf:
    zf.setpassword(b"ShengDongJiXi@36-1-6")
    zf.extractall("extracted")
from PIL import Image
img = Image.open("extracted/image.png")
print(img.size)
pixels = list(img.getdata())
print(f"颜色数量: {len(set(pixels))}")
img = Image.open("extracted/image.png")
px = img.load()
w, h = img.size
 
bits = []
for y in range(h):
    for x in range(w):
        r, g, b = px[x, y]
        bits.append(str(r & 1))
        bits.append(str(g & 1))
        bits.append(str(b & 1))
 
flag_bytes = bytes(
    int(''.join(bits[i:i+8]), 2)
    for i in range(0, len(bits) - 7, 8)
)
 
start = flag_bytes.find(b'ISCC{')
end = flag_bytes.find(b'}', start) + 1
flag = flag_bytes[start:end].decode()
print(flag)

