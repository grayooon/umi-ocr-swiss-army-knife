# 三插件源码审查与修订报告

审查日期：2026-09-07。审查对象：作者上传的“核心代码（不包含模型和sitepackages和pipboot）.zip”。逐文件基线散列见 `evidence/original-inventory.json`。

## 结论与范围

**在已提供的核心源码中，未发现以窃取凭据、上传图片/识别结果、远程控制、挖矿、自启动持久化或破坏任意用户目录为目的的代码。未发现运行功能必须依赖 `D:\Software` 等作者个人固定安装目录。**

这是一份源码审查结论，不是“确保任何情况下都无恶意”的认证。附件没有实际 site-packages、模型与 pipboot，不能据此证明作者电脑上的全部 DLL、ONNX 文件或运行环境安全。静态审查也不能穷尽所有逻辑缺陷。本次另从公开上游下载了固定 wheel 和部分模型，用于来源、哈希、解压结构和 DLL 导入表核对，不能把这些文件与附件未提交的文件视为相同。

作者补充：HyperLPR3 的 `__init__.py` 在原项目中存在，只是附件漏传；原版三插件在 Win10 上识别及切换正常。该事实已从“入口缺陷”更正为“附件范围限制”。本套件补齐了兼容入口，但未审查漏传原文件。本次新增修订不自动继承原版的 Win10 通过状态。

## 方法

- 阅读插件入口、配置、API、推理核心、图像处理、进程通信、BAT 与下载/安装/自检脚本。
- 搜索网络调用、shell/子进程执行、动态代码执行、删除操作、注册表/自启动、凭据关键词与绝对路径，结合调用上下文判断，不把关键词命中直接判作恶意。
- 核对 get-pip 与官方引导脚本的字节散列；核对官方包元数据、Python/ABI/平台、依赖闭包及固定文件散列。
- 使用修订安装器对 16 个实际下载的 wheel 作安全解压检查；不执行其代码。
- 对官方 Windows ORT 二进制检查 PE 导入表；执行 14 项源码/安装/通信回归测试。
- 尝试真实 Linux 模型推理；运行环境错误使其未成功，不据此生成虚假的 Windows 或模型准确率结论。

## 具体发现与处理

| 项目 | 原源码/附件观察 | 本候选版处理与边界 |
| --- | --- | --- |
| 隐私与外传 | 未发现核心识别流程上传图像/结果或带有外传服务器；安装脚本确有下载请求 | 明确分离安装和推理，记录允许下载域名；不把合法下载说成信息上报 |
| ORT 遥测 | 本地模型运行不等于依赖不会使用 OS 遥测；原流程未明确统一关闭 | 在加载时调用 disable_telemetry_events；增加 Python 层网络审计，仍不代替原生 DLL 防火墙 |
| 个人盘符 | 示例/注释有 C:/D: 路径，实际默认通过 __file__ 和相对层级定位 | 保留可移动结构；相对自定义模型路径改为相对插件；用户自己保存的旧绝对配置仍需清空 |
| 跨插件原生依赖 | PP/LPR 在宿主进程导入依赖；原版 Win10 用户反馈正常，但不同 ORT 版本仍可能共用 sys.modules/DLL | 三插件统一独立进程；这是预防和架构修订，不声称用户当前 Win10 正在故障 |
| 启动器与通信 | Umi CLI/解释器可能不同；stdout 中可混入启动日志；旧通信缺少可靠超时边界 | 明确 runtime/python.exe，固定协议前缀与请求编号；读响应最长 120 秒；只结束自己启动的进程 |
| DLL 搜索 | 部分原逻辑未持有 add_dll_directory 返回的句柄 | worker 保留句柄；Win7 是否具备相应系统更新仍依赖实际环境 |
| `.pth` 执行 | site.addsitedir 会处理目录中的 .pth 文件 | 只插入插件依赖路径，不执行 .pth；不是判定现有 .pth 恶意 |
| get-pip 大段编码 | 两份 get-pip.py 与 PyPA Python 3.8 官方脚本哈希一致；编码部分属于正常引导内容 | 不能因编码内容而判恶意。候选版不再需要它，减少引导和联网执行环节 |
| 未固定的下载 | 原工具存在动态取包、未统一校验模型哈希的路径 | 固定 HTTPS、文件大小和 SHA-256，源清单可读；下载失败或哈希不符即停止 |
| HyperLPR 模型下载 | 原下载器优先 HTTP，HTTPS 源可用性不稳定；检查模型数量不足以证明四个所需文件齐全 | 固定到上游历史提交的 4 个模型，逐个校验；尚不能证明与作者省略的模型逐字节相同 |
| wheel 兼容与解压 | 原 no-pip 安装器存在 ABI 筛选不严格、.data 布局处理不足；验证命令拼接路径对引号不稳健 | 固定目标 wheel、正确迁移 purelib/platlib、拒绝越界/驱动器/符号链接目标；不插值生成 Python -c 验证语句 |
| 旧依赖保留 | 直接在现有目录装包可能混合版本 | 新依赖先入暂存目录，保留 site-packages.previous；备份已存在则拒绝重复覆盖 |
| 自检可信度 | 附件没有演示样例；旧脚本可能在没有实际样例时打印成功 | 要求实际图片；无图或无识别结果标记 INCOMPLETE；Path/Bytes/Base64 结果需一致 |
| 识别配置缓存 | PP 的 drop_score、LPR 的 rec_threshold 未充分区分缓存键 | 将阈值纳入键，避免切换设置继续使用旧管线 |
| ddddocr 线程设置 | stock 1.5.6 不读取原代码设置的 DDDDOCR_NUM_THREADS | 去掉无效环境变量和对应 UI 选项，避免假设置；实际线程调优另行实现和验证 |
| HyperLPR 入口 | 作者确认原文件存在，附件漏传 | 补齐交付入口；不列为原版缺陷 |

涉及 `subprocess`、临时目录清理和联网下载的命中均有明确用途。当前桥接不使用 `shell=True`；安装器删除的是自身创建的暂存目录或未完成下载文件，未发现按任意盘符递归删除用户内容的逻辑。上述判断只覆盖当前提交版本。

## Win7：已知官方依赖阻碍，与作者实机测试分开

对下列 PyPI 官方 wheel 校验哈希后，检查得到：

| wheel | 二进制 | 导入 |
| --- | --- | --- |
| onnxruntime 1.19.2 cp38 win_amd64 | onnxruntime.dll | KERNEL32.dll!GetSystemTimePreciseAsFileTime |
| onnxruntime 1.19.2 cp38 win_amd64 | onnxruntime_pybind11_state.pyd | 同上 |
| onnxruntime 1.17.3 cp38 win_amd64 | onnxruntime_pybind11_state.pyd | 同上 |

微软文档将该函数最低客户端列为 Windows 8。因此这些未经兼容处理的官方 DLL 不能据此承诺支持原生 Win7。这不是通过模拟机推测得出的结果，而是已下载文件的静态导入证据。[Microsoft API 要求](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getsystemtimepreciseasfiletime)

这不否定作者可以用其他构建或特定系统环境在 Win7 运行。作者会做真实 Win7 迁移测试；应记录确切依赖、系统补丁和构建来源。候选安装器拒绝在 Win7 覆盖安装已知这两套官方 ORT，模型单独下载不受该依赖保护检查影响。当前未提供假定可用的 Win7 DLL 包。

## 验证结果

| 检查 | 结果 | 不代表什么 |
| --- | --- | --- |
| 14 项 unittest 回归 | 通过 | 不代表 Windows 原生 DLL 或模型准确率通过 |
| Python 3.8 语法解析 | 通过，包含在回归检查内 | 不是在 Python 3.8 Windows 运行完整推理 |
| 三插件发现与宿主导入隔离 | 通过，使用最小 Translator 适配桩 | 不是完整 Umi GUI 操作测试 |
| 子进程通信 | 真实创建/关闭进程；模拟后端验证噪声过滤、输入传输与状态复用 | 后端模拟结果不属于真实模型识别结果 |
| 中文/空格/单引号/感叹号目录 | Linux 进程夹具通过；Windows 解释器定位逻辑检查通过 | Windows BAT/CMD 的完整实机路径场景仍由作者验证 |
| Python 3.8 Windows 依赖元数据闭包 | 三套清单通过 | 元数据满足不等于 DLL 支持 Win7 |
| 16 个 wheel 下载哈希、安全解压 | 通过 | 不等于二进制无恶意或能在每个系统加载 |
| 官方模型下载 | HyperLPR 4 个模型与 PP tiny 模型/配置已下载；其它 PP 模型的固定版本元数据/散列已记录 | 未对 PP small/medium 完成实际模型下载和推理 |
| Linux 真实推理尝试 | 三插件均被 ORT 的 CPU 信息解析错误阻断 | 不报告模型识别成功，不作为 Windows 插件缺陷结论 |
| ONNX checker 尝试 | 当前沙箱进程异常退出，未取得有效结果 | 不报告模型结构/算子检查通过 |
| Windows 10 原版 | 作者反馈通过 | 不自动覆盖本次修订源码 |
| Windows 10/7 候选版 | 待作者实机验收 | 不宣称已测试 |

本次 Linux 使用 Python 3.12.13、Linux ORT 1.19.2 做测试尝试，与目标 Windows Python 3.8/各自 ORT 组合不同。原始失败日志已脱去工作区绝对路径后保存到 `evidence/actual-inference-results.json`。

## 附件证据

- `evidence/original-inventory.json`：原附件各文件大小和散列。
- `evidence/pe-imports.json`：已下载 Windows ORT 的相关导入。
- `evidence/locked-assets-check.json`：依赖闭包和实际 wheel 散列/解压检查。
- `evidence/regression-results.txt`：候选版回归测试输出。
- `evidence/source-changes.json`：原附件与候选源码的新增、修改、删除路径及散列。

get-pip.py 对比源：[PyPA Python 3.8 引导脚本](https://bootstrap.pypa.io/pip/3.8/get-pip.py)。对比 SHA-256：`6ed6e98282a504ee0a6632856e16c39f222d313fc38be33de216d4afb6ac12f7`。这项字节一致性结论针对审查时取得的文件，远端脚本今后可能更新。

正式发行前，按 `WINDOWS_ACCEPTANCE.md` 验收，并将真实结果写入对应版本 Release。项目可以公开安全设计、来源和证据；不应宣传“GitHub 开源即官方认证”“绝对无恶意”或“Win7 全版本必定支持”。
