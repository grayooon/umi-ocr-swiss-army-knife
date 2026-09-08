# 基于 Umi-OCR 的 OCR 瑞士军刀

为 Umi-OCR 增加 **PP-OCRv6 通用文字识别、HyperLPR3 车牌识别、ddddocr 验证码识别**。一次下载依赖和模型，之后在本机离线识别；不需要注册账号、申请 API Key 或安装系统 Python。

本项目是社区插件合集，基于 [Umi-OCR](https://github.com/hiroi-sora/Umi-OCR) 的插件接口开发，与 Umi-OCR 官方项目独立维护。模型和识别算法来自相应上游项目，本项目主要提供插件适配、配置、部署和进程隔离。

**当前版本：1.1.0-rc.1，发布候选版。最低目标系统为 Windows 10 x64。** 

## 立即下载

当前版本：**v1.1.0-rc.1**

| 插件 | 用途 | 下载 |
| --- | --- | --- |
| PP-OCRv6 | 文档、截图、通用文字识别 | [下载 PP-OCRv6](https://github.com/grayooon/umi-ocr-swiss-army-knife/releases/download/v1.1.0-rc.1/PPOCRv6_ONNX_CPU-v1.1.0-rc.1.zip) |
| HyperLPR3 | 中国车牌识别 | [下载 HyperLPR3](https://github.com/grayooon/umi-ocr-swiss-army-knife/releases/download/v1.1.0-rc.1/HyperLPR3_Plate_CPU-v1.1.0-rc.1.zip) |
| ddddocr | 字母数字验证码识别 | [下载 ddddocr](https://github.com/grayooon/umi-ocr-swiss-army-knife/releases/download/v1.1.0-rc.1/DDDDOCR_Captcha_Umi-v1.1.0-rc.1.zip) |

> 第一次安装需要联网下载依赖和模型；安装完成后可以断网识别。

## 选择哪个插件

| 插件目录名 | 用途 | 默认安装内容 | 起始设置 |
| --- | --- | --- | --- |
| `PPOCRv6_ONNX_CPU` | 文档、截图等通用文字 | small 检测与识别模型、对应配置 | small；关闭可选方向分类 |
| `HyperLPR3_Plate_CPU` | 中国车牌 | 320/640 检测、识别、车牌分类，共 4 个模型 | low；保持其余默认值 |
| `DDDDOCR_Captcha_Umi` | 单行字母数字验证码 | ddddocr 1.5.6 及经典/Beta 模型 | Beta；按图片调整字符范围与长度 |


## 第一次安装：无门槛详细教程

准备一个能正常运行的 **Windows x64 版 Umi-OCR**。本安装方案针对 Umi-OCR 2.1.5 自带的 **CPython 3.8 x64**。先双击 Umi-OCR，确认原有功能可以运行，再从托盘菜单彻底退出。

1. 在本仓库右侧 **Releases** 中打开对应版本，下载所需插件的 ZIP。文件名带 `PPOCRv6_ONNX_CPU`、`HyperLPR3_Plate_CPU` 或 `DDDDOCR_Captcha_Umi` 的是单个插件包。
2. 也可以点击绿色 **Code → Download ZIP** 下载整个源码仓库，解压后打开其中的 `plugins` 文件夹。这条路径同样包含完整安装脚本，能够部署插件。
3. 把所需的**插件文件夹本身**复制到 `UmiOCR-data\plugins\`。
4. 核对下表的三个文件。您的 Umi-OCR 可以放在任何有写入权限的盘符和目录，不要求特定盘符或目录。
5. 保持联网，进入该插件的 `tools` 文件夹，双击 `01_setup_online.bat`。安装过程中请不要启动 Umi-OCR，也不要同时运行同一插件的另一个安装窗口。无需管理员权限。
6. 等待出现 `Files installed`。若出现 `[FAIL]`，先按 [故障处理](#故障处理) 解决，若跳过报错尝试使用，插件功能将不能正常运行。
7. （可选，测试可用）双击 `02_self_check.bat`，把一张适合该插件的图片拖进黑色窗口，按 Enter。路径也可以复制粘贴。查看输出文字是否正确。
8. 启动 Umi-OCR，在“全局设置”的 OCR 引擎/接口选择项中选择新插件，再在截图或批量 OCR 页调整该插件的局部设置。

截至本插件发布时间，Umi-OCR官方发布版本为V2.1.5，此版本下插件目录结构如下：
| 文件 | 正确位置（相对 Umi-OCR 软件根目录） |
| --- | --- |
| Python 解释器 | `UmiOCR-data\runtime\python.exe` |
| 插件入口，例如 PP-OCRv6 | `UmiOCR-data\plugins\PPOCRv6_ONNX_CPU\__init__.py` |
| 安装脚本，例如 PP-OCRv6 | `UmiOCR-data\plugins\PPOCRv6_ONNX_CPU\tools\01_setup_online.bat` |

脚本定位解释器使用自身目录逐级回到 `UmiOCR-data`，不会调用系统 Python，也不会把 `Umi-OCR.exe` 当作 Python。双击 BAT 出现黑色窗口是正常现象，窗口会保留错误信息。

## 依赖与模型存放目录


| 内容 | 相对相应插件根目录的位置 |
| --- | --- |
| Python 运行依赖 | `site-packages\` |
| PP-OCRv6 small 检测模型 | `models\PP-OCRv6_small_det\inference.onnx` |
| PP-OCRv6 small 识别模型 | `models\PP-OCRv6_small_rec\inference.onnx` |
| PP-OCRv6 配置/字典 | 各模型文件夹内的 `inference.yml`，不能漏掉 |
| HyperLPR3 检测模型 | `models\y5fu_320x_sim.onnx`、`models\y5fu_640x_sim.onnx` |
| HyperLPR3 识别/分类模型 | `models\rpv3_mdict_160_r3.onnx`、`models\litemodel_cls_96x_r1.onnx` |
| ddddocr Beta 模型 | `site-packages\ddddocr\common.onnx` |
| ddddocr 经典模型 | `site-packages\ddddocr\common_old.onnx` |
| 离线重装缓存 | `_downloads\`，文件名是 SHA-256，不要自行改名 |

ddddocr 两个模型随其官方 wheel 一起下载，并非安装遗漏。本候选版保留官方包原样数据，包内额外的检测权重不用于上述验证码识别模式。

PP-OCRv6 想用 tiny：双击 `tools\download_tiny_models.bat`，成功后在 Umi 里选择 tiny。想安装 tiny/small/medium 全部档位：双击 `tools\download_all_models.bat`。不要在未下载 medium 时直接切换到 medium。可选方向分类模型不在本次自动下载清单内，保持该选项关闭即可使用标准检测与识别流程。

ddddocr 的“四位、小写加数字”仅适用于对应样本。如果识别普通演示图片为空，先关闭严格长度校验，再选择合适字符范围；得分不是经过校准的真实正确率。比赛模式需要更多次推理，是否更准确应以自己的标注样本评测。

## 离线使用与迁移电脑

完成安装和一次成功识别后，关闭 Umi-OCR，断开网络，再重新启动并识别本地图片。识别阶段不会调用安装器，也不会自动下载缺失模型。

换电脑时，关闭程序后复制整个 Umi-OCR 文件夹，或把**已经安装完成的插件文件夹**复制到另一份同架构 Umi-OCR 的 `UmiOCR-data\plugins\`。保留 `site-packages` 和模型；需要离线重装时也保留 `_downloads`。默认模型目录留空，让插件自动找到自身 `models`。如果曾手工填写旧电脑的绝对路径，请清空或改成新路径。

`03_setup_offline.bat` 仅使用已校验的 `_downloads` 缓存重装，缺少文件会报错，不会偷偷联网。已经正常运行的离线电脑无需重新安装。

## 联网边界与隐私

- **安装时**：只有你主动运行安装脚本才下载依赖/模型，访问 PyPI 文件服务器、Hugging Face 及其下载 CDN、GitHub 原始文件服务器。服务器会像普通下载一样看到访问 IP 和文件请求；安装器不读取或上传你的待识别图片。
- **识别时**：图片由 Umi-OCR 通过本机管道交给子进程，结果通过同一管道返回；本插件不需要开放 TCP 端口、远程账号或 API Key。三个插件互相隔离依赖。
- 运行时代码显式调用 `onnxruntime.disable_telemetry_events()`，并阻止子进程中 Python 层的网络连接。这是防护措施，不是操作系统级的原生 DLL 联网证明。
- “断网仍可识别”证明功能不依赖网络；“代码公开、固定来源和哈希、检查代码、限制出站连接”共同帮助用户判断可信度。不能仅凭开源或一次扫描就保证任何版本绝无恶意代码。

完整测试步骤见 [离线与隐私验证](docs/OFFLINE_PRIVACY.md)，下载来源和散列见 [依赖说明](DEPENDENCIES.md)、[模型来源](MODEL_SOURCES.md) 及每个插件的 `tools/assets.lock.json`。

## 故障处理

| 现象 | 处理方式 |
| --- | --- |
| 找不到 Python | 检查上述目录层级；不能隔着多一层解压目录；先安装/解压完整 Umi-OCR |
| Win7 下载依赖被拒绝 | 已知官方 ORT DLL 不兼容，不是被杀毒软件误拦；维护者沿用现有包实测，普通用户等待 Win7 发行包 |
| 下载失败、超时 | 网络未能访问清单内的源；可在能访问这些源的电脑准备完整插件后复制过来；不要关闭 HTTPS 证书校验 |
| SHA-256 不一致 | 停止使用该文件；重试下载，仍失败则报告具体文件名；不要删除校验代码 |
| `site-packages.previous already exists` | 先退出 Umi；将该备份文件夹剪切到另外的备份位置，再重试；不要混用两套包 |
| DLL load failed / 缺少系统入口点 | 核对 x64、Python 3.8、系统和所用 DLL 版本；提供环境报告，不要从不明 DLL 网站补文件 |
| Unsupported model IR version | 依赖和模型不匹配；按当前插件的完整包恢复。清空 `sys.modules` 不能可靠卸载原生 DLL |
| Umi 中没有新插件 | 核对插件根目录存在 `__init__.py`，确认复制了正确目录，彻底退出托盘后重启 |
| `[INCOMPLETE]` / 没有文字 | 无图片或图片不适合该模型，尚未完成验收；车牌插件应使用有清晰车牌的图片 |
| 切换后异常 | 先彻底关闭并重启 Umi；不要在 Umi 正运行时覆盖文件；报告切换顺序与版本 |
| Worker exceeded 120 seconds | 图片/模型可能过大或进程卡住；先用小图或 tiny/low/Beta 模式复试 |

报告问题时，在仓库 **Issues → New issue** 填写系统、Umi 版本、插件版本、步骤和完整报错。`tools\04_export_environment.bat` 可生成本地依赖/模型哈希报告；查看内容后自行决定是否附上。不要上传个人证件、真实业务验证码或隐私图片。

## 开源与贡献

本项目新增集成代码采用 Apache-2.0；第三方代码、模型和依赖各自遵循其原有许可。详见 [LICENSE](LICENSE)、[NOTICE.md](NOTICE.md) 和 [第三方声明](THIRD_PARTY_NOTICES.md)。本项目不把上游模型宣称为自研，也不代表上游提供维护承诺。

欢迎提交可复现的问题、离线/Win7 实测结果与改进建议。开发与提交流程见 [CONTRIBUTING.md](CONTRIBUTING.md)，版本变化见 [CHANGELOG.md](CHANGELOG.md)。维护者首次发布请阅读 [完整 GitHub 发布教程](docs/PUBLISH_GUIDE.md)。

如果项目帮助到了你，可以点 Star 收藏，或分享带安装步骤的仓库链接。
