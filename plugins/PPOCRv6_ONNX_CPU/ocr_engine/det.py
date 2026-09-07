# =================================================
# =============== 文本检测 (DB / PP-OCRv6) =========
# =================================================
# 与 PaddleOCR 官方 DBPostProcess (box_type=quad) 行为对齐。
# 默认参数取自 PP-OCRv6 官方 inference.yml ：
#   thresh 0.2 / box_thresh 0.45 / unclip_ratio 1.4 / max_candidates 3000
# 归一化取自官方配置： scale 1/255, mean(0.485,0.456,0.406), std(0.229,0.224,0.225)

import cv2
import numpy as np

from .ort_utils import make_session, session_io

try:  # 可选依赖：有 pyclipper 时与官方实现完全一致
    import pyclipper
    from shapely.geometry import Polygon as _ShapelyPolygon  # noqa
    _HAS_CLIPPER = True
except Exception:
    try:
        import pyclipper
        _HAS_CLIPPER = True
    except Exception:
        pyclipper = None
        _HAS_CLIPPER = False


class TextDetector:
    def __init__(self, model_path, num_threads=0,
                 limit_side_len=960, limit_type="max",
                 thresh=0.2, box_thresh=0.45, unclip_ratio=1.4,
                 max_candidates=3000, min_size=3,
                 mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)):
        self.sess = make_session(model_path, num_threads)
        self.input_name, self.output_names, _ = session_io(self.sess)
        self.limit_side_len = int(limit_side_len)
        self.limit_type = limit_type or "max"
        self.thresh = float(thresh)
        self.box_thresh = float(box_thresh)
        self.unclip_ratio = float(unclip_ratio)
        self.max_candidates = int(max_candidates)
        self.min_size = int(min_size)
        self.mean = np.array(mean, dtype=np.float32).reshape(1, 1, 3)
        self.std = np.array(std, dtype=np.float32).reshape(1, 1, 3)

    # ---------------- 前处理 ----------------
    def _resize(self, img):
        h, w = img.shape[:2]
        limit = self.limit_side_len
        if self.limit_type == "max":
            ratio = limit / max(h, w) if max(h, w) > limit else 1.0
        else:  # min
            ratio = limit / min(h, w) if min(h, w) < limit else 1.0
        rh, rw = int(h * ratio), int(w * ratio)
        # 长宽必须是 32 的整数倍
        rh = max(int(round(rh / 32) * 32), 32)
        rw = max(int(round(rw / 32) * 32), 32)
        resized = cv2.resize(img, (rw, rh), interpolation=cv2.INTER_LINEAR)
        return resized, (w / float(rw), h / float(rh))

    def _normalize(self, img):
        x = img.astype(np.float32) / 255.0
        x = (x - self.mean) / self.std
        x = x.transpose(2, 0, 1)[None, ...]
        return np.ascontiguousarray(x, dtype=np.float32)

    # ---------------- 主流程 ----------------
    def __call__(self, img):
        src_h, src_w = img.shape[:2]
        resized, (ratio_w, ratio_h) = self._resize(img)
        x = self._normalize(resized)
        out = self.sess.run(self.output_names[:1], {self.input_name: x})[0]
        pred = np.array(out)
        while pred.ndim > 2:  # (1,1,H,W) -> (H,W)
            pred = pred[0]
        boxes, scores = self._boxes_from_bitmap(
            pred, pred > self.thresh, ratio_w, ratio_h, src_w, src_h)
        return boxes, scores

    # ---------------- 后处理 ----------------
    def _boxes_from_bitmap(self, pred, bitmap, ratio_w, ratio_h, src_w, src_h):
        mask = (bitmap * 255).astype(np.uint8)
        contours_info = cv2.findContours(
            mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours_info[0] if len(contours_info) == 2 else contours_info[1]
        boxes, scores = [], []
        for contour in contours[: self.max_candidates]:
            points, sside = self._get_mini_box(contour)
            if sside < self.min_size:
                continue
            score = self._box_score_fast(pred, points)
            if score < self.box_thresh:
                continue
            box = self._unclip(points, contour)
            if box is None:
                continue
            box, sside = self._get_mini_box(box.reshape(-1, 1, 2).astype(np.int32))
            if sside < self.min_size + 2:
                continue
            box[:, 0] = np.clip(np.round(box[:, 0] * ratio_w), 0, src_w - 1)
            box[:, 1] = np.clip(np.round(box[:, 1] * ratio_h), 0, src_h - 1)
            boxes.append(box.astype(np.int32))
            scores.append(float(score))
        return boxes, scores

    @staticmethod
    def _get_mini_box(contour):
        """最小外接矩形 → 顺时针四点(左上、右上、右下、左下)"""
        rect = cv2.minAreaRect(contour)
        pts = sorted(list(cv2.boxPoints(rect)), key=lambda p: p[0])
        if pts[1][1] > pts[0][1]:
            i1, i4 = 0, 1
        else:
            i1, i4 = 1, 0
        if pts[3][1] > pts[2][1]:
            i2, i3 = 2, 3
        else:
            i2, i3 = 3, 2
        box = np.array([pts[i1], pts[i2], pts[i3], pts[i4]], dtype=np.float32)
        return box, min(rect[1])

    @staticmethod
    def _box_score_fast(pred, box):
        h, w = pred.shape[:2]
        b = box.copy()
        xmin = int(np.clip(np.floor(b[:, 0].min()), 0, w - 1))
        xmax = int(np.clip(np.ceil(b[:, 0].max()), 0, w - 1))
        ymin = int(np.clip(np.floor(b[:, 1].min()), 0, h - 1))
        ymax = int(np.clip(np.ceil(b[:, 1].max()), 0, h - 1))
        mask = np.zeros((ymax - ymin + 1, xmax - xmin + 1), dtype=np.uint8)
        b[:, 0] -= xmin
        b[:, 1] -= ymin
        cv2.fillPoly(mask, [b.reshape(1, -1, 2).astype(np.int32)], 1)
        region = pred[ymin:ymax + 1, xmin:xmax + 1]
        if region.size == 0 or mask.sum() == 0:
            return 0.0
        return float(cv2.mean(region.astype(np.float32), mask)[0])

    def _unclip(self, box, contour=None):
        """按 unclip_ratio 外扩文本框。

        有 pyclipper 时使用与 PaddleOCR 完全一致的多边形偏移；
        没有时退化为等价的矩形外扩（对四点框结果几乎一致）。
        """
        poly = box.astype(np.float64)
        area = abs(self._poly_area(poly))
        peri = self._poly_perimeter(poly)
        if peri <= 0:
            return None
        distance = area * self.unclip_ratio / peri
        if _HAS_CLIPPER:
            try:
                offset = pyclipper.PyclipperOffset()
                offset.AddPath(poly.astype(np.int64).tolist(),
                               pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
                expanded = offset.Execute(distance)
                if expanded:
                    return np.array(expanded[0], dtype=np.float32)
            except Exception:
                pass
        # 退化方案：对最小外接矩形的四条边各外移 distance
        # （对四点框而言，与 pyclipper 的多边形偏移结果基本一致）
        rect = cv2.minAreaRect(poly.astype(np.float32))
        (cx, cy), (rw, rh), ang = rect
        expanded = ((cx, cy), (rw + 2.0 * distance, rh + 2.0 * distance), ang)
        return cv2.boxPoints(expanded).astype(np.float32)

    @staticmethod
    def _poly_area(p):
        x, y = p[:, 0], p[:, 1]
        return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)

    @staticmethod
    def _poly_perimeter(p):
        d = p - np.roll(p, -1, axis=0)
        return float(np.sum(np.sqrt((d ** 2).sum(axis=1))))


def sort_boxes(boxes, scores, extra=None):
    """从上到下、从左到右排序（同一行内按 x 排序）。"""
    if not boxes:
        return boxes, scores
    idx = list(range(len(boxes)))
    idx.sort(key=lambda i: (boxes[i][0][1], boxes[i][0][0]))
    b = [boxes[i] for i in idx]
    s = [scores[i] for i in idx]
    # 同一行微调
    for i in range(len(b) - 1):
        for j in range(i, -1, -1):
            if abs(b[j + 1][0][1] - b[j][0][1]) < 10 and b[j + 1][0][0] < b[j][0][0]:
                b[j], b[j + 1] = b[j + 1], b[j]
                s[j], s[j + 1] = s[j + 1], s[j]
            else:
                break
    return b, s
