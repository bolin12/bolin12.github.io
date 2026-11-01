---
layout: page
title: "M3 报告：价值验证（第一轮：OpenPBR 教师）"
permalink: /projects/neural-bsdf-perf/milestones/m3-value-validation/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
group: 里程碑
order: 13
side_title: M3 价值验证
---
更新：2026-10-23。本文回答：神经材质相对“完整 Substrate”和“简化版”是否值得——误差、耗时、着色器、内存四个方面——用已有的 OpenPBR 教师测出的结果，以及这对项目方向意味着什么。路线图原计划用 Fab 的 Automotive Substrate Materials；资产尚未加入 Demo 工程，所以本轮先在 OpenPBR 教师上搭好并跑通整套流程，第二轮换真实材质时只需更换教师。


## 1. 结论

| 判断标准（路线图） | 本轮结果 |
|---|---|
| 神经版误差明显低于简化版 | **未达成**：神经版 11.8%，最优单 Slab（64²）9.8%；同为 32² 时神经版 11.8% 对单 Slab 12.9%，只略好 |
| 神经版耗时低于完整版 | **未达成**：2048² 全屏 latent 15.1 ms、QTP 11.4 ms，完整 OpenPBR 7.7 ms，单 Slab 3.5 ms |

对这个教师，神经材质既不比简化版准，也不比完整版快。原因不在实现细节，而在教师本身：

1. **这个 OpenPBR 教师接近“逐 texel 一个高光波瓣”**。程序化的金属 / 漆面条纹在每个 texel 上基本只有一种材质，单个 GGX 加漫反射就能表达大部分外观；逐 texel 拟合的 Slab 有 64×64×8 个自由参数，而神经版的空间信息只有 32×32×4 个潜变量。
2. **完整 Substrate 在这里并不贵**：OpenPBR 这一层组合在 Substrate 中是 complex tile，7.7 ms；神经版要逐灯运行一个 1000 多次乘加的网络。

所以本轮的意义是：建立了一套能给出“不值得”结论的测量流程，并指出神经材质要证明价值，必须用单 Slab 表达不了、完整 Substrate 又明显更贵的材质——多层车漆（金属片 + 清漆 + glint）、带各向异性的拉丝金属、彩色 glint，正是 Automotive 材质包的内容。

## 2. 三方的定义

| 方 | 材质 | 说明 |
|---|---|---|
| 完整版 | `M_Teacher_OpenPBR` | 引擎内置 OpenPBR Substrate 函数：金属（铜色）/ 青色漆条纹、coat（粗糙度 0.12）、fuzz 区域 |
| 简化版 | `MI_Slab_OPBR_Slab`（64²）、`MI_Slab_OPBR_Slab32`（32²） | 逐 texel 最优单 Slab：`fit_slab_from_capture.py` 直接拟合教师的引擎内捕获（DiffuseAlbedo、F0、F90、Roughness），无 glint 输入，所以落在普通 tile |
| 神经版 | `MI_NeuralSubstrate_OPBR_Latent`（latent MLP，32² 潜平面）；QTP 只参与耗时 | 直接光走网络，间接光走 M4 拟合的代理 |

关于“简化版”：路线图中的简化版指引擎的自动简化（`SCC_FullySimplified`、Material Baking）。Substrate 的完全简化只在光线追踪命中着色器、Lumen 表面缓存等内部路径使用，没有让 base pass 使用它的开关；这里改用“逐 texel 最优单 Slab”，它是任何“压成一个 Slab”的方法能达到的上限，对神经版而言是偏严格的对手。

## 3. 误差

同路径捕获对比（教师捕获 `OPBR_Teacher`：512 对方向、128²、种子 11；各方用相同的对重新捕获）：

| 方 | 相对 L1 | 中位 PSNR | 能量比 |
|---|---:|---:|---:|
| 简化：单 Slab 64² | **9.8%** | 25.2 dB | 1.010 |
| 简化：单 Slab 32² | 12.9% | 22.1 dB | 1.019 |
| 神经 latent | 11.8% | 22.7 dB | 0.977 |

拟合端的留出集误差（教师捕获最后 10% 的对）：单 Slab 64² 5.7%、32² 10.5%，神经 9.9%；引擎内的误差都更高一些，因为 Substrate 的 Slab 还带有能量守恒、多次散射补偿等拟合公式里没有的项。

Lumen 场景（`L_NeuralProxyCheck`，见 [M4 报告](/projects/neural-bsdf-perf/milestones/m4-indirect-proxy/) 第 4 节）中对教师的相对 L1：

| 光照 | 单 Slab 64² | 神经 + 拟合代理 | 神经 + 常数代理 |
|---|---:|---:|---:|
| 只有天光 | 10.4% | 19.0% | 65.9% |
| 太阳 + 天光 | 8.1% | 11.9% | 20.7% |

同一配置两次运行之间相差约 1.5 个百分点（M4 时神经 + 拟合代理为 10.5%），结论不受影响。

## 4. 耗时

2048² 全屏基准（1 方向光 + 2 点光，无阴影），三轮，每轮依次测各材质，中位数：

| 方 | GPU 时间 | 相对完整版 |
|---|---:|---:|
| 完整 OpenPBR | 7.75 ms | 1.00× |
| 单 Slab 64² | 3.50 ms | 0.45× |
| 单 Slab 32² | 3.44 ms | 0.44× |
| 神经 latent | 15.07 ms | 1.95× |
| 神经 QTP | 11.39 ms | 1.47× |

轮间差异：OpenPBR、Slab、QTP 小于 0.1 ms；latent 为 14.5–15.1 ms。

## 5. 着色器与内存

base pass 像素着色器指令数（`MaterialEditingLibrary.GetStatistics`，本机平台）：

| 方 | 像素指令 | 纹理采样 | 光照 tile |
|---|---:|---:|---|
| 完整 OpenPBR | 2711 | 0（程序化） | Complex |
| 单 Slab | 1098 | 2 | Simple / Single |
| 神经 | 1976 | 2 | Complex Special（光照着色器 168–214 寄存器，见 [M2 报告](/projects/neural-bsdf-perf/milestones/m2-storage-decoupling/)） |

base pass 的指令数不是瓶颈：时间几乎都花在延迟光照上，由 tile 类型和光照着色器决定。

PSO 与变体：神经材质的价值主张之一是“外观差异变成数据差异”——所有神经材质共用 `M_NeuralSubstrate` 一个父材质（一套着色器），换材质只换模型槽位和纹理。本轮只有一个教师，看不出这项差异；在 Automotive 这样有数十个不同 Substrate 材质的包上，应统计每种方案的材质着色器图数量和运行时 PSO 数。

内存（本例都很小）：

| 方 | GPU 数据 |
|---|---|
| 完整 OpenPBR | 无纹理 |
| 单 Slab 64² | 2 张 64² BC7 + mip，约 11 KB |
| 神经 | 潜平面 32² RGBA8 4 KB + 网络约 6.3 KB（fp32）+ 1.4 KB（fp16 打包），加 M4 的两张代理纹理约 11 KB |

## 6. 下一轮（Automotive 材质）

流程已经脚本化，换教师只需：

1. 在 Fab 获取 Automotive Substrate Materials 并加入 Demo（需要登录 Epic 账号并接受授权）。
2. 选 3–5 个代表材质：多层车漆（含金属片 / glint）、清漆金属、皮革、拉丝金属。
3. 对每个材质：`capture_material_brdf` 捕获教师 → `train_from_capture.py` 训练 → `fit_proxy.py` 拟合代理 → `import_captured_model`、`create_neural_substrate_instance` → `fit_slab_from_capture.py`、`create_slab_baseline` → `run_m3.py`。
4. 需要先解决的限制：特征平面统一 32×32（真实材质的纹理细节需要更高分辨率潜平面，见 [系统架构](/projects/neural-bsdf-perf/architecture/) 第 11 节）。

预期最能体现神经材质价值的是 glint 车漆和多层清漆：单 Slab 表达不了多个高光波瓣，完整 Substrate 的多 closure 成本又会随层数上升。如果在这些材质上结论仍然是“不值得”，项目方向应转向降低神经求值成本（M5）或只把神经材质用于最贵的少数材质。

## 7. 改动清单

| 位置 | 改动 |
|---|---|
| 插件 `Scripts/NeuralAppearance/fit_slab_from_capture.py` | 新增：逐 texel 最优单 Slab 拟合（直接拟合教师捕获） |
| `NeuralAppearanceEditorLibrary.h/.cpp` | `CreateSlabBaseline`：导入两张纹理，创建 `M_SlabFromTextures` 与 `MI_Slab_<Name>` |
| 编辑器工具 | `create_slab_baseline`、`material_statistics` |
| 插件 `Scripts/NeuralAppearance/run_m3.py` | 新增：三方的误差、耗时、着色器统计；启动时检查图集是否构建 |
| `run_lit_compare.py` | 可选加入简化版 |
| `NeuralBSDFAtlas.h/.cpp` | 修复：启动时 GPU 资源未就绪会让图集构建失败、神经材质读空图集（第一次 M3 测量因此作废），现在每 0.5 秒重试直到成功，失败记为 Error |
