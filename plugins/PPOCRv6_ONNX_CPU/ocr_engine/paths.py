# =====================================================
# =============== 模型目录搜索 / 路径工具 ===============
# =====================================================
# 支持三种放置方式：
#   1. 用户在全局设置里指定的目录
#   2. 本软件目录（插件目录 models/ 、Umi-OCR 根目录 models/ ）
#   3. 用户默认目录（如 C:\Users\Administrator\.umi-ocr\models ）
# 全部为本地文件搜索，不联网。

import os
import sys

# 插件自身目录
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 插件内置模型目录
PLUGIN_MODELS_DIR = os.path.join(PLUGIN_DIR, "models")


def _user_home():
    """返回用户主目录，如 C:\\Users\\Administrator 。兼容 Windows / Linux 。"""
    for key in ("USERPROFILE", "HOME"):
        v = os.environ.get(key, "")
        if v and os.path.isdir(v):
            return v
    drive = os.environ.get("HOMEDRIVE", "")
    path = os.environ.get("HOMEPATH", "")
    if drive and path:
        v = drive + path
        if os.path.isdir(v):
            return v
    try:
        return os.path.expanduser("~")
    except Exception:
        return ""


def _umi_root():
    """返回 Umi-OCR 主程序目录（UmiOCR-data 的上一级）。找不到时返回工作目录。"""
    # 插件位于 <root>/UmiOCR-data/plugins/<插件名>/ocr_engine
    d = os.path.dirname(os.path.dirname(PLUGIN_DIR))  # UmiOCR-data
    root = os.path.dirname(d)
    if os.path.isdir(root):
        return root
    return os.getcwd()


def default_search_dirs(user_dir=""):
    """按优先级返回模型搜索目录列表。"""
    dirs = []
    if user_dir:
        expanded_user = os.path.expandvars(os.path.expanduser(user_dir))
        dirs.append(os.path.abspath(expanded_user if os.path.isabs(expanded_user) else os.path.join(PLUGIN_DIR, expanded_user)))
    # 软件目录
    dirs.append(PLUGIN_MODELS_DIR)
    umi = _umi_root()
    dirs.append(os.path.join(umi, "models"))
    dirs.append(os.path.join(umi, "UmiOCR-data", "models"))
    # 用户默认目录
    home = _user_home()
    if home:
        dirs.append(os.path.join(home, ".umi-ocr", "models"))
        dirs.append(os.path.join(home, "Umi-OCR", "models"))
        # 兼容 PaddleOCR / PaddleX 官方缓存目录
        dirs.append(os.path.join(home, ".paddlex", "official_models"))
        dirs.append(os.path.join(home, ".paddleocr", "official_models"))
    # 环境变量
    env = os.environ.get("UMI_OCR_MODELS_DIR", "")
    if env:
        for p in env.split(os.pathsep):
            if p.strip():
                dirs.append(os.path.abspath(p.strip()))
    # 去重且保持顺序
    out, seen = [], set()
    for d in dirs:
        k = os.path.normcase(os.path.normpath(d))
        if k not in seen:
            seen.add(k)
            out.append(d)
    return out


# 一个模型（如 PP-OCRv6_medium_det ）可能的文件布局
def find_model(name, user_dir="", exts=(".onnx",)):
    """在所有搜索目录中查找模型文件。
    返回 (onnx路径, 配置文件路径 或 "")；找不到返回 ("", "")。
    支持布局：
        <dir>/<name>/inference.onnx        (HuggingFace 官方包结构)
        <dir>/<name>/<name>.onnx
        <dir>/<name>.onnx
        <dir>/<name>/model.onnx
    """
    for d in default_search_dirs(user_dir):
        if not os.path.isdir(d):
            continue
        cands = [
            os.path.join(d, name, "inference.onnx"),
            os.path.join(d, name, name + ".onnx"),
            os.path.join(d, name, "model.onnx"),
            os.path.join(d, name + ".onnx"),
        ]
        for c in cands:
            if os.path.isfile(c):
                return c, _find_cfg(c, name)
        # 宽松匹配：目录内任意 onnx
        sub = os.path.join(d, name)
        if os.path.isdir(sub):
            for f in sorted(os.listdir(sub)):
                if f.lower().endswith(exts):
                    c = os.path.join(sub, f)
                    return c, _find_cfg(c, name)
    return "", ""


def _find_cfg(onnx_path, name):
    """在 onnx 同级目录寻找 PaddleX 的 inference.yml / 字典文件。"""
    d = os.path.dirname(onnx_path)
    for f in ("inference.yml", "inference.yaml", name + ".yml", "config.yml"):
        p = os.path.join(d, f)
        if os.path.isfile(p):
            return p
    for f in ("dict.txt", "ppocr_keys.txt", name + "_dict.txt"):
        p = os.path.join(d, f)
        if os.path.isfile(p):
            return p
    return ""


def describe_search_dirs(user_dir=""):
    """用于报错时提示用户模型该放哪里。"""
    lines = []
    for d in default_search_dirs(user_dir):
        flag = "√" if os.path.isdir(d) else "×"
        lines.append(f"  [{flag}] {d}")
    return "\n".join(lines)
