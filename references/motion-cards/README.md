# 动效卡库

**做法**：一个镜头手法 = 一张卡，记下我们**验收过**的参数，下次照着参考实现复制、换皮，而不是每次凭理解从头重写。思路参考 video-shotcraft（Apache-2.0）的镜头配方卡；卡的内容全部来自我们自己的项目。

## 规则
1. **用卡必须先读「参考实现」的源码**，在它的基础上改，不许凭卡名重写。
2. 「已知坑」里的参数**只升不降**：踩过的坑写进去以后，后面的项目只能更严。
3. **只收验收过的镜头**：可哥认可的成片、或独立评委（`../review.md`）该维度 ≥ 7 分的镜头。新卡在 `skill-feedback.md` 提，由技能迭代对话补进来。
4. 参考实现要放在技能里（`templates/`、`tools/`），或写清楚是哪个本地项目的哪个文件；本地项目路径会失效，重要的卡要把代码搬进 `templates/`。

## 卡片格式（照抄这个结构）
```
# <卡名>
- 一句话意图：这个镜头让观众感到什么 / 看懂什么
- 适合：题材、风格、片中位置；不适合：……
- 参数表：| 参数 | 值 | 说明 |（帧数或秒数、缓动、幅度、错峰、颜色、尺寸）
- 声音：配什么音效，落在哪一帧
- 已知坑：踩过的问题 + 现在的参数
- 参考实现：路径 + 函数名
- 验收记录：哪支片、哪个时间码、谁认可的
```

## 目录
| 卡 | 类别 | 参考实现 |
|---|---|---|
| [年份滚轮](year-odometer.md) | 信息 / 时间锚 | `templates/three-multishot/index.html` `drawYear` |
| [逐字字幕 + 英文副行](typewriter-subtitle.md) | 字幕 | `templates/three-multishot/index.html` `drawSubs` |
| [多镜头 2D 合成叠化](multishot-crossfade.md) | 转场 | `templates/three-multishot/index.html` `SHOTS` / `draw3D` |
| [档案卡片落桌](archive-desk-card.md) | 史料 / 实物质感 | `references/three.md`「档案图做成书桌上的实物卡片」 |
| [3D 金属字逐字落下](title-3d-drop.md) | 片名 | `templates/three-title/index.html` |
| [方块砸字 + 子弹时间](blender-smash.md) | 招牌镜头 | `templates/blender-smash/scene.py` |
