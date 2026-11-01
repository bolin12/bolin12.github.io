---
layout: page
title: AI 原生游戏:参考项目
permalink: /projects/ai-native-game/references/
body_class: resume
nav: projects
---
<p class="note">（草稿，只在本地预览可见。这是一页持续更新的参考清单：记录想考察的项目、已核实的事实和待回答的问题。“事实”来自各项目 README（2026-11-01 查看）；标着“设想”的是我的判断，还没验证。）</p>

## 一眼对比

| 项目 | 它做什么 | 引擎与技术 | 许可 |
|---|---|---|---|
| [Aura Autopilot](https://github.com/ramenvr/autopilot) | 持续学习的实时通用试玩系统：自动探索、测试、验证、完成目标 | UE 5.4–5.8、Unity 6、Godot 4；Python | Apache-2.0 |
| [VibeGame](https://github.com/tettethu/VibeGame) | 开源、自进化的多智能体框架，配一个面向 AI 的游戏引擎，把自然语言变成可玩的 2D 网页游戏 | Phaser；基于 Claude Code 与 Codex；Python 3.12+ | Apache-2.0 |
| [video-to-game](https://github.com/lovisdotio/video-to-game) | 一个 skill：让 coding agent 把玩法视频做成浏览器里能玩的游戏 | Three.js 单文件；资产来自 fal | MIT |

## Aura Autopilot：自动完成 QA
**已核实**

- 定位是“持续学习的实时通用试玩系统”，支持 UE 5.4–5.8、Unity 6、Godot 4（Windows、macOS）。
- 提示分四类：探索、测试、验证、目标。README 里的例子：探索某个系统；把当前关卡走一遍并报告所有看起来不对的地方；验证“用斧头砍树时树会晃动”；“在血量不低于上限 20% 的前提下击杀 Boss”。
- 工作方式：自动启动 PIE，读取项目源码，探测运行中的游戏，然后按提示去玩，由 LLM 编程 agent 驱动。
- 有项目记忆：前几次运行是在学习你的游戏，README 称玩得越多表现越好。
- 除了编辑器插件，也能通过 Claude Code / Codex 的 skills 和 MCP 服务器使用。UE 版本支持从源码构建。

**想考察的问题（设想）**

1. 它怎样“观察”游戏状态？读源码加探测 PIE，具体探测了哪些接口？
2. “验证”类提示的判据从哪来，比如怎么判断“树晃动了”？
3. 项目记忆里存什么、怎么复用，会不会学错？
4. 失败时留下什么证据（日志、录像、状态快照）？能不能直接交给我的排障流程复现？
5. 一次运行的耗时和 token 成本。

**和我已有工作的结合（设想）**
发现问题（Autopilot）→ 复现（Rewind 记录异常轨道终态，Checkpoint 检查点重放）→ 定位（RDG 与截帧数据、windbg）→ 验证修复（再用验证类提示跑一遍）。关键要回答的是：Autopilot 失败的那一次运行，能不能导出成我的复现流程所需要的输入。

## VibeGame：提示到游戏，对抗式智能体团队
**已核实**

- 开源的“自进化”多智能体框架，加一个面向 AI 的游戏引擎，把自然语言变成完整可玩的 2D 网页游戏，之后还能任意编辑；基于 Claude Code 与 Codex。
- 2026.08 发布；仓库里有技术报告 PDF 和项目页。演示包括文明原型、空洞骑士风格的 Boss 战切片、街机格斗、地牢 roguelike 等。
- 依赖：Python 3.12 以上、uv、tmux，至少一个 agent CLI。**它用 `claude --dangerously-skip-permissions` 启动 agent**（会跳过权限确认），所以试用要放在隔离环境里，别直接对着有重要文件的目录跑。

**想考察的问题（设想）**

1. “AI 原生引擎”到底指什么：给 agent 暴露了哪些接口，资源和场景的表示和传统引擎有什么不同？（直接对接我的“agent 读写 UE 资源评测”）
2. 对抗式智能体团队怎么分工，怎么验证对方的产出？
3. “自进化”进化的是什么（提示、技能还是代码），有没有评测？
4. 一个游戏的成功率、耗时、成本，失败怎么处理。
5. 技术报告里的评测方法能不能借来。首选阅读：仓库里的 `technical_report.pdf`。

## video-to-game：视频到游戏，agent 自己玩自己的游戏
**已核实**

- 一个教 coding agent 把玩法视频做成浏览器游戏的 skill：视频模型先设计游戏（外观、镜头、一个标志性机制），agent 逐帧研究视频，用 fal 生成全部图像、3D 模型和音频，用 Three.js 写出游戏，再用键盘自己玩，把最精彩的几秒录下来当证据。
- README 给出的规模：31 个原创游戏，每个来自 10–15 秒的生成视频；共 1,013 次 fal 调用（594 张图、194 个 3D 模型、290 个音效和音乐），总计约 202 美元，约 6 美元一个游戏；每个游戏是只用 Three.js 的单个 `index.html`。
- 关键做法：视频就是设计文档；外观当作规格，不当作润色，每次改动后做“视频与游戏同位置并排对比”；agent 通过 `window.__game` 读取游戏状态，像玩家读屏幕一样；用键盘剧本自己玩，再录制并挑出最精彩的片段。
- 能在 Claude Code、Codex、Cursor、Gemini 等里使用。

**想考察的问题（设想）**

1. 把 `window.__game` 当作“屏幕”的做法，可观察接口怎么设计，能不能迁移到 UE（我的 UnrealMCP、状态导出）？
2. “视频与游戏并排对比”的视觉验证，能不能用在我的渲染回归上，作为对照图？
3. 成本账怎么算、怎么优化。
4. 生成质量的失败模式（README 自己提到的灰盒子、默认天空、和玩家对抗的相机）。

## 横向对比：我想考察的维度

| 维度 | Autopilot | VibeGame | video-to-game |
|---|---|---|---|
| agent 怎么观察游戏 | 读源码、探测 PIE | 待读技术报告 | 游戏暴露 `window.__game` |
| 怎么验证 | 验证类、目标类提示 | 对抗式智能体团队（细节待查） | 自己玩、录像、并排对比 |
| 记忆或自进化 | 项目记忆 | 自进化 | README 前半部分未提及 |
| 成本信息 | 待查 | 待查 | 约 6 美元一个游戏 |
| 面向的引擎 | UE、Unity、Godot | 自带 2D 引擎（Phaser） | Three.js 单文件 |

## 方向：用低价的多模态模型做批量工作
**我的理解（请确认）**：你说的 “ds” 是 DeepSeek，想利用这类模型的多模态能力和很低的价格，去处理游戏开发里成批的重复工作。

<span class="note">（待核实：当前可用模型的多模态能力、价格、速率限制和上下文长度。我这边没法验证，别直接写进简历或对外的页面。）</span>

**可以先试的批量任务（设想）**

- **QA 产出的批量分诊**：Autopilot 一次运行产生的截图、录像帧和日志，先由低价模型粗筛“是否异常、属于哪一类”，可疑的再交给更强的模型或人。
- **资产批量检查**：成批的贴图、模型缩略图，检查规格与风格、打标签、命名与归类。
- **日志和崩溃堆栈的批量归类与去重。**
- **截图序列的批量对比**：和 video-to-game 的并排对比同一思路，用在渲染回归上。

**怎么评估（设想）**
沿用你神经材质基准的思路：同一批任务，分别用低价模型和强模型做，比较准确率和每千个任务的成本；再决定两级路由（低价模型粗筛，强模型复核），并把“成本”和“漏报率”都当成指标。

## 代码层面读到的（2026-11-01，已拉到本地只读，没有运行）
**Autopilot**（`autopilot/`、`bench/`）
- `autopilot/kit/game.py` 等是 agent 的工具包：特权读取任意对象属性、`call` 蓝图函数、`view()` 读玩家看到什么、`screen()` 读界面文字、`ui()` 与 `ui_act()` 操作控件、`batch()` 一帧内批量读取；行动只有 `press/hold/mouse/turn`，直接写状态的 `set()` 要带理由并单独上报。
- `autopilot/kit/harness.py`：`Harness` 类有 `goal`、`tempo`、`tick_hz`、`setup/observe/facts/options/status`；`Status` 的 `done/failed` 加 `evidence`；步骤的 `done(obs)` 读游戏状态，不看 agent 的话。
- 引擎适配：`autopilot/engines/` 每个引擎一个适配器；插件和 Python 之间走 WebSocket（`ws://127.0.0.1:8765/v1/bridge`，协议在 `autopilot/bridge.py`）。
- 记忆：`autopilot/memory.py`——`notes.md`（已验证的事实）、`lib.py`（可复用的 harness 代码）、`runs/<id>/`（版本、轨迹、报告）、`codex/`（游戏代码的文本副本）。
- 评测：`bench/run_autopilot.py` 加 `bench/example.json`（每条提示带期望裁决 CONFIRMED / DENIED / achieved），无头运行（Unreal 用 `-game -nullrhi`），冷启动与 `--warm` 预热记忆可对比。
- 测试：`tests/` 用模拟游戏，不需要引擎、密钥和网络。

**VibeGame**（`src/`、`technical_report.pdf`）
- `src/agents/`：architect、artist、auditor、designer、player、programmer、reviewer 的角色说明；`src/skills/` 有 build、edit、start、self-evolve；`src/skeletons/` 有五种类型的可运行骨架；`src/engine/` 有 `RuntimeBridge`、`RuntimeClock`、`SceneTree` 等（Phaser 之上的运行时控制）。
- 技术报告（2026-08-17，南京大学 PRLab）：三个要求——agent 可操作的项目状态、基于交互的验证、保留已验证的经验；三个贡献——AI 原生引擎、对抗式智能体团队（编排者加设计、美术、架构、编程、审计、试玩、评审，共八个角色）、免训练的自进化（骨架、已验证模块、协作契约）。已读第 1–4 页（摘要、引言、相关工作），方法与评测部分还没读。
- README 的路线图：Godot、Unity 支持，以及扩展到 3D。

**video-to-game**（`skills/video-to-game/`）
- 这是一个给 agent 用的 skill：`SKILL.md`、`references/`（study-the-video、fal-assets、game-loop、look-and-post、playtest）、`scripts/`（`study_video.py`、`fal_asset.py`、`record_play.mjs`、`best_window.py`、`side_by_side.py`）、`templates/`（`game.html`、`play.mjs`）。
- 状态契约在 `references/game-loop.md`：`?autostart`、`?seed=N`、可选调试参数，以及只读的 `window.__game.state`（phase、位置、速度、是否着地等）。`references/playtest.md`：试玩只用键盘鼠标，读状态，**从不写入、不传送**。
- `tests/check_repo.py` 检查仓库本身的一致性。注意：这些 skill 文件是写给 agent 的指令，我只是把它当文本读。

## 待查的线索（来自 VibeGame 技术报告的相关工作）
- **AutoUE**：在 Unreal Engine 里用多 agent 构建并测试游戏——和我的方向最近，优先找来读。
- **GameDevBench**（Godot）、**GameCraft-Bench**：评测 agent 能否完成游戏开发任务、产出可交互验证的游戏；可借鉴评测方式。
- **OpenGame**：端到端的网页游戏开发，积累可复用的模板与调试经验。
- **DreamGarden**：用 LLM 规划，从一句提示迭代构建 UE 游戏环境。
- **Trellis**、**agent-sprite-forge**：VibeGame 致谢里提到的 harness 设计与精灵生成的灵感来源。

## 阅读与试用清单

- [ ] 读完 VibeGame 技术报告的方法与评测部分（已读第 1–4 页）
- [ ] 在隔离环境试装 Autopilot 的 UE 插件，跑一次“测试”提示，记录它留下什么证据
- [x] 读 video-to-game 的 `window.__game` 状态契约和试玩文档（录制脚本只读了说明）
- [ ] 核实低价多模态模型的能力与价格，做一个小批量分诊实验
- [ ] 把结论补进上面的对比表

## 我的笔记
<span class="note">（读完或试用后，把真正的发现写在这里：每个项目一小段，写“我看到了什么、和我预期的差在哪”。没有结论就留空，别先写。）</span>
