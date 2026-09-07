# PP-OCRv6 通用文字识别 — Umi-OCR 社区插件

版本 1.1.0-rc.1。用于 Windows x64、Umi-OCR 自带 CPython 3.8。作者反馈原版在 Win10 工作正常；本次修订版尚需实机识别与切换验收。

**Win7 是最低目标系统，但当前锁定的官方 ORT wheel 有 Win7 系统接口阻碍。** 联网安装器会拒绝在 Win7 覆盖安装这些依赖。作者沿用现有包做实机迁移测试；普通 Win7 用户等待明确实测的兼容发行包。本 ZIP 不含已验证 Win7 二进制。

## 安装

1. 从 Umi-OCR 官方项目获取能运行的 Windows x64 版，先启动一次确认可用，再彻底退出托盘程序。
2. 解压本插件 ZIP，将 `PPOCRv6_ONNX_CPU` 文件夹复制到 `UmiOCR-data\plugins\`。
3. 核对 `UmiOCR-data\plugins\PPOCRv6_ONNX_CPU\__init__.py` 存在；解释器在 `UmiOCR-data\runtime\python.exe`。不要多套一层解压目录。
4. 关闭 Umi，保持联网，双击插件 `tools\01_setup_online.bat`。无需系统 Python、pip 或管理员权限。不要同时运行多个安装窗口。
5. 等待 `Files installed`，再双击 `tools\02_self_check.bat`，将一张适合本插件的本地图片拖入窗口并按 Enter。
6. 自检若提示 FAIL/INCOMPLETE，先解决问题；PASS 之后仍需核对输出文字是否正确。
7. 启动 Umi-OCR，在全局 OCR 引擎/接口选择项选择本插件，在 OCR 页面设置中选择模式，识别测试图片。

也可以从合集仓库 Code → Download ZIP，进入其中 plugins 目录取得同名插件，后续步骤相同。本包是源码+安装器；首次下载依赖与模型后才能识别。

## 本插件的模型与设置

默认下载安装 small 检测/识别两个模型及 inference.yml。安装路径分别是 `models/PP-OCRv6_small_det/` 和 `models/PP-OCRv6_small_rec/`。配置和模型都要保留，模型目录设置留空即可随插件移动。

要用 tiny，双击 `tools/download_tiny_models.bat` 后在 Umi 里选择 tiny。要用全部档位，双击 `tools/download_all_models.bat`。首次建议 small；低性能电脑可选 tiny。可选方向分类权重未包含在本清单中，默认关闭。

## 离线、迁移与隐私

安装后的 `site-packages` 是依赖，模型目录是权重，`_downloads` 是按哈希命名的下载缓存。安装器自动安排路径并检查 HTTPS、文件大小与 SHA-256。它不会要求你提供识别图片去下载依赖。

识别阶段使用本机管道子进程，不自动下载、不监听网络端口、不需要账号/API Key；显式关闭 ORT 遥测并阻止 Python 层网络连接。原生 DLL 的网络限制可用系统防火墙辅助验证。开源和哈希不是“永远无恶意”的认证。

成功安装后断网，彻底退出并重启 Umi，再识别一次。换电脑时复制完整插件，包括依赖和模型；需要离线重装再保留缓存并使用 `03_setup_offline.bat`。跨 Windows 版本仍需验证 DLL 兼容。Win7 沿用现有包测试时不要重装官方依赖。

本插件没有写死个人盘符。默认模型位置基于自身目录；若曾填写旧电脑绝对路径，迁移后清空或重新选择。建议用户目录/数据盘中的可写文件夹，不要为安装强行提权。

## 常见问题

| 问题 | 处理 |
| --- | --- |
| 找不到 Python / Umi 没显示插件 | 核对复制层级，确认 runtime 和插件入口存在；退出托盘后重启 |
| 下载失败 | 查看域名与具体报错；可在能访问源的电脑准备同系统/架构完整插件后复制；不要跳过证书校验 |
| 哈希不一致 | 停止并重试下载；仍失败则反馈文件名，不要删去校验 |
| site-packages.previous 已存在 | 退出 Umi，把旧备份移到其他备份目录后重试，避免覆盖唯一备份 |
| Win7 安装被拒绝 / DLL 缺入口点 | 参阅实机验收说明，核对实际依赖构建；不要从不明网站下载补丁 DLL |
| 无结果 | 换适合模型的图片，检查档位、字符范围、阈值与长度；不能把无图当作自检通过 |
| Worker 超过 120 秒 | 用更小图片和较轻模式复试，记录完整报错 |

环境报告：运行 `tools/04_export_environment.bat`，在插件根目录生成 `environment-report.json`。报告仅本地保存，不自动上传；查看后自行决定是否提交给维护者。

更多说明：[离线验证](docs/OFFLINE_PRIVACY.md)、[Windows 实机验收](docs/WINDOWS_ACCEPTANCE.md)、[依赖](DEPENDENCIES.md)、[模型来源](MODEL_SOURCES.md)、[第三方许可](THIRD_PARTY_NOTICES.md)。本项目不是 Umi-OCR 官方发行。
