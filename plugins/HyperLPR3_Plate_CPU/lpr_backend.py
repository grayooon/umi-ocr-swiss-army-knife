# ==========================================================
# ====== Umi-OCR 插件接口： HyperLPR3 中国车牌识别（纯CPU） ======
# ==========================================================
# 与 OCR 插件使用同一套接口，因此截图识别、批量识别、HTTP 接口识别均可直接使用。

import os
import sys
import time
import traceback

CurrentDir = os.path.dirname(os.path.abspath(__file__))
SitePackages = os.path.join(CurrentDir, "site-packages")

ERR_INIT, ERR_IMAGE, ERR_RUN = 112, 113, 114


def _err(code, msg):
    return {"code": code, "data": f"[Error] {msg}"}


class Api:
    def __init__(self, globalArgd):
        self.globalArgd = globalArgd or {}
        self.pipes = {}
        self.cur = None
        self.argd = {}
        self._pipeline = None
        self._imgio = None

    def _import(self):
        if self._pipeline is not None:
            return ""
        try:
            from .lpr_engine import pipeline as _p
            from .lpr_engine import imgio as _i
        except Exception:
            try:
                if CurrentDir not in sys.path:
                    sys.path.insert(0, CurrentDir)
                from lpr_engine import pipeline as _p
                from lpr_engine import imgio as _i
            except Exception as e:
                return (f"缺少运行依赖或导入失败：{e}\n"
                        f"请先运行插件目录下 tools/install_deps.bat 。\n"
                        f"{traceback.format_exc()}")
        self._pipeline = _p
        self._imgio = _i
        return ""

    def start(self, argd):
        msg = self._import()
        if msg:
            return "[Error] " + msg
        self.argd = argd or {}
        level = str(self.argd.get("detect_level", "low"))
        if level not in ("low", "high"):
            level = "low"
        key = "%s|%s|%s|%s|%s" % (
            level,
            self.argd.get("box_threshold", 0.5),
            self.argd.get("nms_threshold", 0.5),
            bool(self.argd.get("use_cls", True)),
            self.argd.get("rec_threshold", 0.0),
        )
        if key in self.pipes:
            self.cur = self.pipes[key]
            return ""
        g = self.globalArgd
        try:
            p = self._pipeline.LprPipeline(
                models_dir=str(g.get("models_dir", "") or ""),
                detect_level=level,
                num_threads=int(g.get("num_threads", 0) or 0),
                workers=int(g.get("workers", 2) or 2),
                box_threshold=float(self.argd.get("box_threshold", 0.5) or 0.5),
                nms_threshold=float(self.argd.get("nms_threshold", 0.5) or 0.5),
                rec_threshold=float(self.argd.get("rec_threshold", 0.0) or 0.0),
                use_cls=bool(self.argd.get("use_cls", True)),
            )
            t1 = time.time()
            p.load()
            print(f"[HyperLPR3] 模型加载完毕（{level}），耗时 {time.time() - t1:.2f}s")
        except Exception as e:
            return "[Error] " + str(e)
        self.pipes[key] = p
        self.cur = p
        return ""

    def stop(self):
        for p in self.pipes.values():
            try:
                p.stop()
            except Exception:
                pass
        self.pipes.clear()
        self.cur = None

    def runPath(self, imgPath: str):
        return self._run(lambda: self._imgio.from_path(imgPath))

    def runBytes(self, imageBytes):
        return self._run(lambda: self._imgio.from_bytes(imageBytes))

    def runBase64(self, imageBase64):
        return self._run(lambda: self._imgio.from_base64(imageBase64))

    def _run(self, loader):
        if self.cur is None:
            msg = self.start(self.argd)
            if msg:
                return _err(ERR_INIT, msg.replace("[Error] ", "", 1))
        try:
            img = loader()
        except Exception as e:
            return _err(ERR_IMAGE, str(e))
        try:
            plates = self.cur.run(img)
        except Exception as e:
            print("[HyperLPR3] 推理异常：", traceback.format_exc())
            return _err(ERR_RUN, str(e))
        if not plates:
            return {"code": 101, "data": ""}
        show_type = bool(self.argd.get("show_type", False))
        data = []
        for p in plates:
            text = p["text"]
            if show_type:
                text = f"{text} [{p['plate_type_name']}]"
            data.append({
                "text": text,
                "box": p["box"],
                "score": p["score"],
                # 额外信息，Umi-OCR 会忽略未知字段，方便 HTTP 接口二次开发使用
                "plate_type": p["plate_type"],
                "plate_type_name": p["plate_type_name"],
                "layer": p["layer"],
                "det_score": p["det_score"],
            })
        return {"code": 100, "data": data}
