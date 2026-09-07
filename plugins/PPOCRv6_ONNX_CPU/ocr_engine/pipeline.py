# =========================================================
# =============== PP-OCRv6 识别流水线（纯CPU） ==============
# =========================================================
# 三种模式 = PP-OCRv6 官方的三档模型：
#   tiny   ( 1.5M 参数 ) 端侧/极速
#   small  ( 7.7M 参数 ) 均衡（推荐）
#   medium (34.5M 参数 ) 高精度
# 每种模式各由 检测(det) + 识别(rec) 两个 ONNX 模型组成，
# 可另配一个可选的 文本行方向分类(cls) 模型。

import os
import threading

from . import paths
from .cls import TextClassifier
from .det import TextDetector, sort_boxes
from .imgio import get_rotate_crop_image
from .ppyaml import load_infer_config
from .rec import TextRecognizer

# ---------------- 模式定义 ----------------
MODES = {
    "tiny": {
        "title": "PP-OCRv6_tiny",
        "det": "PP-OCRv6_tiny_det",
        "rec": "PP-OCRv6_tiny_rec",
    },
    "small": {
        "title": "PP-OCRv6_small",
        "det": "PP-OCRv6_small_det",
        "rec": "PP-OCRv6_small_rec",
    },
    "medium": {
        "title": "PP-OCRv6_medium",
        "det": "PP-OCRv6_medium_det",
        "rec": "PP-OCRv6_medium_rec",
    },
}
# 可选的方向分类模型（按顺序尝试）
CLS_CANDIDATES = [
    "PP-LCNet_x1_0_textline_ori",
    "PP-LCNet_x0_25_textline_ori",
    "ch_ppocr_mobile_v2.0_cls",
]

# PP-OCRv6 官方 inference.yml 中的默认后处理参数
DEFAULT_DET_POST = {
    "thresh": 0.2,
    "box_thresh": 0.45,
    "unclip_ratio": 1.4,
    "max_candidates": 3000,
}


class EngineError(Exception):
    pass


class OcrPipeline:
    """一个模式对应一条流水线。线程安全（内部加锁保护加载过程）。"""

    def __init__(self, mode, models_dir="", num_threads=0, rec_workers=2,
                 rec_batch=6, limit_side_len=960, limit_type="max",
                 use_cls=False, drop_score=0.0, det_overrides=None):
        if mode not in MODES:
            raise EngineError(f"未知的模型档位：{mode}")
        self.mode = mode
        self.models_dir = models_dir
        self.num_threads = num_threads
        self.rec_workers = rec_workers
        self.rec_batch = rec_batch
        self.limit_side_len = limit_side_len
        self.limit_type = limit_type
        self.use_cls = use_cls
        self.drop_score = float(drop_score)
        self.det_overrides = det_overrides or {}
        self._lock = threading.Lock()
        self.det = None
        self.rec = None
        self.cls = None
        self.info = {}

    # ---------------- 加载 ----------------
    def load(self):
        with self._lock:
            if self.det and self.rec:
                return
            spec = MODES[self.mode]
            det_path, det_cfg_path = paths.find_model(spec["det"], self.models_dir)
            rec_path, rec_cfg_path = paths.find_model(spec["rec"], self.models_dir)
            missing = []
            if not det_path:
                missing.append(spec["det"])
            if not rec_path:
                missing.append(spec["rec"])
            if missing:
                raise EngineError(
                    "未找到模型： " + " 、".join(missing) + "\n"
                    "已搜索的目录：\n" + paths.describe_search_dirs(self.models_dir) +
                    "\n请把模型放入上述任一目录，或在【全局设置 → PP-OCRv6】中指定模型目录。\n"
                    "可运行插件目录下 tools/download_models.bat 一次性下载模型（下载后即可完全离线使用）。"
                )
            det_cfg = load_infer_config(det_cfg_path)
            rec_cfg = load_infer_config(rec_cfg_path)

            post = dict(DEFAULT_DET_POST)
            post.update({k: v for k, v in det_cfg.get("post", {}).items()
                         if k in DEFAULT_DET_POST})
            post.update({k: v for k, v in self.det_overrides.items()
                         if v is not None})
            pre = det_cfg.get("pre", {})
            mean = pre.get("mean", (0.485, 0.456, 0.406))
            std = pre.get("std", (0.229, 0.224, 0.225))

            self.det = TextDetector(
                det_path, num_threads=self.num_threads,
                limit_side_len=self.limit_side_len, limit_type=self.limit_type,
                thresh=post["thresh"], box_thresh=post["box_thresh"],
                unclip_ratio=post["unclip_ratio"],
                max_candidates=post["max_candidates"],
                mean=mean, std=std)

            chars = rec_cfg.get("character_dict")
            if not chars:
                raise EngineError(
                    f"识别模型缺少字符字典：{rec_cfg_path or rec_path}\n"
                    "请确认模型目录中存在官方的 inference.yml （或 dict.txt ）。")
            image_shape = rec_cfg.get("pre", {}).get("image_shape", [3, 48, 320])
            self.rec = TextRecognizer(
                rec_path, chars, num_threads=self.num_threads,
                image_shape=image_shape, batch_size=self.rec_batch,
                workers=self.rec_workers)

            if self.use_cls:
                for name in CLS_CANDIDATES:
                    p, _ = paths.find_model(name, self.models_dir)
                    if p:
                        try:
                            self.cls = TextClassifier(p, num_threads=self.num_threads,
                                                      batch_size=self.rec_batch)
                            break
                        except Exception:
                            self.cls = None
            self.info = {
                "mode": self.mode,
                "det": det_path,
                "rec": rec_path,
                "cls": "" if not self.cls else "on",
                "chars": len(chars),
                "image_shape": list(image_shape),
                "det_post": post,
            }

    def stop(self):
        with self._lock:
            if self.rec:
                try:
                    self.rec.close()
                except Exception:
                    pass
            self.det = None
            self.rec = None
            self.cls = None

    # ---------------- 运行 ----------------
    def run(self, img):
        if self.det is None or self.rec is None:
            self.load()
        boxes, det_scores = self.det(img)
        if not boxes:
            return []
        boxes, det_scores = sort_boxes(boxes, det_scores)
        crops = [get_rotate_crop_image(img, b) for b in boxes]
        if self.cls:
            try:
                crops = self.cls(crops)
            except Exception:
                pass
        rec_res = self.rec(crops)
        out = []
        for box, (text, score) in zip(boxes, rec_res):
            if not text:
                continue
            if score < self.drop_score:
                continue
            out.append({
                "text": text,
                "box": [[int(p[0]), int(p[1])] for p in box],
                "score": round(float(score), 4),
            })
        return out
