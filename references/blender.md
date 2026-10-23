# Blender 无头渲染：招牌镜头 + 模型转换

本机：`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`（5.2.3 LTS），Cycles 用 OptiX 跑 RTX 4070。
下文记 `B="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"`。

## 什么时候用 Blender，什么时候用 Three.js
| 需求 | 选 |
|---|---|
| 上千个刚体真实碰撞堆叠、子弹时间、路径追踪的柔和阴影/反射/焦散，追求"像实拍" | **Blender**（离线渲染，2–5 秒的招牌镜头） |
| 片子主体、多镜头、字幕叠层、要跟 cues 音效和运动模糊流程走 | **Three.js**（`Reel.three`，见 `three.md`） |
| 有现成模型（FBX、OBJ、IFC…）要在 Three.js 里用 | Blender 或 IfcConvert 先**转 glb**，再 `R3.gltf()` |
做法：Blender 渲出 PNG 序列 → 当素材放进 sy-styles-20 / HyperFrames 合成，字幕、HUD、音效仍在代码里做。

## 招牌镜头模板：`templates/blender-smash/scene.py`
3D 中文字 + 550 个刚体方块倾泻砸落 + 子弹时间（物理 `time_scale` 关键帧 1× → 0.12× → 1×）+ Cycles + 景深 + 运动模糊 + 亮面地板倒影。
```
cp <技能目录>/templates/blender-smash/scene.py 项目目录/   # 改 CFG：文字、字体、颜色、方块数、时长、慢动作区间
"$B" -b --factory-startup --python scene.py -- --still 4.5 --samples 32 --scale 50   # 先抽一帧看构图（约 35 秒，含烘焙物理）
"$B" -b --factory-startup --python scene.py -- --from 0 --to 6 --samples 64           # 正式出序列帧 → frames/blender/f00000.png…
ffmpeg -framerate 30 -start_number 0 -i frames/blender/f%05d.png -c:v libx264 -crf 16 -pix_fmt yuv420p out/blender.mp4
```
- 帧号 = 秒 × 30，和 sy-styles-20 的时间轴一致；`--from/--to` 可只重渲一段。
- 物理每次都从头烘焙（确定性：随机数用固定种子），所以 `--still` 和序列帧的同一时刻画面一致。
- 构图经验：八成方块落在字后面，前景留给字；相机慢推 + 轻微下降，对焦在字上（光圈 f/2.8）。
- 中文字体直接用 ttf/otf（`bpy.data.fonts.load`），`simhei.ttf` 已验证；文字转成网格后当被动刚体，方块会砸在字上弹开。
- 性能（RTX 4070 实测）：960×540、16 采样、带运动模糊，120 帧连同物理烘焙共 4 分 24 秒（约 2 秒/帧）；1080p 是 4 倍像素、64 采样还会更慢，正式出片前先渲 10 帧测速。长镜头放后台渲染，渲之前先跟可哥说预计时间。
- 子弹时间要卡在方块**下落途中**（默认 0.5–3.0 秒），落地以后再慢放就看不出来了。

## 模型转 glTF：`tools/to_gltf.py`
```
"$B" -b --factory-startup --python <技能目录>/tools/to_gltf.py -- 输入.fbx 输出.glb [--decimate 0.3] [--scale 0.001] [--center]
```
- 支持 FBX、OBJ、STL、PLY、glTF、USD、Alembic。`--decimate` 给网页减面（几十万面的建筑模型先降到 0.1–0.3），`--scale 0.001` 把毫米单位换成米，`--center` 移到原点并落地。
- **IFC（BIM 模型）**：Blender 不自带 IFC 导入。用 IfcOpenShell 的 `IfcConvert model.ifc model.glb` 直接转；或者在 Blender 里装 Bonsai 扩展后再导入。
- **RVT（Revit）**：只能先在 Revit 里导出 IFC 或 FBX；**DWG/DXF** 先转成 FBX/OBJ。
- 转出来的 glb 用 `const g = (await R3.gltf('model.glb')).scene; R3.scene.add(g)`，自带材质会保留；需要统一质感时遍历 mesh 换成自己的 `MeshStandardMaterial`。
