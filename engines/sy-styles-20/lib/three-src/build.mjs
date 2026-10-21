// 用法：node lib/three-src/build.mjs --nm <装了 three 和 esbuild 的 node_modules 目录>
import { createRequire } from 'module';
import path from 'path';
import { fileURLToPath } from 'url';
const here = path.dirname(fileURLToPath(import.meta.url));
const nm = process.argv[process.argv.indexOf('--nm') + 1];
const esbuild = createRequire(path.join(nm, 'x.js'))('esbuild');
await esbuild.build({
  entryPoints: [path.join(here, 'entry.js')], bundle: true, minify: true, format: 'iife', globalName: 'THREE',
  nodePaths: [nm], outfile: path.join(here, '..', 'three.min.js'), legalComments: 'eof', target: 'chrome110',
});
console.log('✔ lib/three.min.js');
