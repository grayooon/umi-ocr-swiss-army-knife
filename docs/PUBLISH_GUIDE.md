# 从第一次发布开始：把三个 Umi-OCR 插件完整发布到 GitHub

这份教程写给会从 GitHub 下载项目、会操作 Windows，但还没发布过项目的人。你不需要先学习 Git 命令，也不需要理解 OCR 算法。最终要得到的是：一个可读的源码仓库、三个有明确版本的插件下载包，以及普通用户能照着完成的部署说明。

本次准备的仓库叫 `umi-ocr-swiss-army-knife`，中文名称为“基于 Umi-OCR 的 OCR 瑞士军刀”。仓库已经包含 README、插件源码、安装器、下载清单、许可文件、自检脚本、问题模板和本教程。**这些文件已经准备好，但尚未替你上传到 GitHub；本次修订版也尚未完成 Windows 实机识别验收。**

## 1. 先认识六个会用到的词

| GitHub 中的词 | 是什么 | 你这次怎么用 |
| --- | --- | --- |
| Repository，简称 Repo | 项目的文件、说明和修改记录放在一起的仓库 | 三个相关插件放进同一个仓库，集中入口与曝光 |
| README.md | 仓库首页自动显示的说明书；`.md` 是 Markdown 文本 | 普通用户只看它就能选插件、下载和安装 |
| Commit | 一次保存到仓库的改动记录 | 写清“增加安装脚本”“修复路径定位”，便于回退和排错 |
| Tag | 指向某次源码记录的版本标签 | 用 `v1.1.0-rc.1` 对应这一份候选代码 |
| Release | 某个版本的发行页面，附说明和下载文件 | 放三个插件 ZIP 和校验文件，而不是只让用户翻源码 |
| Issue / Pull request | 问题反馈 / 提交一组修改供审核 | 用户报故障用 Issue；以后协作改代码用 PR |

`rc` 表示发布候选版，功能准备好了，但仍有发行前检查。它不是“已通过所有系统测试”的意思。`Source code (zip)` 是 GitHub 自动打包该标签的源码；你另行上传的插件 ZIP 则是为用户整理好的单插件安装入口。两者可以同时存在。

## 2. 选“新仓库”，还是点 Umi-OCR 的 Fork？

目前你交付的是三个外置插件，用户把它们装进已有 Umi-OCR。推荐**新建独立插件仓库**，不需要先 Fork 整个 Umi-OCR，也不必把 Umi-OCR 主程序全部复制进源码仓库。

Fork 是从另一个仓库派生一份、保留 GitHub 上游关系与历史，适合你要持续修改 Umi-OCR 本体的情况。是否点了 Fork 并不单独决定开源是否规范：实际使用了谁的代码、保留了哪些许可、是否写明修改和来源，才是要核对的内容。

首页保留这句话：**“本项目是社区插件合集，基于 Umi-OCR 插件接口开发，与官方项目独立维护。”** 既方便用户理解关系，也避免把第三方扩展误认为官方发行。

## 3. 关于 compressO-rebuild：借鉴文档结构，不能照搬许可

检查到 [compressO-rebuild](https://github.com/1250759846qq/compressO-rebuild/) 的 README 写明上游来源和重制内容，并提供 Release、LICENSE、NOTICE、THIRD_PARTY_NOTICES 与 CHANGELOG。这些是你可以借鉴的公开说明习惯。

但仅凭这些文件，不能认定它每一个捆绑二进制及对应源码的分发都已经完整合规。例如其 FFmpeg 声明列举了 GPL/LGPL，具体发行二进制仍需要结合实际构建选项、版本和对应源码核查。因此这里**不把它当作“已经全面合规认证”的范本**。

它使用的 AGPL 许可不是你三个插件必须使用的许可。你的上游分别涉及 Umi-OCR、PaddleOCR、HyperLPR、ddddocr、ONNX Runtime 等。本套件为新增集成代码准备了 Apache-2.0，并保留第三方许可。发布前请确认自己有权发布附件中的自有代码；如有其他未说明的复制来源，应补充到 NOTICE，不能通过换个仓库名抹去原作者。

## 4. 先整理本地文件，保留能用的原版

1. 把本次交付的压缩包解压到一个工作文件夹，打开里面的 `umi-ocr-swiss-army-knife`。
2. 把你目前 Win10 能用的整个 Umi-OCR 文件夹复制一份作为备份。备份要包括 `site-packages`、模型和 Umi 配置。
3. 本次修订放进另一份测试用 Umi-OCR，不要直接在正在工作的原版里反复覆盖。代码包不包含你附件省略的依赖和模型。
4. 打开 [Windows 实机验收](WINDOWS_ACCEPTANCE.md)，先完成 Win10 回归，再由你迁移到 Win7 实测。此处不需要模拟 Win7。
5. 本候选版可以先作为预发布公开；只有具备对应系统的真实测试结果，才能把它标成正式版并写明“最低支持 Win7”。

你补充的事实已纳入记录：HyperLPR3 原项目实际上有 `__init__.py`，只是本次附件漏传；原版三个插件已由你在 Win10 验证识别与切换正常。本套件补了兼容入口，但不把附件漏传当成原项目缺陷。

## 5. 检查 README：已有正文，不需要从空白写起

双击 Markdown 文件可能没有合适的阅读软件；可以用记事本查看源文，上传到 GitHub 后会自动排版。也可以先阅读随交付提供的 HTML 教程。

本套件的根目录 `README.md` 面向用户，已经按以下顺序写好：用途 → 当前状态 → 选插件 → 下载和复制 → 双击安装 → 模型目录 → 自检 → 离线与迁移 → 故障处理 → 来源和许可。

发布前只需核对与你实际验收相符的内容：

- 名称可沿用“基于 Umi-OCR 的 OCR 瑞士军刀”。如改仓库名，同步检查你后来添加的绝对链接。
- 支持状态必须与当前候选版的实机记录一致。原版通过不代表修改版自动通过。
- 确认实际 Umi 版本、Python 位数、模型模式和压缩包名称。
- 验收完成后，把操作系统、版本和通过的模式补入 `docs/WINDOWS_ACCEPTANCE.md`，再更新 README 的状态段落。
- 可加入你自己制作、没有隐私数据的演示图或短 GIF。当前文件没有虚构截图或准确率。

`.md` 中 `#` 表示标题，`-` 表示列表，反引号包裹文件名，`[文字](地址)` 是链接。不想学语法时，直接保留正文、只改普通文字即可。编辑 BAT 不要用 Word；它会改变文件格式。

## 6. 创建你的第一个仓库

1. 在浏览器登录自己的 GitHub 账号。发布账号与使用者离线识别无关；普通用户下载公开文件通常不需要账号。
2. 点击页面右上角 **+ → New repository**。
3. Owner 选自己的账号；Repository name 填 `umi-ocr-swiss-army-knife`。
4. Description 可直接填：`Umi-OCR 社区插件合集：PP-OCRv6 文字、HyperLPR3 车牌、ddddocr 验证码；本地 CPU 推理与离线部署。`
5. 建议先选 **Private**，把文件和链接整理完整后再改为 Public。Private 是准备阶段别人看不到；Public 是正式公开源码。
6. 因为本套件已经有 README、LICENSE 和 `.gitignore`，不要再让 GitHub生成另一套冲突文件。
7. 点击 **Create repository**。看到空仓库引导页即创建成功。

这是创建存放项目的空间，还不等于用户已经能安装。下一步必须上传完整目录结构。[GitHub 创建仓库说明](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)

## 7. 用网页上传，不必安装 Git

GitHub 网页一次最多上传 100 个文件，单文件限制 25 MiB。源码和文档很小，适合网页上传；模型、依赖和成品 ZIP 不要混进源码文件列表。[GitHub 文件上传说明](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)

1. 空仓库点击 **uploading an existing file**；已有文件时点击 **Add file → Upload files**。
2. 第一次上传仓库根目录的文件，以及 `docs`、`scripts`、`tests`、`LICENSES`。每批不足 100 个文件；如果页面提示超量，就减小这批。
3. **不要拖整个 `umi-ocr-swiss-army-knife` 外层文件夹进去**，而是上传它里面的内容。正确结果是仓库首页直接看到 `README.md`，不是再点击一层同名目录。
4. 上传插件时先在本地复制一个临时的 `plugins` 文件夹，每次只保留其中一个插件，拖该 `plugins` 文件夹到仓库根目录上传。后两批同理。这样网站路径始终为 `plugins/插件名/...`。也可在 GitHub 已有的 `plugins` 目录页面上传对应插件子文件夹。
5. 每批页面底部填写 Commit message，如 `Add project documentation`、`Add PP-OCRv6 plugin`、`Add HyperLPR3 plugin`、`Add ddddocr plugin`，然后提交。首次自己的空仓库可提交到 main；以后多人维护或受保护分支按页面提示建立分支和 PR。
6. `.github`、`.gitignore`、`.gitattributes` 同样需要上传，前面的点是文件名的一部分。若网页不能拖入某个点文件，可用 **Add file → Create new file**，逐字填写文件名，再粘贴对应内容。
7. 若新建仓库最初没有 `plugins` 目录，用第 4 步上传文件夹即可自动创建；不用单独学习创建空文件夹。
8. 不要上传 `site-packages`、`models`、`_downloads`、环境报告、个人测试图片或 `dist`。`.gitignore` 主要约束 Git 工具，不能替代你在网页上手工选择文件时的检查。

检查首页至少有：`README.md`、`LICENSE`、`NOTICE.md`、`plugins`、`docs`、`dependencies.lock.json`、`models.lock.json`。分别点进三个插件，应看到 `__init__.py`、API 文件和 `tools/01_setup_online.bat`。

如果不慎上传了同名外层目录且根目录没有 README，先修正层级再继续。不要靠 README 解释一个错误目录结构来让用户绕路安装。

## 8. 从网站重新下载一遍，按陌生用户的方法装

这是发布前最有价值的一步：**不能只验证自己工作目录中的那份代码。**

1. 在 GitHub 点击 **Code → Download ZIP**。
2. 解压到一个新文件夹，确认三个插件的源码和安装脚本都在。
3. 在测试用 Umi-OCR 中按 README 复制插件并安装。新安装路径与沿用旧依赖路径应分别记录，不能混称“全新下载通过”。
4. 使用有标注的样例，验证自检、Umi 内识别、三插件来回切换、断网重启后的识别。
5. 把整套测试文件移动到另一个有空格/中文的目录再测试。确认默认设置没有引用你旧电脑的模型路径。
6. Win7 按实机验收表进行。若你自己的依赖能用，而联网安装下载的官方依赖不能用，应准备清楚来源、许可和哈希的 Win7 兼容发行包，再给普通用户开放该安装路径。

这一步能够发现漏上传文件、重复目录层级、模型目录不对，以及 README 中遗漏的操作。暂时无法完成的项目保留“待验证”，不要写“全部通过”。

## 9. 生成三个插件下载包和校验文件

Release 下载包不等于把你正在使用的整个文件夹随手压缩。那样可能混入业务图片、缓存和未说明来源的 DLL。

1. 回到本地仓库根目录，双击 `01_check_source.bat`。
2. 窗口提示 Python path 时，把 `UmiOCR-data\runtime\python.exe` 文件拖入窗口并按 Enter。这里使用你已经有的解释器，不需要安装系统 Python。
3. 看到所有测试通过后，双击 `02_make_release.bat`，同样拖入该解释器。
4. 打开新生成的 `dist` 文件夹。它包含一个整仓源码 ZIP、三个插件 ZIP 和 `SHA256SUMS.txt`。
5. 这些插件 ZIP 是**源码 + 安装器**，第一次安装需要联网下载依赖/模型；它们不是已经带齐二进制的免下载便携包。
6. 如果以后发布真正的离线完整版，另用明确的 `win7-x64-offline` 等文件名，必须附对应依赖、模型、来源与许可，不能把本次源码 ZIP 改个名字就称为离线完整版。

SHA-256 是文件内容的指纹。文件变了，指纹通常就变；它方便用户检查文件是否与维护者发布的版本相同，但不等于“无恶意代码证书”。Windows 用户可在文件夹地址栏输入 `cmd`，运行：

```bat
certutil -hashfile DDDDOCR_Captcha_Umi-v1.1.0-rc.1.zip SHA256
```

核对输出与 `SHA256SUMS.txt` 中该文件对应的一行。你的正式版本名改变后，命令中的文件名也要跟着变。

## 10. 创建 Release，把下载入口真正放出来

1. 仓库页面右侧点击 **Releases → Create a new release**，或在 Releases 列表选择 **Draft a new release**。
2. Tag 填 `v1.1.0-rc.1`，创建新标签；Target 选包含本次完整源码的 main。
3. Title 填 `v1.1.0-rc.1 — 三插件部署候选版`。
4. 把 `docs/RELEASE_NOTES_TEMPLATE.md` 的内容复制到说明框，更新实际测试情况。它已经明确区分原版 Win10 反馈与候选版验收。
5. 把 `dist` 中三个插件 ZIP 和 `SHA256SUMS.txt` 拖到附件区。整仓源码 ZIP 可选上传，因为 GitHub 也会自动提供 Source code。
6. 本次存在待验收项，应勾选 **Set as a pre-release**。需要继续准备时先 **Save draft**，草稿不是公开发行。
7. 核对说明和附件后点击 **Publish release**。不要宣称尚未完成的 Win7 或真实推理测试。
8. 打开发布页面，逐一点击附件下载，核对下载的 ZIP 能正常解压、插件入口层级正确、文件哈希相符。

标签必须对应打包时的源码。修改代码后重新生成压缩包、创建新版本，不要悄悄在同一个正式版本下换文件。[GitHub Release 管理说明](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)

## 11. 公开仓库并整理首页

如果第 6 步选了 Private，准备好之后进入 **Settings → General → Danger Zone → Change repository visibility → Public**，按 GitHub 页面要求确认仓库名。此前上传的提交历史也会随公开可见，因此公开前确认没有密码、访问令牌或业务资料。

然后在仓库首页右侧 About 点齿轮：

- Description 使用第 6 步给出的简短说明。
- Website 可先留空；有自己的使用教程或演示站后再填写。
- Topics 可填：`umi-ocr`、`ocr`、`paddleocr`、`hyperlpr3`、`ddddocr`、`onnxruntime`、`offline`、`windows`。标签描述真实内容即可。
- 保留 Releases、Issues，按维护需求开启 Discussions。Discussions 适合使用交流，不是安装必需项。

最后用未登录浏览器打开仓库，确认 README 能阅读、Release 能看到、附件能下载。私人仓库内“自己能下载”不代表其他人能看到。

## 12. 让别人愿意点击、看懂并使用

曝光的前提是访问者能快速判断有没有用。建议发布一段 30～60 秒的屏幕录制：同一份 Umi-OCR 中选择文字、车牌、验证码插件，各识别一张无隐私演示图片，再展示断网后识别仍可执行。

首页第一屏保留项目定位、三个插件用途和下载安装入口。可加入测试硬件、模型模式和耗时，但不要拿单张成功图宣传普遍准确率。测试用“整张验证码完全一致率”等实际指标，写清样本数和测试条件。

可以在 Umi-OCR 官方允许分享的 Discussions/插件交流区介绍项目，或提交符合官方仓库贡献规则的插件收录请求。先阅读当地规则，内容重点是功能、兼容版本、安装方式和链接。不要用无关 Issue 催 Star 或到处重复粘贴推广。

之后可以在你常用的技术社区发布图文教程，统一回到同一个 GitHub 仓库。稳定的下载路径和及时回复问题，比把三个相关插件拆成三个无人维护的仓库更适合初期集中曝光。

## 13. 后续更新：保持用户能够找到对应代码

1. 在本地副本修改源码、更新 CHANGELOG。
2. 跑源码检查和与本次修改有关的实机用例；改变依赖/模型必须更新清单和哈希。
3. 用 GitHub 网页上传修改文件；确认删除的旧文件也在仓库删除，上传不会自动替你删除旧文件。
4. 更新根目录与三个插件的 `VERSION.txt`，例如下一候选版 `1.1.0-rc.2`。
5. 重新打包、上传代码、创建新标签和 Release。
6. 在 Release 中说明“修了什么、谁需要更新、如何迁移、哪些系统已测试”。如果需要删除旧依赖，给出明确的备份和回退步骤。

等 Win10、Win7 的实际发行文件都验收完成，才发布不带 rc 的 `v1.1.0`，去掉 pre-release 标记，并更新 README 支持表。不会因为去掉三个字母就自动获得兼容性。

## 14. 发布完成的验收清单

- [ ] 未登录的访问者能看到仓库和 Release。
- [ ] 仓库首页直接显示 README，三插件目录层级正确。
- [ ] LICENSE、NOTICE、第三方代码/模型来源齐全；没有把上游成果说成自研。
- [ ] Release 标签对应 ZIP 所用源码，校验文件匹配。
- [ ] 普通用户按 README 能找到 Umi 解释器、复制插件、下载依赖和模型。
- [ ] Windows 实机结果与 README 描述一致；未测试项保留明确标记。
- [ ] Win7 依赖来自可追溯的实际验证构建，不能只依据文件名 `cp38` 推断支持。
- [ ] 离线重启后可识别，三个插件切换后都可用。
- [ ] 没有发布缓存、业务图片、令牌、日志或自己的环境路径配置。
- [ ] Issues 有清楚的问题反馈方式，用户能按版本回报错误。

完成以上步骤，就形成了源码、部署说明、下载包、版本记录和反馈入口相互对应的公开项目。
