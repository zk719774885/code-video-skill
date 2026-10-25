# Three.js 3D（sy-styles-20 内用）

sy-styles-20 原有的 3D 风格（05/11/19 等）是手写 raymarch 着色器：质感顶级，但每个新造型都要写 SDF，改起来慢。
Three.js 补上的是**"真实物体"**：3D 中文/英文片名、SVG Logo 挤出、GLTF 产品模型、上千个实例粒子、相机路径、辉光/景深。
两者可以并存：极致质感、抽象画面 → 手写着色器；要具体物体、文字、模型 → Three.js。

## 快速开始
```
node <技能目录>/tools/newproj.js D:\AI\claude视频制作\<项目名> --tpl three-title
cd 进项目 → node <技能目录>/tools/build.js still 1.6 3.2 → clip 0 6 → full --mb 3
```
模板 `templates/three-title`：金属中文片名逐字落下 + 粒子环 + Drop 闪光 + 推镜头，6 秒。改 `Reel.cfg` 里的 title/sub/drop 即可复用。

## 文件
- `engines/sy-styles-20/lib/three.min.js`：three r181 + 常用扩展打成的经典脚本（全局 `THREE`，file:// 直接能用，离线）。
  扩展有：GLTFLoader、HDRLoader、SVGLoader、FontLoader/TTFLoader、TextGeometry、RoundedBoxGeometry、RoomEnvironment、
  EffectComposer/RenderPass/UnrealBloomPass/BokehPass/ShaderPass/OutputPass/SMAAPass、MeshSurfaceSampler、SimplexNoise、BufferGeometryUtils、opentype。
  升级或加扩展：改 `lib/three-src/entry.js`，再 `node lib/three-src/build.mjs --nm <装了 three 和 esbuild 的 node_modules>`。
- `engines/sy-styles-20/lib/three-reel.js`：`Reel.three(stage, opts)` 桥接。

## Reel.three API
```js
const R3 = Reel.three(stage, { bg, fov, exposure, env: true, shadows: true, bloom: { strength, radius, threshold }, dof: { focus, aperture, maxblur } });
R3.scene / R3.camera / R3.renderer / R3.bloom / R3.bokeh   // 直接操作
R3.render()                                                // render(t) 最后调用
await R3.text3d('片名', { font, size, depth, bevel, letterSpacing, material })  // 返回 Group，每个字是一个子 Mesh（原点在字中心，方便逐字动画）
await R3.svg('logo.svg', { depth, bevel, scale })          // SVG Logo → 3D，已居中
await R3.gltf('model.glb')                                 // 返回 gltf，动画用 new THREE.AnimationMixer(gltf.scene) + mixer.setTime(t)
await R3.hdr('studio.hdr', asBackground)                   // 换环境光照
const cam = R3.camPath([[t, [x,y,z], [lookX,lookY,lookZ]], ...]); cam(t)   // 关键帧相机，Catmull-Rom 平滑
```
- 中文 3D 字默认用 `C:/Windows/Fonts/simhei.ttf`（已验证）；想换 `Dengb.ttf`、思源等 ttf/otf，换完先抽帧确认字形完整。opentype 不读 .ttc（微软雅黑 msyh.ttc 不行）。
- 只取用到的字形，几十个字也很快；别用 TTFLoader 转整个中文字库（会卡几十秒）。

## 必守规则（踩过的坑）
- **确定性**：运动只由 t 决定；不用 `THREE.Clock`、`requestAnimationFrame`、`Math.random`（用 `Reel.rng(seed)`）；AnimationMixer 用 `setTime(t)`。不要用 AfterimagePass、GlitchPass（依赖上一帧/随机数）。
- **资源都在 `setup()` 里 await**，render 里不加载东西。
- **`THREE` 是全局变量**：页面里别写 `const { THREE } = R3` 或 `const THREE = ...`，会报 "Identifier 'THREE' has already been declared"，页面直接白屏（render.js 只会显示超时）。
- **file:// 读文件**：GLTF/HDR/字体靠 fetch，render.js 和 build.js 已带 `--allow-file-access-from-files`；用户自己双击打开预览时这些资源会加载失败，预览请 `npx serve` 起个本地服务。图片贴图（TextureLoader）不受影响。
- **地板发灰**：默认的 RoomEnvironment 在掠射角会把整个环境反射到地板上，深色地板变灰。地板材质显式写 `envMap: scene.environment, envMapIntensity: 0.05~0.15`（只设 envMapIntensity 不生效）。
- **辉光别过曝**：UnrealBloomPass 的 threshold 0.9 左右、strength 0.3–0.6；Drop 闪一下最多 +0.5，倒角高光很容易整片发白。
- **--mb 抖动**已由桥接层用 `camera.setViewOffset` 处理（运动模糊 + 抗锯齿都生效），场景里别自己再改 viewOffset。
- 渲染要加 `--hwgpu`（newproj 已写进 render.args）。本机 1080p、带辉光、`--mb 3`：约 1 秒/帧（6 秒片 3 分钟）。
  再加 Bokeh 景深 + 2048 阴影 + 2D 合成：每个子帧约 1 秒，`--mb 3` 约 3 秒/帧，132 秒片约 3.3 小时，BokehPass 是大头。整片用 `build.js full --mb 3 --jobs 10` 分段并行（24 线程机器；一般取线程数的 40%）。
- **--mb 时 t 可能为负**（第 0 帧快门前半）：render.js 已把 t 夹到 ≥ 0；场景里按帧号取数组仍要做正模：`arr[((Math.floor(t * 30) % N) + N) % N]`。

## 光强参考值（RoomEnvironment + SpotLight decay 1.4，实测不过曝）
| 光 | 强度 |
|---|---|
| 主光 SpotLight | 130–260 |
| 轮廓光 SpotLight | 70–140 |
| HemisphereLight | 0.2–0.35 |
| `envIntensity`（Reel.three 参数） | 0.35 |
| bloom | threshold 0.9、strength 0.3 |
初值写成 500–1300 会整片过曝。先抽一帧看曝光，再微调。

## 多镜头片：一张 2D 合成画布做叠化
一支片里有多个 3D 镜头（不同场景、不同机位）时，不要每个镜头一个 WebGL，而是：
```js
const GL = R3.renderer.domElement; GL.style.opacity = 0;          // WebGL 画布只当离屏渲染器
const OUT = Reel.canvas2d(stage), ctx = OUT.ctx;                 // 真正显示的是这张 2D 画布
const SHOTS = [ { a: 0, b: 14.6, f: shotOpen }, { a: 14.3, b: 20.3, xin: 0.3, f: shotTitle }, /* … */ ];  // 相邻镜头时间重叠 = 叠化
function draw3D(f, t, alpha) { f(t); R3.render(); ctx.globalAlpha = alpha; ctx.drawImage(GL, 0, 0, 1920, 1080); ctx.globalAlpha = 1; }
render(t) {
  OUT.begin(); ctx.fillStyle = BG; ctx.fillRect(0, 0, 1920, 1080);
  SHOTS.filter((s) => t >= s.a && t < s.b).forEach((s, i) => draw3D(s.f, t, i === 0 ? 1 : ss(s.a, s.a + s.xin, t)));
  drawSubs(t); drawYear(t); drawGrain(t); drawVignette();          // 字幕、年份滚轮、颗粒、暗角都画在同一张 2D 画布上
}
```
- 每个 `shotX(t)` 负责：切换可见的场景组、设相机、设景深焦点、设灯光。交叉溶解时同一帧渲两次 3D，渲染时间会翻倍，叠化别太长（0.3–0.6 秒）。
- 每个场景是一个 `THREE.Group`，用 `SETS[name].visible` 切换，雾和灯光也随镜头切。
- 常驻浮尘：一组 Points 挂在 `camera` 上（`scene.add(camera); camera.add(dust)`），所有镜头自动都有一层慢速粒子，画面一直在呼吸。

## 档案图做成「书桌上的实物卡片」
真实的老照片、专利图、博物馆照片，比直接平铺好看得多：
1. `createImageBitmap(await (await fetch(url)).blob())` 读图；先用 `assets.py grade duo|ink` 统一调色。
2. 画进一张 2D canvas：米黄底 + 边缘做旧渐变 + 斑点纸纹，图片四周留边，底部宽边写 Courier 说明文字（如 `U.S. PATENT 79,265 · 1868`）。
3. 贴到一个薄 Box（厚 0.03）的 +y 面（材质数组第 3 个），其余五个面用纸边色；`castShadow / receiveShadow` 打开。
4. SpotLight 跟随相机目标点打光，加软阴影和浅景深；卡片入场走抛物线滑入落桌，同时轻微旋转，落桌那一刻配 `paper` 或 `stamp` 音效。
白底博物馆照片放在这种卡片里也不违和。

## 选 Three.js 还是 HyperFrames 的 three 适配器
- 画面主体是 3D、要 sy-styles-20 的运动模糊 / cues 音效 / tools 一条命令出片 → 这里的 `Reel.three`。
- 3D 只是一层，叠在录屏、配音、字幕、HTML 组件上 → HyperFrames，读 `hyperframes-animation` 的 `adapters/three.md`（它用 `hf-seek` 事件驱动）。
