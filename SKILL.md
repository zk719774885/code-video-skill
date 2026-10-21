---
name: code-video
description: 视频任务总入口（优先于 hyperframes / remotion-* 技能先读）。任何"做视频/动画/片头/宣传片/知识科普视频/渲染 MP4"的请求，先读本技能：按场景在 sy-styles-20、Remotion、HyperFrames 三个引擎里选一个，再走统一的四步法（定规格→卡点→配音效→试片逐段推进），卡点用本技能的 beats.py。
---

# 视频总调度（code-video）

> 引擎安装位置记作 `VIDEO_HOME`（作者本机是 `D:\AI\claude视频制作`）。换电脑或分享给别人时，把下文的 `D:\AI\claude视频制作` 全部替换成自己的目录即可；安装步骤见同目录 README.md。

## 第 0 步：选引擎（三个都已装好、实测能出片，2026-10-20）

| 引擎 | 位置 | 配套技能 | 选它的场景 |
|---|---|---|---|
| **sy-styles-20** | `D:\AI\claude视频制作\sy-styles-20` | 本技能下半部分 | 要**极强质感**（WebGL 打光、纸纹、景深、运动模糊）的片头/风格短片；能直接改 40 条现成风格之一；纯代码画面 + 合成音效，无素材 |
| **Remotion** 4.x（React） | `D:\AI\claude视频制作\remotion-studio` | `remotion-best-practices`（路由）→ `remotion-create/markup/captions/render/studio` 等 | **系列化/模板化**内容（知识科普一周一条、换数据批量出）；数据驱动、组件复用；要可视化 Studio 预览拖时间轴；博主「Vibe 知识大赏」用的就是它 |
| **HyperFrames**（HTML + GSAP） | `D:\AI\claude视频制作\hyperframes-studio` | `hyperframes`（路由）→ `-core/-animation/-creative/-registry/-cli`、`media-use`、`figma` | **有素材**要剪进来（录屏、实拍、图片、Logo）；要 **AI 配音（本地 TTS）/ 自动字幕转写**；**网站 URL、GitHub PR、Figma 转视频**；想用约 400 个现成组件/转场/特效（`hyperframes add`）；要竖屏/方屏/4K 预设 |

判断规则：
- 用户点名哪个就用哪个。
- 没点名：先看是否涉及素材/配音/URL/Figma → HyperFrames；是否系列化模板/数据批量 → Remotion；否则追求画面质感 → sy-styles-20。拿不准就用一句话说明推荐理由后直接开工，不要反复问。
- 可以混搭：例如 sy-styles-20 渲一段 10 秒质感片头 mp4，作为素材放进 HyperFrames/Remotion 的成片里。
- **授权提醒**：Remotion 个人和 ≤3 人公司免费商用，更大的营利公司需要买 Company License；若用户是给公司做，开工前提一句。sy-styles-20（MIT，保留署名）和 HyperFrames（Apache-2.0）无此限制。
- HyperFrames 的 `media-use` 里找 BGM、云渲染、`auth` 需要 HeyGen 账号或 API key，**不要主动登录或填 key**；音效 `--type sfx` 与本地 TTS 无需账号。

各引擎常用命令：
```
# Remotion（在 remotion-studio 里）
npx remotion studio                        # 可视化预览
npx remotion still MyComp out/x.png --frame=45
npx remotion render MyComp out/x.mp4 [--frames=0-299]   # 只渲前 10 秒用 --frames
# HyperFrames（在 hyperframes-studio 里，版本固定在 package.json）
npm run dev / npm run check / npm run render
npx hyperframes beats 音乐.mp3              # 它也自带卡点分析，可和 beats.py 互相校验
npx hyperframes tts / transcribe           # 本地配音 / 转写
```
新项目：Remotion 用 `npx create-video@latest --yes --blank 名字`；HyperFrames 用 `npx hyperframes init 名字 --example blank --non-interactive [--resolution portrait]`。

**不管选哪个引擎，下面的「四步法」和「自查」都适用。**

---

# 引擎一：sy-styles-20

本机已装好的引擎仓库：`D:\AI\claude视频制作\sy-styles-20`（MIT，作者肖雄 XIAOXIONG，github.com/xiaoxiong20xx-code/sy-styles-20）。
- 第一期 20 种风格在 `styles/`，第二期（新题材，带 4.5s 钩子和片名）在 `vol2/styles/`，用法相同（进 vol2 再跑命令）。
- 仓库内 `AGENTS.md` 是完整规范（质量标准、场景契约、性能坑）。**动手前先读它。**
- 依赖已就绪：Node 24、Python 3.12 + numpy/scipy、ffmpeg 8、Playwright chromium。

## 原理（一句话）
每个风格是一个 HTML 页，调用 `Reel.scene({duration, fps, setup, render(t), cues, frameKey})`；`render(t)` 只依赖 t（确定性）。
`render.js` 用无头 Chromium 打开 `?render=1&rs=..`，调用 `window.__seek(t)` 逐帧截图；`--mb N` 每帧 N 个抖动子帧再用 ffmpeg tmix 平均 = 运动模糊 + 抗锯齿。
音效：`cues`（时间点 + 音效名）→ `audio/synth.py` 用 numpy 合成 wav → ffmpeg 合成 mp4。

## 常用命令（在仓库根目录执行）
```
node make.js list
node make.js still 09 6.5 --hwgpu     # 单帧 → out/09_6.5s.jpg，先用它调
node make.js style 09 --hwgpu         # 10 秒成片 → out/09.mp4（已渲过加 --force）
node make.js reel 03,09,11 mini       # 挑几个拼短片
node make.js brand 中文名 ENGLISH      # 换署名
node make.js cues                     # 改了 cues 后重导 cues.json
```
WebGL/3D 风格一律加 `--hwgpu`（本机有显卡，快很多）；纯 2D 风格自动走 `--nogpu`。

## 在其他项目里用
1. 简单改字：`?cfg={"title":"..."}` 覆盖 `Reel.cfg` 默认文字，或直接改 index.html 顶部的 `const C = Reel.cfg({...})`。
2. 新做场景：复制一个最接近的风格目录（2D 参考 03-flat / 06-morph / 17-editorial；WebGL 参考 09-collage / 18-ink；3D 参考 11-bauhaus），按 AGENTS.md 契约改；新风格同步 `comp/meta.js` 与 `comp/balls.js`。
3. 输出放到用户项目：渲染完把 `out/xx.mp4` 复制过去。
4. 也可以直接用 `node render.js 某个.html out.mp4 --nogpu` 渲任意符合契约的 HTML（无音轨，最快）。

## 做完整视频的四步法（来自博主 小冯不意why「Vibe知识大赏」教程，作者认可的工作方式）
这类知识科普视频不是拍的，是 AI 写代码、按分镜一幕一幕画出来的。**接到做视频的任务，默认按这四步走，不要一口气生成整片。**

1. **定规格**：开工前把这些定死并写进项目说明里：视频类型（知识科普/片头/产品演示…）、主题、技术栈（本机默认用 sy-styles-20 的 HTML 契约；用户点名 Remotion 再用 Remotion）、1920×1080、30fps、16:9（竖屏就是 1080×1920）、配不配音（默认不配，用中文字幕把知识点讲清楚）、配乐用哪个文件。缺的信息先问用户，尤其是**主题**和**配乐**。
2. **卡点**：有配乐就先分析，不要凭感觉对节奏：
   `python -P ~/.claude/skills/code-video/beats.py 音乐.mp3 beats.json`
   → 得到 BPM、每一拍、小节首拍、最强重音的秒数（实测误差小于 1 帧）。规则：**画面每换一次（切镜、新元素入场、字幕出现）都落在拍点上**；换场景踩小节首拍；片名/钩子时刻踩最强重音。把 beats.json 里的时间直接写进场景代码的时间轴常量，不要手写近似值。没有配乐就按 120 BPM（每拍 0.5s）设计，之后再用合成音乐对齐。
3. **配音效**：每个关键动作配一个音（`cues`），用代码合成（`audio/synth.py`）。音色要和画面主体的乐器/材质契合（例如纪念碑谷式的叮咚清脆音、钢琴单音、木琴、玻璃声），**越关键的画面，音效越讲究**。连续出现的动作可以做音阶递进（do→re→mi…，越往上越高）。音效同样落在拍点上。
4. **试片，逐段推进**（最容易漏掉，也最重要）：先只做**开头 10 秒**，渲染给用户看（still 抽帧 + 小样 mp4），确认后再一段一段往下做；哪段不好就只重做那一段。一句话一次出片质量很低；分 5 轮来改虽然慢（博主实测 5 轮约 37 分钟，一次出片约 6 分钟），但质量高很多。分段渲染：`node render.js 场景.html x --from 0 --to 10 --frames 输出目录`。

博主给的四段提示词（用户可能直接这样下指令）：
- 定规格：帮我做一部知识科普视频，主题：XXX。用 Remotion 来做，1920×1080，30 帧，16:9 横屏；不配音，用中文字幕把知识点讲清楚；配乐用文件夹里这首音乐。
- 卡点：先分析这首音乐，测出每分钟多少拍，把每个重拍在第几秒列出来；画面每变一次，都落在重拍上。
- 配音效：每个关键动作都配一个音，用代码合成；音色用契合画面重点的乐器。
- 试片：先做开头 10 秒给我看；我确认后再一段一段往下做，哪段不好就重做那一段。

「Vibe知识大赏」视觉范式（做知识科普类时可参考）：深海军蓝/近黑背景 + 金色强调色；思源宋体等衬线中文大标题，字距拉宽；极简的粒子/点阵/细线图示，用数字放大来讲知识点（例如「0.1 毫米 → 857 毫米」）；四角放小号英文 HUD 标签（如 `STEP 1 / 4`、`1920 × 1080 · 30 FPS`）；底部居中一行中文字幕，关键词标黄；每个知识点一幕，用一句诗意的话开场（例如「失之毫厘，谬以千里」）。

## 自查（交付前必须）
- still 看开头 / 钩子时刻 / 结尾三帧（用 Read 查看图片）。
- 成片抽 6–9 帧拼联系表：`ffmpeg -i out/x.mp4 -vf "fps=0.8,scale=640:-1,tile=3x3" -frames:v 1 out/sheet.jpg`
- 响度：`ffmpeg -i out/x.mp4 -af ebur128=peak=true -f null -`，目标约 -15 LUFS，真峰值 ≤ -1 dBTP。

## 本机已修的坑
- Windows 下 `render.js` 的 `--still t:路径` 原本按 `:` 拆分会把 `D:` 盘符拆坏（图片写成一个叫 `D` 的文件）。已改成只按第一个冒号拆（根目录和 vol2 的 render.js 都改了）。若重新拉仓库需再修。

## 整片构建工具（tools/）
多段落、60–90 秒的整片推荐用 `tools/build.js` + `tools/mixplan.py`（实战出过 6 版宣传片）：
- 项目目录放 `index.html`（sy-styles-20 场景契约，`duration` 设成整片时长，cues 写全片音效）、`music.json`（`{"name","total","note":"piano|guzheng|marimba|bell|epiano|toy","sections":[{"kind":"04","start":0,"dur":60}]}`，kind 用 synth.py 里的风格配乐编号 02–20 / intro / outro）、可选 `render.args`（WebGL 场景写 `--hwgpu`，默认 `--nogpu`）。
- 环境变量 `SY_STYLES` 指向 sy-styles-20 目录（或设 `VIDEO_HOME`，工具会找 `VIDEO_HOME/sy-styles-20`）。
- 命令（在项目目录）：`node <技能目录>/tools/build.js still 3 8.5` 抽帧；`... clip 0 10` 小样；`... full --mb 3` 整片 → `out/<name>.mp4`。
- 经验：字幕、标签全部画在 canvas 里；每段先抽 6–9 帧拼联系表检查重叠/出界再整片渲染；WebGL 重场景（如 18 水墨）1080p 约 3 秒/帧，提前预估时间。
