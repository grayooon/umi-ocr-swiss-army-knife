# ===================================================
# =============== 文本行方向分类（可选） ==============
# ===================================================
# 用于把倒置(180°)的文本行转正。模型缺失时自动跳过，不影响识别。
# 兼容 ch_ppocr_mobile_v2.0_cls 与 PP-LCNet_x*_textline_ori 。

import cv2
import numpy as np

from .ort_utils import make_session, session_io


class TextClassifier:
    def __init__(self, model_path, num_threads=0, batch_size=6, thresh=0.9):
        self.sess = make_session(model_path, num_threads)
        self.input_name, self.output_names, shape = session_io(self.sess)
        # 从模型自身推断输入尺寸，动态维用默认值
        h = shape[2] if isinstance(shape[2], int) and shape[2] > 0 else 48
        w = shape[3] if isinstance(shape[3], int) and shape[3] > 0 else 192
        self.image_shape = (3, int(h), int(w))
        self.batch_size = max(1, int(batch_size))
        self.thresh = float(thresh)

    def _resize_norm(self, img):
        imgC, imgH, imgW = self.image_shape
        h, w = img.shape[:2]
        ratio = w / float(h) if h > 0 else 1.0
        rw = min(int(np.ceil(imgH * ratio)), imgW)
        rw = max(rw, 1)
        resized = cv2.resize(img, (rw, imgH)).astype(np.float32)
        resized = resized.transpose(2, 0, 1) / 255.0
        resized -= 0.5
        resized /= 0.5
        padded = np.zeros((imgC, imgH, imgW), dtype=np.float32)
        padded[:, :, :rw] = resized
        return padded

    def __call__(self, img_list):
        """就地把倒置的文本行旋转 180°，返回处理后的列表。"""
        out = list(img_list)
        for beg in range(0, len(out), self.batch_size):
            chunk = out[beg: beg + self.batch_size]
            batch = np.stack([self._resize_norm(im) for im in chunk])
            preds = np.array(self.sess.run(
                self.output_names[:1], {self.input_name: batch})[0])
            if preds.ndim == 1:
                preds = preds[None, :]
            for i in range(len(chunk)):
                label = int(np.argmax(preds[i]))
                score = float(np.max(preds[i]))
                if label == 1 and score > self.thresh:  # 1 → 180 度
                    out[beg + i] = cv2.rotate(chunk[i], cv2.ROTATE_180)
        return out
