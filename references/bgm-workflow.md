# 成品配乐 + 卡点 + 动效音效（实战流程）

纯代码合成的配乐音色单薄，撑不起“高级感”宣传片。更好的做法：**选一首优秀的成品配乐当骨架 → 画面卡音乐 → 动效音效按配乐的调性生成、柔化后叠上去**。

## 1. 找配乐（免费、免登录优先）
| 来源 | 说明 |
|---|---|
| **Mixkit**（mixkit.co/free-stock-music） | 免费、无需注册，广告质感精选。页面里每首的 `data-audio-player-preview-url-value` 就是完整 mp3（`https://assets.mixkit.co/music/<id>/<id>.mp3`），可用 fetch 批量列出标题/时长/地址 |
| **Pixabay Music** | 曲库最大、免费；常有 Cloudflare 人机验证——验证必须由用户本人点，不能代点 |
| YouTube 音频库 | 质量稳，需用户自己登录谷歌账号（登录状态留在浏览器，不记录密码） |
| Uppbeat / Bensound / Incompetech | 免费档常需注册或署名 |
| Suno / Stable Audio | 可按描述生成专属曲，需账号 |

关键词：luxury、cinematic、elegant、premium、fashion、corporate、technology、ambient。
对外/商用必须确认授权；下载文件前先告诉用户文件名、来源、大小并征得同意。

## 2. 批量分析 + 试听挑选
```
python tools/bgmcard.py <放 mp3 的目录>
```
每首输出 BPM、时长、“最响 15 秒”起点，生成 `preview/*_15s.mp3` 和 `index.html` 试听页（用系统默认浏览器打开，内置预览面板里音频可能不能播）。让用户按编号挑。

## 3. 拆结构、测调
```
python -P beats.py 配乐.mp3 beats.json        # 拍点、小节首拍、重音
python tools/keydetect.py 配乐.mp3            # 例：C minor
```
再按小节算 RMS / 低频能量，找出：前奏、Drop（低频突然变强）、桥段、Breakdown（变安静）、第二次 Drop、结尾重音。
**对齐重击用 `onsets` / `accents`（10ms 精度的真实起音），不要直接用 `downbeats`**：小节首拍是拍格推算的，实测 We Never 的 Drop 在 17.051 秒，拍格给的小节首拍是 17.299 秒，晚了约半拍。impact/boom 照小节首拍放，就会和音乐重拍错开，形成「双响」，听起来像音乐被剪了一刀。`mixbgm.py` 混音时会自动检查：重击音效 ±0.4 秒内有音乐强起音、但差超过 30ms，就会提示该挪到哪里。

## 4. 画面卡音乐：分段线性时间映射
画面原本按自己的时间（“片时间”）设计，用映射把关键时刻钉到音乐上，其余段落按比例伸缩（每段速度最好在 0.85–1.25 倍之间，太快太慢都别扭）：
```js
// [片时间, 成片时间]：片名→小节首拍，爆发→Drop，高潮→第二次 Drop，终场→结尾重音
const WARP = [[0, 0], [8, 9.45], [10, 11.31], [18, 20.6], [34, 37.34], /* … */ [90, 95.6]];
function outToFilm(o) { for (let i = 0; i < WARP.length - 1; i++) { const [f0, o0] = WARP[i], [f1, o1] = WARP[i + 1]; if (o <= o1 || i === WARP.length - 2) return f0 + (f1 - f0) * Math.min(1, Math.max(0, (o - o0) / (o1 - o0))); } }
function filmToOut(f) { /* 反过来插值，用于把音效 cue 从片时间换到成片时间 */ }
Reel.scene({ duration: 95.6, render(tOut) { const t = outToFilm(tOut); /* 原 render(t) */ } });
// cues：CUES_ORIG.map(c => ({ ...c, t: filmToOut(c.t) }))
```
**默认：整首连续，不剪曲**（可哥的明确偏好：按小节剪接拼出来的配乐听起来「突然变成另一段、被截断」）。做法是：
1. `edit` 只写一段 `[[起点, null]]`，只选起点偏移，让最重要的一个重拍落在片名上；
2. 其余关键时刻用上面的分段映射去贴音乐（画面变速，不动音乐）；
3. 结尾 `fade_out` 约 4 秒长淡出，开头可加 `fade_in` 0.3–0.5 秒。
卡点不用刻意，叠化跟着**乐句**走就够了（爆款知识片实测也是这样）。
按小节补剪（`edit` 写多段，接口落在小节首拍、60ms 交叉淡化）只作为不得已的选项，一次最多一个接口，用之前先跟可哥说。

**已经渲染完才换配乐，不用重渲**：`tools/rewarp.py` 把已渲染的帧和 cues 按锚点分段变速（每段 0.9–1.1 倍，非整数帧处用相邻两帧混合），132 秒的片子几分钟就能换完曲。锚点取新配乐的 `accents` / `onsets`。

## 5. 动效音效：保留，但要适配
- **不要删**：每个元素出现、扫描、锁定、数据流都要有声音，否则画面显得单调。
- **有音高的一律进配乐的调**：`mixbgm.py` 会把 note 吸附到该调五声音阶并降八度，音色用柔和拨弦（基音 + 少量泛音 + 低八度），提示音/锁定/亮片/铺底和弦也按调生成。
- **去刺**：音高类低通 3.5–4 kHz，其余 5–7 kHz；加短混响（湿声约 0.2–0.35）。
- **关键时刻**加低频下沉重音（sub boom），Drop 前 3–4 秒加上升音。
- **电平**：音效总线比音乐低 5–9 dB；只软削极少数尖峰，**不要因为单个峰值把整条音效轨压低**（踩过的坑：实际被压了 8 dB）。
- 出片后测：`ffmpeg -i x.mp4 -af ebur128=peak=true -f null -`，目标 -14 ~ -16 LUFS、真峰值 ≤ -1 dBTP（AAC 编码会冒峰，混音末端加 alimiter）。
- **响度用静态增益，不用 loudnorm**：单遍 `loudnorm` 是动态增益，会把安静段抬起来、重拍压下去，音乐忽大忽小、不连贯。`mixbgm.py` 末端已经改成「ebur128 测整体响度 → 整条乘同一个增益 → alimiter 只挡峰值」，目标响度用 `lufs` 设置（默认 -15）。
- 只改声音时**不用重渲画面**：重混 `music.wav` 后 `ffmpeg -i 原片.mp4 -i music.wav -map 0:v -map 1:a -c:v copy -c:a aac 新片.mp4`。

## 6. bgm.json 示例（放项目目录，tools/build.js 会自动使用）
```json
{"music": "../bgm/wenever/opus_src.wav", "edit": [[2.115, null]], "total": 132.7, "key": "F minor", "sfx_db": -7, "fade_in": 0.5, "fade_out": 4.5}
```
按小节补剪的写法（不得已时）：`"edit": [[0, 15.02], [7.59, 15.02], [15.02, null]]`。
可哥喜欢用抖音爆款同款 BGM（如 We Never），会自己提供原视频，从里面分离音轨来用。
