# 发布与校验指南

发布附件以实际上传的文件为准。`SHA256SUMS.txt` 只是 ZIP 的 SHA-256 校验清单，不是插件或运行依赖；没有它不会影响安装和识别。GitHub 自动提供的 `Source code (zip)`、`Source code (tar.gz)` 也不是另外两个插件。

## 1. 对齐版本和实际验证结果

- 确认三个插件目录完整，并保留许可、来源和安装脚本。
- 将根目录和三个插件的 `VERSION.txt` 更新为同一个待发布版本，同时更新 README、CHANGELOG 和发布说明。脚本会拒绝缺失插件或四处版本不一致的情况。
- Release 标签、附件文件名与包内版本应一致。当前仓库四份 `VERSION.txt` 仍是 `1.1.0-rc.1`，已有 Release 名为 `v1.1.0`；不能只重命名 ZIP 来同步包内版本。后续代码修订应使用新版本，不覆盖既有正式版 ZIP。
- 运行 `01_check_source.bat`，按提示拖入 `UmiOCR-data\runtime\python.exe`。这只做源码与发布工具回归，不代表 Windows 实际识别验收。实测范围如实写入发布说明。

## 2. 生成一批完整附件

双击 `02_make_release.bat` 并拖入同一个 Python 解释器。也可以在仓库根目录执行：

```bat
"<Umi目录>\UmiOCR-data\runtime\python.exe" scripts\make_release.py
```

脚本每次创建一个独立的 `dist/v<版本号>-<随机后缀>/` 文件夹，保留旧批次，不混用它们的附件。仅在 ZIP 和清单都通过校验后才显示最终文件夹。**上传本次打印出的文件夹内全部四个文件：**

- `DDDDOCR_Captcha_Umi-v<版本号>.zip`
- `HyperLPR3_Plate_CPU-v<版本号>.zip`
- `PPOCRv6_ONNX_CPU-v<版本号>.zip`
- `SHA256SUMS.txt`

默认不再额外生成整仓源码 ZIP，因为 GitHub 已提供对应标签的源码下载。确实需要自定义整仓源码包时，运行：

```bat
"<Umi目录>\UmiOCR-data\runtime\python.exe" scripts\make_release.py --include-source
```

这时该批次含四个 ZIP 和一份清单，需一起上传。清单只列本次实际 ZIP，不含它自己，也不含 GitHub 自动生成的源码附件。

这些包仍是源码和安装器，不含预装依赖、模型或个人环境报告。ZIP 内部时间戳和权限已固定；同一运行环境下、相同文件字节重复打包不会因源文件修改时间变化而改变哈希。不同 Python/zlib 版本或换行符变化仍可能影响压缩包字节，因此线上已发布文件的校验值必须从线上原文件计算。

## 3. 上传前核验

双击 `03_verify_release.bat`，按提示拖入 Python 解释器和本次附件文件夹；或执行：

```bat
"<Umi目录>\UmiOCR-data\runtime\python.exe" scripts\make_release.py --verify "dist\v<版本号>-<随机后缀>"
```

该检查不仅验证内容散列，还会拒绝清单中的缺失文件、文件夹中未列出的 ZIP、重复条目和不安全路径。失败时退出码为 2，不应发布。

不要混用不同批次的 ZIP 和清单；不要在生成清单后手工增删或替换 ZIP。如果确实调整了附件组合，把**最终要上传的 ZIP** 放进一个单独文件夹，按下一节重新生成清单，然后再次验证。

## 4. 给已有 Release 补校验清单

不需要重新打包插件，更不要把重新打包后的哈希用于已有附件。

1. 从目标 Release 下载当前保留的三个插件 ZIP，放进一个新的空文件夹，例如 `downloaded-v1.1.0`。不要放其他版本或 GitHub 自动源码包。
2. 在仓库根目录运行：

```bat
"<Umi目录>\UmiOCR-data\runtime\python.exe" scripts\make_release.py --checksums-only "downloaded-v1.1.0"
```

此命令只更新该文件夹中的 `SHA256SUMS.txt`，不改动、解压或重新压缩 ZIP。它按当前文件夹中实际存在的 ZIP 重建清单，并立即验证。

3. 再运行 `--verify "downloaded-v1.1.0"`。确认是目标版本的原始附件后，可以把清单作为新附件加入该 Release。
4. 如果维护者决定不提供清单，删除 Release 说明中对应的下载条目即可。缺少独立清单不等于缺少插件文件。

## 5. 发布后复查

- Tag 指向打包所用源码；说明中的下载列表与实际附件一致。
- 使用 `docs/RELEASE_NOTES_TEMPLATE.md` 时替换版本占位符，并只保留实际提供的附件条目。
- 从公开 Release 重新下载 ZIP 和清单到一个干净文件夹，运行 `--verify`。
- 能正常解压，插件入口位于同名插件文件夹内；安装与 Windows 实测结果另行验收。
- SHA-256 用于发现文件损坏或内容不一致，不是恶意代码检测，也不是独立数字签名。
