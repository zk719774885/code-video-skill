#!/usr/bin/env node
// 从模板新建项目：node <技能目录>/tools/newproj.js <项目目录> [--tpl three-title]
// 复制 templates/<tpl>/ 到项目目录，把 index.html 里的 SY/ 换成引擎 lib 的实际路径（同盘用相对路径，跨盘用 file:/// 绝对路径），
// 并补上 music.json；three 模板自动写 render.args = --hwgpu。
const fs = require('fs'), path = require('path');
const { pathToFileURL } = require('url');
const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const dest = path.resolve(argv.find((a, i) => !a.startsWith('--') && !(argv[i - 1] || '').startsWith('--')) || '');
const tpl = opt('tpl', 'three-title');
const src = path.join(__dirname, '..', 'templates', tpl);
const SY = process.env.SY_STYLES || path.join(__dirname, '..', 'engines', 'sy-styles-20');
if (!fs.existsSync(src)) { console.error('没有这个模板：' + tpl + '（可选：' + fs.readdirSync(path.join(__dirname, '..', 'templates')).join(' / ') + '）'); process.exit(1); }
if (fs.existsSync(path.join(dest, 'index.html'))) { console.error('目标目录已有 index.html，不覆盖：' + dest); process.exit(1); }
// 不用 fs.cpSync：Node 24 在 Windows 上复制到含中文的目录时什么都不复制也不报错
function copyDir(a, b) {
  fs.mkdirSync(b, { recursive: true });
  for (const e of fs.readdirSync(a, { withFileTypes: true })) {
    const s = path.join(a, e.name), d = path.join(b, e.name);
    if (e.isDirectory()) copyDir(s, d); else fs.writeFileSync(d, fs.readFileSync(s));
  }
}
copyDir(src, dest);
if (!fs.existsSync(path.join(dest, 'index.html'))) { console.error('复制模板失败：' + dest); process.exit(1); }
const sameDrive = path.parse(dest).root.toLowerCase() === path.parse(SY).root.toLowerCase();
const syRef = sameDrive ? path.relative(dest, SY).split(path.sep).join('/') : pathToFileURL(SY).href;
const html = path.join(dest, 'index.html');
fs.writeFileSync(html, fs.readFileSync(html, 'utf8').replace(/(["'])SY\//g, `$1${syRef}/`));
const mj = path.join(dest, 'music.json');
if (!fs.existsSync(mj)) fs.writeFileSync(mj, JSON.stringify({ name: path.basename(dest), total: 6, note: 'bell', sections: [{ kind: '05', start: 0, dur: 6 }] }, null, 1));
if (tpl.startsWith('three') && !fs.existsSync(path.join(dest, 'render.args'))) fs.writeFileSync(path.join(dest, 'render.args'), '--hwgpu');
console.log(`✔ ${dest}\n  引擎引用：${syRef}\n  下一步：cd 进去，node ${path.join(__dirname, 'build.js')} still 1.6 3.2`);
