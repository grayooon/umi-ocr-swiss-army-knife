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

## 测试状态与限制

作者反馈原版三个插件在 Windows 10 正常识别、切换；本修订版的 Windows 实机验收尚待填写。14 项源码/部署/通信回归测试通过，不能替代真实 Windows 模型推理。本次 Linux 实际推理尝试被 ONNX Runtime 的 CPU 信息解析错误阻断。

最低目标系统为 Win7 x64，作者将进行实机测试。当前联网安装器固定的官方 ORT DLL 有 Win7 API 兼容性阻碍，Win7 依赖安装会明确停止；已有可用包的维护者按实机验收说明沿用原依赖测试。本候选版不宣称已提供可从零部署的 Win7 兼容依赖包。

发布前请将这段状态更新为你实际完成的测试，不要删掉尚未解决的限制。本版使用 GitHub pre-release 标记。
