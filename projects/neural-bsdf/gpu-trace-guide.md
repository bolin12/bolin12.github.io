---
layout: page
title: "性能方法手册"
permalink: /projects/neural-bsdf-perf/gpu-trace-guide/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
group: 测量方法
order: 20
side_title: GPU Trace 手册
---
更新：2026-11-01。本文回答：怎么在本项目里测神经 BSDF 的性能——环境设置、跑基准、录 GPU Trace、读 GPU Trace 的关键几步。界面逐项介绍、第三方工具的编译细节这类内容不在这里展开，以 Nsight 官方文档为准。

## 1. 工具与环境

| 工具 | 用途 |
|---|---|
| Nsight Graphics（2026.3.1） | GPU Trace：硬件计数器、PC 采样、寄存器数 |
| RenderDoc（1.46） | 逐像素历史、shader 单步，需要时在编辑器里抓帧 |
| nsight-graphics MCP | 用结构化数据读取 GPU Trace，不必手动翻界面 |
| 编辑器 MCP | 打开关卡、设置视口相机、增删 Actor、跑基准与捕获 |

测量前的三项一次性设置：

- **GPU 性能计数器权限**：NVIDIA 控制面板 → 开发者 → 管理 GPU 性能计数器 → 允许所有用户访问。否则 GPU Trace 报 "GPU Performance Counters unavailable"。
- **编辑器后台限帧**：关闭编辑器偏好里的「Use Less CPU when in Background」；不想改设置时，每次启动加 `-ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False`。原因见 3.3。
- **GPU 时钟**：UnrealEditor.exe 的电源管理设为「Prefer maximum performance」。锁屏时 GPU 停在空闲时钟，不要在锁屏状态下测时间。

## 2. 跑基准

编辑器运行（带 MCP）时，用批量脚本测 4 种参考材质（Slab、OpenPBR、神经 latent、神经 QTP），2048²；另有 `capture` 做 latent 与 QTP 的 BRDF 捕获。要点：

- 测量前切到空地图，避免主视口与基准争抢 GPU。
- 对比一个开关（例如打包权重）时，用启动参数设置，并做 A-B-A：每次切换代码或开关都重启编辑器；shader 改动后的第一次启动要重编光照 shader，之后从缓存读取。
- 数值对比用对比脚本比较两次捕获；逐字节一致可以直接比较像素文件。
- 时钟记录在每次运行的汇总里；运行前若要等 shader 编译，采样器会把等待期间的空闲时钟也算进去，基准本身的计时不受影响。

测量方法的细节（R0 计时修正、比较规则）见 [性能报告](/projects/neural-bsdf-perf/performance/) 第 2 节。

## 3. 录 GPU Trace

用编辑器而不是 `-game`：shader 已编译、相机就是视口，可以用编辑器 MCP 精确设置。

### 3.1 启动与固定相机

用 `ngfx.exe` 的 "GPU Trace Profiler" 活动启动编辑器，关键参数：

- `--no-timeout`：**必须**。编辑器帧较大，默认超时会在导出阶段中断，只留下 trace 文件、没有导出表格。
- `--limit-to-frames 1`、`--start-after-ms`：只录一帧，并给编辑器启动、打开关卡、设置相机留出时间。
- `--metric-set-name "Throughput Metrics"` 加 `--real-time-shader-profiler`；不要开多遍指标，它会额外回放二十多遍，导出更容易超时。
- 输出目录必须事先存在。
- 要读寄存器数，启动加 `-dpcvars=r.Shaders.Symbols=0,r.Shaders.ExtraData=0`（见 3.2）。

之后用编辑器 MCP 打开对比关卡并固定相机（例如位置 (560, 0, 230)、俯仰 −14°、偏航 180°）。对照实验时，在同一位置移除神经物体（只改内存中的关卡，不保存），两份 trace 按范围名称对齐求差。

### 3.2 读取与常见问题

用 nsight-graphics MCP 打开导出目录。常用查询：每个 pass 多久（范围列表）、某个范围的吞吐和占用（范围摘要）、每个 shader 的 warp 占用、停顿原因与热点指令（PC 采样，按 shader 哈希过滤）、寄存器数与代码体积（管线列表里的代码块）。

- **多帧导出读不了**：多帧时表格每帧一列，复制一份只保留第一帧再读。所以建议只录单帧。
- **导出范围的粒度**：指标只到中等深度的标记（例如每盏灯），单个绘制没有独立指标；需要更细时用有无对照扣除。
- **开启 shader 符号后读不到寄存器数**：MCP 解码二进制元数据会报错，导出的表格不受影响；用上面的 `-dpcvars` 启动参数避开。
- **shader 哈希随设置变化**：开关 `r.Shaders.ExtraData` 会改变哈希，不同设置录的 trace 不能按哈希对应，要按 tile 和代码体积对应。

### 3.3 已解决：编辑器在后台只有约 3 fps（2026-10-20）

**现象**：录到的每一帧约 333 ms，几乎全是图元场景更新，没有场景渲染，视口和基准捕获都不在帧内。

**原因**：编辑器不在前台时被「Use Less CPU when in Background」限帧到 3 fps，期间 GPU 几乎空闲，和 Nsight、shader 符号、神经 BSDF 的改动都无关。

**证据**：不挂 Nsight 也是 3 fps；进程只占约 0.05 个 CPU 核，GPU 停在 210 MHz；用编辑器 MCP 读到该设置实际仍是 true（界面里关了但没有真正保存）。

**修复**：启动参数加上面的 `-ini:…=False`，只对这一次启动生效；加上后编辑器在后台、挂着 Nsight 时约 85 fps。

## 4. 读 GPU Trace

### 4.1 时间轴的两套层级

- **API 执行层级**（GPU 怎么执行）：Frame → Queue（3D / Compute / Copy）→ Submit → Command Buffer → Pipeline Range（两次 SetPipelineState 之间）→ Action（Draw / Dispatch / ExecuteIndirect / Clear / Copy）。Substrate 按 tile 分类后的光照用 `ExecuteIndirect`，阴影投射用 `Dispatch`。
- **标记层级**（引擎认为这些工作是什么）：UE 用 `BeginEvent` / `EndEvent` 打的软件标签，例如 SceneRender → RenderGraphExecute → Scene → RenderDeferredLighting → Lights → DirectLighting。它和 API 层级相互独立。分析时用标记找到 pass，再看它覆盖了哪些 Action 和 PSO。

用法：在时间轴的 Markers 行点一个块（例如 Lights），右侧的 Summary、Metrics、Shader Warp Occupancy 和下方的着色器分析面板就切换到这个范围。没有 shader 调试符号时有黄条提示，热点只显示指令地址。

### 4.2 排查顺序

时间轴下方的曲线说明当时硬件被用得怎么样；右侧 Summary 的数字是这些曲线在选区内的平均值。平均值会把不同性质的工作混在一起（例如 Lights 里的阴影投射和光照），需要看曲线或缩小选区。

```text
1. GPU Active 有缺口？
   有   → 先查同步和 CPU 端（前端停顿、Synchronization 行）
   没有 ↓
2. Unit Throughputs 哪条最高？
   ├─ SM 高（>60–70%）            → 计算受限：SM Instruction Throughput、Warps Stalled
   ├─ L2 / VRAM / L1TEX 高        → 内存受限：命中率与带宽
   ├─ World / Screen Pipe、ROP 高 → 几何或光栅受限
   └─ 都不高                      → 延迟或占用受限：SM Warp Occupancy、Warp Can't Launch、FE Stalls
3. Clock Frequencies：确认没有降频，否则不同 trace 的耗时不可比
```

神经光照分析常用 6 行曲线：GPU Active、Unit Throughputs、SM Warp Occupancy、Per Shader Warp Occupancy、Warp Can't Launch、SM Warps Stalled at Issue Stage。

**Warp Can't Launch** 把「新 warp 无法启动」的原因分开计数（寄存器分配、共享内存、warp 槽位等），和 SM Warp Occupancy 一起回答「为什么占用率低」。它的百分比容易饱和，比较时看周期数（例子见 [性能报告](/projects/neural-bsdf-perf/performance/) 第 4 节）。

### 4.3 停顿原因（PC 采样）

| 名称 | 含义 | 常见原因与方向 |
|---|---|---|
| Not Selected | 已就绪，但调度器选了别的 warp | 本身不是问题；占比高说明执行单元繁忙 |
| No Instruction | 等待取指 | 指令缓存未命中（代码太大、跳转多）；减少展开、拆分变体 |
| Math Pipe Throttle | 等待数学执行单元空闲 | 算术吞吐饱和；减少指令（打包、低精度、点积指令） |
| Short Scoreboard | 等待 MIO 类操作的结果 | 共享内存、特殊函数（`exp`、`rcp`）、部分常量读取 |
| Long Scoreboard | 等待 L1TEX 类操作的结果 | 显存、纹理、local memory（寄存器溢出）；改善访问局部性 |
| Wait | 固定延迟的依赖 | 指令间依赖链太长 |
| Tex Throttle | 纹理单元队列已满 | 纹理请求过多 |

占用率（能驻留多少 warp）和停顿原因（已驻留的 warp 在等什么）是两个维度：占用率低时，延迟更难被其他 warp 掩盖，各种停顿的影响都会放大。寄存器数决定占用率上限：Ada 每个 SM 有 65536 个寄存器、最多 48 个 warp，每线程 r 个寄存器时最多驻留 ⌊65536 / (32 × r)⌋ 个 warp（168 → 12，128 → 16，96 → 21，64 → 32）。

## 5. Shader 调试符号

默认 UE 编译的 shader 不带符号，Nsight 只能显示指令地址。要看源码行：UE 端设置 `r.Shaders.Symbols=1`（DXC 生成 PDB 并单独写出，符号不改变生成的代码，不影响性能测试），`r.Shaders.ExtraData=1` 可选（附带 shader 名称，但会改变哈希）；Nsight 端在 Search Paths 里加入符号目录。**不要**为性能分析设置 `r.Shaders.Optimize=0`，它改变生成的代码，测出的性能失真。代价是第一次启动重编全部 shader，符号占用数 GB；打开符号后要重新录制，并注意 3.2 中读不到寄存器数的问题。
