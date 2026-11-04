"""Global photo correction: light, white balance, colour and sharpness only.

Every adjustment is applied uniformly to the whole image (no object is added,
removed or replaced). Usage:
    python3 enhance_photos.py <in_dir> <out_dir> [ids...]
"""
import glob
import os
import sys

import cv2
import numpy as np

IN, OUT = sys.argv[1], sys.argv[2]
IDS = sys.argv[3:]
os.makedirs(OUT, exist_ok=True)


def enhance(img):
    f = img.astype(np.float32) / 255.0

    # 1. white balance: pull channel means toward neutral grey (partial, 60%)
    means = f.reshape(-1, 3).mean(0)
    gains = 1 + 0.6 * (means.mean() / means - 1)
    f = np.clip(f * gains, 0, 1)

    # 2. local contrast / shadow detail on luminance only (gentle CLAHE)
    lab = cv2.cvtColor((f * 255).astype(np.uint8), cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.4, tileGridSize=(8, 8))
    L2 = clahe.apply(L)
    L = cv2.addWeighted(L, 0.5, L2, 0.5, 0)

    # 3. lift shadows, protect highlights (tone curve on luminance)
    x = L.astype(np.float32) / 255.0
    x = x + 0.12 * x * (1 - x) ** 2 * 4          # boosts dark/mid tones
    L = np.clip(x * 255, 0, 255).astype(np.uint8)
    f = cv2.cvtColor(cv2.merge([L, A, B]), cv2.COLOR_LAB2BGR).astype(np.float32) / 255.0

    # 4. slight saturation boost (+8%)
    hsv = cv2.cvtColor((f * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.08, 0, 255)
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # 5. mild sharpening (unsharp mask)
    blur = cv2.GaussianBlur(out, (0, 0), 1.2)
    return cv2.addWeighted(out, 1.35, blur, -0.35, 0)


files = sorted(glob.glob(f"{IN}/*.jpg"))
if IDS:
    files = [f for f in files if os.path.basename(f)[:-4] in IDS]
for fn in files:
    cv2.imwrite(f"{OUT}/{os.path.basename(fn)}", enhance(cv2.imread(fn)),
                [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("ok", os.path.basename(fn))
