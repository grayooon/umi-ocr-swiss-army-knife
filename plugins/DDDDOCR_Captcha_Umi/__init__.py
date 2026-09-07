# ==============================================
# ===== Umi-OCR plugin: ddddocr Captcha CPU =====
# ==============================================

from . import ddddocr_api
from . import ddddocr_config

PluginInfo = {
    "group": "ocr",
    "global_options": ddddocr_config.globalOptions,
    "local_options": ddddocr_config.localOptions,
    "api_class": ddddocr_api.Api,
}
