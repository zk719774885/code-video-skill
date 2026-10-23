# 图像 / 视频素材层

爆款片的"真实感"主要来自真实图像打底（见 `viral-study.md`）。素材统一用 `tools/assets.py` 搜、挑、下，并自动记账。

## 来源怎么选
| 来源 | 适合 | key | 授权要点 |
|---|---|---|---|
| **Wikimedia Commons** (`commons`) | 历史/人文/科普：名画、古籍、文物、历史照片、地图 | 不要 | 只收 PD / CC0 / CC BY / CC BY-SA；**CC BY 类片尾必须署名**（作者 + 授权），BY-SA 不要拿去做闭源商用素材包 |
| **Pexels** (`pexels`) | 写实照片和**高清视频**：自然、城市、人物、微距 | `PEXELS_API_KEY` | Pexels License：可商用、可改，不强制署名；不能把素材原样转卖，不能让人误以为图中人物背书 |
| **Pixabay** (`pixabay`) | 照片、插画、矢量、视频 | `PIXABAY_API_KEY` | Pixabay Content License：可商用、可改，不强制署名；限制同上 |
| AI 生图（可哥公司资源，待接） | 要"不存在的画面"、统一画风的系列背景 | 待定 | 按公司规定 |

## 用法
```
python -X utf8 <技能目录>/tools/assets.py search commons "Antikythera mechanism" --n 12
# → 编号列表 + assets/_preview.jpg 联系表，Read 看图挑
python -X utf8 <技能目录>/tools/assets.py get 2 5
# → assets/commons_<id>.jpg，账本 assets/ASSETS.json
```
`--video` 搜视频（Pexels/Pixabay/Commons），`--portrait` 竖图。搜索词用英文效果最好。

## 用在画面里（从爆款学到的做法）
- 背景慢推（Ken Burns，10 秒内放大 4–8%）+ 叠化 0.6–1 秒；一幕一张图。
- 统一调色：同一支片所有图压到同一色调（暗角 + 颗粒 + 统一色温/饱和度），否则会像 PPT。
- 代码只做"叠在上面的东西"：粒子、字幕、光斑、标注、图表、飘落物。
- 交付时把 `ASSETS.json` 里需要署名的条目写进片尾或简介。

## 注册步骤（给可哥）
key 不要发到对话里，存成本机环境变量，工具会自动读取：
```powershell
setx PEXELS_API_KEY "你的key"
setx PIXABAY_API_KEY "你的key"
```
**Pexels**：pexels.com → 右上角 Join（邮箱或 Google 账号注册）→ 打开 pexels.com/api → 点 "Your API Key"，填一个简单表单（用途写 "personal video projects"）→ 页面直接显示 key。免费额度约每小时 200 次、每月 2 万次。
**Pixabay**：pixabay.com → 右上角 Join（注册后去邮箱点验证链接）→ 登录状态下打开 pixabay.com/api/docs → 页面 "Parameters" 表格里 `key` 那一行就显示你的 key。免费额度每分钟 100 次。
