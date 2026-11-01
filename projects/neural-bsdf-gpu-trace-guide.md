---
layout: page
title: GPU Trace 方法手册
permalink: /projects/neural-bsdf-perf/gpu-trace-guide/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
---
更新：2026-10-21。本文回答：怎么用 Nsight Graphics 的 GPU Trace 测神经 BSDF 的性能——环境、录制、读法，以及我踩过的坑。结果见[性能报告]({{ '/projects/neural-bsdf-perf/performance/' | relative_url }})。这是在 UE + D3D12 + NVIDIA（Ada）上的经验，其他平台的命名可能不同。

## 1. 环境（一次性设置）

- **GPU 性能计数器权限**：NVIDIA 控制面板 → 桌面 → 启用开发者设置 → 开发者 → 管理 GPU 性能计数器 → 允许所有用户访问。否则 GPU Trace 报 "GPU Performance Counters unavailable"。
- **编辑器后台限帧**：编辑器偏好 → 常规 → 性能 → 关闭「Use Less CPU when in Background」。这一步很容易没有真正保存，所以更稳妥的做法是每次启动都加参数（原因见第 6 节的案例）：

  ```text
  -ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False
  ```

- **GPU 时钟**：NVIDIA 控制面板 → 管理 3D 设置 → 程序设置 → UnrealEditor.exe → 电源管理模式 → 「Prefer maximum performance」。锁屏时 GPU 停在空闲时钟，不要在锁屏状态下测时间。

## 2. 录制
用编辑器而不是 `-game`：shader 已编译、相机就是视口，可以精确设置。命令（`<...>` 换成你自己的路径）：

```text
ngfx.exe --activity "GPU Trace Profiler" ^
  --exe "<UnrealEditor.exe>" --dir "<UnrealEditor.exe 所在目录>" ^
  --args "<项目>.uproject -dx12 -noxgeshadercompile -ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False" ^
  --output-dir "<输出目录>" ^
  --no-timeout --start-after-ms 120000 --limit-to-frames 1 ^
  --architecture Ada --metric-set-name "Throughput Metrics" ^
  --real-time-shader-profiler --auto-export
```

- `bThrottleCPUWhenNotForeground=False`：除非确认编辑器偏好里已关闭并保存，否则**必须**加。
- `--no-timeout`：**必须**。编辑器帧较大，默认超时会在导出阶段中断，只留下 `.ngfx-gputrace`、没有 `BASE/*.xls` 表格。
- 输出目录必须事先存在，否则 ngfx 报 "No such output directory" 并退出。
- `--start-after-ms`：给编辑器启动、打开关卡、设置相机留出时间。
- 不建议开 `--multi-pass-metrics`：会额外回放二十多遍，导出更容易超时；单遍指标加 PC 采样已经足够。
- 已有一个编辑器在运行时，要让两个实例的自动化端口不冲突。
- 需要读寄存器数时，录制时关闭 shader 符号和 ExtraData（第 7 节会说明原因）。

## 3. 固定场景，用对照说话

- **固定相机**：打开同一个关卡、固定相机位置与朝向，两份 trace 的屏幕面积才相同。
- **有无对照**：在同一相机下，录制前从内存中的关卡移除被测物体（不保存地图），录两份，按范围名称对齐求差。
- 编辑器帧包含 Slate、编辑器图元合成、TSR 上采样，所以**只用差值说话**，绝对耗时以全屏基准为准。
- 记录被测的代码版本：trace 里跑的可能是工作区里还没提交的代码。

## 4. 读 GPU Trace（Nsight 界面）
### 4.1 界面分区

| 区域 | 内容 | 回答什么 |
|---|---|---|
| 左上：事件列表 | 这一帧所有 D3D12 调用，按 UE 标记折叠成树；Δt 列是 GPU 耗时 | 这一帧发了哪些命令 |
| 中间：时间轴 | 队列、提交、命令列表、PSO、Action、标记，以及下方的指标曲线 | 什么时候跑了什么、硬件当时多忙 |
| 右上：选区面板 | Summary（吞吐、warp 占用）、Metrics（全部计数器）、Shader Warp Occupancy、Trace Information | 选中范围内的平均值 |
| 下方中间：Instruction Mix | 指令类别占比（FP32、FP16、整数、逻辑等），分采样数和指令数 | 执行的是哪类指令 |
| 下方右侧：着色器分析 | Flame Graph、Top-Down、Bottom-Up、Hotspots、Shader Pipelines | 哪个 shader、哪条指令最热，为什么停 |

用法：在时间轴的 Markers 行点一个块（例如 Lights），右侧和下方面板就切换到这个范围。没有 shader 调试符号时有黄条提示 "Missing Debug Info"：Shader Source 不可用，热点只显示指令地址（开启方法见第 7 节）。

### 4.2 时间轴的两套层级
API 执行层级（GPU 怎么执行）：

```text
Frame（以 Present 为界）
└─ Queue（3D / Compute / Copy）
   ├─ Synchronization：提交之间的 Fence Signal / Wait
   └─ Submit：一次 ExecuteCommandLists，可包含多个命令列表
      └─ Command Buffer：一个 ID3D12CommandList
         └─ Pipeline Range：两次 SetPipelineState 之间
            └─ Action：Draw / Dispatch / ExecuteIndirect / Clear / Copy
```

- D3D12 的 PSO 状态不跨命令列表保留，所以 Pipeline Range 一定在某个 Command Buffer 里面。
- Action 不全是 draw：Substrate 按 tile 分类后的光照用 `ExecuteIndirect`，阴影投射用 `Dispatch`；Clear 和 Copy 不使用 PSO。

标记层级（引擎认为这些工作是什么）：Markers 行是 UE 用 `BeginEvent` / `EndEvent` 打的软件标签，例如 SceneRender → RenderGraphExecute → Scene → RenderDeferredLighting → Lights → DirectLighting。它和 API 层级相互独立，可以跨越多个命令列表和提交。分析时用标记找到 pass，再看它覆盖了哪些 Action 和 PSO。

| 行 | 看什么 |
|---|---|
| Frames | 帧总时长与 active 时长之差：GPU 空闲多，瓶颈可能在 CPU 端或 Present |
| GPU Contexts | 多设备或多上下文时才有意义 |
| 3D / Compute / Copy Queue | 各队列的工作；对照 3D 和 Compute 队列，看 async compute 是否真的并行 |
| Synchronization | 两段工作之间的空隙是否来自等待 |
| Submits / Command Buffers | 提交次数和大小、并行录制的命令列表怎么排布 |
| Pipeline Ranges | PSO 切换频率、哪个 PSO 持续最久 |
| Actions | 单个 draw 或 dispatch 的耗时 |
| Markers | 把硬件时间对应回引擎 pass，最常用 |
| User Ranges | 应用自定义范围，UE 一般不写 |

D3D12 与 Vulkan 对照：

| D3D12 | Vulkan |
|---|---|
| Direct / Compute / Copy Queue | Graphics / Compute / Transfer Queue |
| `ExecuteCommandLists` | `vkQueueSubmit` |
| `ID3D12GraphicsCommandList` | `VkCommandBuffer` |
| `SetPipelineState` | `vkCmdBindPipeline` |
| `DrawInstanced` / `Dispatch` | `vkCmdDraw` / `vkCmdDispatch` |
| `ExecuteIndirect` | `vkCmdDrawIndirect` / `vkCmdDispatchIndirect` |
| Fence | Fence / Timeline Semaphore |
| `BeginEvent` / `EndEvent` | `vkCmdBeginDebugUtilsLabelEXT` |

### 4.3 指标曲线与排查顺序
时间轴下方的曲线说明当时硬件被用得怎么样；右侧 Summary 的数字是这些曲线在选区内的平均值。平均值会把不同性质的工作混在一起（例如 Lights 里的阴影投射和光照），需要看曲线或缩小选区。

| 组 | 行 | 回答什么 |
|---|---|---|
| A. 总览 | GPU Active、Unit Throughputs、Clock Frequencies | GPU 是否在工作、哪个单元最忙、频率是否稳定 |
| B. 着色器（SM） | SM Warp Occupancy、Per Shader Warp Occupancy、Warps Launched、Warp Can't Launch、Range-Avg. Warp Latency、SM Instruction Throughput、SM Warps Stalled at Issue Stage | shader 是否跑满、为什么放不下更多 warp、warp 在等什么 |
| C. 内存 | L1TEX Hit Rate、L2 Bandwidth、L2 Hit Rates、VRAM Bandwidth | 是否在等数据、缓存命中如何 |
| D. 前端与同步 | FE Stalls、FE Pipeline Stalling Commands | 是否有 barrier、等待空闲等命令把管线排空 |
| E. 几何与光栅 | PD Primitives In、ISBE / TRAM Allocation Stalled、Depth Test in LateZ Mode、World / Screen Pipe Throughput、Screen Pipe Data Flow、ROP Bandwidth、PCIe | 三角形数量、阶段间属性缓冲、深度测试是否退化为 Late Z、写出带宽、CPU 与 GPU 之间的传输 |

排查顺序：

```text
1. GPU Active 有缺口？
   有   → 先查同步和 CPU 端（D 组、Synchronization 行）
   没有 ↓
2. Unit Throughputs 哪条最高？
   ├─ SM 高（>60–70%）            → 计算受限：SM Instruction Throughput、Warps Stalled
   ├─ L2 / VRAM / L1TEX 高        → 内存受限：C 组的命中率与带宽
   ├─ World / Screen Pipe、ROP 高 → 几何或光栅受限：E 组
   └─ 都不高                      → 延迟或占用受限：SM Warp Occupancy、Warp Can't Launch、FE Stalls
3. Clock Frequencies：确认没有降频，否则不同 trace 的耗时不可比
```

神经光照分析常用 6 行：GPU Active、Unit Throughputs、SM Warp Occupancy、Per Shader Warp Occupancy、Warp Can't Launch、SM Warps Stalled at Issue Stage。E 组与全屏 tile 光照关系不大，可以折叠；用行右侧的图钉把常用行固定到顶部。

**Warp Can't Launch** 把「新 warp 无法启动」的原因分开计数（寄存器分配、共享内存、warp 槽位等），对应计数器形如 `tpc__warp_launch_cycles_stalled_shader_ps_reason_register_allocation`，和 SM Warp Occupancy 一起回答「为什么占用率低」。注意它的百分比容易饱和，比较时看**周期数**（例子见性能报告 4.5 节）。

### 4.4 停顿原因术语（PC 采样）

| 名称 | 含义 | 常见原因与方向 |
|---|---|---|
| Selected | 本周期被发射 | 正常工作 |
| Not Selected | 已就绪，但调度器选了别的 warp | 本身不是问题；占比高说明执行单元繁忙 |
| No Instruction | 等待取指 | 指令缓存未命中（代码太大、跳转多）；减少展开、拆分变体 |
| Math Pipe Throttle | 等待数学执行单元空闲 | 算术吞吐饱和；减少指令（打包、低精度、点积指令） |
| Short Scoreboard | 等待 MIO 类操作的结果 | 共享内存、特殊函数（`exp`、`rcp` 等）、部分常量读取 |
| Long Scoreboard | 等待 L1TEX 类操作的结果 | 显存、纹理、local memory（寄存器溢出）；改善访问局部性或减少读取 |
| Wait | 固定延迟的依赖 | 指令间依赖链太长 |
| Tex Throttle | 纹理单元队列已满 | 纹理请求过多 |
| Dispatch Stall | 发射阶段冲突 | 通常占比小 |
| Barrier / Membar | 等待同步或内存屏障 | 计算 shader 中的同步 |
| Misc | 其他 | — |

占用率（能驻留多少 warp）和停顿原因（已驻留的 warp 在等什么）是两个维度：占用率低时，延迟更难被其他 warp 掩盖，各种停顿的影响都会放大。**寄存器数决定占用率上限**：Ada 每个 SM 有 65536 个寄存器、最多 48 个 warp，每线程 r 个寄存器时最多驻留 ⌊65536 / (32 × r)⌋ 个 warp：

| 每线程寄存器数 | 最多驻留 warp 数 |
|---|---|
| 168 | 12 |
| 128 | 16 |
| 96 | 21 |
| 64 | 32 |

## 5. 常见问题

- **导出范围的粒度**：指标表只到中等深度的标记（例如每盏灯），单个 `RenderLight` 绘制没有独立指标；需要更细时用有无对照扣除，或在 Nsight 界面里选中单个 Action。
- **关闭 ExtraData 后管线没有名字**：用时间线对应。`SetPipelineState` 参数里的 `objectLink.Accessor` 就是 `pipeline-N` 的编号；Substrate 每盏灯 4 次绘制，对应 4 种 tile 排列。
- **shader 哈希随设置变化**：开关 `r.Shaders.ExtraData` 会改变哈希，不同设置录的 trace 不能按哈希对应，要按 tile 和代码体积对应。
- **开启 shader 符号后读不到寄存器数**：我用的 MCP 读取工具解码二进制元数据时报错，导出的表格不受影响。录制时关闭符号和 ExtraData 可以避开。

## 6. 案例：编辑器在后台只有约 3 fps（2026-10-20）
**现象**：录到的每一帧约 333 ms，几乎全是 `RenderGraphExecute - UpdateAllPrimitiveSceneInfos`，没有 `SceneRender`，视口和基准捕获都不在帧内。

**原因**：编辑器不在前台时被「Use Less CPU when in Background」限帧。引擎里负责取最大帧率的函数 `UEditorEngine::GetMaxTickRate`（`EditorEngine.cpp`）在 `ShouldThrottleCPUUsage()` 为真时返回 3 fps，正好 333 ms 一帧，期间 GPU 几乎空闲。和 Nsight、shader 符号、神经 BSDF 的改动都无关。

**排查证据**：

1. 不挂 Nsight 也是 3 fps：23 秒内日志帧号 531 → 600。
2. 编辑器在等而不是在忙：进程只占约 0.05 个 CPU 核，GPU 210 MHz、clock event reason 为 Idle。
3. 设置实际没关：读 `EditorPerformanceSettings` 的默认对象得到 `bThrottleCPUWhenNotForeground = true`，各级 `EditorSettings.ini` 中都没有这个键。
4. 前台是别的程序；把编辑器窗口置顶（topmost）不改变前台归属，所以置顶试验无效。

**修复**：启动参数加 `-ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False`，只对这一次启动生效。加上后编辑器在后台、挂着 Nsight 时约 85 fps。

这个案例的教训：**先验证测量环境本身**，再怀疑自己的代码。

## 7. Shader 调试符号（看源码行）
默认 UE 编译的 shader 不带符号，Nsight 只能显示指令地址。UE 端在 `ConsoleVariables.ini` 或项目的 `DefaultEngine.ini` 的 `[SystemSettings]` 里设置：

```ini
r.Shaders.Symbols=1
r.Shaders.ExtraData=1
```

- `r.Shaders.Symbols=1` 等于同时打开 `r.Shaders.GenerateSymbols` 和 `r.Shaders.WriteSymbols`。DXC 以 `-Zi` 生成 PDB，再用 `-Qstrip_debug` 从二进制中剥离，单独写到一个符号目录。符号不改变生成的代码，不影响性能测试。
- `r.Shaders.ExtraData=1` 可选：附带 shader 名称，抓帧工具里更易读；会改变 shader 哈希。
- **不要**为性能分析设置 `r.Shaders.Optimize=0`：它改变生成的代码，测出的性能失真。
- 代价：第一次启动重编全部 shader；符号目录占用数 GB。必须在启动时生效。

Nsight 端：Tools → Options → Search Paths → **Separate Shader Debug Information (.lld / .pdb)**，添加符号目录，Search sub-directories 设为 Yes。如果提示找不到源文件，再在 **Shader Source** 中加入引擎的 `Shaders` 目录和项目的 `Intermediate/ShaderAutogen`。打开符号后要重新录制。
