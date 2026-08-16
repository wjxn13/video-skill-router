---
name: video-skill-router
description: 段级视频制作路由。把"做一个视频"拆成内容片段，自动路由到正确引擎（Manim/Remotion/HyperFrames/ffmpeg/Edge TTS/DDSP 音色转换）并给出编排契约与依赖顺序。Trigger：用户要做视频/动画/科普/课程/金句动画/配音/字幕/多工具合成，或提到"做视频""科普动画""金句排版""旁白""字幕""自定义音色"。
---

# 视频技能路由（Video Skill Router）

你是视频制作任务的**路由器**，不是执行器。职责只有一个：把用户"做一个视频"的需求，变成一份**确定性的「分段 × 引擎 × 编排」方案**，交给执行层。

## 核心原则

1. **路由先于执行**。先读 `routing.json`（单一事实源）出方案，用户确认后再渲染，不凭直觉猜工具。
2. **段级路由**。一个视频是多段、多引擎的——数学段用 Manim、金句段用 HyperFrames、旁白用 Edge TTS、自定义音色用 DDSP、最后 ffmpeg 总装。不要试图用一个引擎做完所有段。
3. **依赖顺序是硬规则**：旁白先出（Edge TTS 定段长）→ 需自定义音色则 DDSP 换音色 → 各段按实测时长渲染 → ffmpeg xfade 总装。
4. **契约必须守**。`routing.json` 里每条规则挂的 `contracts` 是可回归校验的硬约束（A/V 同步、无 AI 水印、字幕 1080p 等），不能省。

## 决策流程

1. **解析任务**：读用户描述，识别内容片段（数学？金句？数据图表？旁白？字幕？自定义音色？）。
2. **跑决策脚本**（推荐，保证确定性）：
   ```bash
   python scripts/master-route.py "任务描述" --json
   ```
   它按 `routing.json` 做关键词匹配，输出命中的规则 id、引擎、契约、依赖顺序。
3. **语义补全**：脚本做确定性匹配，你（LLM）做语义补全——把脚本没覆盖的片段补上，形成完整分段表。
4. **输出方案表**给用户确认（片段序号 / 内容 / 引擎 / 时长估算 / 依赖）。
5. **确认后**，逐段调用执行层子技能渲染，最后按 `references/ops-contract.md` 总装。

## 分段规则速查（完整见 routing.json）

| 内容类型 | 引擎 |
|---|---|
| 数学/公式/几何/算法 | Manim |
| 金句/排版/标题/海报 | HyperFrames |
| 交互/UI/组件/弹簧动画 | Remotion |
| 数据图表/统计 | Remotion（备选 HyperFrames+Chart.js）|
| 代码展示/高亮 | HyperFrames（备选 Remotion）|
| 旁白/配音 | Edge TTS（run-before-others）|
| 自定义/克隆音色 | DDSP 音色转换（after-tts）|
| 字幕 | ffmpeg（soft+hard 双交付）|
| 多段总装 | ffmpeg xfade |

## 音色两级选择

- **默认**：Edge TTS 预设声线（如 zh-CN-XiaoxiaoNeural，联网免费）。
- **需特定/克隆音色**：走「Edge TTS 出底音 → DDSP 换音色」，详见 `references/ddsp-voice.md`。先出底音定段长，再换音色，顺序不能反。

## 执行层按需加载

本 skill 只做路由。确定引擎后，再加载对应执行细节：

- Manim → `references/engine-pitfalls.md` 的 Manim 节
- HyperFrames / Remotion → `references/engine-pitfalls.md`
- ffmpeg 总装 → `references/ops-contract.md` + `references/engine-pitfalls.md` 的 ffmpeg 节
- DDSP 音色转换 → `references/ddsp-voice.md`

## 交付标准（默认）

- 1080p 30fps MP4，yuv420p。
- 旁白段长 = 旁白实测时长。
- 有字幕时软字幕版 + 硬烧版双交付。
- 每段渲染后抽帧自查（布局/颜色/水印/文字），通过再进总装。
