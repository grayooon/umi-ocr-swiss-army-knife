# ==========================================
# =============== 图像输入输出 ===============
# ==========================================
# 统一把 路径 / 字节流 / base64 转成 OpenCV BGR ndarray 。
# 路径读取使用 np.fromfile + imdecode ，可正确处理 Windows 中文路径。

import base64
import os

import cv2
import numpy as np


class ImageError(Exception):
    pass


def _decode(buf):
    arr = np.frombuffer(buf, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ImageError("图片解码失败（格式不支持或文件损坏）。")
    return img


def from_path(path):
    if not os.path.isfile(path):
        raise ImageError(f"文件不存在：{path}")
    try:
        with open(path, "rb") as f:
            buf = f.read()
    except Exception as e:
        raise ImageError(f"文件读取失败：{e}")
    return _decode(buf)


def from_bytes(data):
    if isinstance(data, (bytearray, memoryview)):
        data = bytes(data)
    if not isinstance(data, bytes):
        raise ImageError("输入不是合法的字节流。")
    return _decode(data)


def from_base64(s):
    if isinstance(s, bytes):
        s = s.decode("utf-8", "ignore")
    s = s.strip()
    if s.startswith("data:"):  # data:image/png;base64,xxxx
        idx = s.find(",")
        if idx >= 0:
            s = s[idx + 1:]
    s = "".join(s.split())
    pad = len(s) % 4
    if pad:
        s += "=" * (4 - pad)
    try:
        buf = base64.b64decode(s)
    except Exception as e:
        raise ImageError(f"base64 解码失败：{e}")
    return _decode(buf)


def get_rotate_crop_image(img, points):
    """按四点包围盒透视变换裁剪出文本行图像。"""
    points = np.asarray(points, dtype=np.float32)
    w = int(max(np.linalg.norm(points[0] - points[1]),
                np.linalg.norm(points[2] - points[3])))
    h = int(max(np.linalg.norm(points[0] - points[3]),
                np.linalg.norm(points[1] - points[2])))
    w = max(w, 1)
    h = max(h, 1)
    std = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    M = cv2.getPerspectiveTransform(points, std)
    dst = cv2.warpPerspective(
        img, M, (w, h),
        borderMode=cv2.BORDER_REPLICATE, flags=cv2.INTER_CUBIC)
    if dst.shape[0] * 1.0 / dst.shape[1] >= 1.5:  # 竖排文本转正
        dst = np.rot90(dst)
    return np.ascontiguousarray(dst)
