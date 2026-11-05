import base64, gzip, hashlib
import numpy as np
from PIL import Image
from io import BytesIO
import zipfile

# 从分析train.exe提取到的三个随机种子
SEEDS = {"R": 863148490, "G": 72199925, "B": 2239801264}
CH_IDX = {"R": 0, "G": 1, "B": 2}

def extract_lsb(img, ch, nbytes=16):
    """从指定颜色通道提取LSB数据"""
    arr = np.array(img.convert("RGB"))
    bits = (arr[:, :, CH_IDX[ch]] & 1).flatten()[:nbytes * 8]
    return np.packbits(bits, bitorder="big").tobytes()

def do_shuffle(data, seed):
    """用给定种子随机打乱字节顺序"""
    arr = np.frombuffer(data, dtype=np.uint8).copy()
    idx = np.arange(len(arr), dtype=np.int64)
    np.random.RandomState(seed).shuffle(idx)
    inv = np.argsort(idx)
    return bytes(arr[inv])

def main():
    with zipfile.ZipFile("TrainModel.zip") as zf:
        img = Image.open(BytesIO(zf.read("Input.png")))
        state = np.load(BytesIO(zf.read("model_state.npz")))

    hint = gzip.decompress(
        base64.b64decode(bytes(state["base_hint_bytes"]))
    ).decode()
    print(f"[*] Hint: {hint}")

    r = extract_lsb(img, "R")
    g = extract_lsb(img, "G")
    b = extract_lsb(img, "B")
    print(f"R:{r.decode()}")
    print(f"G:{g.decode()}")
    print(f"B:{b.decode()}")

    # 通道映射 (R,G,B) -> (G,B,R)
    inner_b = b[5:-1]
    descrambled = do_shuffle(inner_b, SEEDS["B"])
    output_g = b"ISCC{" + descrambled + b"}"

    flag1 = r[5:-1].decode()
    flag2 = output_g[5:-1].decode()
    print(f"flag1R={flag1}")
    print(f"flag2G={flag2}")

    digest = hashlib.md5((flag1 + flag2).encode()).hexdigest()
    final = f"ISCC{{{digest}}}"
    print(f"FLAG:{final}")
    return final
if __name__ == "__main__":
    main()
