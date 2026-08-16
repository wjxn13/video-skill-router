# 视频技能路由（Video Skill Router）

让 AI 编程助手在遇到「做视频」需求时，不仅**选对制作引擎**（Manim / Remotion / HyperFrames / ffmpeg / Edge TTS / DDSP 音色转换），更把「怎么分段、怎么编排、怎么保证音画同步」变成**可回归测试的确定性决策**——而不是靠猜、靠提示词、靠返工。

一个客户端中立的 Agent Skill 路由包，以 **dsh-plugin** 形态优先发布到 DeepSeek Harness，同时兼容 Claude Code / Codex。

## 定位

- **不是「视频工厂」**：不追求全场景自动出片，专注「路由决策」这一层。
- **不是「任务级分类」**：一个视频是多段、多引擎、需要总装的；我们路由的是「片段 → 引擎 + 编排契约 + 依赖顺序」。
- **段级路由 + 编排契约 + 可测试**：把踩坑经验（A/V 同步、ffmpeg 坑、DDSP 音色转换）固化进 `routing.json`，用回归测试锁定。

## 目录结构

```
video-skill-router/
├── dsh-plugin/                         # dsh 插件包（git 子目录安装入口）
│   ├── package.json                    # dsh.bundle.patch 声明
│   ├── cordis.patch.yml                # 向 profile 贡献一行 bundle
│   ├── index.js                        # 运行时 ctx.skills.register()
│   └── skills/video-skill-router/      # skill 目录包（随包分发）
│       ├── SKILL.md                    # 路由主控（客户端中立）
│       ├── routing.json                # 段级路由规则（单一事实源）
│       ├── references/
│       │   ├── ops-contract.md         # A/V 同步、交付物、校验门禁
│       │   ├── engine-pitfalls.md      # 各引擎通用避坑
│       │   └── ddsp-voice.md           # DDSP 音色转换流程
│       └── scripts/
│           ├── master-route.py         # 决策脚本
│           └── bootstrap.py            # 工具检测自举
└── tests/test_routing.py               # 段级回归测试
```

## 安装

### DeepSeek Harness（dsh-plugin）

```bash
dsh plugin --profile web add "github:<你的用户名>/video-skill-router#path:/dsh-plugin"
```

（引号别省——`#` 在 shell 里是注释起点，不加引号后半截会被吃掉。）

重启 profile 后，输入 `/` 在 Skills 分组能看到 `video-skill-router`。

### Claude Code / Codex（目录拷贝）

skill 是标准 SKILL.md 契约，客户端中立：

```bash
cp -r dsh-plugin/skills/video-skill-router ~/.agents/skills/
# 或 Claude Code：~/.claude/skills/
```

## 使用

```bash
# 直接说人话
"做一个最短路径的科普动画，金句排版，女声解说，加字幕"

# 或先跑决策脚本看确定性路由
python dsh-plugin/skills/video-skill-router/scripts/master-route.py \
  "做一个最短路径的科普动画，金句排版，女声解说" --json
```

AI 会产出「Manim 段（最短路径）→ Edge TTS 段（先配音定长）→ HyperFrames 段（金句）→ ffmpeg xfade 总装 + 字幕双交付」的确定性方案，全程不用手动选工具。

## 路由规则（完整见 routing.json）

| 内容类型 | 引擎 |
|---|---|
| 数学/公式/几何/算法 | Manim |
| 金句/排版/标题/海报 | HyperFrames |
| 交互/UI/组件/弹簧动画 | Remotion |
| 数据图表/统计 | Remotion（备选 HyperFrames+Chart.js）|
| 代码展示/高亮 | HyperFrames（备选 Remotion）|
| 旁白/配音 | Edge TTS（先出，定段长）|
| 自定义/克隆音色 | DDSP 音色转换（后出，换音色）|
| 字幕 | ffmpeg（软+硬双交付）|
| 多段总装 | ffmpeg xfade |

## 测试

```bash
python tests/test_routing.py
```

每条路由规则都有「任务描述 → 期望命中 + 依赖顺序」的段级回归用例，CI 在 Windows / Linux 跨平台跑，防止路由规则被改坏。

## License

MIT
