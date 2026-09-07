from plugin_i18n import Translator

tr = Translator(__file__, "i18n.csv")

# ================= 全局配置 =================
globalOptions = {
    "title": tr("车牌识别") + " HyperLPR3" + tr("（本地）"),
    "type": "group",
    "tips": {
        "title": tr("中国车牌识别，ONNX Runtime 纯 CPU 推理，完全离线。"),
        "btnsList": [],
    },
    "models_dir": {
        "title": tr("模型目录"),
        "type": "file",
        "default": "",
        "selectExisting": True,
        "selectFolder": True,
        "dialogTitle": tr("选择存放车牌模型的目录"),
        "toolTip": tr("留空则自动搜索：插件目录 models 、软件目录 models 、用户目录 .hyperlpr3 。"),
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
    "workers": {
        "title": tr("并发车牌数"),
        "default": 2,
        "isInt": True,
        "min": 1,
        "max": 16,
        "toolTip": tr("一张图中有多个车牌时，并行识别的数量。"),
        "advanced": True,
    },
}

# ================= 局部配置 =================
localOptions = {
    "title": tr("车牌识别") + " (HyperLPR3)",
    "type": "group",
    "detect_level": {
        "title": tr("检测精度"),
        "optionsList": [
            ["low", tr("320 - 高速（推荐）")],
            ["high", tr("640 - 高精度/远景小车牌")],
        ],
        "toolTip": tr("640 输入更适合车牌较小或较远的场景，速度约为 320 的三分之一。"),
    },
    "box_threshold": {
        "title": tr("检测置信度阈值"),
        "default": 0.5,
        "isInt": False,
        "min": 0.05,
        "max": 1.0,
        "toolTip": tr("低于该分数的车牌框会被丢弃。漏检时可调低。"),
    },
    "rec_threshold": {
        "title": tr("识别置信度下限"),
        "default": 0.0,
        "isInt": False,
        "min": 0.0,
        "max": 1.0,
        "toolTip": tr("丢弃识别置信度低于该值的车牌。0 表示不丢弃。"),
        "advanced": True,
    },
    "use_cls": {
        "title": tr("识别车牌颜色"),
        "default": True,
        "toolTip": tr("用颜色分类模型区分蓝牌/黄牌/绿牌。关闭可略微提速。"),
    },
    "show_type": {
        "title": tr("输出车牌类型"),
        "default": False,
        "toolTip": tr("开启后，识别文本形如：京A12345 [蓝牌]"),
    },
    "nms_threshold": {
        "title": tr("NMS 阈值"),
        "default": 0.5,
        "isInt": False,
        "min": 0.1,
        "max": 1.0,
        "toolTip": tr("重叠框抑制阈值。默认 0.5 。"),
        "advanced": True,
    },
}
