---
name: code-video
description: 视频任务总入口（优先于 hyperframes / remotion-* 技能先读）。任何"做视频/动画/片头/宣传片/知识科普视频/渲染 MP4/配 BGM/卡点"的请求，先读本技能：按场景在 sy-styles-20（随技能自带）、Remotion、HyperFrames 三个引擎里选一个；先定配乐（优先免费成品配乐）再卡点；走四步法（定规格→卡点→配音效→试片逐段推进）；用 tools/ 一条命令出整片。
---

# 视频总调度（code-video）

本技能目录（下文记作 `<技能目录>`，通常是 `~/.claude/skills/code-video`）里：
- `engines/sy-styles-20/`：随技能自带的 sy-styles-20 引擎（MIT，作者肖雄 XIAOXIONG，已修 Windows 盘符 bug）。首次使用前运行一次 `install.ps1` / `install.sh` 装依赖。
- `beats.py`：卡点分析；`tools/`：整片构建、配乐混音、选曲、测调工具。
- `templates/`：项目模板（`three-title`：Three.js 3D 中文片名），用 `tools/newproj.js` 新建。
- `references/`：`bgm-workflow.md`（成品配乐 + 卡点 + 动效音效全流程）、`three.md`（Three.js 3D 用法与坑）、`lessons.md`（实战经验）、`xiaofeng-method.md`（小冯不意why「Vibe 知识大赏」教程整理）。**做完整片前先读 bgm-workflow.md 和 lessons.md。**
- 视频项目放在用户自己的工作目录（例如 `D:\AI\claude视频制作\<项目名>`），不要放进技能目录。

## 第 0 步：选引擎

| 引擎 | 位置 | 配套技能 | 选它的场景 |
|---|---|---|---|
| **sy-styles-20** | `<技能目录>/engines/sy-styles-20`（或环境变量 `SY_STYLES`） | 本技能 | 要**极强质感**的片头/宣传片/风格短片；40 条现成风格可改；纯代码画面；`tools/` 一条命令出整片；要 **3D 中文片名 / SVG Logo 挤出 / GLTF 模型 / 大量 3D 粒子** 时用内置 Three.js 桥接（`references/three.md`） |
| **Remotion** 4.x（React） | 用户工作目录下 `remotion-studio`（`install --remotion` 生成） | `remotion-best-practices` → `remotion-*` | **系列化/模板化**、数据驱动批量出片、Studio 可视化拖时间轴 |
| **HyperFrames**（HTML + GSAP） | 用户工作目录下 `hyperframes-studio`（`install --hyperframes` 生成） | `hyperframes` → `-core/-animation/...`、`media-use`、`figma` | **有素材**（录屏、实拍、Logo）、要 **AI 配音 / 自动字幕**、网站/Figma 转视频、约 400 个现成组件 |

判断规则：
- 用户点名哪个就用哪个；没点名：素材/配音/URL/Figma → HyperFrames；系列化模板 → Remotion；否则 → sy-styles-20。拿不准就一句话说明理由后直接开工。
- 可以混搭：sy-styles-20 渲质感片段，作为素材放进 HyperFrames/Remotion。
- **授权**：Remotion 个人和 ≤3 人公司免费商用，更大的营利公司要买 Company License，给公司做时开工前提一句。sy-styles-20（MIT）与 HyperFrames（Apache-2.0）无此限制。
- HyperFrames 的找 BGM、云渲染需要 HeyGen 账号或 key，**不要主动登录或填 key**；本地 TTS、音效无需账号。

常用命令：
```
# Remotion（在 remotion-studio 里）
npx remotion studio | npx remotion still MyComp out/x.png --frame=45 | npx remotion render MyComp out/x.mp4 [--frames=0-299]
# HyperFrames（在 hyperframes-studio 里）
npm run dev / npm run check / npm run render ; npx hyperframes beats 音乐.mp3 ; npx hyperframes tts / transcribe
```
新项目：`npx create-video@latest --yes --blank 名字`；`npx hyperframes init 名字 --example blank --non-interactive [--resolution portrait]`。

---

## 四步法（不管选哪个引擎都适用；来自小冯不意why 教程，详见 references/xiaofeng-method.md）
**接到做视频的任务，默认按四步走，不要一口气生成整片。**

1. **定规格 + 定配乐**：类型、主题、引擎、1920×1080 / 30fps / 16:9（竖屏 1080×1920）、配不配音（默认不配，中文字幕讲清楚）、时长、口径约束，写进项目 SPEC.md。**配乐最影响质感**：
   - 用户给了曲子就用；没给就按 `references/bgm-workflow.md` 去 Mixkit 等免费曲库挑 8–12 首候选，`tools/bgmcard.py` 生成试听页让用户挑（下载前告诉用户文件名、来源、大小并征得同意）。
   - 纯代码合成的配乐只作兜底（`tools/mixplan.py`），合成的高音“叮”容易刺耳。
2. **卡点**：`python -P <技能目录>/beats.py 配乐.mp3 beats.json` 得到 BPM、每拍、小节首拍、重音；`python <技能目录>/tools/keydetect.py 配乐.mp3` 测调。按小节能量找出前奏/Drop/桥段/结尾重音。规则：换场踩小节首拍，片名/最重要画面踩 Drop 或最强重音；已有画面用**分段时间映射**钉到音乐上（见 bgm-workflow.md 第 4 节），各段速度 0.85–1.25 倍，宁慢勿赶；音乐长度不对就按小节补/剪（`bgm.json` 的 `edit`）。
3. **配音效**：**每个关键动作都要有声音**（元素出现、扫描、锁定、数据流、关卡、印章……），不要因为嫌吵就删掉。用了成品配乐时：有音高的音效一律吸附到配乐的调、柔和拨弦音色、降一个八度；全部低通去刺 + 短混响；关键时刻加低频重音，Drop 前加上升音；音效总线比音乐低 5–9 dB。`tools/mixbgm.py` 已实现这些规则。
4. **试片，逐段推进**：先做开头 10 秒（still 抽帧 + 小样 mp4）给用户看，确认后再一段一段往下做；哪段不好只重做那段。用户明确说“一次做完”时可以整片做，但仍要先抽帧自查。

「Vibe 知识大赏」视觉范式（知识科普类可参考）：深蓝/近黑 + 金色；衬线大标题拉宽字距；点阵/细线图示；数字放大讲知识点；四角英文 HUD 小字；底部一行字幕关键词标黄；每幕一句诗意开场。

---

## 引擎一：sy-styles-20（随技能自带）
- 第一期 20 种风格在 `styles/`，第二期（新题材，带 4.5s 钩子和片名）在 `vol2/styles/`。仓库内 `AGENTS.md` 是完整规范（质量标准、场景契约、性能坑），**新做场景前先读它。**
- 原理：每个风格是一个 HTML 页，调用 `Reel.scene({duration, fps, setup, render(t), cues, frameKey})`，`render(t)` 只依赖 t；`render.js` 用无头 Chromium 逐帧截图，`--mb N` 子帧叠加出运动模糊；cues → `audio/synth.py` 合成音效。
- 单风格命令（在 `engines/sy-styles-20` 里）：`node make.js list | still 09 6.5 --hwgpu | style 09 --hwgpu | reel 03,09,11 mini | cues`。WebGL/3D 风格加 `--hwgpu`，纯 2D 走 `--nogpu`。
- **Three.js（3D 实体）**：`lib/three.min.js` + `lib/three-reel.js`（`Reel.three`），模板 `templates/three-title`。抽象质感、光影材质继续用手写着色器；具体物体、文字、模型、相机路径用 Three.js。**写之前先读 `references/three.md`**（确定性规则、全局 THREE 冲突、地板发灰等坑）。
- 新做场景：复制最接近的风格（2D：03-flat / 06-morph / 08-hud / 17-editorial；WebGL：09-collage / 18-ink；3D：11-bauhaus；等轴城市：02-isometric），引用 `<技能目录>/engines/sy-styles-20/lib/core.js`（相对路径即可）。

## 整片构建（tools/）
新项目可直接 `node <技能目录>/tools/newproj.js <项目目录> --tpl three-title` 从模板生成（自动填引擎路径、music.json、render.args）。
项目目录放：
- `index.html`：sy-styles-20 场景契约，`duration` = 整片时长，cues 写全片音效；
- `music.json`：`{"name": "成片名", "total": 60}`（纯合成配乐时再加 `"note"` 与 `"sections":[{"kind":"04","start":0,"dur":60}]`）；
- `bgm.json`（用成品配乐时）：`{"music": "配乐.mp3", "edit": [[0, null]], "total": 60, "key": "C minor", "sfx_db": -5}`；
- 可选 `render.args`：WebGL 场景写 `--hwgpu`（默认 `--nogpu`）。

命令（在项目目录）：`node <技能目录>/tools/build.js still 3 8.5` 抽帧 → `... clip 0 10` 小样 → `... full --mb 3` 整片（`out/<name>.mp4`）。
只改声音不用重渲画面：重跑 `python <技能目录>/tools/mixbgm.py bgm.json out/cues.json out/music.wav`，再 `ffmpeg -i 片.mp4 -i out/music.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k 新片.mp4`。

## 自查（交付前必须）
- 抽帧看开头 / 钩子 / 高潮 / 结尾（Read 看图）；整片抽 9–15 帧拼联系表：`ffmpeg -i x.mp4 -vf "fps=1/6,scale=480:-1,tile=5x3" -frames:v 1 sheet.jpg`，查重叠、出界、遮挡。
- 响度：`ffmpeg -i x.mp4 -af ebur128=peak=true -f null -`，目标 -14 ~ -16 LUFS，真峰值 ≤ -1 dBTP。
- 对齐：关键时刻抽帧确认落在音乐重音上。
- 更多经验见 `references/lessons.md`。
