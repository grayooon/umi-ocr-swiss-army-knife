# =========================================================
# ====== HyperLPR3 通用工具（改编自上游 Prj-Python 实现） ======
# =========================================================
# 上游项目： https://github.com/szad670401/HyperLPR  (Apache-2.0)
# 本文件在保持算法一致的前提下做了裁剪与整理，去掉了 MNN / 训练相关代码。

import cv2
import numpy as np

# ---------------- 字符表（CTC，0 号为 blank） ----------------
PLATE_CHARS = [
    "blank", "'", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N",
    "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
    "云", "京", "冀", "吉", "学", "宁", "川", "挂", "新", "晋", "桂", "民",
    "沪", "津", "浙", "渝", "港", "湘", "琼", "甘", "皖", "粤", "航", "苏",
    "蒙", "藏", "警", "豫", "贵", "赣", "辽", "鄂", "闽", "陕", "青", "鲁",
    "黑", "领", "使", "澳",
]

# ---------------- 车牌层数 / 类型 ----------------
MONO, DOUBLE = 0, 1
UNKNOWN = -1
BLUE = 0
YELLOW_SINGLE = 1
WHITE_SINGLE = 2
GREEN = 3
BLACK_HK_MACAO = 4
YELLOW_DOUBLE = 9

PLATE_TYPE_BLUE, PLATE_TYPE_GREEN, PLATE_TYPE_YELLOW = 0, 1, 2

TYPE_NAMES = {
    UNKNOWN: "未知",
    BLUE: "蓝牌",
    YELLOW_SINGLE: "黄牌单层",
    WHITE_SINGLE: "白牌",
    GREEN: "绿牌新能源",
    BLACK_HK_MACAO: "黑牌港澳",
    YELLOW_DOUBLE: "黄牌双层",
}


def code_filter(code):
    """按车牌号规则粗判类型（与上游一致）。"""
    t = UNKNOWN
    if len(code) >= 2 and code[0] == "W" and code[1] == "J":
        t = WHITE_SINGLE
    elif len(code) == 8:
        t = GREEN
    elif "学" in code:
        t = BLUE
    elif "港" in code or "澳" in code:
        t = BLACK_HK_MACAO
    elif "警" in code:
        t = WHITE_SINGLE
    elif "粤Z" in code:
        t = BLACK_HK_MACAO
    return t


# ---------------- 检测前后处理 ----------------
def letter_box(img, size=(640, 640)):
    h, w = img.shape[:2]
    r = min(size[0] / h, size[1] / w)
    new_h, new_w = int(h * r), int(w * r)
    top = int((size[0] - new_h) / 2)
    left = int((size[1] - new_w) / 2)
    bottom = size[0] - new_h - top
    right = size[1] - new_w - left
    resized = cv2.resize(img, (new_w, new_h))
    out = cv2.copyMakeBorder(resized, top, bottom, left, right,
                             borderType=cv2.BORDER_CONSTANT, value=(0, 0, 0))
    return out, r, left, top


def xywh2xyxy(boxes):
    out = boxes.copy()
    out[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
    out[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
    out[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
    out[:, 3] = boxes[:, 1] + boxes[:, 3] / 2
    return out


def nms(boxes, iou_thresh):
    index = np.argsort(boxes[:, 4])[::-1]
    keep = []
    while index.size > 0:
        i = index[0]
        keep.append(i)
        x1 = np.maximum(boxes[i, 0], boxes[index[1:], 0])
        y1 = np.maximum(boxes[i, 1], boxes[index[1:], 1])
        x2 = np.minimum(boxes[i, 2], boxes[index[1:], 2])
        y2 = np.minimum(boxes[i, 3], boxes[index[1:], 3])
        w = np.maximum(0, x2 - x1)
        h = np.maximum(0, y2 - y1)
        inter = w * h
        union = ((boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1]) +
                 (boxes[index[1:], 2] - boxes[index[1:], 0]) *
                 (boxes[index[1:], 3] - boxes[index[1:], 1]))
        iou = inter / np.maximum(union - inter, 1e-9)
        index = index[np.where(iou <= iou_thresh)[0] + 1]
    return keep


def restore_box(boxes, r, left, top):
    boxes[:, [0, 2, 5, 7, 9, 11]] -= left
    boxes[:, [1, 3, 6, 8, 10, 12]] -= top
    boxes[:, [0, 2, 5, 7, 9, 11]] /= r
    boxes[:, [1, 3, 6, 8, 10, 12]] /= r
    return boxes


def detect_preprocess(img, size):
    img_lb, r, left, top = letter_box(img, size)
    x = img_lb[:, :, ::-1].transpose(2, 0, 1).copy().astype(np.float32) / 255.0
    return x.reshape(1, *x.shape), r, left, top


def detect_postprocess(dets, r, left, top, conf_thresh=0.5, iou_thresh=0.5):
    """dets: (1, N, 15) → (M, 14)  [x1,y1,x2,y2,score, 8个关键点, 层数]"""
    choice = dets[:, :, 4] > conf_thresh
    dets = dets[choice]
    if dets.shape[0] == 0:
        return np.zeros((0, 14), dtype=np.float32)
    dets[:, 13:15] *= dets[:, 4:5]
    boxes = xywh2xyxy(dets[:, :4])
    score = np.max(dets[:, 13:15], axis=-1, keepdims=True)
    index = np.argmax(dets[:, 13:15], axis=-1).reshape(-1, 1)
    output = np.concatenate((boxes, score, dets[:, 5:13], index), axis=1)
    keep = nms(output, iou_thresh)
    output = output[keep]
    return restore_box(output, r, left, top)


def get_rotate_crop_image(img, points):
    """按四个角点透视变换取出车牌区域。"""
    points = np.asarray(points, dtype=np.float32).reshape(4, 2)
    w = int(max(np.linalg.norm(points[0] - points[1]),
                np.linalg.norm(points[2] - points[3])))
    h = int(max(np.linalg.norm(points[0] - points[3]),
                np.linalg.norm(points[1] - points[2])))
    w, h = max(w, 1), max(h, 1)
    std = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    M = cv2.getPerspectiveTransform(points, std)
    dst = cv2.warpPerspective(img, M, (w, h),
                              borderMode=cv2.BORDER_REPLICATE,
                              flags=cv2.INTER_CUBIC)
    if dst.shape[0] * 1.0 / dst.shape[1] >= 1.5:
        dst = np.rot90(dst)
    return np.ascontiguousarray(dst)
