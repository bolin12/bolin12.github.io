---
layout: page
title: "UE 神经外观系统路线图"
permalink: /projects/neural-bsdf-perf/roadmap/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
group: 设计与规划
order: 2
side_title: 路线图
---
更新：2026-11-01。本文回答：这个项目要做什么、目标架构是什么、分几个阶段、现在到哪了、接下来展示什么。当前实现见 [系统架构](/projects/neural-bsdf-perf/architecture/)，各阶段的结果与被推翻的判断见 [里程碑总览](/projects/neural-bsdf-perf/milestones/)。

## 1. 定位

神经材质在游戏里有说服力的价值主要有三点：

1. **固定成本替代昂贵材质**：多层车漆、带清漆的布料、复杂皮肤等多 closure 材质，在 Substrate 里光照成本随层数上升；神经版是一次固定成本的求值。
2. **减少 PSO 与 shader 变体**：外观差异变成数据差异，大量材质共用同一个 shader。
3. **显存与带宽**：latent 纹理可配合神经纹理压缩（NTC）。

因此项目的核心交付是：**高效的神经着色运行时 + 证明它比原方案划算的测量数据**。判断标准是：**误差明显低于简化版（烘焙为单 Slab），同时成本明显低于完整 Substrate**，两者都用引擎内捕获与同路径对比来量化。

| 方案 | 外观 | 光照成本 |
|---|---|---|
| 完整 Substrate（多 closure） | 参考答案 | 高，随层数增加 |
| 简化 / 烘焙为单 Slab | 丢失多波瓣与视角相关的分层效果 | 最低 |
| 神经材质 | 接近完整版 | 固定，取决于实现优化 |

波动光学（衍射、薄膜、结构色）不作为主线，只是一篇调研，见 [神经外观与波动光学](/projects/neural-bsdf-perf/wave-optics/)。

## 2. 目标架构

1. **求值器**：权重放在常量缓冲；按网络形状编译特化、循环展开；fp16 打包运算，量化模型用 dp4a；后期接 cooperative vector（tensor core），保留普通 shader 回退。
2. **编码器 / 解码器两段式**：base pass 采样 latent 纹理并写入 GBuffer，光照阶段只运行解码器；latent 纹理可压缩。
3. **与 Substrate 解耦**：专用标志位和数据，不借用 glint 槽位；神经材质作为 opt-in 的 tile 类型。
4. **间接光混合方案**：直接光用网络；Lumen / 反射使用从网络拟合的逐 texel 代理参数。
5. **引擎补丁最小化**：主体放在插件，引擎只保留少量明确的接入点，便于跟随引擎升级。

## 3. 阶段与现状

| 阶段 | 内容 | 状态 | 报告 |
|---|---|---|---|
| M0 原型 | BSDF 契约、模型资产、Substrate 延迟光照接入、同路径对比 | 完成 | [系统架构](/projects/neural-bsdf-perf/architecture/)、[捕获与对比](/projects/neural-bsdf-perf/capture-and-comparison/) |
| M1 求值器优化 | 基准工具、权重进常量缓冲、特化展开、打包权重 | 进行中：2048² 下 latent 约 16 ms、QTP 约 12.5 ms，完整 OpenPBR 约 8 ms；瓶颈是寄存器数（168–214）导致的低占用率 | [性能报告](/projects/neural-bsdf-perf/performance/) |
| M2 存储解耦 | 专用标志位与逐像素数据，去掉 glint 依赖 | 完成：逐灯光照快 11%；拆成独立绘制实测更慢，默认关闭 | [M2 报告](/projects/neural-bsdf-perf/milestones/m2-storage-decoupling/) |
| M3 价值验证 | 完整、简化、神经三方对比误差、耗时、PSO 数与内存 | 第一轮（OpenPBR 教师）两项都未达成；第二轮等待 Automotive 资产 | [M3 报告](/projects/neural-bsdf-perf/milestones/m3-value-validation/) |
| M4 间接光 | 逐 texel 代理参数拟合 | 完成：只有天光时对教师误差 66.6% → 18.6% | [M4 报告](/projects/neural-bsdf-perf/milestones/m4-indirect-proxy/) |
| M5 进阶 | cooperative vector、NTC、更多材质类型 | 部分完成：打包 fp16 神经核反而慢 7%；tensor core 需要预览版 SDK | [M5 报告](/projects/neural-bsdf-perf/milestones/m5-advanced/) |

## 4. 展示计划

每个 demo 只回答一个问题，同屏对比，屏幕上实时显示耗时和误差，测量沿用 A-B-A 与对照材质（见 [GPU Trace 手册](/projects/neural-bsdf-perf/gpu-trace-guide/)）。以下都是计划，尚未开始。

1. **神经材质展示厅（最优先）**：用 Epic 官方 Automotive Substrate Materials 的车漆、清漆金属、皮革，完整 Substrate、简化版、神经版并排，回答「神经版比完整版省多少、比简化版准多少」。它就是 M3 第二轮。
2. **神经超分对比**：TSR、DLSS 超分、Ray Reconstruction、帧生成的画质与耗时，以及各自对渲染管线的要求。
3. 其余按兴趣择一：角色 ML Deformer、数字人小片段、学习型对手、神经纹理压缩。

神经材质的场景测试按三层推进，不要用一张复杂大地图同时判断画质、带宽和算法：先做**材质微基准**（固定相机、光源、曝光，比较误差、耗时与内存），再放进 **UE 小场景**检查与 Nanite、Lumen 的兼容性，最后才测**规模**。

## 5. 早期原型

最早的实验是在 UE 材质的 Custom 节点里运行网络，验证模型在 UE 中能得到与训练端一致的结果：两条路线（latent MLP、QTP）在 CPU 与 GPU 上数值对齐，QTP 的平均绝对差在手动插值后降到约 3e-6。这条路径后来被原生接入取代，保留作对照。

## 6. 工作约定

- 编辑器启动加 `-noxgeshadercompile`；编译前关闭编辑器。
- 性能测量用 A-B-A、OpenPBR 对照、2048² 基准，编辑器不能处于后台限帧状态。
- 每轮改动一次提交，结果写进性能报告或对应里程碑页。
- 修改 `NeuralBSDFCommon.ush`、Substrate shader 或 View / Substrate 统一缓冲会触发大范围 shader 重编，首次启动耗时较长。
