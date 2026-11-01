---
layout: page
title: "里程碑报告（M2–M5）"
permalink: /projects/neural-bsdf-perf/milestones/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
group: 里程碑
order: 10
side_title: 里程碑总览
---
更新：2026-10-23。本文回答：路线图 M2–M5 各做了什么、结论是什么、整体上项目现在处在什么位置、下一步该做什么。每个里程碑的设计、数据和推理在各自的报告里。


## 1. 一览

| 里程碑 | 判断标准 | 结果 | 报告 |
|---|---|---|---|
| M2 存储解耦 | 普通材质性能不受影响；关闭 glint 后神经材质照常工作 | 独立标志与逐像素数据，不需要 glint（关闭后逐像素一致）；逐灯光照快 11%。拆成独立光照绘制实测更慢，默认关闭 | [M2](/projects/neural-bsdf-perf/milestones/m2-storage-decoupling/) |
| M3 价值验证（第一轮，OpenPBR 教师） | 神经版误差明显低于简化版，耗时低于完整版 | 两项都未达成：最优单 Slab 9.8% 对神经 11.8%；神经 15.1 ms 对完整 OpenPBR 7.7 ms。第二轮需要 Automotive 资产 | [M3](/projects/neural-bsdf-perf/milestones/m3-value-validation/) |
| M4 间接光 | 开启 Lumen 时金属与清漆外观基本一致 | 达成：逐 texel 拟合代理，只有天光时误差 66.6% → 18.6%，太阳 + 天光 22.2% → 10.5%；清漆锐利反射仍弱 | [M4](/projects/neural-bsdf-perf/milestones/m4-indirect-proxy/) |
| M5 进阶 | 进一步降低耗时与显存 | 打包 fp16 把寄存器从 214 降到 168，但神经核自己慢 7%；tensor core 在本引擎不可用（只有预览 SDK）；NTC 需要先支持大潜平面 | [M5](/projects/neural-bsdf-perf/milestones/m5-advanced/) |

## 2. 被推翻的判断

| 判断 | 来自 | 推翻它的测量 |
|---|---|---|
| 神经核把 Complex Special 光照着色器推到 168 寄存器，拆出去普通光照就轻了 | M1 / R2 分析 | M2：去掉神经核后仍需约 162；单独的神经着色器反而 212–218 |
| 寄存器降下来神经求值就会快 | M2 之后的预期 | M5：寄存器 214 → 168、占用率 +40%，神经 latent 反而慢 7%（指令数增加） |
| 神经材质比“简化版”更准 | 路线图的定位 | M3：对 OpenPBR 教师，逐 texel 最优单 Slab 更准也更快 |
| 在任意光照场景中都能看出代理的好坏 | M4 第一次测量 | 没有天空的场景里间接光很弱，代理差异被网络误差和噪声淹没；需要间接光占主导的场景 |

## 3. 现在的位置与下一步

神经材质在本项目中目前**没有证明自己划算**：对已有的教师，它比完整 Substrate 慢一倍，也不比一张逐 texel 的单 Slab 准。已经完成的是让这个判断可信的全部基础设施：同路径捕获对比、A-B-A 基准、可解析的 GPU Trace、三方对比脚本、间接光代理。

下一步按优先级：

1. **M3 第二轮（需要先在 Fab 获取 Automotive Substrate Materials）**：多层车漆、glint、拉丝金属——单 Slab 表达不了、完整 Substrate 又更贵的材质，才是神经材质应当证明价值的地方。前置工作：图集支持更大的潜平面。
2. **如果第二轮成立**：降低神经求值成本的唯一明显手段是 tensor core（M5 第 3 节），需要升级到预览版 Agility SDK / DXC，宜在独立分支上试验。
3. **如果第二轮仍不成立**：把神经材质限定为少数最贵材质的离线 / 高端选项，或转向其他神经技术方向（[全景与研究路线](/projects/neural-bsdf-perf/research/)）。
