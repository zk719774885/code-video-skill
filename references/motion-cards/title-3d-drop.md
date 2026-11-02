# 3D 金属字逐字落下
- 一句话意图：片名一个字一个字从上方落下、弹簧回弹，Drop 那一拍粒子炸开、光晕一闪。
- 适合：片头、章节标题、片尾落版。中文用 `R3.text3d`（只取用到的字形）。
- 参数表：
| 参数 | 值 | 说明 |
|---|---|---|
| 字 | size 1.5、depth 0.35、bevel 0.03，金属 metalness 1 roughness 0.22 | |
| 落下 | 每字间隔 0.4 s，`spring(k 120, c 9)`，起始高度 5，旋转 1.2 rad 归零 | |
| Drop | 轮廓光 25 × 冲击衰减；bloom 0.35 → +0.5 | 粒子环 320 个，outExpo 1.2 s 炸开 |
| 地板 | metalness 0.6、roughness 0.32、显式 `envMap` + envMapIntensity 0.08 | 只设 intensity 会发灰 |
| 机位 | 低机位慢推、Drop 后摇起 | |
- 声音：每字落地一个 block，Drop 前 riser_short，Drop 一个 impact（对齐 `beats.py` 的 onsets，避免双响）。
- 已知坑：bloom 过曝（threshold 0.92、strength ≤ 0.6）；页面里不要再声明 `THREE`。
- 参考实现：`templates/three-title/index.html`。
- 验收记录：技能样片（2026-10-21）。
