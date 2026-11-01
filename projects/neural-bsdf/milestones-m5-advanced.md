---
layout: page
title: "M5 报告：进阶——打包 fp16、tensor core 与压缩"
permalink: /projects/neural-bsdf-perf/milestones/m5-advanced/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
group: 里程碑
order: 15
side_title: M5 进阶
---
更新：2026-10-23。本文回答：路线图 M5 的三项（cooperative vector / tensor core、NTC 压缩潜纹理、更多材质类型）在这台机器和这个引擎版本上能做到哪一步；做了哪个实验、结果如何。


## 1. 结论

| 项 | 结果 |
|---|---|
| 打包 fp16（实时 16 位类型 + `dot2add`） | 实现并测量。光照着色器寄存器 214 → 168（方向光），占用率 +40%，同 tile 的 glint 像素快 4–7%；但**神经 latent 本身慢 7%**（15.1 → 16.2 ms）。保留为默认关闭的开关 `r.NeuralBSDF.Real16` |
| 只打开实时 16 位类型 | 寄存器反而上升到 220，耗时不变：Substrate 的 `half` 运算变成 fp16 并没有让编译器少用寄存器 |
| Tensor core（cooperative vector / LinAlg） | 本引擎做不到：cooperative vector 已被弃用，后继的 SM 6.10 LinAlg 只有预览版 Agility SDK / DXC；本引擎带的是 1.618.5。第 3 节列出需要的改动 |
| NTC 压缩潜纹理 | 当前没有意义：每个模型的潜平面只有 32×32×4（4 KB）。先要让图集支持每模型不同尺寸的潜平面（真实材质，M3 第二轮），压缩才有对象 |
| 更多材质类型 | 运行时已能求值任意形状（通用求值器）；限制在训练端（只有 latent 能从捕获训练）和图集（平面统一 32²） |

M5 的主线结论：**在这块 GPU 上，神经 latent 核同时受寄存器（占用率）和指令发射两方面限制**。降低寄存器而增加指令（`dot2add` 需要 16 位解包）得不偿失；要明显降低成本，需要把乘加移出标量管线，也就是 tensor core——而这在当前引擎版本中不可用。

## 2. 打包 fp16 实验

### 2.1 做了什么

UE 在 D3D 上默认把 `half` 映射为 32 位 `float`；着色器要用真正的 fp16，需要编译标志 `CFLAG_AllowRealTypes`（DXC `-enable-16bit-types`，SM 6.6）。新的只读设置 `r.NeuralBSDF.Real16` 只作用于 Complex Special tile 的延迟光照着色器（只有它重新编译）：

| 模式 | 含义 |
|---|---|
| 0 | 现状（默认） |
| 1 | 实时 16 位类型；神经核不变。Substrate 自身的 `half` 运算变为 fp16 |
| 2 | 同 1，并换用打包 fp16 的 latent 核 |

模式 2 的 latent 核：FP16x2 权重字直接作为 `float16_t2` 使用；隐藏层激活以 `float16_t2[16]` 存储（原来是 `float[32]`）；每两个乘加是一条 `dot2add(half2, half2, float)`（fp16 乘积、fp32 累加）。理论上激活寄存器减半、乘加指令减半。

### 2.2 结果

2048² 全屏基准，每个模式一次编辑器会话、三轮中位数（模式 0 来自 M3 第一轮与 M2 的会话）：

| 材质 | 模式 0 | 模式 1 | 模式 2 |
|---|---:|---:|---:|
| OpenPBR（对照，不在 Complex Special tile） | 7.75 ms | 7.67 ms | 7.73 ms |
| 神经 latent | 15.07 ms | 14.94 ms | **16.18 ms** |
| 神经 QTP（dp4a 核，不受模式 2 影响） | 11.39 ms | 11.30 ms | 11.36 ms |
| glint 对照材质（与神经核同一个光照着色器） | 14.14 ms | 13.86 ms | **13.22 ms** |

场景 GPU Trace（`L_NeuralCaptured_OPBR`），Complex Special tile 上的 `DeferredLightPixelMain`：

| | 模式 0 | 模式 1 | 模式 2 |
|---|---:|---:|---:|
| 点光：寄存器 / 占用率 | 168 / 0.42 | 220 / 0.35 | 168 / 0.49 |
| 方向光：寄存器 / 占用率 | 214 / 0.24 | 220 / 0.23 | **168 / 0.33** |
| UnbatchedLights | 1.025 ms | 1.111 ms | 1.097 ms |

数值（同种子捕获，对模式 0）：模式 1 latent 相对 L1 0.08%、QTP 0.29%（Substrate 的 fp16 运算）；模式 2 latent 0.25%（PSNR 59 dB，激活舍入到 fp16）。

### 2.3 解读

1. **只打开 16 位类型（模式 1）没有好处**：编译器没有因为 Substrate 的 `half` 变成 fp16 而少用寄存器，反而在两种灯上都到了 220。fp16 的标量运算在这块 GPU 上并不比 fp32 快，只有成对打包时才省。
2. **打包核（模式 2）达到了降寄存器的目的**：方向光着色器从 214 降到 168，与点光一致，占用率提高约 40%。受益最明显的是与神经核共用这个着色器、但自己并不运行神经核的像素（glint 对照快 4–7%）。
3. **神经 latent 自己却慢了**：`dot2add` 的输入要从 32 位字中拆出两个 16 位值，激活还要在 fp32 与 fp16 之间转换；这些额外指令抵消并超过了占用率带来的收益。M1 时的分析已经显示神经部分的数学管线约 35% 饱和、取指等待约 23%（[性能报告](/projects/neural-bsdf-perf/performance/) 第 4 节），即它不只是缺 warp，每个 warp 的指令也多。
4. **场景中三者差别在噪声附近**（1.03–1.11 ms）：场景里神经像素只占一部分。

默认保持模式 0。如果项目中 Complex Special tile 里大部分是 glint 等非神经像素，模式 2 有意义；神经像素为主时不值得。

## 3. Tensor core（cooperative vector / LinAlg）的可行性

### 3.1 现状（2026-10）

| 项 | 状态 |
|---|---|
| D3D12 Cooperative Vector | 2025 年以 Agility SDK 1.717-preview 发布预览；之后被微软标为弃用，改为 Shader Model 6.10 中统一矩阵乘矩阵与向量乘矩阵的新设计 |
| Shader Model 6.10 与 LinAlg | Agility SDK 1.720 起的公开预览；NVIDIA 的 RTXNTC 已改称 “LinAlg（原 Cooperative Vector）”，要求 1.721.0-preview |
| 本引擎 | 自带 Agility SDK 1.618.5（支持到 SM 6.9，没有 cooperative vector 接口），DXC 也是对应的正式版 |
| 驱动 | 预览 API 需要开发者驱动和 D3D12 实验特性开关（`D3D12EnableExperimentalFeatures`） |

结论：在这个引擎里直接“打开 tensor core”做不到。需要同时替换 Agility SDK、DXC，打开实验特性，并在 RHI 中暴露新的着色器模型；这些都属于预览，接口还在变。

### 3.2 如果要做，需要改什么

| 层 | 改动 |
|---|---|
| 运行时 | 把 `Engine/Source/ThirdParty/Windows/AgilitySDK` 换成 1.720+ 预览，`D3D12SDKVersion` 导出改为对应版本；创建设备前调用 `D3D12EnableExperimentalFeatures` 打开实验着色器模型 |
| 编译器 | 换用支持 SM 6.10 的 DXC 预览版；`ShaderFormatD3D` 增加 6.10 目标与对应的编译标志 |
| RHI | 查询 LinAlg 支持，作为平台能力暴露给渲染器；没有时回退到现在的标量核 |
| 着色器 | 权重改成 LinAlg 要求的矩阵布局（fp16 或 fp8），放在 ByteAddressBuffer 中而不是常量缓冲；每层一次矩阵向量乘 |
| 本项目的特殊问题 | 延迟光照是**像素着色器**，每个像素一个网络、按灯求值。tensor core 的收益来自 wave 内的协作：一个 wave 的线程一起做一次矩阵乘，只有 wave 内各线程用同一个模型时才能合并，这正是常见情况（同一物体）；混合模型的 wave 需要回退 |

### 3.3 预期

M1–M2 与本报告第 2 节的分析表明瓶颈是寄存器（占用率）和标量数学管线两方面。tensor core 在原理上同时缓解两者：矩阵乘不占用标量 FMA 管线，中间结果由矩阵运算的累加器承载。实际收益本机无法测量；它取决于 wave 内模型是否一致、每次矩阵调用的固定开销，以及像素着色器中逐灯调用的频率。这里不给预期数字。

## 4. NTC 压缩潜纹理

NTC（神经纹理压缩，本地 `RTXNTC`）把一组高分辨率材质纹理压成潜变量与一个小网络，按需解码。它对本项目的意义是：真实材质的潜平面需要远高于 32² 的分辨率（[M3 报告](/projects/neural-bsdf-perf/milestones/m3-value-validation/) 第 6 节），那时潜平面的显存会变得可观，压缩才有对象。现在的前置条件是：

1. 图集支持每个模型不同尺寸的潜平面（网络头部记录尺寸；修改 `NeuralBSDFCommon.ush`，触发全局重编）；
2. 训练端支持更高分辨率的潜平面；
3. 之后再评估：BC 压缩潜平面（已有硬件，但 RGBA8 → BC7 的误差需要和量化阈值一起验证），或 NTC（RTXNTC 的快速推理路径同样依赖 LinAlg 预览）。

本轮没有实现，留给 M3 第二轮之后。

## 5. 更多材质类型

| 层 | 现状 |
|---|---|
| 运行时 | latent 与 QTP 有特化核；其他形状由通用求值器 `NeuralBSDF_EvalAtlas` 处理（逐像素数据存 UV） |
| 训练 | 只有 latent 能从引擎内捕获训练；QTP 只能用解析教师 |
| 代理 | 只有 latent 有拟合代理（M4） |
| 资产 | 平面统一 32²，是真实材质的主要限制 |

## 6. 改动清单

| 位置 | 改动 |
|---|---|
| `LightRendering.cpp` | `r.NeuralBSDF.Real16`（只读，默认 0）：Complex Special tile 的延迟光照着色器加 `CFLAG_AllowRealTypes` 与 `NEURAL_BSDF_REAL16` |
| `NeuralBSDFSpecialized.ush` | 模式 2 的打包 fp16 latent 核（`dot2add`） |
| 测量脚本（本地） | 每个模式一次会话：设置 → 启动 → 基准三轮 → 捕获对比 → 场景 GPU Trace；读取 trace 的 nsight-graphics-mcp 本地副本修复了多块 LZ4 元数据的解析（见 [M2 报告](/projects/neural-bsdf-perf/milestones/m2-storage-decoupling/) 第 4.4 节） |
