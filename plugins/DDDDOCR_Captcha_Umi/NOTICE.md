# 来源与修改声明

本项目是 Umi-OCR 的社区插件合集，不是 Umi-OCR 官方发行版。

本次基线来自维护者提供的三个插件核心源码。HyperLPR3 入口文件在本次附件中漏传，由维护者确认其原项目确有该文件；当前入口是按照其现有 API/配置补齐的兼容实现。

新增部署、文档和集成修改采用根目录 Apache-2.0 许可，权利归相应作者/贡献者。该许可只适用于可由本项目授权的部分，不覆盖或撤销第三方已有版权与许可。原文件中的上游说明、版权和许可证应继续保留。

## 上游

- Umi-OCR：<https://github.com/hiroi-sora/Umi-OCR>，提供宿主程序与插件接口，MIT。
- PaddleOCR：<https://github.com/PaddlePaddle/PaddleOCR>，PP-OCR 系列算法与模型来源，Apache-2.0。
- HyperLPR：<https://github.com/szad670401/HyperLPR>，车牌检测、分类与识别的上游，Apache-2.0。
- ddddocr：<https://github.com/sml2h3/ddddocr>，验证码识别上游，MIT；此安装方案固定使用 1.5.6。
- ONNX Runtime：<https://github.com/microsoft/onnxruntime>，CPU 推理运行库，MIT。

## 1.1.0-rc.1 修改范围

2026-09-07：整理三插件的独立进程适配器、worker 通信、依赖定位；替换安装和下载脚本；固定来源与散列；增加环境报告；修正配置缓存键；改进自检和批量评测；补齐说明、回归检查和发行材料。

模型权重不是本项目训练，原始来源与版本见 MODEL_SOURCES.md。上游库的第三方依赖也保留各自许可，见 THIRD_PARTY_NOTICES.md。重发完整二进制包时应一并携带包内许可文件，不能只附根目录 LICENSE。
