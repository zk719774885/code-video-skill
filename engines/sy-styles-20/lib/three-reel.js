/* Three.js 桥接：在 sy-styles-20 的 Reel 契约里用 three 搭 3D 场景（需先引 core.js、three.min.js）。
 *   const R3 = Reel.three(stage, { bg: '#0b0d12', fov: 32, bloom: { strength: .6, radius: .4, threshold: .85 } });
 *   R3.scene.add(...);  Reel.scene({ duration, setup: async () => { ...await R3.gltf(url) / R3.text3d(...) }, render(t) { ...; R3.render(); } });
 * 约定：所有运动只由 t 决定（不用 Clock / requestAnimationFrame / Math.random，随机用 Reel.rng）；
 *       AnimationMixer 用 mixer.setTime(t)；资源一律在 setup 里 await 加载完。
 * 渲染：渲染分辨率跟随 rs，--mb 的子像素抖动通过 camera.setViewOffset 实现（运动模糊 + 抗锯齿都生效）。
 */
(function () {
  const THREE = window.THREE;
  const { W, H, RS } = Reel;

  function three(stage, o = {}) {
    Reel.ownJitter = true;
    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, alpha: !!o.alpha, powerPreference: 'high-performance' });
    renderer.setPixelRatio(1);
    renderer.setSize(Math.round(W * RS), Math.round(H * RS), false);
    renderer.domElement.style.cssText = `position:absolute;left:0;top:0;width:${W}px;height:${H}px`;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = o.exposure ?? 1;
    if (o.shadows !== false) { renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; }
    stage.prepend(renderer.domElement);

    const scene = new THREE.Scene();
    if (!o.alpha) scene.background = new THREE.Color(o.bg || '#000');
    const camera = new THREE.PerspectiveCamera(o.fov || 35, W / H, o.near || 0.1, o.far || 200);
    // 默认给一个摄影棚环境光照，金属/玻璃/车漆不用 HDR 文件也有反射
    if (o.env !== false) {
      const pm = new THREE.PMREMGenerator(renderer);
      scene.environment = pm.fromScene(new THREE.RoomEnvironment(), 0.04).texture;
      scene.environmentIntensity = o.envIntensity ?? 1;
    }

    let composer = null, bloom = null, bokeh = null;
    if (o.bloom || o.dof) {
      composer = new THREE.EffectComposer(renderer);
      composer.setPixelRatio(1);
      composer.setSize(Math.round(W * RS), Math.round(H * RS));
      composer.addPass(new THREE.RenderPass(scene, camera));
      if (o.bloom) { const b = o.bloom; bloom = new THREE.UnrealBloomPass(new THREE.Vector2(W * RS, H * RS), b.strength ?? 0.6, b.radius ?? 0.4, b.threshold ?? 0.85); composer.addPass(bloom); }
      if (o.dof) { const d = o.dof; bokeh = new THREE.BokehPass(scene, camera, { focus: d.focus ?? 10, aperture: d.aperture ?? 0.002, maxblur: d.maxblur ?? 0.008 }); composer.addPass(bokeh); }
      composer.addPass(new THREE.OutputPass());
    }

    function render() {
      // --mb 抖动：Reel.jit 是输出像素，换算到 1920x1080 的视口偏移
      const j = Reel.jit || [0, 0];
      if (j[0] || j[1]) camera.setViewOffset(W, H, -j[0] / RS, -j[1] / RS, W, H); else camera.clearViewOffset();
      if (composer) composer.render(); else renderer.render(scene, camera);
    }

    // ---- 资源（file:// 下需 render.js 带 --allow-file-access-from-files，已默认加）----
    const gltf = (url) => new THREE.GLTFLoader().loadAsync(url);
    const hdr = async (url, asBackground) => {
      const tex = await new THREE.HDRLoader().loadAsync(url); tex.mapping = THREE.EquirectangularReflectionMapping;
      scene.environment = tex; if (asBackground) scene.background = tex; return tex;
    };
    const svg = async (url, { depth = 20, bevel = 2, material, scale = 1 } = {}) => {
      // SVG Logo → 挤出 3D，居中，y 轴翻正
      const data = await new THREE.SVGLoader().loadAsync(url);
      const g = new THREE.Group();
      for (const p of data.paths) {
        const mat = material || new THREE.MeshStandardMaterial({ color: p.color, metalness: 0.3, roughness: 0.35 });
        for (const s of THREE.SVGLoader.createShapes(p)) g.add(new THREE.Mesh(new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: bevel > 0, bevelSize: bevel, bevelThickness: bevel, bevelSegments: 4, curveSegments: 16 }), mat));
      }
      g.scale.set(scale, -scale, scale);
      const box = new THREE.Box3().setFromObject(g), c = box.getCenter(new THREE.Vector3());
      g.children.forEach((m) => m.geometry.translate(-c.x / scale, c.y / scale, -c.z / scale));
      return g;
    };

    // 3D 文字（支持中文）：只取用到的字形，不像 TTFLoader 那样把整个中文字库转一遍
    const fonts = {};
    async function font(url) {
      if (!fonts[url]) fonts[url] = fetch(url).then((r) => r.arrayBuffer()).then((b) => THREE.opentype.parse(b));
      return fonts[url];
    }
    async function text3d(str, { font: url = 'C:/Windows/Fonts/simhei.ttf', size = 1, depth = 0.2, bevel = 0.02, letterSpacing = 0, material, align = 'center', perChar = false } = {}) {
      const f = await font(url.includes(':') && !url.startsWith('file:') && !url.startsWith('http') ? 'file:///' + url : url);
      const mat = material || new THREE.MeshStandardMaterial({ color: '#ffffff', metalness: 0.6, roughness: 0.25 });
      const k = size / f.unitsPerEm;
      const group = new THREE.Group();
      let x = 0;
      for (const ch of Array.from(str)) {
        const glyph = f.charToGlyph(ch);
        const sp = new THREE.ShapePath();
        for (const c of glyph.getPath(0, 0, f.unitsPerEm).commands) {
          // opentype 是 y 向下，翻成 y 向上
          if (c.type === 'M') sp.moveTo(c.x, -c.y);
          else if (c.type === 'L') sp.lineTo(c.x, -c.y);
          else if (c.type === 'Q') sp.quadraticCurveTo(c.x1, -c.y1, c.x, -c.y);
          else if (c.type === 'C') sp.bezierCurveTo(c.x1, -c.y1, c.x2, -c.y2, c.x, -c.y);
        }
        const shapes = sp.toShapes(true);
        const adv = (glyph.advanceWidth || f.unitsPerEm) * k;
        if (shapes.length) {
          const geo = new THREE.ExtrudeGeometry(shapes, { depth: depth / k, bevelEnabled: bevel > 0, bevelSize: bevel / k, bevelThickness: bevel / k, bevelSegments: 3, curveSegments: 8 });
          geo.scale(k, k, k);
          geo.translate(-adv / 2, -size * 0.38, -depth / 2);   // 每个字以自身中心为原点，方便逐字动画
          const m = new THREE.Mesh(geo, mat); m.castShadow = true;
          m.position.x = x + adv / 2; m.userData.char = ch;
          group.add(m);
        }
        x += adv + letterSpacing * size;
      }
      const w = x - letterSpacing * size, off = align === 'center' ? -w / 2 : align === 'right' ? -w : 0;
      group.children.forEach((m) => (m.position.x += off));
      group.userData.width = w;
      return group;
    }

    // 相机路径：keys = [[t, [x,y,z], [lookX,lookY,lookZ]], ...]，Catmull-Rom 平滑插值，ease 作用在段内
    function camPath(keys, ease = Reel.E.inOutSine) {
      const pos = new THREE.CatmullRomCurve3(keys.map((k) => new THREE.Vector3(...k[1])));
      const tgt = new THREE.CatmullRomCurve3(keys.map((k) => new THREE.Vector3(...k[2])));
      const n = keys.length - 1;
      return (t) => {
        let i = 0; while (i < n - 1 && t > keys[i + 1][0]) i++;
        const u = (i + ease(Reel.inv(keys[i][0], keys[i + 1][0], t))) / n;
        camera.position.copy(pos.getPoint(u)); camera.lookAt(tgt.getPoint(u));
      };
    }

    return { THREE, renderer, scene, camera, composer, bloom, bokeh, render, gltf, hdr, svg, font, text3d, camPath };
  }

  Reel.three = three;
})();
