# v1.1.0-rc.1 — 三插件部署候选版

本项目为 Umi-OCR 社区插件合集，提供 PP-OCRv6 通用文字、HyperLPR3 车牌和 ddddocr 验证码识别。

## 下载

- `PPOCRv6_ONNX_CPU-v1.1.0-rc.1.zip`：通用文字插件。
- `HyperLPR3_Plate_CPU-v1.1.0-rc.1.zip`：车牌插件。
- `DDDDOCR_Captcha_Umi-v1.1.0-rc.1.zip`：验证码插件，含经典/Beta 接口。
- `SHA256SUMS.txt`：核对附件内容指纹。

这些 ZIP 包含源码和安装器，首次安装需要联网下载依赖与模型，不是带齐二进制的离线完整版。安装完成后可在本机离线识别。也可从仓库 Code → Download ZIP 获取三个插件。

## 安装

解压所需插件，将插件文件夹复制到 `UmiOCR-data\plugins\`，退出 Umi，运行插件内 `tools\01_setup_online.bat`，然后运行 `tools\02_self_check.bat` 并提供一张合适的图片。重新启动 Umi 并选择插件。完整步骤见仓库 README。

## 本次修改

- 三插件统一独立子进程加载依赖，主进程使用标准库通信接口。
- 固定 HTTPS 下载来源、版本、大小与 SHA-256，自动放置依赖和模型。
- 增加离线缓存安装、自检与本地环境报告。
- 禁用 ONNX Runtime 遥测并限制 Python 层推理网络访问。
- 补齐 README、来源/许可、发布教程和实机验收说明。

