# ==================================================
# =============== 文本识别 (CTC / PP-OCRv6) =========
# ==================================================
# 前处理与 PaddleOCR RecResizeImg 对齐： 高固定 48 ，宽按比例缩放并补零，
# 归一化 (x/255 - 0.5) / 0.5 。
# 后处理为标准 CTCLabelDecode ： 0 号为 blank ，字符表从 1 开始。

import math
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

from .ort_utils import make_session, session_io


class TextRecognizer:
    def __init__(self, model_path, character_dict, num_threads=0,
                 image_shape=(3, 48, 320), batch_size=6, workers=1):
        self.sess = make_session(model_path, num_threads)
        self.input_name, self.output_names, _ = session_io(self.sess)
        self.image_shape = tuple(int(x) for x in image_shape)
        self.batch_size = max(1, int(batch_size))
        self.workers = max(1, int(workers))
        self._pool = ThreadPoolExecutor(max_workers=self.workers) if self.workers > 1 else None
        # 字符表： index 0 = blank
        chars = list(character_dict)
        self.character = ["<blank>"] + chars
        if len(chars) == 0:
            raise ValueError("识别字典为空，请检查 inference.yml 或 dict.txt 。")

    def close(self):
        if self._pool:
            self._pool.shutdown(wait=False)
            self._pool = None

    # ---------------- 前处理 ----------------
    def _resize_norm(self, img, max_wh_ratio):
        imgC, imgH, imgW = self.image_shape
        imgW = int(imgH * max_wh_ratio)
        h, w = img.shape[:2]
        ratio = w / float(h) if h > 0 else 1.0
        rw = int(math.ceil(imgH * ratio))
        rw = min(rw, imgW)
        rw = max(rw, 1)
        resized = cv2.resize(img, (rw, imgH), interpolation=cv2.INTER_LINEAR)
        resized = resized.astype(np.float32).transpose(2, 0, 1) / 255.0
        resized -= 0.5
        resized /= 0.5
        padded = np.zeros((imgC, imgH, imgW), dtype=np.float32)
        padded[:, :, :rw] = resized
        return padded

    # ---------------- 推理 ----------------
    def __call__(self, img_list):
        n = len(img_list)
        results = [("", 0.0)] * n
        if n == 0:
            return results
        # 按宽高比排序，减少 padding 浪费
        ratios = [im.shape[1] / max(float(im.shape[0]), 1.0) for im in img_list]
        order = np.argsort(np.array(ratios))
        jobs = []
        for beg in range(0, n, self.batch_size):
            idxs = order[beg: beg + self.batch_size]
            jobs.append(list(idxs))
        if self._pool:
            futs = [self._pool.submit(self._run_batch, img_list, idxs, ratios) for idxs in jobs]
            for f in futs:
                for i, r in f.result():
                    results[i] = r
        else:
            for idxs in jobs:
                for i, r in self._run_batch(img_list, idxs, ratios):
                    results[i] = r
        return results

    def _run_batch(self, img_list, idxs, ratios):
        imgC, imgH, imgW = self.image_shape
        max_wh_ratio = imgW / float(imgH)
        for i in idxs:
            max_wh_ratio = max(max_wh_ratio, ratios[i])
        batch = np.stack([self._resize_norm(img_list[i], max_wh_ratio) for i in idxs])
        preds = self.sess.run(self.output_names[:1], {self.input_name: batch})[0]
        preds = np.array(preds)
        if preds.ndim == 2:  # (T,C) -> (1,T,C)
            preds = preds[None, ...]
        out = []
        for k, i in enumerate(idxs):
            out.append((int(i), self._ctc_decode(preds[k])))
        return out

    # ---------------- CTC 解码 ----------------
    def _ctc_decode(self, prob):
        idx = np.argmax(prob, axis=-1)
        conf = np.max(prob, axis=-1)
        chars, confs = [], []
        last = -1
        for t in range(len(idx)):
            c = int(idx[t])
            if c == last:
                last = c
                continue
            last = c
            if c == 0:  # blank
                continue
            if c < len(self.character):
                chars.append(self.character[c])
                confs.append(float(conf[t]))
        text = "".join(chars)
        score = float(np.mean(confs)) if confs else 0.0
        return text, score
