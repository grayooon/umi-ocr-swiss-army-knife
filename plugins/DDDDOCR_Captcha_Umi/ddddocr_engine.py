import os
import threading

try:
    from .captcha_preprocess import conservative_gray_removal
    from .ctc_decoder import decode_probability
except ImportError:
    from captcha_preprocess import conservative_gray_removal
    from ctc_decoder import decode_probability


RANGE_MAP = {
    "digits": 0,
    "lower": 1,
    "upper": 2,
    "letters": 3,
    "lower_digits": 4,
    "upper_digits": 5,
    "alnum": 6,
}


class EngineError(Exception):
    pass


class CaptchaEngine(object):
    def __init__(self, global_args=None):
        self.global_args = global_args or {}
        self.engines = {}
        self.lock = threading.RLock()

    def _new_engine(self, name, local_args):
        import onnxruntime as ort
        ort.disable_telemetry_events()
        import ddddocr

        common = {"show_ad": False, "use_gpu": False}
        if name == "custom":
            model = str(self.global_args.get("custom_model", "") or "")
            charset = str(self.global_args.get("custom_charset_file", "") or "")
            base = os.path.dirname(os.path.abspath(__file__))
            model = model if os.path.isabs(model) else os.path.join(base, model)
            charset = charset if os.path.isabs(charset) else os.path.join(base, charset)
            if not os.path.isfile(model) or not os.path.isfile(charset):
                raise EngineError("自定义模型模式需要有效的 ONNX 模型和 charsets.json。")
            engine = ddddocr.DdddOcr(import_onnx_path=model, charsets_path=charset, **common)
        else:
            engine = ddddocr.DdddOcr(beta=(name == "beta"), **common)
            custom_chars = str(local_args.get("custom_chars", "") or "").strip()
            charset_mode = str(local_args.get("charset", "lower_digits"))
            if custom_chars:
                engine.set_ranges(custom_chars)
            else:
                engine.set_ranges(RANGE_MAP.get(charset_mode, 4))
        return engine

    def get_engine(self, name, local_args):
        custom_chars = str(local_args.get("custom_chars", "") or "")
        charset_mode = str(local_args.get("charset", "lower_digits"))
        key = "%s|%s|%s" % (name, charset_mode, custom_chars)
        with self.lock:
            if key not in self.engines:
                self.engines[key] = self._new_engine(name, local_args)
            return self.engines[key]

    def close(self):
        with self.lock:
            self.engines.clear()

    def _recognize_one(self, engine_name, source_name, image_bytes, local_args):
        engine = self.get_engine(engine_name, local_args)
        if engine_name == "custom":
            text = engine.classification(image_bytes)
            return {
                "text": str(text), "score": 0.5, "char_scores": [],
                "source": source_name, "model": engine_name,
            }
        probability = engine.classification(image_bytes, probability=True)
        text, score, char_scores = decode_probability(
            probability,
            expected_length=int(local_args.get("expected_length", 4) or 4),
            decoder=str(local_args.get("decoder", "exact_beam")),
            beam_width=int(local_args.get("beam_width", 12) or 12),
        )
        return {
            "text": text, "score": float(score), "char_scores": char_scores,
            "source": source_name, "model": engine_name,
        }

    @staticmethod
    def _select(candidates, expected_length):
        grouped = {}
        for item in candidates:
            text = item["text"]
            grouped.setdefault(text, []).append(item)
        ranked = []
        for text, items in grouped.items():
            scores = [float(item["score"]) for item in items]
            beta_bonus = 0.002 if any(item["model"] == "beta" for item in items) else 0.0
            rank = (
                int(len(text) == expected_length),
                len(items),
                sum(scores) / max(len(scores), 1) + beta_bonus,
                max(scores),
            )
            ranked.append((rank, text, items))
        if not ranked:
            return {"text": "", "score": 0.0, "char_scores": [], "source": "none", "model": "none"}
        _, _, winners = max(ranked, key=lambda item: item[0])
        best = max(winners, key=lambda item: float(item["score"]))
        best = dict(best)
        best["votes"] = len(winners)
        best["candidates"] = candidates
        return best

    def run(self, image_bytes, local_args):
        mode = str(local_args.get("mode", "beta"))
        expected_length = int(local_args.get("expected_length", 4) or 4)
        variants = [("raw", image_bytes)]
        model_names = ["beta"]
        if mode == "classic":
            model_names = ["classic"]
        elif mode == "dual":
            model_names = ["beta", "classic"]
        elif mode == "race":
            model_names = ["beta", "classic"]
            safe, removed = conservative_gray_removal(
                image_bytes,
                max_chroma=int(local_args.get("gray_chroma", 8) or 8),
                min_luma=int(local_args.get("gray_min_luma", 105) or 105),
                max_luma=int(local_args.get("gray_max_luma", 242) or 242),
            )
            variants.append(("safe_gray_%d" % removed, safe))
        elif mode == "custom":
            model_names = ["custom"]
        candidates = []
        for model_name in model_names:
            for variant_name, data in variants:
                candidates.append(
                    self._recognize_one(
                        model_name,
                        "%s/%s" % (model_name, variant_name),
                        data,
                        local_args,
                    )
                )
        return self._select(candidates, expected_length)
