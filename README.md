# code-video · 让 Claude 用代码做视频的总调度技能

一个 [Claude Code](https://claude.com/claude-code) 技能（Skill）。你对 Claude 说“帮我做一个 xx 宣传片 / 知识科普视频 / 片头”，它会：

1. 在三个开源引擎里按场景选一个：**sy-styles-20**（质感短片、40 种现成风格，随本仓库自带）、**Remotion**（React、系列化模板）、**HyperFrames**（HTML+GSAP，素材/配音/网页转视频）；
2. 先定配乐（优先免费成品配乐），用 `beats.py` 测节拍和重音、`keydetect.py` 测调，画面卡音乐；
3. 动效音效按配乐的调性生成、柔化后叠上去；
4. 按“四步法”推进：定规格 → 卡点 → 配音效 → 先出 10 秒试片再逐段做；
5. 用 `tools/build.js` 一条命令出整片（逐帧渲染 + 混音 + ffmpeg 合成）。

画面全程纯代码，不用素材库。

## 安装（两步）

```bash
# 1. 克隆到 Claude 的技能目录（Windows 下 ~ 是 C:\Users\<你的用户名>）
git clone https://github.com/zk719774885/code-video-skill.git ~/.claude/skills/code-video

# 2. 运行一次安装脚本（自动装 numpy/scipy、引擎依赖、无头浏览器）
cd ~/.claude/skills/code-video
powershell -ExecutionPolicy Bypass -File install.ps1          # Windows
bash install.sh                                               # macOS / Linux
```

前置：Node 18+、Python 3.10+、ffmpeg（脚本会检查）。
可选：加 `-Remotion -HyperFrames`（Windows）或 `--remotion --hyperframes`（macOS/Linux）同时安装 Remotion、HyperFrames 及它们的官方 Claude 技能；`-VideoHome <目录>` / `--video-home <目录>` 指定视频项目存放目录。

**sy-styles-20 引擎已经随本仓库自带**（`engines/sy-styles-20`），不用另外下载。

## 仓库里有什么

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 技能本体：选引擎、四步法、配乐与音效规则、构建命令 |
| `engines/sy-styles-20/` | 渲染引擎与 40 种风格（作者肖雄 XIAOXIONG，MIT，已修 Windows 盘符 bug） |
| `beats.py` | 卡点：BPM、每拍、小节首拍、重音 |
| `tools/build.js` | 一条命令出整片（逐帧渲染 + 配乐 + 合成） |
| `tools/mixbgm.py` | 成品配乐 + 动效音效混音（按配乐调性生成、柔化、混响、限幅） |
| `tools/mixplan.py` | 纯代码合成配乐（兜底） |
| `tools/bgmcard.py` | 候选配乐批量分析 + 试听页 |
| `tools/keydetect.py` | 测配乐的调 |
| `references/` | 配乐全流程、实战经验、小冯「Vibe 知识大赏」教程整理 |

## 用法

在 Claude Code 里直接说，例如：

> 帮我做一部 60 秒的产品宣传片，主题是 xxx，1920×1080，不配音、中文字幕，风格要赛博 HUD。先帮我找几首高级感的免费配乐让我挑，再做开头 10 秒给我看。

## 更新

```bash
cd ~/.claude/skills/code-video && git pull
```

## 授权与致谢

- 本仓库：MIT。
- `engines/sy-styles-20`：MIT，Copyright (c) 2026 肖雄 XIAOXIONG（原仓库 github.com/xiaoxiong20xx-code/sy-styles-20），原 LICENSE 保留在该目录。
- HyperFrames：Apache-2.0；Remotion：个人及 ≤3 人公司免费商用，更大的营利公司需购买 Company License（二者由安装脚本从官方下载，未收录在本仓库）。
- 四步法与「Vibe 知识大赏」范式参考博主 小冯不意why 的教程，整理见 `references/xiaofeng-method.md`。
- 配乐请遵守各曲库授权；本仓库不含任何音乐文件。
