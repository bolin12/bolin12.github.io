---
layout: page
title: SIGGRAPH 2026 高斯泼溅:论文速览与工程判断
permalink: /projects/3dgs-survey/
body_class: resume
---
<p class="note">（草稿骨架，未发布。把这个文件从 drafts/ 移到 projects/ 即可上线。内容来自你 D:\3dgs 里的论文笔记；括号处是待你补充的部分。公开笔记里复述论文要点前，请确认只用自己的话概括，不大段摘抄原文。）</p>

## 为什么做这件事
<span class="note">（建议补：你为什么关注 3DGS，和游戏生产、渲染管线的关系是什么，想回答什么问题。）</span>

## 总体趋势
<span class="note">（来自笔记第 1 节，建议压缩成 3–5 句你自己的判断。）</span>

## 重点论文与工程判断
从 23 篇里挑出对游戏与实时渲染最相关的几篇，每篇只写三件事：解决什么问题、核心思路、**放进引擎我会怎么看**。

- **Hybrid Gaussian Wang Tiles**（类别感知的创作与渲染）：<span class="note">（待补你的判断）</span>
- **Structure-Aware Densification**（更快收敛）：<span class="note">（待补）</span>
- **Gaussian Point Splatting**：<span class="note">（待补）</span>
- **SHARP-GS**（超高分辨率的可扩展渲染管线）：<span class="note">（待补）</span>
- **A LoD of Gaussians**（外存训练与渲染，超大场景）：<span class="note">（待补）</span>
- **Mobile3DGS³**（移动端：超采样与插帧）：<span class="note">（待补）</span>

## 我动手测了什么
<span class="note">（这一节决定整个项目的分量，建议至少做一项：选一个下载好的代码仓库跑起来，在固定场景下测量渲染耗时、显存、画质，最好和你的神经材质基准用同一套“固定环境加对照”的方法；也可以选与移动端或 LoD 相关的仓库，对应你的移动端优化背景。写清楚：测了什么、环境、结果、和论文声称的差距。）</span>

## 它和游戏生产怎么连接
<span class="note">（建议补：3DGS 资产进入引擎的流程、预算（面数、显存、帧时间）怎么管、和传统网格加材质、和神经材质相比各自的取舍。这是把“折腾”升级成“体系”的一段。）</span>

## 局限与下一步
<span class="note">（建议补。）</span>
