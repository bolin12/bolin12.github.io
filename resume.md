---
layout: page
title: 简历
permalink: /resume/
body_class: resume
---
[下载 PDF 版]({{ "/assets/resume.pdf" | relative_url }}) （PDF 尚未生成，用 Overleaf 编译后放到 assets/resume.pdf）

## 教育经历 （我调成了倒序，与工作经历一致，可改回）
<div class="entry"><span>中国科学院大学 · 硕士 · 计算机视觉 & 计算机图形</span><span class="when">2022.09 – 2025.06</span></div>
<div class="entry"><span>中国海洋大学 · 本科 · 电子信息</span><span class="when">2018.09 – 2022.06</span></div>

## 工作经历
<div class="entry"><span>腾讯 · 游戏引擎开发 （原文为"广州腾讯科技有限公司"，我简写了，正式投递可改回）</span><span class="when">2025.06 – 至今</span></div>

**渲染特性开发**
- Unreal Engine 渲染特性定制:调试视图、光束遮蔽、半透明阴影、灯光函数
- 引擎插件移植与多平台画质适配 （建议补：移植了哪些插件、覆盖哪些平台）

**性能与资源优化**
- 渲染与资源:骨骼剔除、Shader 变体清理、离线阴影压缩 （建议补数字：Shader 变体减少多少、GPU 耗时降低多少）
- 内存与加载:HLOD 卸载、纹理降级、资源流送分帧 （建议补数字：内存降低 X MB、加载时间缩短 X%）
- 多平台资产与材质分离,编辑器与运行时统一管理

**工具链与稳定性** （你说的"工具移植"，我改成这个名字，因为崩溃修复也归在这里，可改回）
- 调试与统计工具:模型面数、像素开销、场景资源统计 （建议补：谁在用、节省了多少排查时间）
- 定位并修复数值精度、资产导入、Shader 翻译、图形 API 相关崩溃;用 RenderDoc、Unreal Insights、ProfileGPU 分析渲染异常与性能瓶颈 （建议补：修复崩溃的数量或影响范围）

<div class="entry"><span>AI 研发基建:CodeGraph、UE Reviewer、UnrealMCP、TraceMCP、RenderTrail （体量较大，按你的想法单开一项）</span><span class="when">（建议补：起止时间）</span></div>
- 面向 Unreal Engine 的 AI 辅助研发工作流,覆盖代码审查、性能分析、问题定位 （建议补：你具体负责哪几个、使用规模、节省了多少时间）
- 探索自动化调试闭环,推动 AI 在引擎研发流程中的落地

<div class="entry"><span>腾讯 · 游戏引擎开发(实习)</span><span class="when">2024.03 – 2024.09</span></div>
- 把 Overdraw 调试视图移植到手机端(UE5.0 早期不支持),用于查看特效着色层数
- 开启移动端 VRS(可变着色率),降低着色压力

## 个人项目 （我把神经材质相关放在最前面，因为与图形岗位最相关，可调整）
<div class="entry"><span>神经材质 GPU 性能基准与回归体系 （新增，基于你的基准脚本，详见<a href="/projects/neural-bsdf-perf/">项目页</a>）</span><span class="when">2026.10 – 至今 （按最早一份基准报告 2026-10-18 推算，请核对）</span></div>
- 固定渲染环境并批量计时,用 nvidia-smi 采样 GPU 时钟识别降频;归档 190 份报告、33 个 2048px 实验、4 套测量协议
- 发现并处理两类"不可比":测量协议不同(1024px 逐帧约 109 ms 与 2048px 批量约 17 ms),以及会话漂移(未改动的对照材质在 7.7–8.8 ms 间波动约 15%);回归检查改用相对对照材质的耗时比值
- 钉基线加 5% 容差检查,超限返回非零退出码可接 CI;人为放大 15% 的数据被识别为 +14.0%

<div class="entry"><span>神经材质(Neural BSDF)在 UE 的适配与优化</span><span class="when">2026.06 – 至今</span></div>
- 将神经材质接入 UE 引擎并做性能优化 （原文只有一句，待展开。建议补：推理耗时、与 baseline 的对比、效果图、用了哪些优化手段，如 packed-fp16、tensor core 可行性评估等）

<div class="entry"><span>无状态 Vulkan 层新特性</span><span class="when">2026.07 – 至今</span></div>
- 在 UE VulkanRHI 中实现 NoGraphicsAPI 风格的公共 Root 地址参数模型,保留原 Renderer 与业务 Shader
- 完成真实图形 / 计算路径、生命周期与性能成本的对照验证 （建议补：这件事的目的和收益，如降低 CPU 侧绑定开销，并写出对照结果）

<div class="entry"><span>UE 开发自动化排障工作流</span><span class="when">2026.07 – 至今</span></div>
- **逻辑与画面层闭环**（原文偏长，我已精简，可核对）:运行时中间状态无法全量记录、日志方案需重启进程。用 Rewind 记录异常轨道终态,Checkpoint 保存关键检查点并迭代重放,windbg 记录异常流程,实现不停机的半自动 bug 排查闭环
- **渲染层数据结构化**:渲染 bug 涉及 RDG 与 GPU 层,综合 RDG 与截帧数据,以异常区域为起点定位资源或 Shader 问题,形成渲染侧排查闭环 （原文"最终窗口异常区域作为排查起点"表述不清，我按理解改写，请核对原意；建议补：用它定位过多少个真实问题）

（说明：原简历的“专业能力”栏已删除，工具和技术关键词已分散在各条经历里；网页版未放手机号和邮箱。以上括号内容是建议或待核对项，定稿前请逐条处理并删除括号。）
