---
layout: page
title: "引擎内捕获与公平对比"
permalink: /projects/neural-bsdf-perf/capture-and-comparison/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
group: 测量方法
order: 22
side_title: 捕获与对比
---
更新：2026-10-22（初稿 2026-10-18）。本文回答：神经材质的误差怎样公平地测——教师数据和对比参考都来自 Substrate 延迟光照实际渲染出的结果，而不是一份手写的解析近似；以及 OpenPBR 教师的结果。


## 1. 为什么需要

此前的 ref（`NeuralBSDF_Teacher`，双 GGX + 漫反射）同时是训练目标和参考答案，只能证明网络学会了这个公式，不能说明它能否替换一个真实的 Substrate 材质；数值验证（Python vs GPU）只衡量推理一致性。要评估后续三项优化（按材质 opt-in 的 permutation、网络形状编译期特化、与 glint 存储解耦），需要一套固定的度量：外观误差、运行时、编译期（permutation / PSO）、内容与内存成本。本文负责外观误差；运行时见 [性能报告](/projects/neural-bsdf-perf/performance/)，并且要能扩展到更复杂的真实材质。

## 2. 教师材质来源

| 来源 | 内容 | 状态 |
|---|---|---|
| 引擎内置 `MF_Substrate_OpenPBR_Opaque` | 完整 OpenPBR：金属、coat、fuzz、thin film、SSS、透射 | 已用于 `M_Teacher_OpenPBR`（程序化 UV 图案驱动金属/铜色、青色漆、coat 条带、fuzz 区域） |
| 引擎内置 `Substrate-StandardSurface-Opaque` | Autodesk Standard Surface | 备选 |
| Epic 官方 **Automotive Substrate Materials**（Fab 免费，2026-02） | 280 个材质、约 150 个 setup、约 50 个模板；单/双/三层车漆、glint 与彩色 glint、thin film、各向异性、上蜡皮革、实测金属、指纹划痕；含总览地图和 lookdev 地图 | 需要在 Fab 登录并加入库后导入 Demo；要求 UE 5.7.3+ 与 Adaptive GBuffer，本工程均满足。用于 Roadmap M3 与 [路线图](/projects/neural-bsdf-perf/roadmap/) |
| Electric Dreams 样例 | Substrate 欧泊材质球（UE 5.2 时代） | 可选补充 |
| 本机 Zorah 样例（UE 5.4 NvRTX） | 扫描纹理的金属、大理石、石灰岩等，但为旧材质（Substrate 下转换为单层 Slab） | 留作后续真实场景阶段，需要迁移 |

参考：[Fab 上的 Automotive Substrate Materials](https://www.fab.com/listings/1272587c-1431-4878-9d78-2a6b84ebe839)、[Digital Production 的介绍](https://digitalproduction.com/2026/03/02/280-free-automotive-substrate-materials-for-ue-5-7-epic-drops-a-ready-made-lookdev-kit/)。

## 3. 捕获方法

`UNeuralAppearanceEditorLibrary::CaptureMaterialBRDF`（MCP 工具 `capture_material_brdf`）：

- 在独立的 `FPreviewScene` 中放一个单位四边形（`/Engine/BasicShapes/Plane`），一盏方向光（1 lux、光源角 0、不投影），一个正交 `SceneCaptureComponent2D`（`SCS_SceneColorHDR`，线性 HDR）。
- 关闭 Lumen GI / 反射、天光、雾、AO、SSR、抗锯齿、泛光、自动曝光；手动曝光 EV0。
- 对每个 (wi, wo) 对：像素值即 `f(uv, wi, wo) · cosθi`，这正是 Substrate 延迟光照对该材质的渲染结果。
- 采样：40% 为镜面方向附近的对（±0.25 扰动），60% 为半球均匀；θ 限制在 cosθ ≥ 0.08。
- 像素到 UV 由正交射线与 z=0 平面求交解析得到，四边形的 UV 映射和切线从网格渲染数据读取；每次捕获先用 unlit `(u, v, 1)` 材质校验映射（误差需小于 2 像素），并从蓝色通道测出曝光系数。
- 局部坐标系：z = 法线，x = 网格切线，y = cross(z, x)，与 Substrate 由存储切线重建的基一致。
- 输出 `Saved/Capture/<Name>/index.json` 与 `pixels.bin`（float32 `[pairs][res²][u, v, r, g, b]`，u < 0 表示四边形外）。

三个踩坑记录（第 1 条的启动参数见 [系统架构](/projects/neural-bsdf-perf/architecture/) 第 9 节）：

1. **XGE shader 编译控制器卡死**：启动时派发到 XGE controller 的 22 个 shader 任务永远不返回，`IsCompiling()` 一直为真，`FinishAllCompilation` 因此无限等待。启动编辑器时加 `-noxgeshadercompile` 只用本地 16 个 worker 解决。
2. **编辑器按需编译 shader**：材质 shader 在第一次渲染时才请求编译，期间显示默认材质。捕获因此改为跨帧运行的异步任务（`FTSTicker` 状态机）：先渲染预热，直到连续三帧没有新的编译任务，再正式捕获；MCP 调用立即返回，进度写入 `status.json`。
3. **引擎 bug：SceneCapture 中的 complex-special tile 被截断**。`InitialiseSubstrateFrameSceneData` 只从主视图累积 `UsesTileTypeMask`（排除 `bIsSceneCapture`），而 tile 列表偏移按场景级 mask 决定是否给 complex-special 区段分配空间。预览场景只有捕获视图，于是该区段只有 4 个条目，视图却仍按 complex-special 分类和光照，结果是成块的 tile 没有光照。普通正 glint 材质出现完全相同的缺块，确认不是神经代码的问题。修复：`Substrate.cpp` 计算偏移时同时考虑当前视图的 mask。修复前神经材质捕获的能量只有教师的 25%，修复后 97.7%。

实测：`M_Teacher_OpenPBR` 512 对、128² 分辨率，捕获耗时 3.5 秒，UV 校验误差 0.0005，曝光系数 1.0。

## 4. 训练与导入

- `Scripts/NeuralAppearance/train_from_capture.py`：潜纹理 MLP（与实验室模型同结构：4 通道 32×32 潜平面，2×32 隐藏层，Exp 输出）。损失在辐亮度空间比较 `f·cosθi` 与捕获值（log1p L1），避免掠射角除以 cos 放大噪声。最后 10% 的捕获对作为留出集。
- 输出 `Content/Data/Captured/<Name>/manifest.json` 和潜平面 PNG。
- `ImportCapturedModel(<Name>)`：C++ 解码 PNG 为 BGRA8 线性纹理，生成模型和网络纹理，把模型加入 Project Settings › Neural BSDF 的槽位列表并重建 atlas。
- `CreateNeuralSubstrateInstance(<Name>)` 生成选择该槽位的 `MI_NeuralSubstrate_<Name>`。

## 5. 对比

- `compare_captures.py`：用同一种子再捕获一次神经材质，两份捕获按对逐像素比较，输出 `report.json`（MAE、相对 L1、每对 PSNR、能量比）和最差/中位数对的对照图（参考 | 神经 | 差异×4）。度量范围：单方向光照下平面上的直接光，不含 GI、反射、阴影与曲率。
- `BuildPairedComparison`：教师与神经材质并排放在同一场景（太阳、两盏点光、投影横杆），用于目视检查阴影和多光源下的表现。

## 6. 结果：OpenPBR 教师（2026-10-18）

教师 `M_Teacher_OpenPBR`：OpenPBR 金属（铜色）/ 青色漆条纹、coat 条带（coat 粗糙度 0.12）、fuzz 区域，空间周期为 UV 的一半。捕获 512 对 × 128²，有效像素约 213 万。

| 阶段 | 结果 |
|---|---|
| 捕获 | 3.5 秒；UV 校验误差 0.0005；曝光系数 1.0 |
| 训练（CPU，6000 步，batch 16384） | 32 秒；训练集辐亮度相对 L1 12.0%，留出集 9.9%，log MAE 0.016 |
| 导入 | `OPBR_Latent` 分到槽位 2，`MI_NeuralSubstrate_OPBR_Latent` |
| 引擎内同路径对比（同种子 512 对） | 相对 L1 11.8%，能量比 0.977，中位数 PSNR 22.7 dB |
| 按视角拆分 | 掠射（cosθo < 0.25，95 对）中位相对 L1 37%、PSNR 16.5 dB；其余 417 对中位相对 L1 12.8%、PSNR 25.1 dB |

引擎内对比和 Python 留出集误差一致（11.8% vs 9.9–12.0%），说明从训练到 Substrate 延迟光照的整条链路没有额外损失，误差来自模型容量和数据。

场景对比（`L_NeuralCaptured_OPBR`，太阳 + 两盏点光 + 投影横杆）：

- 开启 Lumen：教师的铜色金属明显更亮。原因是神经材质只接管直接光，间接光和反射走代理 Slab（非金属、反照率 0.3/0.2/0.12），金属区域差距最大。
- 关闭 Lumen GI 和反射：两者接近，阴影带、点光高光、条纹布局一致；剩余差异集中在金属 / coat 区域靠近轮廓的掠射角，与捕获指标一致。
- 截图与报告：插件 `Saved/Benchmarks/OPBR_Latent/`（`report.json`、`contact_sheet.png`、`scene_full_lumen.png`、`scene_direct_only.png`）。

## 7. 质量方面的后续工作

1. **代理参数逐 texel 拟合**（Roadmap M4，已完成）：拟合到网络的 DiffuseAlbedo / F0 / F90 / 粗糙度写成代理纹理，Lumen 和反射与神经直接光基本一致，见 [M4 报告](/projects/neural-bsdf-perf/milestones/m4-indirect-proxy/)。
2. **掠射角**：增加掠射方向的采样比例，或在损失中按 cosθo 重新加权；32 宽的网络对掠射 Fresnel + coat 的表达不足时，考虑加宽或换 QTP。
3. **真实材质**（Roadmap M3）：换成 Automotive Substrate Materials 中的车漆、皮革、金属，需要更高分辨率潜平面（见第 8 节）。

## 8. 尚未覆盖

- 运行时已有全屏基准与 GPU Trace（[性能报告](/projects/neural-bsdf-perf/performance/)）；编译期（permutation / PSO 数、编译时间）和内存指标仍未接入，归入 Roadmap M3。
- atlas 要求所有特征平面同尺寸（当前 32×32）；真实纹理材质需要更高分辨率潜平面，须在网络纹理头中记录每模型平面尺寸（引擎 shader 改动，会触发全局重编）。
- 仅潜纹理 MLP 支持从捕获训练；QTP 待接入。
- 32×32 潜平面只能表达低频空间变化；glint、法线贴图等高频细节需要更大的潜平面或不同编码。
