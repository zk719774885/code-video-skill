#!/usr/bin/env node
// 通用构建：在项目目录执行 node <技能目录>/tools/build.js still 3 5 | clip a b [--mb N] [--jobs N] | full [--mb N] [--jobs N]（--jobs 分段并行渲染，独显上 2–4 合适）
// 项目目录需有 index.html、music.json（name、total；纯合成配乐时再写 sections、note）；用成品配乐时另放 bgm.json；可选 render.args（如 --hwgpu）
const { spawnSync, spawn } = require('child_process');
const fs = require('fs'), path = require('path');
const ROOT = process.cwd(), SY = process.env.SY_STYLES || path.join(__dirname, '..', 'engines', 'sy-styles-20');
const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const args = argv.filter((a, i) => !a.startsWith('--') && !(argv[i - 1] || '').startsWith('--'));
const out = (...p) => path.join(ROOT, 'out', ...p);
fs.mkdirSync(out(), { recursive: true });
const HTML = path.join(ROOT, 'index.html');
const MJ = JSON.parse(fs.readFileSync(path.join(ROOT, 'music.json'), 'utf8'));
const extra = fs.existsSync(path.join(ROOT, 'render.args')) ? fs.readFileSync(path.join(ROOT, 'render.args'), 'utf8').trim().split(/\s+/) : ['--nogpu'];
function run(cmd, a) { const r = spawnSync(cmd, a, { cwd: ROOT, stdio: 'inherit' }); if (r.status !== 0) { console.error(`${cmd} 失败（${r.status}）`); process.exit(1); } }
async function dumpCues() {
  const { chromium } = require(path.join(SY, 'node_modules', 'playwright'));
  const b = await chromium.launch({ args: ['--disable-gpu', '--allow-file-access-from-files'] }); const p = await b.newPage();
  await p.goto(require('url').pathToFileURL(HTML).href + '?render=1');
  await p.waitForFunction(() => typeof window.__seek === 'function');
  const cues = await p.evaluate(() => window.__cues); await b.close();
  fs.writeFileSync(out('cues.json'), JSON.stringify(cues));
}
async function clip(a, b, name) {
  const fdir = path.join(ROOT, 'frames', name); fs.rmSync(fdir, { recursive: true, force: true });
  // --jobs N：按帧号切成 N 段，各开一个浏览器并行渲染到同一个 frames 目录
  const jobs = Math.max(1, parseInt(opt('jobs', '1'))), n0 = Math.round(a * 30), n1 = Math.round(b * 30);
  const segs = Array.from({ length: jobs }, (_, i) => [n0 + Math.round(((n1 - n0) * i) / jobs), n0 + Math.round(((n1 - n0) * (i + 1)) / jobs)]).filter(([x, y]) => y > x);
  const codes = await Promise.all(segs.map(([x, y]) => new Promise((res) => {
    const p = spawn('node', [path.join(SY, 'render.js'), HTML, 'x', ...extra, '--mb', opt('mb', '3'), '--from', String(x / 30), '--to', String(y / 30), '--frames', fdir], { cwd: ROOT, stdio: jobs > 1 ? ['ignore', 'ignore', 'inherit'] : 'inherit' });
    p.on('close', res);
  })));
  if (codes.some((c) => c !== 0)) { console.error('渲染失败（退出码 ' + codes.join(',') + '）'); process.exit(1); }
  await dumpCues();
  if (fs.existsSync(path.join(ROOT, 'bgm.json'))) {      // 成品配乐 + 动效音效
    run('python', ['-X', 'utf8', path.join(__dirname, 'mixbgm.py'), path.join(ROOT, 'bgm.json'), out('cues.json'), out('music.wav')]);
  } else {                                              // 纯代码合成配乐
    fs.writeFileSync(out('music_plan.json'), JSON.stringify(MJ));
    run('python', ['-X', 'utf8', path.join(__dirname, 'mixplan.py'), out('music_plan.json'), out('cues.json'), out('music.wav')]);
  }
  const mp4 = out(`${name}.mp4`);
  run('ffmpeg', ['-y', '-v', 'error', '-framerate', '30', '-start_number', String(Math.round(a * 30)), '-i', path.join(fdir, 'f%05d.jpg'), '-ss', String(a), '-t', String(b - a), '-i', out('music.wav'),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', mp4]);
  console.log('✔ ' + mp4);
}
(async () => {
  const cmd = args[0];
  if (cmd === 'still') run('node', [path.join(SY, 'render.js'), HTML, 'x', ...extra, ...args.slice(1).flatMap((t) => ['--still', `${t}:${out(`still_${t}.jpg`)}`])]);
  else if (cmd === 'clip') await clip(parseFloat(args[1]), parseFloat(args[2]), `clip_${args[1]}-${args[2]}`);
  else if (cmd === 'full') await clip(0, MJ.total, MJ.name || 'full');
  else console.log('用法见文件头');
})();
