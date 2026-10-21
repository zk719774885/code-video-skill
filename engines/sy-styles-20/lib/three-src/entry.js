// 打包入口：three 本体 + 做视频常用的扩展 → lib/three.min.js（经典脚本，挂到 window.THREE，file:// 直接能用）
// 重新打包：node lib/three-src/build.mjs（需先在任意目录 npm i three@<版本> esbuild，并传 --nm <node_modules 路径>）
export * from 'three';
export { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
export { HDRLoader } from 'three/examples/jsm/loaders/HDRLoader.js';
export { SVGLoader } from 'three/examples/jsm/loaders/SVGLoader.js';
export { FontLoader, Font } from 'three/examples/jsm/loaders/FontLoader.js';
export { TTFLoader } from 'three/examples/jsm/loaders/TTFLoader.js';
export { TextGeometry } from 'three/examples/jsm/geometries/TextGeometry.js';
export { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
export { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
export { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
export { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
export { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
export { BokehPass } from 'three/examples/jsm/postprocessing/BokehPass.js';
export { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';
export { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
export { SMAAPass } from 'three/examples/jsm/postprocessing/SMAAPass.js';
export { MeshSurfaceSampler } from 'three/examples/jsm/math/MeshSurfaceSampler.js';
export { SimplexNoise } from 'three/examples/jsm/math/SimplexNoise.js';
export * as BufferGeometryUtils from 'three/examples/jsm/utils/BufferGeometryUtils.js';
export { default as opentype } from 'three/examples/jsm/libs/opentype.module.js';
