# =====================================================
# =============== 车牌模型目录搜索 =====================
# =====================================================
# 支持：插件目录 models/ 、软件目录 models/ 、
#       用户目录 C:\Users\Administrator\.hyperlpr3\ 或 .umi-ocr\models\hyperlpr3\

import os

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_MODELS_DIR = os.path.join(PLUGIN_DIR, "models")

# 官方模型版本目录名
MODEL_VERSION = "20230229"

MODEL_FILES = {
    "det_320": "y5fu_320x_sim.onnx",
    "det_640": "y5fu_640x_sim.onnx",
    "rec": "rpv3_mdict_160_r3.onnx",
    "cls": "litemodel_cls_96x_r1.onnx",
}


def _user_home():
    for key in ("USERPROFILE", "HOME"):
        v = os.environ.get(key, "")
        if v and os.path.isdir(v):
            return v
    drive, path = os.environ.get("HOMEDRIVE", ""), os.environ.get("HOMEPATH", "")
    if drive and path and os.path.isdir(drive + path):
        return drive + path
    try:
        return os.path.expanduser("~")
    except Exception:
        return ""


def _umi_root():
    d = os.path.dirname(os.path.dirname(PLUGIN_DIR))  # UmiOCR-data
    root = os.path.dirname(d)
    return root if os.path.isdir(root) else os.getcwd()


def search_dirs(user_dir=""):
    dirs = []
    if user_dir:
        expanded_user = os.path.expandvars(os.path.expanduser(user_dir))
        dirs.append(os.path.abspath(expanded_user if os.path.isabs(expanded_user) else os.path.join(PLUGIN_DIR, expanded_user)))
    dirs.append(PLUGIN_MODELS_DIR)
    umi = _umi_root()
    dirs += [os.path.join(umi, "models"),
             os.path.join(umi, "UmiOCR-data", "models")]
    home = _user_home()
    if home:
        dirs += [
            os.path.join(home, ".hyperlpr3"),
            os.path.join(home, ".umi-ocr", "models"),
            os.path.join(home, "Umi-OCR", "models"),
        ]
    env = os.environ.get("UMI_LPR_MODELS_DIR", "")
    if env:
        dirs += [p.strip() for p in env.split(os.pathsep) if p.strip()]

    # 每个基准目录再展开常见子目录布局
    expanded = []
    for d in dirs:
        expanded += [
            d,
            os.path.join(d, "onnx"),
            os.path.join(d, MODEL_VERSION, "onnx"),
            os.path.join(d, MODEL_VERSION),
            os.path.join(d, "hyperlpr3"),
            os.path.join(d, "hyperlpr3", MODEL_VERSION, "onnx"),
            os.path.join(d, "hyperlpr3", "onnx"),
        ]
    out, seen = [], set()
    for d in expanded:
        k = os.path.normcase(os.path.normpath(d))
        if k not in seen:
            seen.add(k)
            out.append(d)
    return out


def find_model(key, user_dir=""):
    """key ∈ det_320 / det_640 / rec / cls ，返回文件路径或 "" 。"""
    fname = MODEL_FILES[key]
    for d in search_dirs(user_dir):
        p = os.path.join(d, fname)
        if os.path.isfile(p):
            return p
    return ""


def find_charset(user_dir=""):
    """可选：外部字符表文件，用于覆盖内置字符表。"""
    for d in search_dirs(user_dir):
        for name in ("plate_chars.txt", "plate_dict.txt"):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return p
    return ""


def describe(user_dir=""):
    lines = []
    for d in search_dirs(user_dir)[:12]:
        lines.append(f"  [{'√' if os.path.isdir(d) else '×'}] {d}")
    return "\n".join(lines)
