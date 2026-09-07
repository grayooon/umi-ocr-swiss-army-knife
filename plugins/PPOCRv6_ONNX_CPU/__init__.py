# ==========================================
# ====== Umi-OCR 插件： PP-OCRv6 (CPU) ======
# ==========================================
# 引擎: PaddleOCR PP-OCRv6 (tiny / small / medium 三档模型 = 三种模式)
# 推理: ONNX Runtime, 纯 CPU, 多线程, 完全离线
# 平台: Windows / Linux (使用 Umi-OCR 自带的 python 环境)

from . import ppocr_api
from . import ppocr_config

PluginInfo = {
    "group": "ocr",                                # 固定写法，OCR 插件组
    "global_options": ppocr_config.globalOptions,  # 全局配置字典
    "local_options": ppocr_config.localOptions,    # 局部配置字典
    "api_class": ppocr_api.Api,                    # 接口类
}
