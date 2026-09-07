from plugin_i18n import Translator


tr = Translator(__file__, "i18n.csv")


globalOptions = {
    "title": "ddddocr " + tr("验证码识别（本地）"),
    "type": "group",
    "tips": {
        "title": tr("两套验证码专用ONNX模型，纯CPU、完全离线。Beta模式推荐先用于比赛。"),
        "btnsList": [],
    },
    "custom_model": {
        "title": tr("自定义ONNX模型"),
        "type": "file",
        "default": "",
        "selectExisting": True,
        "toolTip": tr("仅在局部模式选择custom时使用。"),
        "advanced": True,
    },
    "custom_charset_file": {
        "title": tr("自定义charsets.json"),
        "type": "file",
        "default": "",
        "selectExisting": True,
        "toolTip": tr("由dddd_trainer导出的字符集配置。"),
        "advanced": True,
    },
    "keep_loaded": {
        "title": tr("模型常驻内存"),
        "default": True,
        "toolTip": tr("建议开启，避免每张验证码重复加载模型。"),
        "advanced": True,
    },
}


localOptions = {
    "title": tr("文字识别") + " (ddddocr Captcha)",
    "type": "group",
    "mode": {
        "title": tr("模型模式"),
        "optionsList": [
            ["beta", tr("Beta单模型（推荐/快速）")],
            ["classic", tr("经典单模型")],
            ["dual", tr("双模型原图投票")],
            ["race", tr("比赛模式：双模型×原图/保守去灰")],
            ["custom", tr("自定义训练模型")],
        ],
        "toolTip": tr("比赛模式每图推理4次；先评测，确认有收益后再启用。"),
    },
    "charset": {
        "title": tr("字符范围"),
        "optionsList": [
            ["lower_digits", tr("小写字母+数字（推荐）")],
            ["alnum", tr("大小写字母+数字")],
            ["digits", tr("纯数字")],
            ["lower", tr("纯小写字母")],
            ["upper_digits", tr("大写字母+数字")],
        ],
        "toolTip": tr("范围越准确，误识别候选越少。"),
    },
    "custom_chars": {
        "title": tr("精确字符表"),
        "default": "",
        "toolTip": tr("非空时覆盖上面的字符范围，例如23456789abcdefghjkmnpqrstuvwxyz。"),
        "advanced": True,
    },
    "expected_length": {
        "title": tr("验证码长度"),
        "default": 4,
        "isInt": True,
        "min": 1,
        "max": 12,
    },
    "strict_length": {
        "title": tr("严格长度校验"),
        "default": True,
        "toolTip": tr("长度不符时返回无结果，便于外部程序切换验证码。"),
    },
    "decoder": {
        "title": tr("解码器"),
        "optionsList": [
            ["exact_beam", tr("定长CTC束搜索（推荐）")],
            ["greedy", tr("贪心解码（更快）")],
        ],
        "advanced": True,
    },
    "beam_width": {
        "title": tr("束搜索宽度"),
        "default": 12,
        "isInt": True,
        "min": 2,
        "max": 64,
        "advanced": True,
    },
    "min_confidence": {
        "title": tr("最低置信度"),
        "default": 0.0,
        "isInt": False,
        "min": 0.0,
        "max": 1.0,
        "toolTip": tr("先保持0收集评测数据，再按错误样本分布设置阈值。"),
        "advanced": True,
    },
    "gray_chroma": {
        "title": tr("保守去灰色差"),
        "default": 8,
        "isInt": True,
        "min": 2,
        "max": 20,
        "toolTip": tr("仅比赛模式使用；数值越小越保守。"),
        "advanced": True,
    },
    "gray_min_luma": {
        "title": tr("去灰最低亮度"),
        "default": 105,
        "isInt": True,
        "min": 0,
        "max": 255,
        "advanced": True,
    },
    "gray_max_luma": {
        "title": tr("去灰最高亮度"),
        "default": 242,
        "isInt": True,
        "min": 0,
        "max": 255,
        "advanced": True,
    },
}
