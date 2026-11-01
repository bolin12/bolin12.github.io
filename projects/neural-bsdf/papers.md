---
layout: page
title: "逐篇解析索引"
permalink: /projects/neural-bsdf-perf/papers/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
group: 论文
order: 50
side_title: 论文笔记总览
---
更新：2026-10-22。本文回答：每份论文与课程资料讲了什么、在全景中的位置。12 份 PDF（正文、补充材料、课程讲义和幻灯片）各自对应一份中文解析。PDF 原文保存在 `papers`，本目录只保存解析。


| 资料 | 全景中的位置 | 解析 | 来源 | 页数 |
|---|---|---|---|---:|
| Real-Time Neural Appearance Models（SIGGRAPH 2024）：从复杂材质图到可求值、可采样的神经外观 | 材质：路线一基础方法（求值、采样、LOD） | [解析](/projects/neural-bsdf-perf/papers/real-time-neural-appearance-models/) | [NVIDIA Research](https://research.nvidia.com/labs/rtr/neural_appearance_models/) | 17 |
| Bridging the Gap 课程讲义（SIGGRAPH 2025 Course）：Substrate 材质如何训练并回到 UE | 材质：路线一的 UE 工程实践、Lumen 适配 | [解析](/projects/neural-bsdf-perf/papers/bridging-course-notes/) | [课程页](https://blog.selfshadow.com/publications/s2025-shading-course/) | 11 |
| Bridging the Gap 幻灯片：逐阶段读懂模型、性能和 UE 实现 | 同上 | [解析](/projects/neural-bsdf-perf/papers/bridging-slides/) | 同上 | 27 |
| Taming Optimization Variance（SIGGRAPH 2026）：让小型神经着色网络更稳定地训练 | 公共底座：训练（`neuralappearance` 直接配套） | [解析](/projects/neural-bsdf-perf/papers/taming-optimization-variance/) | [NVIDIA Research](https://research.nvidia.com/labs/rtr/publication/bitterli2026taming/) | 9 |
| Taming Optimization Variance 补充材料：裁剪计划、共享数据与消融结果 | 同上 | [解析](/projects/neural-bsdf-perf/papers/taming-optimization-variance-supplement/) | 同上 | 7 |
| Towards Comprehensive Neural Materials（SIGGRAPH 2025）：量化反射、结构合成与位移轮廓 | 材质：路线二（本项目 QTP 模型的来源） | [解析](/projects/neural-bsdf-perf/papers/comprehensive-neural-materials/) | [ACM DOI](https://doi.org/10.1145/3721238.3730626) | 11 |
| Comprehensive Neural Materials 补充材料：训练、INT8 布局与两级求交 | 同上 | [解析](/projects/neural-bsdf-perf/papers/comprehensive-neural-materials-supplement/) | [作者补充材料](https://sites.cs.ucsb.edu/~lingqi/publications/supp_sig25_cnm.pdf) | 2 |
| Random-Access Neural Compression of Material Textures（SIGGRAPH 2023）：材质贴图组的随机访问压缩 | 纹理：NTC | [解析](/projects/neural-bsdf-perf/papers/random-access-ntc/) | [NVIDIA Research](https://research.nvidia.com/publication/2023-08_random-access-neural-compression-material-textures)；[RTXNTC](https://github.com/NVIDIA-RTX/RTXNTC) | 15 |
| Neural Layered BRDFs（SIGGRAPH 2022）：把分层操作放进神经潜空间 | 材质：可组合的分层 | [解析](/projects/neural-bsdf-perf/papers/neural-layered-brdfs/) | [作者项目页](https://wangningbei.github.io/2022/NLBRDF.html) | 8 |
| PureSample（SIGGRAPH 2026）：从微几何随机游走学习反射分布与能量 | 材质：采样与 pdf | [解析](/projects/neural-bsdf-perf/papers/puresample/) | [作者页](https://www.rendering-zixuan.com/paper_pages/PureSample/)；[arXiv:2508.07240](https://arxiv.org/abs/2508.07240) | 16 |
| GratNet（arXiv 2025）：用神经代理近似衍射表面的受限反射响应 | 材质：波动光学（衍射） | [解析](/projects/neural-bsdf-perf/papers/gratnet/) | [arXiv:2506.15815](https://arxiv.org/abs/2506.15815) | 15 |
| Toward Richer Material Generation（SIGGRAPH 2026）：先增强材质数据，再生成神经材质 | 其他模块：内容生产工具 | [解析](/projects/neural-bsdf-perf/papers/richer-material-generation/) | [NVIDIA Research](https://research.nvidia.com/labs/rtr/publication/yu2026toward/) | 11 |

SDK：[RTXNS](https://github.com/NVIDIA-RTX/RTXNS)（神经 shader 的训练与推理，属于公共底座）不对应单篇论文，见 [本地研究代码导读](/projects/neural-bsdf-perf/code-guide/) 2.5 节。

论文文件是来源处提供的 PDF，没有重新排版或改写；阅读时以原文和作者仓库为准，解析中的工程建议是基于这些来源和本地代码结构的归纳。阅读顺序见 [全景与研究路线](/projects/neural-bsdf-perf/research/) 第 6 节。
