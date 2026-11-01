---
layout: page
title: "Taming Optimization Variance：让小型神经着色网络更稳定地训练"
permalink: /projects/neural-bsdf-perf/papers/taming-optimization-variance/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
group: 论文
order: 43
side_title: Taming 2026
mermaid: true
---
对应 PDF：`Taming_Optimization_Variance_SIGGRAPH2026.pdf`，共 9 页。本文页码均指 PDF 物理页，从 1 开始。更新：2026-10-18。

本文基于该本地 PDF；“原文方法”与“UE 接入推断”分开说明。图是帮助理解的流程示意，不是论文原图。

## 问题与全局流程

同样的小网络和训练数据，仅改变初始化，就可能得到明显不同的反射重建质量。加宽网络能改善训练，却会增加运行时推理成本。本文把更多探索放在离线训练阶段，最终仍只保留一个小模型。

```mermaid
flowchart LR
    I["初始化多个同尺寸网络实例"] --> B["共享训练样本；每实例先用小 batch"]
    B --> R["按损失排序"] --> C["分阶段淘汰较差实例"]
    C --> A["给存活实例增加 batch"] --> R
    C --> W["最后只剩一个实例"] --> RT["导出到常规单网络推理"]
```

图中的循环表示多阶段训练，不是运行时执行多个网络后平均。

## 三个改动为什么要一起看

PDF 3–4 页第 3 节分开讨论：直接训练多个实例、早期淘汰、batch size annealing。直接把模型复制 64 份并完整训练很贵；早期排序具有一定预测力，可以提前放弃较差候选；再让实例数下降时 batch 增大，以接近固定的网络求值预算。

示例计划是实例数 `64→16→4→1`，每实例 batch `1k→4k→16k→64k`。这些数来自论文配置，不是所有材料都必须使用的通用参数。训练算量相近，也不意味着数据生成、内存访问和调度的墙钟耗时必然完全相同。

第 5 节（PDF 7–8 页）另讨论高动态范围损失映射、激活函数和方向参数化。它们是改善拟合的额外选择，与多实例筛选是不同因素；不能把所有质量收益归给其中一个改动。

## 当前代码中的可核对配置

`multi_instance_training_small.json:9` 包含真实配置项 `"instance_schedule": [64, 16, 4, 1]`；同文件的数据生成部分设置 `batch_size_schedule` 和 `share_data_between_instances`。该文件包含注释，不能直接按严格无注释 JSON 理解。

BatchInstanceScheduler 负责按训练进度返回实例数和 batch；它本身不完成网络损失排序或裁剪全部逻辑。不要只看这个类就把整个淘汰算法当作已经读完。

## 一个具体案例

同一个带窄高光的釉面材质，用两层 16 宽的小解码器训练。单次初始化可能把高光拟合成过宽、过弱的响应。多实例方案在早期保留不同候选，再集中训练表现较好的实例；UE 最后加载的依然是一份两层 16 宽的网络。

## 阅读定位与结论边界

| PDF 页 | 关注内容 |
|---|---|
| 1–2 | 训练结果方差与问题背景 |
| 3–4 | 多实例、排序预测力、裁剪与 batch 调度 |
| 5–7 | 材质集、选择质量和训练耗时 |
| 7–8 | 损失、激活与输入参数化 |

论文的统计结论基于所测材质、网络和硬件；提前裁剪不保证每次都留下全部候选中最终最优的一个。更细的排名和消融数据见 [补充材料解析](/projects/neural-bsdf-perf/papers/taming-optimization-variance-supplement/)。

**UE 接入推断：**这是训练稳定性工具，不需要为了获得该收益而在 UE 中加入 64 网络运行时。先保持训练端与运行时架构、激活及参数化一致；训练改进不能解决引擎资产格式或光照接口不匹配。
