---
layout: page
title: "UE 神经外观系统路线图"
permalink: /projects/neural-bsdf-perf/roadmap/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
group: 规划
order: 30
side_title: 路线图
---
更新：2026-10-22（初稿 2026-10-18）。本文回答：这个项目要做什么、为什么值得做、目标架构是什么、分几个阶段、现在到哪了。当前实现见 [系统架构](/projects/neural-bsdf-perf/architecture/)，做过的事见 [项目历程](/projects/neural-bsdf-perf/history/)。


## 1. 定位

神经材质在游戏里有说服力的价值主要有三点：

1. **固定成本替代昂贵材质**：多层车漆、带清漆的布料、复杂皮肤等多 closure 材质，在 Substrate 里光照成本随层数上升；神经版是一次固定成本的求值。
2. **减少 PSO 与 shader 变体**：外观差异变成数据差异，大量材质共用同一个 shader。
3. **显存与带宽**：latent 纹理可配合神经纹理压缩（NTC）。

因此项目的核心交付是：**高效的神经着色运行时 + 证明它比原方案划算的测量数据**。

神经材质的定位是完整 Substrate 与简化版之间的中间点：

| 方案 | 外观 | 光照成本 |
|---|---|---|
| 完整 Substrate（多 closure） | 参考答案 | 高，随层数增加 |
| 简化 / 烘焙为单 Slab（Material Baking、Parameter Blending、`SCC_FullySimplified`） | 丢失多波瓣与视角相关的分层效果 | 最低 |
| 神经材质 | 接近完整版 | 固定，取决于实现优化 |

判断标准：**误差明显低于简化版，同时成本明显低于完整版**。两者都用引擎内捕获与同路径对比来量化。

波动光学（衍射、薄膜、结构色）不作为主线，适合在运行时成熟后作为展示项，见 [神经外观与波动光学](/projects/neural-bsdf-perf/wave-optics/)。

## 2. 目标架构

1. **求值器**：权重放在常量缓冲（wave 内统一地址时为标量读取）；按网络形状编译特化，循环展开、中间结果留在寄存器；fp16 打包运算，量化模型用 dp4a；后期接 cooperative vector（DX12 SM 6.9，tensor core），保留普通 shader 回退。
2. **编码器 / 解码器两段式**：base pass 采样 latent 纹理并写入 GBuffer（例如 8 个 fp16），光照阶段只运行解码器；latent 纹理可 BC / NTC 压缩，从而支持高分辨率真实材质。
3. **与 Substrate 解耦**：专用标志位和数据，不再借用 glint 槽位，不再要求项目开启 glint；神经材质作为 opt-in 的 tile 类型，只有用到它的 tile 才运行神经 permutation。
4. **间接光混合方案**：直接光用网络；Lumen / 反射使用从网络拟合的逐 texel 代理参数；需要时再为网络增加环境光预积分输出头。
5. **引擎补丁最小化**：主体放在插件，引擎只保留少量明确的接入点，便于跟随引擎升级。

## 3. 分阶段计划

| 阶段 | 内容 | 判断标准 | 状态 |
|---|---|---|---|
| M0 原型 | 共享 BSDF 契约、模型资产、Substrate 延迟光照接入（借用 glint 槽位）、引擎内捕获与同路径对比 | 神经材质接收阴影与多光源；同路径误差与训练一致 | 完成，见 [系统架构](/projects/neural-bsdf-perf/architecture/)、[捕获与对比](/projects/neural-bsdf-perf/capture-and-comparison/) |
| M1 求值器优化 | GPU 着色基准工具；权重进常量缓冲；按形状特化展开；QTP 输入量化外提 | 神经部分耗时降至基线的十分之一以下（ProfileGPU / 基准工具实测）；捕获结果与优化前一致 | 进行中：M1 后又做了 R0–R4；当前 2048² 下 latent 约 16 ms、QTP 约 12.5 ms（完整 OpenPBR 约 8 ms），fp16 误差 0.14%、dp4a 逐字节一致。瓶颈是光照排列的寄存器数（168–214）；拆分成独立绘制已在 M2 中实测无效，见 [性能报告](/projects/neural-bsdf-perf/performance/) |
| M2 存储解耦 | 专用标志位、latent 写入 GBuffer、opt-in tile 类型，去掉 glint 依赖 | 普通材质性能不受影响；关闭 glint 后神经材质照常工作 | 完成：独立标志与 3 uint 逐像素数据，glint 关闭时逐像素一致，逐灯光照快 11%；拆分绘制实测更慢，保留为默认关闭的开关。见 [M2 报告](/projects/neural-bsdf-perf/milestones/m2-storage-decoupling/) |
| M3 价值验证 | Automotive Substrate Materials 的车漆、皮革、金属：完整 Substrate、简化版、神经版三方对比误差、耗时、PSO 数与内存 | 神经版误差明显低于简化版，耗时低于完整版 | 第一轮（OpenPBR 教师）完成，两项都未达成：最优单 Slab 误差 9.8% 低于神经 11.8%，神经 15.1 ms 慢于完整 OpenPBR 7.7 ms；流程已脚本化。第二轮需要 Fab 上的 Automotive 资产（[Demo 1](/projects/neural-bsdf-perf/demos/)）。见 [M3 报告](/projects/neural-bsdf-perf/milestones/m3-value-validation/) |
| M4 间接光 | 逐 texel 代理参数拟合 | 开启 Lumen 时金属与清漆外观基本一致 | 完成：只有天光时对教师误差 66.6% → 18.6%，太阳 + 天光 22.2% → 10.5%；清漆锐利反射仍弱于教师。见 [M4 报告](/projects/neural-bsdf-perf/milestones/m4-indirect-proxy/) |
| M5 进阶 | cooperative vector、NTC 压缩 latent、更多材质类型 | 进一步降低耗时与显存 | 部分完成：打包 fp16（`r.NeuralBSDF.Real16`）寄存器 214 → 168 但神经核慢 7%，默认关闭；tensor core 需要预览版 SDK，本引擎不可用；NTC 需要先支持大潜平面。见 [M5 报告](/projects/neural-bsdf-perf/milestones/m5-advanced/) |
| 可选 | 波动光学展示效果 | 在成熟运行时上的特色效果 | 未开始，见 [神经外观与波动光学](/projects/neural-bsdf-perf/wave-optics/) |

## 4. M0 产出的去留

- 保留：BSDF 契约、模型资产与 atlas 子系统、捕获与对比框架、MCP 自动化、插件结构。
- 已替换：借用 glint 槽位的存储（M2）、光照中读取网络纹理的求值方式（M1 / M2）。

## 5. 工作约定

- 编辑器启动加 `-noxgeshadercompile`（XGE shader 控制器会卡住任务）。
- 编译命令见 [系统架构](/projects/neural-bsdf-perf/architecture/) 第 9 节；编译前关闭编辑器。
- 性能测量用 A-B-A、OpenPBR 对照、2048² 基准，编辑器不能处于后台限帧状态，见 [性能方法手册](/projects/neural-bsdf-perf/gpu-trace-guide/)。
- 每轮改动一次提交，结果写进性能报告或对应文档，里程碑记入 [项目历程](/projects/neural-bsdf-perf/history/)。
- 修改 `NeuralBSDFCommon.ush`、Substrate shader 或 View / Substrate 统一缓冲会触发大范围 shader 重编，首次启动耗时较长。
