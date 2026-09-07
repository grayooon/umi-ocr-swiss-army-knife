# 运行依赖与下载说明

此清单为 Windows CPython 3.8 x64 候选安装方案，不为 Win7 DLL 兼容保证。实际文件 URL、SHA-256、大小与依赖元数据记录在 dependencies.lock.json；每个插件 tools/assets.lock.json 是该插件安装器直接使用的清单。

Python 版本、wheel ABI、操作系统接口和模型 IR 是不同条件。cp38 表示 Python 接口，不表示该 DLL 能在 Win7 运行。参见 docs/WINDOWS_ACCEPTANCE.md。

| 包 | 固定版本 | 原始包信息 |
| --- | --- | --- |
| numpy | 1.24.4 | [PyPI](https://pypi.org/project/numpy/1.24.4/) |
| opencv-python-headless | 4.10.0.84 | [PyPI](https://pypi.org/project/opencv-python-headless/4.10.0.84/) |
| onnxruntime | 1.19.2 | [PyPI](https://pypi.org/project/onnxruntime/1.19.2/) |
| pyclipper | 1.3.0.post5 | [PyPI](https://pypi.org/project/pyclipper/1.3.0.post5/) |
| coloredlogs | 15.0.1 | [PyPI](https://pypi.org/project/coloredlogs/15.0.1/) |
| humanfriendly | 10.0 | [PyPI](https://pypi.org/project/humanfriendly/10.0/) |
| pyreadline3 | 3.4.1 | [PyPI](https://pypi.org/project/pyreadline3/3.4.1/) |
| flatbuffers | 24.3.25 | [PyPI](https://pypi.org/project/flatbuffers/24.3.25/) |
| packaging | 24.2 | [PyPI](https://pypi.org/project/packaging/24.2/) |
| protobuf | 5.29.5 | [PyPI](https://pypi.org/project/protobuf/5.29.5/) |
| sympy | 1.13.3 | [PyPI](https://pypi.org/project/sympy/1.13.3/) |
| mpmath | 1.3.0 | [PyPI](https://pypi.org/project/mpmath/1.3.0/) |
| Pillow | 10.4.0 | [PyPI](https://pypi.org/project/Pillow/10.4.0/) |
| ddddocr | 1.5.6 | [PyPI](https://pypi.org/project/ddddocr/1.5.6/) |
| PyYAML | 6.0.2 | [PyPI](https://pypi.org/project/PyYAML/6.0.2/) |
| onnxruntime | 1.17.3 | [PyPI](https://pypi.org/project/onnxruntime/1.17.3/) |

三个插件分别使用自己的 site-packages。PP-OCRv6 与 HyperLPR3 清单固定 ORT 1.19.2；ddddocr 清单固定 ORT 1.17.3，沿用其独立运行设计。无需也不应往 Umi 主环境安装一套全局 ORT 来“统一版本”。

安装器只下载官方 wheel，不安装 pip，不执行 get-pip.py、setup.py 或 .pth。包内 .dist-info、许可证与数据文件保留。ddddocr 的官方包会导入 cv2，所以清单保留 opencv-python-headless，不能仅因没有使用点选识别就删掉这个依赖。

## 下载量

以下为首次安装所选 wheel 与默认模型的压缩/源文件总量估算；不包含 Umi-OCR 本体。解压后占用更多空间，建议预留至少 1 GB，安装所有 PP 档位另多预留空间。缓存也会占用磁盘，保留缓存才能离线重装。

| 插件 | wheel 数 | 默认下载约 MiB |
| --- | --- | --- |
| DDDDOCR_Captcha_Umi | 13 | 138.4 |
| HyperLPR3_Plate_CPU | 11 | 86.1 |
| PPOCRv6_ONNX_CPU | 13 | 98.8 |

安装器缓存目录 `_downloads` 按文件 SHA-256 命名，这是正常设计。缺少源文件、证书验证失败或哈希不同会停止；不要使用关闭 HTTPS 校验的办法继续。如果需要维护者更换下载源，应重新核查来源并更新公开清单。

