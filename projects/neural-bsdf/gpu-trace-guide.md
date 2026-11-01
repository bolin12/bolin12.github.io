---
layout: page
title: "性能方法手册"
permalink: /projects/neural-bsdf-perf/gpu-trace-guide/
body_class: resume
nav: projects
parent: /projects/neural-bsdf-perf/
parent_title: 神经材质
group: 性能
order: 21
side_title: GPU Trace 手册
---
更新：2026-10-21。本文回答：怎么在本项目里测神经 BSDF 的性能——工具和环境、跑基准、录 GPU Trace、读 GPU Trace。


## 1. 工具与环境

### 1.1 工具

| 工具 | 版本 / 位置 | 用途 |
|---|---|---|
| Nsight Graphics | 2026.3.1，`C:\Program Files\NVIDIA Corporation\Nsight Graphics 2026.3.1\` | GPU Trace（硬件计数器、PC 采样、寄存器数） |
| RenderDoc | 1.46，`C:\Program Files\RenderDoc\` | 逐像素历史、shader 单步、资源查看（UE 的 RenderDoc 插件加载这一份） |
| nsight-graphics MCP | `<nsight-graphics-mcp 目录>`（社区项目 scarletfantasy，已审查代码） | 用结构化数据读取 GPU Trace |
| RenderDoc MCP | `<renderdoc-mcp 目录>` | 无界面读取 `.rdc` |
| 编辑器 MCP | `http://127.0.0.1:8000/mcp`；客户端 `Engine/Plugins/Experimental/NeuralAppearanceLab/Scripts/Tools/mcp_client.py` | 打开关卡、设置视口相机、增删 Actor、跑基准与捕获 |
| Python 环境 | `python`（含 numpy） | `compare_captures.py` 等脚本 |

两个分析 MCP 写在 `~/.claude.json` 的用户级 `mcpServers` 中。

RenderDoc MCP 需要用与本机 RenderDoc 相同版本的源码编译 `renderdoc.pyd`，否则读不了 UE 抓的 `.rdc`。2026-10-19 的构建做了这些本地修改（目录不是 git 仓库）：

1. `renderdoc/` 子模块拉取 `v1.46` 源码。
2. `build_and_install.ps1`：VS 2026（版本号 18）映射到 v145 工具集；设置 `VSPythonOverridePath`（RenderDoc 1.46 的 `python.props` 读这个变量，旧脚本只设 `RENDERDOC_PYTHON_PREFIX64`，会静默链接到自带的 Python 3.6）。
3. `mcpserver/pyproject.toml`：固定 `mcp[cli]>=1.0.0,<2`（MCP Python SDK 2.x 把 `FastMCP` 改了名）。
4. `mcpserver/src/renderdoc_mcp/util.py`：RenderDoc 1.46 把 `ActionDescription.previous/next` 改名为 `previousAction/nextAction`，`get_action` 因此报错。

### 1.2 一次性设置

- **GPU 性能计数器权限**：NVIDIA 控制面板 → 桌面 → 启用开发者设置 → 开发者 → 管理 GPU 性能计数器 → 允许所有用户访问。否则 GPU Trace 报 "GPU Performance Counters unavailable"。
- **编辑器后台限帧**：编辑器偏好 → 常规 → 性能 → 关闭「Use Less CPU when in Background」，并确认 `Engine/Saved/Config/WindowsEditor/EditorSettings.ini` 中出现 `bThrottleCPUWhenNotForeground=False`（2026-10-20 时这一步没有真正保存，见 3.5）。不想改设置时，每次启动加：

  ```
  -ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False
  ```

- **GPU 时钟**：NVIDIA 控制面板 → 管理 3D 设置 → 程序设置 → UnrealEditor.exe → 电源管理模式 → 「Prefer maximum performance」。锁屏时 GPU 停在空闲时钟，不要在锁屏状态下测时间。

## 2. 跑基准

方法、R0 的计时修正和比较规则见 [README.md](/projects/neural-bsdf-perf/performance/) 第 2 节。

编辑器运行（带 MCP）时：

```bash
python Engine/Plugins/Experimental/NeuralAppearanceLab/Scripts/NeuralAppearance/run_shading_benchmarks.py <prefix> bench capture
```

- `bench` 测 4 种参考材质（Slab、OpenPBR、神经 latent、神经 QTP），2048²；`capture` 做 latent 与 QTP 的 BRDF 捕获；`only=<名称>` 只跑其中一项。
- 测量前用 `SceneTools.load_level` 切到空地图 `/Engine/Maps/Entry`，避免主视口与基准争抢 GPU。
- 对比打包权重开关：用 `-ExecCmds="r.NeuralBSDF.PackedWeights 0"` 启动编辑器（编辑器 MCP 没有设置 cvar 的工具）。
- A-B-A：每次切换代码或开关都重启编辑器；shader 改动后的第一次启动要重编光照 shader，之后从 DDC 读取。
- 数值对比：

  ```bash
  python Engine/Plugins/Experimental/NeuralAppearanceLab/Scripts/NeuralAppearance/compare_captures.py --reference <参考捕获目录> --test <新捕获目录> --out <输出目录>
  ```

  捕获在插件 `Saved/Capture/<名称>/`；逐字节一致可以直接比较 `pixels.bin`。

- 时钟记录在 `<prefix>_summary.json`。如果运行前要等 shader 编译，采样器会把等待期间的空闲时钟也算进去（例如显示 345 MHz / P8），基准本身的计时不受影响。

## 3. 录 GPU Trace

用编辑器而不是 `-game`：shader 已编译、相机就是视口，可以用编辑器 MCP 精确设置。

### 3.1 启动

```bash
"C:/Program Files/NVIDIA Corporation/Nsight Graphics 2026.3.1/host/windows-desktop-nomad-x64/ngfx.exe" \
  --activity "GPU Trace Profiler" \
  --exe '<UE 根目录>\Engine\Binaries\Win64\UnrealEditor.exe' \
  --dir '<UE 根目录>\Engine\Binaries\Win64' \
  --args '"<项目目录>/<项目>.uproject" -dx12 -noxgeshadercompile -ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False' \
  --output-dir '<项目目录>\Saved\NsightTraces\<名称>' \
  --no-timeout --start-after-ms 120000 --limit-to-frames 1 \
  --architecture Ada --metric-set-name "Throughput Metrics" \
  --real-time-shader-profiler --auto-export
```

- `bThrottleCPUWhenNotForeground=False`：除非确认编辑器偏好里已关闭并保存，否则**必须**加，见 3.5。
- `--no-timeout`：**必须**。编辑器帧较大，默认超时会在导出阶段中断，只留下 `.ngfx-gputrace`、没有 `BASE/*.xls` 表格。
- 输出目录必须事先存在，否则 ngfx 报 "No such output directory" 并退出。
- `--start-after-ms`：给编辑器启动、打开关卡、设置相机留出时间。
- 不建议开 `--multi-pass-metrics`：会额外回放二十多遍，导出更容易超时；单遍指标加 PC 采样已经足够。
- 已有一个编辑器在运行时，加 `-ModelContextProtocolPort=8001` 避开 8000 端口，脚本里把 `mcp_client.URL` 改成 `http://127.0.0.1:8001/mcp`。
- 需要用 MCP 读寄存器数时，加 `-dpcvars=r.Shaders.Symbols=0,r.Shaders.ExtraData=0`（`Engine/Config/ConsoleVariables.ini` 目前打开了这两项），见 3.4。
- 在 Git Bash 中运行时，如果参数里有以 `/` 开头的 UE 包路径，需要 `export MSYS_NO_PATHCONV=1`，否则会被改写成 `C:/Program Files/Git/...`。

### 3.2 打开关卡、固定相机

```python
import mcp_client as m
S = 'editor_toolset.toolsets.scene.SceneTools'
m.tool(S, 'load_level', {'level_path': '/NeuralAppearanceLab/Maps/L_NeuralCaptured_OPBR'})
m.call('call_tool', {'toolset_name': 'EditorToolset.EditorAppToolset', 'tool_name': 'SetCameraTransform',
       'arguments': {'transform': {'location': {'x': 560, 'y': 0, 'z': 230},
                                   'rotation': {'pitch': -14, 'yaw': 180, 'roll': 0}}}})
```

对照实验时，在同一位置移除神经物体（只改内存中的关卡，不保存）：

```python
for name in ['Proto_Sphere_Neural', 'Proto_Preview_Neural']:
    for actor in m.tool(S, 'find_actors', {'name': name, 'tag': '', 'collision_channels': []})['returnValue']:
        m.tool(S, 'remove_from_scene', {'actor': actor})
```

### 3.3 输出与读取

`<output-dir>` 下有 `*.ngfx-gputrace` 和 `BASE/`（`FRAME.xls`、`GPUTRACE_FRAME.xls`、`GPUTRACE_REGIMES.xls`、`D3DPERF_EVENTS.xls`、`REPRO_INFO.xls`）。用 nsight-graphics MCP 的 `open_gpu_trace_export` 打开这个目录，常用工具：

| 问题 | 工具 |
|---|---|
| 每个 pass 多久 | `list_gpu_trace_ranges`（按名称路径对齐两份 trace） |
| 某个范围的吞吐和占用 | `summarize_gpu_trace_range` |
| 某个范围的任意计数器 | `list_gpu_trace_metrics`（`name_regex` 是 JavaScript 正则，不支持 `(?i)`） |
| 每个 shader 的 warp 占用 | `list_gpu_trace_shader_occupancy` |
| 停顿原因与热点指令 | `analyze_gpu_trace_pc_sampling`（按 `shader_hash` 过滤） |
| 寄存器数与代码体积 | `list_gpu_trace_shader_pipelines` 的 `codeBlocks[].registersPerThread / sizeBytes` |

### 3.4 常见问题

- **多帧导出读不了**：多帧时 `FRAME.xls`、`GPUTRACE_FRAME.xls` 每帧一列，`GPUTRACE_REGIMES.xls` 每个指标连续 N 列。复制一份，只保留第一帧：

  ```bash
  awk -F'\t' 'BEGIN{OFS="\t"}{print $1,$2}' src/BASE/FRAME.xls > dst/BASE/FRAME.xls          # GPUTRACE_FRAME.xls 同理
  awk -F'\t' 'BEGIN{OFS="\t"}{s=$1; for(i=2;i<=NF;i+=3) s=s OFS $i; print s}' \
      src/BASE/GPUTRACE_REGIMES.xls > dst/BASE/GPUTRACE_REGIMES.xls                        # 3 帧时步长为 3
  ```

  其余文件和 `.ngfx-gputrace` 原样复制。

- **导出范围的粒度**：`GPUTRACE_REGIMES.xls` 只到中等深度的标记（例如每盏灯），单个 `RenderLight` 绘制没有独立指标；需要更细时用有无对照扣除，或在 Nsight 界面里选中单个 Action。
- **开启 shader 符号后读不到寄存器数**：MCP 解码二进制元数据报 "chunk 0 has inconsistent uncompressed sizes"（提高 `NSIGHT_MCP_MAX_GPUTRACE_METADATA_MB` 仍失败）；导出的表格不受影响。用 `-dpcvars=r.Shaders.Symbols=0,r.Shaders.ExtraData=0` 启动可以避开。
- **关闭 ExtraData 后管线没有名字**：用时间线对应。`SetPipelineState` 参数里的 `objectLink.Accessor` 就是 `pipeline-N` 的编号；Substrate 每盏灯 4 次绘制，对应 4 种 tile 排列。
- **shader 哈希随设置变化**：开关 `r.Shaders.ExtraData` 会改变哈希，不同设置录的 trace 不能按哈希对应，要按 tile 和代码体积对应。

### 3.5 已解决：编辑器在后台只有约 3 fps（2026-10-20）

**现象**：录到的每一帧约 333 ms，几乎全是 `RenderGraphExecute - UpdateAllPrimitiveSceneInfos`，没有 `SceneRender`，视口和基准捕获都不在帧内。

**原因**：编辑器不在前台时被「Use Less CPU when in Background」限帧。`UEditorEngine::GetMaxTickRate`（`Engine/Source/Editor/UnrealEd/Private/EditorEngine.cpp`）在 `ShouldThrottleCPUUsage()` 为真时返回 3 fps，正好 333 ms 一帧，期间 GPU 几乎空闲。和 Nsight、shader 符号、神经 BSDF 的改动都无关。

**排查证据**：

1. 不挂 Nsight 也是 3 fps：23 秒内日志帧号 531 → 600。
2. 编辑器在等而不是在忙：进程只占约 0.05 个 CPU 核，GPU 210 MHz、clock event reason 为 Idle。
3. 设置实际没关：用编辑器 MCP 读 `/Script/UnrealEd.Default__EditorPerformanceSettings` 得到 `bThrottleCPUWhenNotForeground = true`，各级 `EditorSettings.ini` 中都没有这个键。
4. 前台是别的程序；把编辑器窗口置顶（topmost）不改变前台归属，所以置顶试验无效。

**修复**：启动参数加 `-ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False`，只对这一次启动生效。加上后编辑器在后台、挂着 Nsight 时约 85 fps。

## 4. 读 GPU Trace（Nsight 界面）

### 4.1 界面分区

| 区域 | 内容 | 回答什么 | 对应的 MCP 工具 |
|---|---|---|---|
| 左上：事件列表 | 这一帧所有 D3D12 调用，按 UE 标记折叠成树；Δt 列是 GPU 耗时 | 这一帧发了哪些命令 | `list_gpu_trace_timeline_events` |
| 中间：时间轴 | 队列、提交、命令列表、PSO、Action、标记，以及下方的指标曲线 | 什么时候跑了什么、硬件当时多忙 | `list_gpu_trace_ranges`、`list_gpu_trace_marker_ranges` |
| 右上：选区面板 | Summary（吞吐、warp 占用）、Metrics（全部计数器）、Shader Warp Occupancy、Trace Information | 选中范围内的平均值 | `summarize_gpu_trace_range`、`list_gpu_trace_metrics`、`list_gpu_trace_shader_occupancy` |
| 下方中间：Instruction Mix | 指令类别占比（FP32、FP16、整数、逻辑等），分采样数和指令数 | 执行的是哪类指令 | — |
| 下方右侧：着色器分析 | Flame Graph、Top-Down、Bottom-Up、Hotspots、Shader Pipelines | 哪个 shader、哪条指令最热，为什么停 | `analyze_gpu_trace_pc_sampling`、`list_gpu_trace_shader_pipelines` |

用法：在时间轴的 Markers 行点一个块（例如 Lights），右侧和下方面板就切换到这个范围。没有 shader 调试符号时有黄条提示 "Missing Debug Info"：Shader Source 不可用，热点只显示指令地址（开启方法见第 5 节）。

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

### 4.3 指标曲线

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

**Warp Can't Launch** 把「新 warp 无法启动」的原因分开计数（寄存器分配、共享内存、warp 槽位等），对应计数器形如 `tpc__warp_launch_cycles_stalled_shader_ps_reason_register_allocation`，和 SM Warp Occupancy 一起回答「为什么占用率低」。注意它的百分比容易饱和，比较时看周期数（例子见 [README.md](/projects/neural-bsdf-perf/performance/) 4.5 节）。

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

nsight-graphics MCP 输出的名称里有 "Long Scoreboard (RT Core)"，按 Long Scoreboard 理解即可。

占用率（能驻留多少 warp）和停顿原因（已驻留的 warp 在等什么）是两个维度：占用率低时，延迟更难被其他 warp 掩盖，各种停顿的影响都会放大。寄存器数决定占用率上限：Ada 每个 SM 有 65536 个寄存器、最多 48 个 warp，每线程 r 个寄存器时最多驻留 ⌊65536 / (32 × r)⌋ 个 warp（168 → 12，128 → 16，96 → 21，64 → 32）。

## 5. Shader 调试符号（看源码行）

默认 UE 编译的 shader 不带符号，Nsight 只能显示指令地址。

UE 端，在 `Engine/Config/ConsoleVariables.ini`（当前已打开）或宿主项目 `DefaultEngine.ini` 的 `[SystemSettings]`：

```ini
r.Shaders.Symbols=1
r.Shaders.ExtraData=1
```

- `r.Shaders.Symbols=1` 等于同时打开 `r.Shaders.GenerateSymbols` 和 `r.Shaders.WriteSymbols`。DXC 以 `-Zi` 生成 PDB，再用 `-Qstrip_debug` 从二进制中剥离，单独写到 `<项目目录>\Saved\ShaderSymbols\PCD3D_SM6\`（来源：`ShaderCompiler.cpp`、`D3DShaderCompilerDXC.cpp`）。符号不改变生成的代码，不影响性能测试。
- `r.Shaders.ExtraData=1` 可选：附带 shader 名称，抓帧工具里更易读；会改变 shader 哈希。
- **不要**为性能分析设置 `r.Shaders.Optimize=0`：它改变生成的代码，测出的性能失真。
- 代价：第一次启动重编全部 shader；`Saved/ShaderSymbols` 占用数 GB。必须在启动时生效。

Nsight 端：Tools → Options → Search Paths → **Separate Shader Debug Information (.lld / .pdb)**，添加 `<项目目录>\Saved\ShaderSymbols\PCD3D_SM6`，Search sub-directories 设为 Yes。如果提示找不到源文件，再在 **Shader Source** 中加入 `<UE 根目录>\Engine\Shaders` 和 `<项目目录>\Intermediate\ShaderAutogen`。打开符号后要重新录制。注意 3.4 中开启符号后 MCP 读不到寄存器数的问题。

## 6. RenderDoc 抓帧（备用）

2026-10-19 在 `-game` 模式下抓了几次，都没有得到可用的帧，记录原因供下次参考：

- 启动参数 `-AttachRenderDoc`，命令 `renderdoc.CaptureFrame`；输出在 `<项目目录>\Saved\RenderDocCaptures\*.rdc`。
- 插件设置默认 `renderdoc.CaptureDelayInSeconds=1`，`renderdoc.CaptureDelay` 的单位是秒而不是帧。
- `L_NeuralCaptured_OPBR` 没有 PlayerStart，`-game` 下默认 Pawn 在原点朝 +X，看不到两列物体；`BugItGo` 需要先 `EnableCheats`。
- 即使相机日志显示已移动，三次抓到的画面仍相同（只有标签文字），原因没有查清；可能与 3.5 的后台限帧有关。
- RenderDoc 的资源 ID 在每次抓帧之间都会变化，不能沿用上一份 `.rdc` 的 ID。

结论：性能分析用编辑器 + Nsight；需要逐像素历史或 shader 单步时，再在编辑器里用 RenderDoc 抓帧。
