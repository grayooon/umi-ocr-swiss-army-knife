# 第三方组件说明

源码、运行依赖和模型是不同层次的分发对象。本仓库不包含 Umi-OCR 主程序、预装依赖或预装模型；安装器按固定清单下载第三方包。以后制作离线完整版时，仍需保留实际分发文件附带的许可证。

| 项目 | 主要用途 | 上游声明的许可 | 来源 |
| --- | --- | --- | --- |
| Umi-OCR | 宿主与插件接口 | MIT | https://github.com/hiroi-sora/Umi-OCR |
| PaddleOCR / PP-OCRv6 | 通用 OCR 算法、模型、配置 | Apache-2.0 | https://github.com/PaddlePaddle/PaddleOCR |
| HyperLPR | 车牌识别算法与模型 | Apache-2.0 | https://github.com/szad670401/HyperLPR |
| ddddocr 1.5.6 | 验证码识别与内置模型 | MIT | https://github.com/sml2h3/ddddocr |
| ONNX Runtime | ONNX 模型推理 | MIT | https://github.com/microsoft/onnxruntime |

上述主要许可证原文位于 `LICENSES/`，其中 `sources.json` 记录抓取地址。上游声明中的版权行按原文保留，包括上游自身的占位文字；这不是本项目重新指定其版权人。模型分发还应遵循具体模型页/版本声明，不应仅凭代码仓库许可推断所有后来模型的许可。

完整依赖还有 NumPy、OpenCV、Pillow、PyYAML、pyclipper、protobuf、SymPy 等。精确版本和下载文件见 `dependencies.lock.json` 或每个插件的 `tools/assets.lock.json`。安装器解压时保留 wheel 的 `.dist-info` 和其他包内许可文件；这些文件才与下载的实际版本相对应，不能在瘦身时随意删除。

OpenCV 等二进制包可能包含自身第三方组件声明。重新分发时应保留实际包中的 license/notice 文本，而不是用“所有内容均为 Apache-2.0”概括。本套件没有对附件省略的私人 DLL 或补丁作来源认证。

如果维护者确认附件中的自有代码还引用了这里未列出的实现，应在正式发行前补充文件来源、原作者及许可。公开仓库、标注“仅供学习”或注明“非商业”都不能替代相应许可义务。
