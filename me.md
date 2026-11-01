---
layout: page
title: 个人
permalink: /me/
nav: me
hide_title: true
body_class: me
---
{% comment %}
  TODO(补充) —— 个人页还可以放这些容易展示的内容，补了再加：
  1) 一张头像或照片、所在地；
  2) 一两句更个人化的介绍（兴趣、做事方式）；
  3) 开源贡献、获奖、演讲或文章的链接；
  4) 3DGS 论文笔记、AI 原生游戏参考页做成可公开的版本后，放在“正在关注”里。
{% endcomment %}
## 关于我
图形渲染与 GPU 优化方向的工程师。目前在腾讯做游戏引擎开发，主要在 Unreal Engine 里做渲染特性、性能与资源优化和调试工具；业余研究神经材质，以及用 AI 辅助引擎研发与排障。

教育：中国科学院大学，计算机视觉与计算机图形（硕士，2022–2025）；中国海洋大学，电子信息（本科）。

## 现在在做
- **[神经材质（Neural BSDF）在 UE 的适配与优化]({{ '/projects/neural-bsdf-perf/' | relative_url }})**：把神经材质接入 Unreal Engine，并用可复现的 GPU 基准和回归检查去度量它的开销。
- **[AI 辅助的 UE 研发与排障体系]({{ '/projects/ue-ai-infra/' | relative_url }})**：AI 研发基建加自动化排障工作流，让问题从发现到定位尽量由工具串起来。

## 数字速览
<div class="stats">
  <div class="stat"><b>190</b><span>份 GPU 基准报告</span></div>
  <div class="stat"><b>33</b><span>个 2048px 实验</span></div>
  <div class="stat"><b>4</b><span>套测量协议</span></div>
  <div class="stat"><b>5%</b><span>回归检查容差</span></div>
</div>

## 技术栈
<p class="chips-line">
  <span class="tag">Unreal Engine</span><span class="tag">C++</span><span class="tag">HLSL / GLSL</span><span class="tag">Python</span><span class="tag">GPU 性能分析</span><span class="tag">Shader 优化</span><span class="tag">移动端渲染</span><span class="tag">RenderDoc</span><span class="tag">Unreal Insights</span><span class="tag">Nsight Graphics</span>
</p>

## 联系
- GitHub：[bolin12](https://github.com/{{ site.minima.social_links.github }})
- 邮箱：{{ site.data.resume.email }}
- 简历：[中文]({{ '/resume/' | relative_url }}) · [English]({{ '/en/resume/' | relative_url }})
