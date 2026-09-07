# ============================================================
# ====== HyperLPR3 车牌识别流水线（ONNX Runtime，纯 CPU） ======
# ============================================================
# 上游算法： https://github.com/szad670401/HyperLPR  (Apache-2.0)
# 流程： 多任务检测(带4关键点+单双层分类) → 透视矫正 → CTC 识别 → 颜色分类

import math
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

from . import paths
from .utils import (BLACK_HK_MACAO, BLUE, DOUBLE, GREEN, PLATE_CHARS,
                    PLATE_TYPE_BLUE, PLATE_TYPE_GREEN, PLATE_TYPE_YELLOW,
                    TYPE_NAMES, UNKNOWN, YELLOW_DOUBLE, YELLOW_SINGLE,
                    code_filter, detect_postprocess, detect_preprocess,
                    get_rotate_crop_image)


class LprError(Exception):
    pass


def _make_session(model_path, num_threads=0):
    import onnxruntime as ort
    ort.disable_telemetry_events()
    ort.set_default_logger_severity(3)
    so = ort.SessionOptions()
    so.intra_op_num_threads = int(num_threads) if num_threads and num_threads > 0 \
        else max(1, os.cpu_count() or 4)
    so.inter_op_num_threads = 1
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(model_path, sess_options=so,
                                providers=["CPUExecutionProvider"])


# ---------------------- 检测 ----------------------
class PlateDetector:
    def __init__(self, model_path, input_size=320, num_threads=0,
                 box_threshold=0.5, nms_threshold=0.5):
        self.sess = _make_session(model_path, num_threads)
        inp = self.sess.get_inputs()[0]
        self.input_name = inp.name
        self.output_name = self.sess.get_outputs()[0].name
        shape = inp.shape
        h = shape[2] if isinstance(shape[2], int) and shape[2] > 0 else input_size
        w = shape[3] if isinstance(shape[3], int) and shape[3] > 0 else input_size
        self.input_size = (int(h), int(w))
        self.box_threshold = float(box_threshold)
        self.nms_threshold = float(nms_threshold)

    def __call__(self, img):
        x, r, left, top = detect_preprocess(img, self.input_size)
        out = self.sess.run([self.output_name], {self.input_name: x})[0]
        out = np.array(out, dtype=np.float32)
        if out.ndim == 2:
            out = out[None, ...]
        return detect_postprocess(out, r, left, top,
                                  self.box_threshold, self.nms_threshold)


# ---------------------- 识别 ----------------------
class PlateRecognizer:
    def __init__(self, model_path, charset=None, num_threads=0,
                 input_size=(48, 160), limited_max_width=160, limited_min_width=48):
        self.sess = _make_session(model_path, num_threads)
        inp = self.sess.get_inputs()[0]
        self.input_name = inp.name
        self.output_name = self.sess.get_outputs()[0].name
        shape = inp.shape
        h = shape[2] if isinstance(shape[2], int) and shape[2] > 0 else input_size[0]
        w = shape[3] if isinstance(shape[3], int) and shape[3] > 0 else input_size[1]
        self.input_size = (int(h), int(w))
        self.limited_max_width = int(limited_max_width)
        self.limited_min_width = int(limited_min_width)
        self.charset = list(charset) if charset else list(PLATE_CHARS)
        self._checked = False

    def _preprocess(self, image):
        imgH, imgW = self.input_size
        h, w = image.shape[:2]
        max_wh_ratio = max(w / float(max(h, 1)), imgW / float(imgH))
        target_w = int(imgH * max_wh_ratio)
        target_w = max(min(target_w, self.limited_max_width), self.limited_min_width)
        ratio = w / float(max(h, 1))
        rw = max(int(math.ceil(imgH * ratio)), self.limited_min_width)
        rw = min(rw, target_w)
        resized = cv2.resize(image, (rw, imgH)).astype(np.float32)
        resized = (resized.transpose(2, 0, 1) - 127.5) / 127.5
        padded = np.zeros((3, imgH, target_w), dtype=np.float32)
        padded[:, :, :rw] = resized
        return padded[None, ...]

    def __call__(self, image):
        x = self._preprocess(image)
        out = self.sess.run([self.output_name], {self.input_name: x})[0]
        prob = np.array(out, dtype=np.float32)
        while prob.ndim > 3:
            prob = prob[0]
        if prob.ndim == 2:
            prob = prob[None, ...]
        if not self._checked:
            c = int(prob.shape[-1])
            n = len(self.charset)
            if c > n:
                # 模型类别数多于字符表：末尾多出的通常是训练时预留的占位类
                # （上游 HyperLPR3 的 77 项字符表 + 78 类输出即属此情况）。
                # 补空占位，命中时不产生字符，不影响正常车牌号。
                self.charset = self.charset + [""] * (c - n)
                print(f"[HyperLPR3] 模型输出 {c} 类，字符表 {n} 项，"
                      f"已按占位补齐 {c - n} 项（正常现象）。")
            elif c < n:
                raise LprError(
                    f"识别模型输出维度 {c} 小于字符表长度 {n} ，模型与字符表不匹配。\n"
                    "请确认使用的是 rpv3_mdict_160_r3.onnx ；"
                    "若为自定义模型，请在模型目录放置 plate_chars.txt "
                    "（每行一个字符，第一行为 blank ）。")
            self._checked = True
        idx = np.argmax(prob[0], axis=-1)
        conf = np.max(prob[0], axis=-1)
        chars, confs, last = [], [], -1
        for t in range(len(idx)):
            c = int(idx[t])
            if c == last:
                continue
            last = c
            if c == 0:  # blank
                continue
            if 0 < c < len(self.charset) and self.charset[c]:
                chars.append(self.charset[c])
                confs.append(float(conf[t]))
        return "".join(chars), (float(np.mean(confs)) if confs else 0.0)


# ---------------------- 颜色分类 ----------------------
class PlateClassifier:
    def __init__(self, model_path, num_threads=0, input_size=(96, 96)):
        self.sess = _make_session(model_path, num_threads)
        inp = self.sess.get_inputs()[0]
        self.input_name = inp.name
        self.output_name = self.sess.get_outputs()[0].name
        shape = inp.shape
        h = shape[2] if isinstance(shape[2], int) and shape[2] > 0 else input_size[0]
        w = shape[3] if isinstance(shape[3], int) and shape[3] > 0 else input_size[1]
        self.input_size = (int(w), int(h))  # cv2.resize 用 (w,h)

    def __call__(self, image):
        resized = cv2.resize(image, self.input_size).astype(np.float32) / 255.0
        x = resized.transpose(2, 0, 1)[None, ...].astype(np.float32)
        out = self.sess.run([self.output_name], {self.input_name: x})[0]
        return np.array(out).reshape(-1)


# ---------------------- 流水线 ----------------------
class LprPipeline:
    def __init__(self, models_dir="", detect_level="low", num_threads=0,
                 workers=2, box_threshold=0.5, nms_threshold=0.5,
                 rec_threshold=0.0, use_cls=True):
        self.models_dir = models_dir
        self.detect_level = detect_level  # low=320 高速 / high=640 高精度
        self.num_threads = num_threads
        self.workers = max(1, int(workers))
        self.box_threshold = box_threshold
        self.nms_threshold = nms_threshold
        self.rec_threshold = float(rec_threshold)
        self.use_cls = use_cls
        self._lock = threading.Lock()
        self._pool = None
        self.det = self.rec = self.cls = None
        self.info = {}

    def load(self):
        with self._lock:
            if self.det and self.rec:
                return
            det_key = "det_640" if self.detect_level == "high" else "det_320"
            det_path = paths.find_model(det_key, self.models_dir)
            rec_path = paths.find_model("rec", self.models_dir)
            cls_path = paths.find_model("cls", self.models_dir) if self.use_cls else ""
            missing = []
            if not det_path:
                missing.append(paths.MODEL_FILES[det_key])
            if not rec_path:
                missing.append(paths.MODEL_FILES["rec"])
            if missing:
                raise LprError(
                    "未找到车牌模型： " + " 、".join(missing) + "\n"
                    "已搜索的目录（部分）：\n" + paths.describe(self.models_dir) +
                    "\n请运行插件目录下 tools/download_models.bat 一次性下载模型，"
                    "或手动把模型文件放入上述任一目录。下载完成后即可完全离线运行。")
            charset = None
            cs = paths.find_charset(self.models_dir)
            if cs:
                with open(cs, "r", encoding="utf-8") as f:
                    charset = [l.rstrip("\r\n") for l in f if l.strip() != "" or True]
            self.det = PlateDetector(det_path, num_threads=self.num_threads,
                                     box_threshold=self.box_threshold,
                                     nms_threshold=self.nms_threshold)
            self.rec = PlateRecognizer(rec_path, charset=charset,
                                       num_threads=self.num_threads)
            self.cls = None
            if cls_path:
                try:
                    self.cls = PlateClassifier(cls_path, num_threads=self.num_threads)
                except Exception:
                    self.cls = None
            if self.workers > 1 and self._pool is None:
                self._pool = ThreadPoolExecutor(max_workers=self.workers)
            self.info = {"det": det_path, "rec": rec_path,
                         "cls": cls_path, "level": self.detect_level}

    def stop(self):
        with self._lock:
            if self._pool:
                self._pool.shutdown(wait=False)
                self._pool = None
            self.det = self.rec = self.cls = None

    # ---------- 单个车牌的识别 ----------
    def _one(self, img, out):
        rect = out[:4].astype(int)
        det_score = float(out[4])
        vertex = out[5:13].reshape(4, 2)
        layer = int(out[13])
        pad = get_rotate_crop_image(img, vertex)
        if pad.size == 0:
            return None
        if layer == DOUBLE:  # 双层车牌：上下拆开分别识别再拼接
            h = pad.shape[0]
            line = max(int(h * 0.4), 1)
            top_code, top_conf = self.rec(pad[:line, :])
            bot_code, bot_conf = self.rec(pad[line:, :])
            code = top_code + bot_code
            conf = (top_conf + bot_conf) / 2.0
        else:
            code, conf = self.rec(pad)
        if not code or len(code) < 6:
            return None
        if conf < self.rec_threshold:
            return None
        ptype = code_filter(code)
        if ptype == UNKNOWN and self.cls is not None:
            try:
                probs = self.cls(pad)
                idx = int(np.argmax(probs))
                if idx == PLATE_TYPE_YELLOW:
                    ptype = YELLOW_DOUBLE if layer == DOUBLE else YELLOW_SINGLE
                elif idx == PLATE_TYPE_BLUE:
                    ptype = BLUE
                elif idx == PLATE_TYPE_GREEN:
                    ptype = GREEN
            except Exception:
                pass
        return {
            "text": code,
            "box": [[int(p[0]), int(p[1])] for p in vertex],
            "rect": [int(v) for v in rect],
            "score": round(float(conf), 4),
            "det_score": round(det_score, 4),
            "layer": "double" if layer == DOUBLE else "single",
            "plate_type": ptype,
            "plate_type_name": TYPE_NAMES.get(ptype, "未知"),
        }

    def run(self, img):
        if self.det is None or self.rec is None:
            self.load()
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        dets = self.det(img)
        if dets is None or len(dets) == 0:
            return []
        if self._pool and len(dets) > 1:
            futs = [self._pool.submit(self._one, img, d) for d in dets]
            results = [f.result() for f in futs]
        else:
            results = [self._one(img, d) for d in dets]
        return [r for r in results if r]
