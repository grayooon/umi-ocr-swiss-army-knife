# 模型与配置来源

模型权重来自上游；本项目没有声称自行训练这些模型。维护者原版的模型未在附件中提供，所以下列公开文件尚不能与其私人部署逐字节比较。安装器写入插件根目录下的 `models`，ddddocr 内置模型例外，位于其官方 Python 包内。

精确 URL、固定 revision、文件大小和 SHA-256 全文见 `models.lock.json` 与每插件 `tools/assets.lock.json`。PP 各档必须同时保留检测/识别模型以及对应 inference.yml。下载脚本不会自动重写模型的 IR 或权重。

## PPOCRv6_ONNX_CPU

| 插件内模型路径 | MiB | 固定来源 | SHA-256 |
| --- | --- | --- | --- |
| `models/PP-OCRv6_tiny_det/inference.onnx` | 1.70 | [原始文件](https://huggingface.co/PaddlePaddle/PP-OCRv6_tiny_det_onnx/resolve/2ba1506c0380b8f0b03dd142459aac66d4421f6c/inference.onnx) | `193bab7a04fca699a6c82e6abb5b81bdb28177f0abd4062552b04908dafb19f8` |
| `models/PP-OCRv6_tiny_det/inference.yml` | 0.00 | [原始文件](https://huggingface.co/PaddlePaddle/PP-OCRv6_tiny_det_onnx/resolve/2ba1506c0380b8f0b03dd142459aac66d4421f6c/inference.yml) | `3ac018be6f97499a08faa3bbdeb33640968d9307f6736d152902747a9f259593` |
| `models/PP-OCRv6_tiny_rec/inference.onnx` | 4.26 | [原始文件](https://huggingface.co/PaddlePaddle/PP-OCRv6_tiny_rec_onnx/resolve/2612ab37152ae0a677521bae4e1e3d4fb4cf7c30/inference.onnx) | `9ef676d6ed3c88256a2d92c640c44f25b0c40947e111b14b8be8f594091563e6` |
| `models/PP-OCRv6_tiny_rec/inference.yml` | 0.05 | [原始文件](https://huggingface.co/PaddlePaddle/PP-OCRv6_tiny_rec_onnx/resolve/2612ab37152ae0a677521bae4e1e3d4fb4cf7c30/inference.yml) | `66170210bad538e83fff3c4a3867e547d6bf20b50d64b20347c4b913f3034ea1` |
| `models/PP-OCRv6_small_det/inference.onnx` | 9.42 | [原始文件](https://huggingface.co/PaddlePaddle/PP-OCRv6_small_det_onnx/resolve/28fe5895c24fd108c19eb3e8479f4ab385fbfc62/inference.onnx) | `d73e0058b7a8086bbd57f3d10b8bcd4ff95363f67e06e2762b5e814fe9c9410e` |
| `models/PP-OCRv6_small_det/inference.yml` | 0.00 | [原始文件](https://huggingface.co/PaddlePaddle/PP-OCRv6_small_det_onnx/resolve/28fe5895c24fd108c19eb3e8479f4ab385fbfc62/inference.yml) | `193f435274bf9f0b5f71a929bbfbcf148282df7e633b34e7c373e8f44741b516` |
| `models/PP-OCRv6_small_rec/inference.onnx` | 20.18 | [原始文件](https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec_onnx/resolve/b8f84f0b80c529de40b4fbb3544b84fa7233a513/inference.onnx) | `5435fd747c9e0efe15a96d0b378d5bd157e9492ed8fd80edf08f30d02fa24634` |
| `models/PP-OCRv6_small_rec/inference.yml` | 0.14 | [原始文件](https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec_onnx/resolve/b8f84f0b80c529de40b4fbb3544b84fa7233a513/inference.yml) | `ab078671bb49f06228eadccd34f1bb501e157f7a047095ffb943ba81512c77d1` |
| `models/PP-OCRv6_medium_det/inference.onnx` | 59.16 | [原始文件](https://huggingface.co/PaddlePaddle/PP-OCRv6_medium_det_onnx/resolve/61323801669c338b7891481ec7bac61ce31b576a/inference.onnx) | `eb13b44b25bb36f89528b68720af8a61d9cf381176107f465db1757b65d086e1` |
| `models/PP-OCRv6_medium_det/inference.yml` | 0.00 | [原始文件](https://huggingface.co/PaddlePaddle/PP-OCRv6_medium_det_onnx/resolve/61323801669c338b7891481ec7bac61ce31b576a/inference.yml) | `7298d5ead546584af2504d03355f881ac7a7bc0eb1e282d3e159277c1d0af871` |
| `models/PP-OCRv6_medium_rec/inference.onnx` | 73.01 | [原始文件](https://huggingface.co/PaddlePaddle/PP-OCRv6_medium_rec_onnx/resolve/50c7eacafc52fa7bcf4194e8cd08e46f8558504b/inference.onnx) | `9c09abf0957f7968c7586464b7397b84ad2387a0497a351af40e9acc71b673ba` |
| `models/PP-OCRv6_medium_rec/inference.yml` | 0.14 | [原始文件](https://huggingface.co/PaddlePaddle/PP-OCRv6_medium_rec_onnx/resolve/50c7eacafc52fa7bcf4194e8cd08e46f8558504b/inference.yml) | `991b700facf5b50a7de193468207d5f4255b538dde0d312ae3b7c7a9b6873129` |
## HyperLPR3_Plate_CPU

| 插件内模型路径 | MiB | 固定来源 | SHA-256 |
| --- | --- | --- | --- |
| `models/y5fu_320x_sim.onnx` | 2.23 | [原始文件](https://raw.githubusercontent.com/szad670401/HyperLPR/58ad4ef736fec5289e8c8cb842e066e70c4672c3/resource/models/onnx/y5fu_320x_sim.onnx) | `2a985dc63a5cc947ec36d18503d6fc0fd54525b9dba17f2fe29a71e86b44456d` |
| `models/y5fu_640x_sim.onnx` | 3.75 | [原始文件](https://raw.githubusercontent.com/szad670401/HyperLPR/58ad4ef736fec5289e8c8cb842e066e70c4672c3/resource/models/onnx/y5fu_640x_sim.onnx) | `0306de937471b87f56eb3f5620815e7e7058f8ab7428e0734fc64627cc4d716c` |
| `models/rpv3_mdict_160_r3.onnx` | 9.78 | [原始文件](https://raw.githubusercontent.com/szad670401/HyperLPR/58ad4ef736fec5289e8c8cb842e066e70c4672c3/resource/models/onnx/rpv3_mdict_160_r3.onnx) | `35521a46fd8beaa6fd942f969bc666f4ef5c8433d2082eae002e6c94c5d307a2` |
| `models/litemodel_cls_96x_r1.onnx` | 1.53 | [原始文件](https://raw.githubusercontent.com/szad670401/HyperLPR/58ad4ef736fec5289e8c8cb842e066e70c4672c3/resource/models/onnx/litemodel_cls_96x_r1.onnx) | `fe123688d3bf08b9ef029fcd57f3ac4644ac2e5ef8b9e7a676aacd5fad152142` |

HyperLPR 文件固定到官方仓库提交 `58ad4ef736fec5289e8c8cb842e066e70c4672c3` 的 resource/models/onnx，而非未校验的 HTTP ZIP。固定历史提交便于重现，不代表这些模型是上游最新模型。

## DDDDOCR_Captcha_Umi

官方 ddddocr 1.5.6 wheel 包含 `ddddocr/common.onnx`（Beta）和 `ddddocr/common_old.onnx`（经典）。安装后分别位于 `site-packages/ddddocr/`，不要移动到其他插件的 models 目录。完整 wheel 的 SHA-256 已固定，见依赖清单。

默认部署不需要自定义模型。已有 dddd_trainer 导出的 ONNX 和 charsets.json 时，可放进插件 `models/custom/`，在全局配置选择这两个文件，并在局部配置选择“自定义训练模型”。自定义模型的格式、许可和效果由其提供者确认；本次没有收到或验收用户自定义权重。

PP 模型许可按对应 PaddlePaddle 模型仓库的 Apache-2.0 声明记录；HyperLPR 见上游 LICENSE；ddddocr 使用其官方发行包内许可。本项目保留这些来源，不另行给上游权重改许可。
