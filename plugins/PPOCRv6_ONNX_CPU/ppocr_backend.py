# =====================================================
# ====== Umi-OCR 插件接口： PP-OCRv6 （ONNX / 纯CPU） ======
# =====================================================
# 实现 Umi-OCR 规定的 OCR 插件接口： start / stop / runPath / runBytes / runBase64
# 三种模型档位（tiny / small / medium）以“模式”的形式在局部配置中切换，
# 截图识别、批量识别、HTTP 接口识别都会经由同一套接口，无需额外适配。

import os
import sys
import time
import traceback

# ---------- 把插件自带的依赖目录加入搜索路径 ----------
CurrentDir = os.path.dirname(os.path.abspath(__file__))
SitePackages = os.path.join(CurrentDir, "site-packages")

# 错误码（>101 为自定义）
ERR_INIT = 102     # 引擎初始化/模型加载失败
ERR_IMAGE = 103    # 图片读取失败
ERR_RUN = 104      # 推理过程异常
ERR_DEPEND = 105   # 缺少依赖库


def _err(code, msg):
    return {"code": code, "data": f"[Error] {msg}"}


class Api:
    def __init__(self, globalArgd):
        self.globalArgd = globalArgd or {}
        self.pipelines = {}     # mode -> OcrPipeline
        self.cur = None         # 当前流水线
        self.argd = {}
        self._imgio = None
        self._engine = None
        self._loadErr = ""

    # ---------------- 依赖导入 ----------------
    def _import(self):
        """延迟导入重量级依赖，避免拖慢 Umi-OCR 启动。"""
        if self._engine is not None:
            return ""
        try:
            # 插件被 Umi-OCR 作为包导入，优先使用包内相对导入
            from .ocr_engine import pipeline as _pipeline  # noqa
            from .ocr_engine import imgio as _imgio  # noqa
        except Exception:
            # 直接以脚本方式运行时（自检、单元测试）的兜底
            try:
                if CurrentDir not in sys.path:
                    sys.path.insert(0, CurrentDir)
                from ocr_engine import pipeline as _pipeline  # noqa
                from ocr_engine import imgio as _imgio  # noqa
            except Exception as e:
                return (f"缺少运行依赖或导入失败：{e}\n"
                        f"请先运行插件目录下 tools/install_deps.bat 安装 "
                        f"onnxruntime / numpy / opencv 到 {SitePackages} 。\n"
                        f"{traceback.format_exc()}")
        self._engine = _pipeline
        self._imgio = _imgio
        return ""

    # ---------------- 启动 ----------------
    def start(self, argd):
        """由 Umi-OCR 在每次任务开始前调用，传入局部配置。"""
        msg = self._import()
        if msg:
            return "[Error] " + msg
        self.argd = argd or {}
        mode = str(self.argd.get("mode", "small"))
        if mode not in self._engine.MODES:
            mode = "small"
        key = "%s|%s|%s|%s|%s|%s" % (
            mode,
            self.argd.get("limit_side_len", 960),
            bool(self.argd.get("use_cls", False)),
            self.argd.get("box_thresh", ""),
            self.argd.get("unclip_ratio", ""),
            self.argd.get("drop_score", 0.0),
        )
        if key in self.pipelines:
            self.cur = self.pipelines[key]
            return ""
        g = self.globalArgd
        try:
            p = self._engine.OcrPipeline(
                mode=mode,
                models_dir=str(g.get("models_dir", "") or ""),
                num_threads=int(g.get("num_threads", 0) or 0),
                rec_workers=int(g.get("rec_workers", 2) or 2),
                rec_batch=int(g.get("rec_batch", 6) or 6),
                limit_side_len=int(self.argd.get("limit_side_len", 960) or 960),
                use_cls=bool(self.argd.get("use_cls", False)),
                drop_score=float(self.argd.get("drop_score", 0.0) or 0.0),
                det_overrides={
                    "box_thresh": _f(self.argd.get("box_thresh")),
                    "unclip_ratio": _f(self.argd.get("unclip_ratio")),
                },
            )
            t1 = time.time()
            p.load()
            print(f"[PP-OCRv6] 模型加载完毕（{mode}），耗时 {time.time() - t1:.2f}s")
            print(f"[PP-OCRv6] {p.info}")
        except Exception as e:
            return "[Error] " + str(e)
        if not self.globalArgd.get("keep_loaded", True):
            self.pipelines.clear()
        self.pipelines[key] = p
        self.cur = p
        return ""

    # ---------------- 停止 ----------------
    def stop(self):
        for p in self.pipelines.values():
            try:
                p.stop()
            except Exception:
                pass
        self.pipelines.clear()
        self.cur = None

    # ---------------- 三种输入 ----------------
    def runPath(self, imgPath: str):
        return self._run(lambda: self._imgio.from_path(imgPath))

    def runBytes(self, imageBytes):
        return self._run(lambda: self._imgio.from_bytes(imageBytes))

    def runBase64(self, imageBase64):
        return self._run(lambda: self._imgio.from_base64(imageBase64))

    # ---------------- 核心 ----------------
    def _run(self, loader):
        if self.cur is None:
            msg = self.start(self.argd)
            if msg:
                return _err(ERR_INIT, msg[8:] if msg.startswith("[Error] ") else msg)
        try:
            img = loader()
        except Exception as e:
            return _err(ERR_IMAGE, str(e))
        try:
            data = self.cur.run(img)
        except Exception as e:
            print("[PP-OCRv6] 推理异常：", traceback.format_exc())
            return _err(ERR_RUN, str(e))
        if not data:
            return {"code": 101, "data": ""}
        return {"code": 100, "data": data}


def _f(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None
