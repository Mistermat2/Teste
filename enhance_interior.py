"""Bright, real-estate style correction for our own interior photos.

Global adjustments only, nothing added, removed or replaced:
  1. straighten (small rotation from detected vertical lines, then crop the
     borders the rotation leaves)
  2. white balance from the brightest near-neutral pixels (walls/ceiling)
  3. exposure: lift mid-tones toward a target brightness, protect highlights
  4. gentle local contrast, +10% saturation, mild sharpening

Usage: python3 enhance_interior.py <in_dir> <out_dir>
"""
import glob
import math
import os
import sys

import cv2
import numpy as np

IN, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)


def straighten(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(g, (5, 5), 0), 50, 150)
    h, w = g.shape
    lines = cv2.HoughLinesP(edges, 1, np.pi / 720, 120,
                            minLineLength=h // 6, maxLineGap=10)
    angles = []
    for x1, y1, x2, y2 in (lines.reshape(-1, 4) if lines is not None else []):
        a = math.degrees(math.atan2(x2 - x1, y2 - y1))
        a = (a + 90) % 180 - 90                     # deviation from vertical
        if abs(a) < 4:
            angles.append(a)
    if len(angles) < 8:
        return img, 0.0
    ang = float(np.median(angles))
    if abs(ang) < 0.3:
        return img, 0.0
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -ang, 1.0)
    rot = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC)
    # crop the largest centred rectangle without empty corners
    t = abs(math.radians(ang))
    s = 1 / (math.cos(t) + max(w / h, h / w) * math.sin(t))
    cw, ch = int(w * s), int(h * s)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    return cv2.resize(rot[y0:y0 + ch, x0:x0 + cw], (w, h),
                      interpolation=cv2.INTER_CUBIC), ang


def white_balance(f):
    lum = f.mean(2)
    sat = f.max(2) - f.min(2)
    mask = (lum > np.percentile(lum, 70)) & (sat < 0.12) & (lum < 0.98)
    if mask.sum() < 500:
        mask = lum > np.percentile(lum, 80)
    ref = f[mask].mean(0)
    gains = ref.mean() / ref
    gains = 1 + 1.0 * (gains - 1)                   # full correction
    return np.clip(f * gains, 0, 1)


def exposure(f, target=0.70):
    lab = cv2.cvtColor((f * 255).astype(np.uint8), cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    x = L.astype(np.float32) / 255
    med = float(np.median(x))
    gamma = np.clip(math.log(target) / math.log(max(med, 1e-3)), 0.45, 1.0)
    x = x ** gamma                                  # brighten mid-tones
    x = x + 0.14 * x * (1 - x) ** 2 * 4             # extra shadow lift
    L = np.clip(x * 255, 0, 255).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=1.3, tileGridSize=(8, 8))
    L = cv2.addWeighted(L, 0.6, clahe.apply(L), 0.4, 0)
    return cv2.cvtColor(cv2.merge([L, A, B]), cv2.COLOR_LAB2BGR)


def finish(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.10, 0, 255)
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    blur = cv2.GaussianBlur(out, (0, 0), 1.2)
    return cv2.addWeighted(out, 1.3, blur, -0.3, 0)


for fn in sorted(glob.glob(f"{IN}/*.jpg")):
    img, ang = straighten(cv2.imread(fn))
    f = white_balance(img.astype(np.float32) / 255)
    out = finish(exposure(f))
    cv2.imwrite(f"{OUT}/{os.path.basename(fn)}", out, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(os.path.basename(fn), "rotation %.2f deg" % ang)
