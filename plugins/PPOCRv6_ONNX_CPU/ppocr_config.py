from plugin_i18n import Translator

tr = Translator(__file__, "i18n.csv")

# ================= 全局配置 =================
# 对所有标签页生效：模型目录、线程数等。
globalOptions = {
    "title": tr("PP-OCRv6") + tr("（本地）"),
    "type": "group",
    "tips": {
        "title": tr("百度飞桨 PP-OCRv6 ，ONNX Runtime 纯 CPU 推理，完全离线。"),
        "btnsList": [],
    },
    "tips_mode": {
        "title": tr("切换 tiny/small/medium 三档模型：请到【截图OCR】或【批量OCR】"
                    "页面的设置栏 →「文字识别 (PP-OCRv6)」→「模型档位」。"
                    "各标签页可分别使用不同档位。"),
        "btnsList": [],
    },
    "models_dir": {
        "title": tr("模型目录"),
        "type": "file",
        "default": "",
        "selectExisting": True,
        "selectFolder": True,
        "dialogTitle": tr("选择存放 PP-OCRv6 模型的目录"),
        "toolTip": tr(
            "留空则自动搜索：插件目录 models 、软件目录 models 、用户目录 .umi-ocr/models 。"
        ),
    },
    "num_threads": {
        "title": tr("推理线程数"),
        "default": 0,
        "isInt": True,
        "min": 0,
        "max": 64,
        "unit": tr("线程"),
        "toolTip": tr("单个模型内部的并行线程数。0 = 自动（按 CPU 核心数）。"),
    },
    "rec_workers": {
        "title": tr("识别并发批数"),
        "default": 2,
        "isInt": True,
        "min": 1,
        "max": 16,
        "toolTip": tr("同时并行推理的文本行批次数量。多核 CPU 上调大可提速。"),
        "advanced": True,
    },
    "rec_batch": {
        "title": tr("识别批大小"),
        "default": 6,
        "isInt": True,
        "min": 1,
        "max": 64,
        "toolTip": tr("每批同时送入识别模型的文本行数量。"),
        "advanced": True,
    },
    "keep_loaded": {
        "title": tr("常驻内存"),
        "default": True,
        "toolTip": tr("关闭后，切换引擎时会立即释放模型占用的内存。"),
        "advanced": True,
    },
}

# ================= 局部配置 =================
# 每个标签页可不同：模型档位（三种模式）、精度参数等。
localOptions = {
    "title": tr("文字识别") + " (PP-OCRv6)",
    "type": "group",
    "mode": {
        "title": tr("模型档位（三档切换）"),
        "optionsList": [
            ["small", tr("small - 均衡（推荐）")],
            ["tiny", tr("tiny - 极速/低配")],
            ["medium", tr("medium - 高精度")],
        ],
        "toolTip": tr(
            "三档官方模型：tiny 1.5M 参数最快；small 7.7M 参数速度与精度均衡；"
            "medium 34.5M 参数精度最高、速度最慢。"
        ),
    },
    "limit_side_len": {
        "title": tr("限制图像边长"),
        "optionsList": [
            [960, "960 " + tr("（默认）")],
            [736, "736"],
            [1280, "1280"],
            [1600, "1600"],
            [2048, "2048"],
        ],
        "toolTip": tr("检测前把图片长边缩放到该值以内。调大更适合小字，但更慢。"),
    },
    "use_cls": {
        "title": tr("方向分类"),
        "default": False,
        "toolTip": tr("自动纠正 180° 倒置的文本行。需要额外的方向分类模型，缺失时自动跳过。"),
        "advanced": True,
    },
    "box_thresh": {
        "title": tr("检测框阈值"),
        "default": 0.45,
        "isInt": False,
        "min": 0.0,
        "max": 1.0,
        "toolTip": tr("低于该分数的文本框会被丢弃。默认 0.45 。"),
        "advanced": True,
    },
    "unclip_ratio": {
        "title": tr("文本框扩张系数"),
        "default": 1.4,
        "isInt": False,
        "min": 1.0,
        "max": 3.0,
        "toolTip": tr("检测框向外扩张的比例。默认 1.4 。文字被切边时可调大。"),
        "advanced": True,
    },
    "drop_score": {
        "title": tr("识别置信度下限"),
        "default": 0.0,
        "isInt": False,
        "min": 0.0,
        "max": 1.0,
        "toolTip": tr("丢弃置信度低于该值的结果。0 表示不丢弃。"),
        "advanced": True,
    },
}
