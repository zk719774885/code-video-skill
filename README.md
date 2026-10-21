# code-video · 让 Claude 用代码做视频的总调度技能

一个 [Claude Code](https://claude.com/claude-code) 技能（Skill）。你对 Claude 说“帮我做一个 xx 宣传片 / 知识科普视频 / 片头”，它会：

1. 在三个开源引擎里按场景选一个：**sy-styles-20**（质感短片、40 种现成风格）、**Remotion**（React、系列化模板）、**HyperFrames**（HTML+GSAP，素材/配音/网页转视频）；
2. 按“四步法”推进：定规格 → 卡点（`beats.py` 测 BPM 与重拍）→ 代码合成音效 → 先出 10 秒试片再逐段做；
3. 用 `tools/` 里的构建脚本一条命令出整片（画面逐帧渲染 + 代码合成配乐 + ffmpeg 合成）。

全程纯代码：不用素材库、不用版权音乐。

## 安装

**1. 装技能**（任选其一）

```bash
# 推荐：直接克隆到 Claude 的技能目录，以后 git pull 就能更新
git clone https://github.com/zk719774885/code-video-skill.git ~/.claude/skills/code-video
```

Windows 下 `~` 是 `C:\Users\<你的用户名>`。也可以下载 ZIP，把整个文件夹解压成 `~/.claude/skills/code-video/`（里面直接是 `SKILL.md`）。

**2. 装依赖**：Node 18+、Python 3.10+（`pip install numpy scipy`）、ffmpeg。

**3. 装引擎**（放在同一个目录下，记作 `VIDEO_HOME`，例如 `D:\AI\claude视频制作`）：

```bash
cd VIDEO_HOME
git clone https://github.com/xiaoxiong20xx-code/sy-styles-20.git
cd sy-styles-20 && npm install && npx playwright install chromium && cd ..
npx create-video@latest --yes --blank remotion-studio          # 可选：Remotion
npx hyperframes init hyperframes-studio --example blank --non-interactive   # 可选：HyperFrames
```

Remotion / HyperFrames 的官方 Claude 技能请按各自文档安装（可选）。

**4. 改路径**：打开 `SKILL.md`，把 `D:\AI\claude视频制作` 全部替换成你的 `VIDEO_HOME`；用 `tools/` 时设置环境变量 `SY_STYLES=<VIDEO_HOME>/sy-styles-20`。

## 用法

在 Claude Code 里直接说，例如：

> 帮我做一部 60 秒的产品宣传片，主题是 xxx，1920×1080，不配音、中文字幕，风格要水墨国风。先做开头 10 秒给我看。

## 更新

```bash
cd ~/.claude/skills/code-video && git pull
```

## 授权与致谢

- 本仓库：MIT。
- sy-styles-20：MIT，作者肖雄 XIAOXIONG；HyperFrames：Apache-2.0；Remotion：个人及 ≤3 人公司免费商用，更大的营利公司需购买 Company License。
- 四步法参考 B 站博主 小冯不意why「Vibe 知识大赏」教程。
