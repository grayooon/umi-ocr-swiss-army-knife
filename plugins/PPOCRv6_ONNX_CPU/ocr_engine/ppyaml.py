# ==========================================================
# ====== PaddleX inference.yml 极简解析（不依赖 PyYAML） ======
# ==========================================================
# 只解析 PP-OCR 推理配置中我们需要的部分：
#   PostProcess: thresh / box_thresh / unclip_ratio / max_candidates / name
#   PostProcess: character_dict （识别字典，超长列表）
#   PreProcess : RecResizeImg.image_shape 、NormalizeImage.mean/std/scale
# 若环境中存在 PyYAML 则优先使用它，保证完全一致的解析结果。

import os
import re


def _try_pyyaml(text):
    try:
        import yaml  # noqa
    except Exception:
        return None
    try:
        return yaml.safe_load(text)
    except Exception:
        return None


def _unquote(v):
    v = v.rstrip("\n")
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        inner = v[1:-1]
        if v[0] == "'":
            inner = inner.replace("''", "'")
        return inner
    return v


def parse_character_dict(text):
    """从 inference.yml 文本中提取 character_dict 列表。"""
    lines = text.splitlines()
    chars = []
    inside = False
    base_indent = None
    for raw in lines:
        line = raw.rstrip("\n")
        if not inside:
            if re.match(r"^\s*character_dict\s*:\s*$", line):
                inside = True
            continue
        stripped = line.strip()
        if stripped == "":
            continue
        indent = len(line) - len(line.lstrip(" "))
        if not stripped.startswith("- "):
            if stripped == "-":
                # "- " 后为空 → 空格字符
                chars.append(" ")
                continue
            # 列表结束
            break
        if base_indent is None:
            base_indent = indent
        elif indent < base_indent:
            break
        val = line.lstrip()[2:]  # 去掉 "- "
        if val == "":
            chars.append(" ")
        else:
            chars.append(_unquote(val))
    return chars


_NUM_RE = r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?"


def _find_scalar(text, key):
    m = re.search(r"^\s*%s\s*:\s*(%s)\s*$" % (re.escape(key), _NUM_RE), text, re.M)
    if m:
        s = m.group(1)
        try:
            return float(s) if ("." in s or "e" in s.lower()) else int(s)
        except Exception:
            return None
    return None


def _find_str(text, key):
    m = re.search(r"^\s*%s\s*:\s*(\S+)\s*$" % re.escape(key), text, re.M)
    return m.group(1) if m else None


def _find_num_list(text, key, count=None):
    """解析形如
        key:
        - 0.485
        - 0.456
    的数字列表。
    """
    m = re.search(r"^([ \t]*)%s\s*:\s*$" % re.escape(key), text, re.M)
    if not m:
        # 也可能是行内列表 key: [1, 2, 3]
        m2 = re.search(r"^\s*%s\s*:\s*\[([^\]]*)\]" % re.escape(key), text, re.M)
        if m2:
            out = []
            for p in m2.group(1).split(","):
                p = p.strip()
                if p:
                    try:
                        out.append(float(p))
                    except Exception:
                        pass
            return out or None
        return None
    out = []
    for line in text[m.end():].splitlines():
        s = line.strip()
        if s.startswith("- "):
            v = s[2:].strip()
            try:
                out.append(float(v))
            except Exception:
                break
        elif s == "":
            continue
        else:
            break
        if count and len(out) >= count:
            break
    return out or None


def load_infer_config(path):
    """读取 inference.yml / dict.txt ，返回统一的配置字典。"""
    cfg = {"character_dict": None, "post": {}, "pre": {}}
    if not path or not os.path.isfile(path):
        return cfg
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    # 纯文本字典文件（每行一个字符）
    if ext in (".txt",):
        chars = [l.rstrip("\n").rstrip("\r") for l in text.splitlines()]
        cfg["character_dict"] = chars
        return cfg

    data = _try_pyyaml(text)
    if isinstance(data, dict):
        post = data.get("PostProcess") or {}
        if isinstance(post, dict):
            cd = post.get("character_dict")
            if isinstance(cd, list):
                cfg["character_dict"] = [
                    (" " if c is None else str(c)) for c in cd
                ]
            for k in ("thresh", "box_thresh", "unclip_ratio", "max_candidates", "name",
                      "score_mode", "box_type"):
                if k in post:
                    cfg["post"][k] = post[k]
        pre = data.get("PreProcess") or {}
        ops = pre.get("transform_ops") if isinstance(pre, dict) else None
        if isinstance(ops, list):
            for op in ops:
                if not isinstance(op, dict):
                    continue
                if "RecResizeImg" in op and isinstance(op["RecResizeImg"], dict):
                    shp = op["RecResizeImg"].get("image_shape")
                    if isinstance(shp, list) and len(shp) == 3:
                        cfg["pre"]["image_shape"] = [int(x) for x in shp]
                if "NormalizeImage" in op and isinstance(op["NormalizeImage"], dict):
                    n = op["NormalizeImage"]
                    if isinstance(n.get("mean"), list):
                        cfg["pre"]["mean"] = [float(x) for x in n["mean"]]
                    if isinstance(n.get("std"), list):
                        cfg["pre"]["std"] = [float(x) for x in n["std"]]
                if "DetResizeForTest" in op and isinstance(op["DetResizeForTest"], dict):
                    d = op["DetResizeForTest"]
                    if "limit_side_len" in d:
                        cfg["pre"]["limit_side_len"] = int(d["limit_side_len"])
                    if "limit_type" in d:
                        cfg["pre"]["limit_type"] = str(d["limit_type"])
        return cfg

    # --------- 无 PyYAML 时的降级解析 ---------
    chars = parse_character_dict(text)
    if chars:
        cfg["character_dict"] = chars
    for k in ("thresh", "box_thresh", "unclip_ratio", "max_candidates",
              "limit_side_len"):
        v = _find_scalar(text, k)
        if v is not None:
            (cfg["pre"] if k == "limit_side_len" else cfg["post"])[k] = v
    lt = _find_str(text, "limit_type")
    if lt:
        cfg["pre"]["limit_type"] = _unquote(lt)
    name = _find_str(text, "name")
    if name:
        cfg["post"]["name"] = _unquote(name)
    mean = _find_num_list(text, "mean", 3)
    std = _find_num_list(text, "std", 3)
    if mean:
        cfg["pre"]["mean"] = mean
    if std:
        cfg["pre"]["std"] = std
    shp = _find_num_list(text, "image_shape", 3)
    if shp and len(shp) == 3:
        cfg["pre"]["image_shape"] = [int(x) for x in shp]
    return cfg
