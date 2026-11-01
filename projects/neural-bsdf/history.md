---
layout: page
title: "项目历程"
permalink: /projects/neural-bsdf-perf/history/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
group: 规划
order: 32
side_title: 项目历程
---
更新：2026-10-22。本文回答：这个项目按什么顺序做到了现在，每一步的结果和当时的判断是什么。当前系统见 [系统架构](/projects/neural-bsdf-perf/architecture/)；早期文档中已过时的计划归档在第 3 节。


## 1. 时间线

| 日期 | 里程碑 | 结果 | 提交 / 详情 |
|---|---|---|---|
| 10-17 | 技术调研 | 区分神经材质、神经纹理、神经几何、NRC、DLSS 与波动光学；核实本地 Zorah 没有集成神经材质 | [神经外观与波动光学](/projects/neural-bsdf-perf/wave-optics/) |
| 10-18 | 材质 Custom 节点原型 | 两条路线（latent MLP、QTP）在 UE 材质中推理，CPU 与 GPU 数值对齐 | 第 2 节 |
| 10-18 | 原生接入（M0） | C++ 模块、模型资产、网络纹理、compute 验证路径、预览 Actor | [系统架构](/projects/neural-bsdf-perf/architecture/) 第 2、3、8 节 |
| 10-18 | Unlit 灯光原型 | 场景方向光驱动神经材质；潜纹理接近教师，QTP 有斑驳噪声；不接收阴影 | [系统架构](/projects/neural-bsdf-perf/architecture/) 第 8 节 |
| 10-18 | Substrate 延迟光照接入 | 神经材质接收阴影与多盏点光（借用 glint 槽位） | `e8fbe6fd6231`；[系统架构](/projects/neural-bsdf-perf/architecture/) 第 6 节 |
| 10-18 | 引擎内捕获与同路径对比 | OpenPBR 教师，同路径相对 L1 11.8%；修复 SceneCapture 中 Complex Special tile 截断的引擎 bug | `576125bf4688`、`234827ff6fd1`；[捕获与对比](/projects/neural-bsdf-perf/capture-and-comparison/) |
| 10-19 | M1 求值器优化 | 权重进常量缓冲、按形状完全展开；旧计时下 latent 108.8 → 18.8 ms、QTP 187.5 → 40.0 ms（1024²，后来发现受空闲时钟影响） | `90ef901a5ae3`；[性能报告](/projects/neural-bsdf-perf/performance/) 3.2 |
| 10-19 | Nsight GPU Trace 分析 | 定位神经光照排列；寄存器受限的占用率是主要瓶颈；推翻「常量读取是主要瓶颈」 | `d0df54e0fa3b`；[性能报告](/projects/neural-bsdf-perf/performance/) 第 4 节 |
| 10-20 | R0 计时修正 | 连续提交、双缓冲读回、3 秒预热、记录时钟；基准改为 2048² | `cb8343eba8c2`、`1928e0f34f57` |
| 10-20 | R1 打包权重 | latent 38.1 → 15.7 ms（2.4×），QTP 81.4 → 11.5 ms（7.1×）；dp4a 逐字节一致，fp16 误差 0.14% | `d1a16cc8b894` |
| 10-20 | R2–R4 | R2 融合层逐字节一致、无收益，保留；R3、R4 无收益，未合入 | `5b1528e0db04`、`605102e1d3eb`、`263df1c4e82e` |
| 10-20 | GPU Trace 录不到场景帧 | 原因是编辑器后台限帧（3 fps），用启动参数解决；读到神经排列 168 寄存器 / 线程 | `61efa15a1a3b`；[性能方法手册](/projects/neural-bsdf-perf/gpu-trace-guide/) 3.5 |
| 10-21–22 | 文档整理与规划 | 性能报告与方法手册；游戏引擎神经技术全景；Demo 计划与资源 | `60055ecf14d6` 起 |
| 10-23 | M5 进阶 | 打包 fp16 寄存器 214 → 168，但神经核慢 7%；tensor core 需要预览 SDK | [M5 报告](/projects/neural-bsdf-perf/milestones/m5-advanced/) |
| 10-23 | M3 价值验证（第一轮） | OpenPBR 教师上神经版既不比最优单 Slab 准（11.8% 对 9.8%），也不比完整 Substrate 快（15.1 对 7.7 ms）；修复图集启动竞争 | [M3 报告](/projects/neural-bsdf-perf/milestones/m3-value-validation/) |
| 10-23 | M4 间接光代理 | 逐 texel 拟合 Slab 代理；只有天光时对教师误差 66.6% → 18.6% | [M4 报告](/projects/neural-bsdf-perf/milestones/m4-indirect-proxy/) |
| 10-22–23 | M2 存储解耦 | 独立标志与逐像素数据，不再需要 glint，逐灯光照快 11%；拆分成独立绘制实测更慢，默认关闭 | [M2 报告](/projects/neural-bsdf-perf/milestones/m2-storage-decoupling/) |

## 2. 材质 Custom 节点原型（10-18）

最早的实验：在 UE 材质的 Custom 节点里运行网络，验证模型能在 UE 中得到与训练端一致的结果。

- **路线 A（latent MLP）**：NVIDIA 方法相关的潜纹理与方向解码参考实现，4 通道 32×32 潜纹理，两层宽 32 的隐藏层，Exp 输出。没有导入 NVLabs 官方检查点，不能称为官方工程的复现。
- **路线 B（QTP）**：调用 `ComprehensiveNeuralMaterial-Train/networks.py` 的 `QuantizedTriplePlane` 与 Brevitas QAT，三个 32×32 四通道平面，宽 32 的网络；对 CPU 初始化做了适配，未修改作者仓库。
- **训练**：两条路线各 2600 步，统一的解析教师（双 GGX + 漫反射）、方向约定和显式直射光。8192 个留出样本上对教师的平均绝对误差：latent `0.0128264`，QTP `0.0225818`。
- **呈现**：UE 用 Unlit / Emissive 输出承载结果，地图 `/NeuralAppearanceLab/Maps/L_NeuralAppearanceLab`：左为解析参考，中为 latent，右为 QTP，下方两球显示放大十倍的误差；`MI_Reference`、`MI_NALatent`、`MI_QTP8` 等实例的光照参数由 MCP 工具 `set_lab_light` 统一更新。
- **特征平面**：无压缩线性 RGBA8，无 mip；HLSL 中手动双线性插值，避免硬件过滤精度影响量化阈值。

CPU 与 GPU 一致性（RTX 4060，每个模型 1024 个固定输入，Python 预测对比 32×32 浮点渲染目标回读）：

| 模型 | 平均绝对差 | 最大绝对差 |
|---|---:|---:|
| 解析参考 | 1.96e-7 | 7.57e-6 |
| latent | 1.83e-8 | 2.98e-7 |
| QTP | 2.84e-6 | 3.61e-3 |

改为手动插值后，QTP 平均差从 `2.63e-4` 降到 `2.84e-6`；剩余残差与浮点运算和量化阈值有关。结果在插件 `Saved/gpu_validation.json`。这条路径之后被原生接入取代，地图和材质保留作对照。

## 3. 已完成或已被取代的计划

早期文档里的「下一步」与「限制」，后来的状态：

| 当时的计划或限制 | 出自 | 后来 |
|---|---|---|
| 缩小 QTP 的 CPU / GPU 残差，再导入官方检查点 | Custom 节点原型 | 残差保持在容差内，未继续；官方检查点未导入 |
| 实现 BSDF 契约，接入 UE 光照（先一盏动态灯与阴影，再多灯） | Custom 节点原型、外部光照说明 | 已完成：Substrate 延迟光照接入（10-18） |
| GPU buffer 随评估上传、同步回读，不是生产方案；增加持久 GPU 资源 | 原生接入 | 光照路径已改用图集与常量缓冲（M1）；compute 路径仍只用于验证 |
| 每像素读取约 1.5k 个网络纹理 texel，未测性能 | 原生接入 | M1 改为常量缓冲权重与特化核；性能已系统测量（R0–R4） |
| QTP 以 FP32 累加 INT8，尚无 dp4a | 原生接入 | R1 实现 dp4a，与 fp32 逐字节一致 |
| 运行时、编译期、内存指标尚未接入报告 | 捕获与对比 | 运行时已有基准与 GPU Trace；编译期（PSO 数）与内存仍待做，归入 Roadmap M3 |
| 常量读取可能是主要瓶颈 | M1 | 被 GPU Trace 推翻（10-19） |
| 不执行的 fp32 分支决定寄存器数 | R2 分析 | 被 R3 推翻（10-20） |
