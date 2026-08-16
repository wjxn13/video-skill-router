# 各引擎避坑（通用，跨平台）

> 多项目实战验证。本机特定路径（ffmpeg 绝对位置、沙箱拦截等）不在此列，用 `scripts/bootstrap.py` 检测定位，别硬编码。

## Manim（数学/几何/算法动画）

- **v0.20 API**：`self.camera.frame` 在 ManimCE v0.20 不可用。做"放大某点再拉远"，把世界装进 `Group(*mobjects)` 后 `.animate.scale()/.shift()`。
- 混装 `ImageMobject` 时用 **`Group` 而非 `VGroup`**（VGroup 混装会报类型错）。
- 渲染：`manim -qm <script>.py <Scene>`。
- 文字建议预生成 PNG + `ImageMobject` 引用，避免 `MathTex`/`Text` 批量临时文件问题。

## HyperFrames（文字排版/海报式动画）

- **GSAP 不是全局内置**：本地放 `gsap.min.js` 并 `<script src>`，否则时间轴静默不执行，渲出一帧静态图。
- **GSAP 属性白名单**：只支持 `opacity/x/y/scale/scaleX/scaleY/rotation/width/height/visibility`；`filter/backgroundColor/color` 等**静默忽略**。想"变暗"用 opacity 叠黑幕，不靠 filter。
- 渲染：`npx hyperframes render <html> -o <输出>`。

## Remotion（React 动效/表格/弹簧）

- CJK 用 `@remotion/google-fonts/NotoSansSC`，否则中文方块。
- **颜色插值报错**：`interpolate(frame,[a,b],["#3A3F47","#5AA9E6"])` 会抛 TypeError。用分层 div + `opacity` 数值插值渐显目标色，不要插值颜色字符串。
- 时长用帧数：`DURATION = 秒 × fps`。

## ffmpeg（总装/字幕，本机 8.1.1 实测）

- **`acrossfade` 无 `transition` 参数**：旧写法 `acrossfade=transition=fade` 报错，改用 `acrossfade=d=<时长>`。`xfade` 的 `transition=dissolve`（值 25）仍有效，别混淆。
- **`xfade` 要求 pix_fmt 一致**：Remotion 段是 `yuvj420p`、Manim/HyperFrames 段是 `yuv420p` → 每个视频输入加 `format=yuv420p` 再进 xfade。
- **`amix`/`acrossfade` 要求声道一致**：都加 `-ac 2`。
- **防削波**：`amix` 已归一化 ~1.0，再 `volume=2` 必削波，用 `volume=1.0`。
- **字幕致命坑**：纯 SRT 无分辨率头，libass 默认 `PlayResY=288`，1080p 视频里 `FontSize` 会被放大 **~3.75 倍**，长句折行占满半屏。先转显式 `PlayResX:1920 / PlayResY:1080` 的 ASS 再烧录（字号即 1:1 真实像素）。`subtitles` 滤镜**无 `fontfile`**，用 `force_style='FontName=...'` 指定系统字体。
