---
layout: page
title: "UE 神经外观项目"
permalink: /projects/neural-bsdf-perf/
body_class: resume
nav: projects
side_title: 神经材质
---
更新：2026-11-01。本页回答：这个项目是什么、做到哪了、文档在哪里、从哪里开始读。

个人项目：在 UE 中做一套以性能为核心、能用于游戏的神经外观（神经材质）系统，并用测量数据证明它比原方案划算。实现与资产在引擎的实验性插件 `NeuralAppearanceLab` 里，一个独立的 UE 项目只作为编辑器宿主；论文 PDF 与研究工程保存在本地，不随站点发布。

**诚实的结论：** 到目前为止，神经材质还没有证明自己比原方案划算（见[性能报告](/projects/neural-bsdf-perf/performance/)与[里程碑总览](/projects/neural-bsdf-perf/milestones/)）。

## 当前状态

| 方面 | 现状 | 见 |
|---|---|---|
| 阶段 | M0–M2、M4 完成；M3 第一轮完成（对 OpenPBR 教师不划算），第二轮等待 Automotive 资产；M5 部分完成（tensor core 需要预览 SDK） | [里程碑报告一览](/projects/neural-bsdf-perf/milestones/) |
| 接入 | 神经 BSDF 接入 Substrate 延迟光照（独立标志与逐像素数据，不需要 glint），接收阴影与多光源；间接光使用拟合到网络的逐 texel Slab 代理 | [系统架构](/projects/neural-bsdf-perf/architecture/) |
| 质量 | 以 OpenPBR 多层材质为教师，同路径误差 11.8% | [捕获与对比](/projects/neural-bsdf-perf/capture-and-comparison/) |
| 性能 | 2048² 全屏：神经 latent 约 16 ms、QTP 约 12.5 ms，完整 OpenPBR 约 8 ms；瓶颈是 168 寄存器 / 线程导致的低占用率 | [性能报告](/projects/neural-bsdf-perf/performance/) |
| 下一步 | 把神经求值从 `DeferredLightPixelMain` 拆成独立 pass；之后是间接光适配 | [性能报告](/projects/neural-bsdf-perf/performance/) 第 6 节 |

## 文档目录

左侧的目录树与下面一一对应。

| 分组 | 页面 | 内容 |
|---|---|---|
| 设计 | [系统架构](/projects/neural-bsdf-perf/architecture/) | 当前系统：模块、BSDF 契约、图集、Substrate 接入、求值器、命令与限制 |
| | [代码导读](/projects/neural-bsdf-perf/code-guide/) | 本项目与研究仓库的代码怎么读 |
| 里程碑 | [里程碑总览](/projects/neural-bsdf-perf/milestones/) | M2–M5 的一览，以及被推翻的判断和项目现在的位置 |
| | M2 / M3 / M4 / M5 | 各里程碑的独立报告，见左侧目录 |
| 性能 | [性能报告](/projects/neural-bsdf-perf/performance/) | 结论、各轮结果、瓶颈分析、下一步 |
| | [GPU Trace 手册](/projects/neural-bsdf-perf/gpu-trace-guide/) | 工具、基准、录与读 GPU Trace |
| | [基准与回归](/projects/neural-bsdf-perf/benchmark/) | 固定环境的基准、190 份历史报告归档、回归检查 |
| | [捕获与对比](/projects/neural-bsdf-perf/capture-and-comparison/) | 教师材质、引擎内捕获、训练、同路径对比 |
| 规划 | [路线图](/projects/neural-bsdf-perf/roadmap/) | 定位、目标架构、M0–M5 计划与状态 |
| | [Demo 计划](/projects/neural-bsdf-perf/demos/) | Demo 计划与公开场景、资产清单 |
| | [项目历程](/projects/neural-bsdf-perf/history/) | 时间线、最早的 Custom 节点原型、已完成或被取代的计划 |
| 调研 | [全景与研究路线](/projects/neural-bsdf-perf/research/) | 游戏引擎各模块的神经技术地图、材质与光照边界、阅读顺序 |
| | [波动光学（调研）](/projects/neural-bsdf-perf/wave-optics/) | 调研，项目未涉及；神经外观与波动光学的边界 |
| 论文 | [论文笔记总览](/projects/neural-bsdf-perf/papers/) | 12 份论文与课程资料的逐篇解析 |

## 从哪里开始读

| 想知道 | 读 |
|---|---|
| 项目要做什么、做到哪了 | [路线图](/projects/neural-bsdf-perf/roadmap/) |
| 神经技术在游戏引擎各模块的全景，神经材质的位置 | [全景与研究路线](/projects/neural-bsdf-perf/research/) |
| GPU 基准与回归检查怎么做的 | [基准与回归](/projects/neural-bsdf-perf/benchmark/) |
| 现在多快、为什么慢、下一步改什么 | [性能报告](/projects/neural-bsdf-perf/performance/) |
| 怎么自己测一遍、怎么读 Nsight | [GPU Trace 手册](/projects/neural-bsdf-perf/gpu-trace-guide/) |
| 神经材质怎样接进 UE 的渲染、光照怎样作用于它 | [系统架构](/projects/neural-bsdf-perf/architecture/) |
| 这个项目是怎么一步步做到现在的 | [项目历程](/projects/neural-bsdf-perf/history/) |
| 误差怎么测、和教师差多少 | [捕获与对比](/projects/neural-bsdf-perf/capture-and-comparison/) |
| M2–M5 做了什么、测到什么、项目现在在哪 | [里程碑报告一览](/projects/neural-bsdf-perf/milestones/) |
| 接下来做哪些 demo、用什么资源 | [Demo 计划与资源](/projects/neural-bsdf-perf/demos/) |
| 某篇论文讲了什么 | [逐篇解析索引](/projects/neural-bsdf-perf/papers/) |
| 衍射、结构色能否神经化；Zorah / NvRTX 有没有神经材质 | [神经外观与波动光学](/projects/neural-bsdf-perf/wave-optics/) |

外部资料（论文 PDF 索引、本地研究仓库的状态说明、插件 README 与复现说明）保存在本地，不随站点发布。研究仓库中的工程已下载不等于已构建或复现，准备状态以各仓库自己的 README 为准。
