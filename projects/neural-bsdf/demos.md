---
layout: page
title: "Demo 计划与资源"
permalink: /projects/neural-bsdf-perf/demos/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
group: 规划
order: 31
side_title: Demo 计划
---
更新：2026-10-22。本文回答：接下来做哪些 demo、每个 demo 回答什么问题、用哪些公开场景与资产。每个 demo 配一份短报告（做了什么、测到什么、取舍是什么）。资源状态于 2026-10-22 查询，授权和版本支持经常变化，获取前以官方页面为准。


## 1. 原则

- **一个 demo 回答一个问题**：例如「神经车漆比完整 Substrate 省多少，误差多大」。
- **对比呈现**：同屏或同一镜头切换方案，屏幕上实时显示耗时和误差。
- **测量沿用现有方法**：A-B-A、对照材质、GPU Trace（[性能方法手册](/projects/neural-bsdf-perf/gpu-trace-guide/)）。
- **美术用现成资产**：资产不能成为瓶颈；需要补的是 lookdev、灯光、相机这类判断能力。
- **授权**：Fab 资源需要登录 Epic 账号并接受授权后加入资产库；CC BY 资源要按要求署名。

## 2. Demo 列表

| # | Demo | 回答的问题 | 全景位置 | 优先级 |
|---|---|---|---|---|
| 1 | 神经材质展示厅 | 神经车漆 / 皮革比完整 Substrate 省多少、误差多大，是否明显优于简化版 | 渲染：材质（Roadmap M3） | **最高**：直接延续当前项目 |
| 2 | 神经超分对比 | TSR、DLSS 超分、Ray Reconstruction、帧生成各自的画质与耗时，以及对渲染管线的要求 | 渲染：重建 / 后处理 | 高：面试最常见 |
| 3 | 角色 ML Deformer | 线性蒙皮、ML Deformer、离线模拟三者的效果与耗时 | 动画与物理：从离线模拟学变形 | 中 |
| 4 | 数字人小片段 | 语音驱动面部 + 神经超分在一个镜头中的整体效果与预算 | 渲染、动画、音频的交汇 | 中：有版本风险，见下 |
| 5 | 学习型对手 | 强化学习训练的 NPC 能否替代手写行为 | 其他模块：AI / NPC | 低：体验策划视角 |
| 6 | 神经纹理压缩 | NTC 能省多少显存，解码代价多大 | 渲染：纹理 | 低：显存故事 |

### Demo 1：神经材质展示厅

- **场景**：Automotive Substrate Materials 自带的标定 lookdev 地图；车身或材质球放在转台上，三个版本并排：完整 Substrate、简化（`SCC_FullySimplified` 或烘焙为单 Slab）、神经。
- **流程**：选 3–5 个代表材质（多层车漆、清漆金属、皮革）→ 用现有的 `capture_material_brdf` 捕获教师 → 训练 → 导入 → `BuildPairedComparison` 生成对比布局 → 测量。
- **测量**：同路径误差（`compare_captures.py`）、全屏耗时（`BenchmarkMaterialShading`，2048²）、场景 GPU Trace、PSO 数。
- **判断标准**（Roadmap M3）：神经版误差明显低于简化版，耗时低于完整版。
- **要补的能力**：lookdev（在标准 HDRI 下检查材质）、灯光与曝光、转台相机。

### Demo 2：神经超分对比

- **场景**：本地 Zorah（已启用 DLSS 与帧生成插件）；或 ORCA 的 Amazon Lumberyard Bistro（室内外两个场景，有大量细节、透明和植被，常用于抗锯齿与超分评测）。
- **对比**：原生分辨率 TAA / TSR、TSR 超分、DLSS 超分、DLSS Ray Reconstruction（光追场景）、帧生成。
- **测量**：各方案的 GPU 耗时；与高分辨率参考帧的 FLIP 误差；重点镜头的问题（快速运动的拖影、遮挡区域、透明物体、细线闪烁）。
- **要讲清的管线要求**：运动向量、抖动采样、反应遮罩、透明与粒子的处理、UI 合成位置。参考本地 `本地的 DLSS 集成指南目录` 中的集成指南。

### Demo 3：角色 ML Deformer

- **资源**：Epic 的 ML Deformer Sample（含肌肉骨骼模型、训练数据和网络参数，以及 Houdini 训练源资产）。
- **对比**：同一段动作下的线性蒙皮、ML Deformer（Neural Morph Model）、离线模拟结果。
- **测量**：GPU 与内存开销（官方称 Bone Mask 可减少约 40%）、视觉差异。
- **注意**：先确认 Fab 列表中的支持版本与本地 5.8 是否一致。

### Demo 4：数字人小片段

- **资源**：MetaHuman Creator（UE 5.6 起集成在引擎内）；NVIDIA Audio2Face（2025 年 9 月开源模型、SDK、训练框架，UE 插件 2.5 支持 UE 5.5 / 5.6）。
- **风险**：Audio2Face 的 UE 插件未标明支持 5.8，需要移植或在 5.6 工程中做。
- **测量**：口型与表情的主观质量、整体帧预算（面部、头发、皮肤、超分）。

### Demo 5：学习型对手

- **资源**：本地 `本地的 nvdemo 项目`（第三人称模板，含战斗与平台跳跃变体）；引擎内置 Learning Agents 插件。
- **做法**：训练一个追逐或竞速对手，与手写的行为树 / StateTree 对比。
- **注意**：官方教程多为 5.3 时期，Epic 论坛有「Learning Agents Tutorial 5.6+」帖子，Blueprint 示例可能需要按新版本调整。

### Demo 6：神经纹理压缩

- **资源**：本地 `RTXNTC`（SDK 与 renderer 样例）；Bistro 或 Megascans 的高分辨率 PBR 贴图组。
- **测量**：显存、每像素解码代价、与 BC 压缩的画质对比。

## 3. 资源清单

| 资源 | 用于 | 获取 | 授权 / 费用 | 版本 | 本地状态 |
|---|---|---|---|---|---|
| [Automotive Substrate Materials](https://www.unrealengine.com/en-US/news/get-over-280-production-ready-automotive-substrate-materials-for-ue-5-7-free-on-fab) | Demo 1 | Fab，加入资产库 | 免费（Fab 授权） | UE 5.7.3 及以上，本地 5.8.3 可用 | 未获取 |
| [ML Deformer Sample](https://dev.epicgames.com/documentation/unreal-engine/ml-deformer-sample-in-unreal-engine) | Demo 3 | Fab，加入资产库后在 Launcher 中创建工程 | 免费（Fab 授权） | 以 Fab 列表为准 | 未获取 |
| [MetaHuman Creator](https://dev.epicgames.com/documentation/metahuman/metahuman-creator-in-unreal-engine) | Demo 4 | 引擎内启用插件 | MetaHuman 授权 | UE 5.6 起在引擎内 | 引擎自带 |
| [Audio2Face（开源）](https://developer.nvidia.com/blog/nvidia-open-sources-audio2face-animation-model) | Demo 4 | GitHub `NVIDIA/Audio2Face-3D-SDK`；ACE for Games 页面 | 开源（具体许可证以仓库为准） | UE 插件 2.5：5.5 / 5.6 | 未获取 |
| [Amazon Lumberyard Bistro（ORCA）](https://developer.nvidia.com/orca/amazon-lumberyard-bistro) | Demo 2、6 | NVIDIA ORCA 页面下载（FBX，约 850 MB） | CC BY 4.0，需署名「Amazon Lumberyard Bistro, Open Research Content Archive (ORCA)」 | FBX，需导入 | 未获取 |
| [MaterialX Teapot 与 Lion](https://github.com/DigitalProductionExampleLibrary/MaterialXTeapotLion) | Demo 1 的材质微基准（多层陶瓷、涂层、UDIM） | GitHub（DPEL） | 以仓库许可为准 | MaterialX / USD，不是现成 UE 关卡；导入时检查节点映射、色彩空间、UDIM | 未获取 |
| [Electric Dreams](https://dev.epicgames.com/documentation/en-us/unreal-engine/electric-dreams-environment-in-unreal-engine) | 神经材质进入真实 UE 场景（Substrate、Nanite、Lumen）；Opal 材质与 `ElectricDreams_PCGCloseRange` 小关卡 | Fab / Launcher | 免费（Fab 授权） | 全量场景很重，先用小关卡 | 未获取 |
| [City Sample](https://dev.epicgames.com/documentation/unreal-engine/city-sample-project-unreal-engine-demonstration?lang=en-US) | 后期规模压力测试（Nanite、World Partition、流送） | Fab | 免费（Fab 授权） | 很重，不适合作第一阶段误差基准 | 未获取 |
| [Crytek Sponza（Khronos glTF）](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/Sponza) | 固定室内照明、间接光的轻量基线 | GitHub | 以仓库许可为准 | glTF | 未获取 |
| Megascans 免费入门内容 | 各 demo 的道具与地面 | Fab | 约 1500 个资产，Fab Standard 授权（2025 年公布的数字，[Epic 论坛](https://forums.unrealengine.com/t/megascans-starter-content-on-fab/2255322)） | — | 未获取 |
| [NVIDIA vMaterials](https://developer.nvidia.com/vmaterials) | Demo 1 的额外教师材质（MDL，与 NVIDIA 神经外观的训练输入一致） | NVIDIA 页面下载，可能需填表 | 免费，再分发需遵守许可 | MDL | 未获取 |
| Poly Haven / ambientCG | lookdev 用的 HDRI、PBR 贴图 | 官网直接下载 | CC0 | — | 未获取 |
| Zorah | Demo 2 | — | NVIDIA 示例授权 | NvRTX 分支 | **本地已有**（102 GB） |
| nvdemo | Demo 5 | — | — | 本地引擎 | **本地已有** |
| DLSS 集成文档 | Demo 2 | — | NVIDIA RTX SDK EULA | — | **本地已有** |
| RTXNTC、RTXNS | Demo 6、通用神经 shader | — | NVIDIA SDK 许可 | — | **本地已有** |
| gs（高斯泼溅实验工程） | 辐射场路线的对照 | — | — | 本地引擎 | **本地已有**，属于全景中暂不考虑的路线 |

## 4. 建议的顺序

1. **Demo 1**：在 Fab 获取 Automotive Substrate Materials，完成 Roadmap M3。它最依赖现有工作，也最能体现项目价值。
2. **Demo 2**：用本地 Zorah 做超分对比，补上面试最常见的神经技术。
3. 之后按兴趣在 Demo 3、4、5 中选一个，补一条非渲染方向的实践。

神经材质的场景测试按三层推进，不要用一张复杂大地图同时判断画质、带宽和算法正确性：

1. **材质微基准**：从 Automotive 或 MaterialX Teapot / Lion 选 2–3 个代表材质，固定相机、光源、曝光和色彩管理，比较参考、原材质、神经材质的误差、GPU 耗时与内存；再改变视角、HDR 环境和距离检查泛化。
2. **UE 小场景**：放进 Electric Dreams 小关卡或 Zorah，检查与 Nanite、Lumen、NvRTX 路径的兼容性。
3. **规模**：最后用 City Sample 或 Bistro 测规模化表现。每层固定分辨率、屏幕百分比、灯光、机位和渲染开关。

波动光学的测试场景另见 [神经外观与波动光学](/projects/neural-bsdf-perf/wave-optics/) 第 4 节。

## 5. 资料来源

- [Epic：280+ 免费 Automotive Substrate 材质（UE 5.7）](https://www.unrealengine.com/en-US/news/get-over-280-production-ready-automotive-substrate-materials-for-ue-5-7-free-on-fab)；[Digital Production 报道](https://digitalproduction.com/2026/03/02/280-free-automotive-substrate-materials-for-ue-5-7-epic-drops-a-ready-made-lookdev-kit/)
- [Epic：ML Deformer Sample 文档](https://dev.epicgames.com/documentation/unreal-engine/ml-deformer-sample-in-unreal-engine)；[80.lv：ML Deformer Sample 更新](https://80.lv/articles/unreal-engine-5-s-ml-deformer-sample-gets-updated/)
- [NVIDIA：开源 Audio2Face](https://developer.nvidia.com/blog/nvidia-open-sources-audio2face-animation-model)
- [NVIDIA ORCA：Amazon Lumberyard Bistro](https://developer.nvidia.com/orca/amazon-lumberyard-bistro)
- [Epic 论坛：Megascans starter content on Fab](https://forums.unrealengine.com/t/megascans-starter-content-on-fab/2255322)
- [Epic：MetaHuman Creator in Unreal Engine](https://dev.epicgames.com/documentation/metahuman/metahuman-creator-in-unreal-engine)
- [NVIDIA vMaterials](https://developer.nvidia.com/vmaterials)
- [Epic：Electric Dreams Environment](https://dev.epicgames.com/documentation/en-us/unreal-engine/electric-dreams-environment-in-unreal-engine)；[Epic：City Sample](https://dev.epicgames.com/documentation/unreal-engine/city-sample-project-unreal-engine-demonstration?lang=en-US)
- [DPEL：MaterialX Teapot and Lion](https://github.com/DigitalProductionExampleLibrary/MaterialXTeapotLion)；[Khronos：glTF Sponza](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/Sponza)
- [Epic：Learning Agents API 参考](https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/LearningAgents/ULearningAgentsManager?lang=en-US)
