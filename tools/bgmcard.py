"""候选配乐批量分析 + 试听页：python bgmcard.py <放 mp3 的目录>
每首：beats.py 测 BPM/重拍；找最响的 15 秒当“高潮试听”；输出 cards.json 和 index.html（浏览器打开即可试听）。"""
import json, subprocess, sys, os, glob
import numpy as np
d = sys.argv[1]; beats = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'beats.py')
os.makedirs(os.path.join(d, 'preview'), exist_ok=True); cards = []
for f in sorted(glob.glob(os.path.join(d, '*.mp3'))):
    name = os.path.splitext(os.path.basename(f))[0]
    bj = os.path.join(d, 'preview', name + '.beats.json')
    subprocess.run([sys.executable, '-P', beats, f, bj], capture_output=True)
    b = json.load(open(bj, encoding='utf8')) if os.path.exists(bj) else {}
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', '8000', '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32); sr = 8000
    rms = np.sqrt(np.convolve(x * x, np.ones(sr) / sr, 'valid')[::sr // 4] + 1e-12)   # 1s 窗口，每 0.25s
    win = 60  # 15s
    cs = np.convolve(rms, np.ones(win), 'valid'); start = float(np.argmax(cs)) * 0.25
    peak = float(np.argmax(rms)) * 0.25
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', str(start), '-t', '15', '-i', f, '-af', 'afade=t=in:d=0.5,afade=t=out:st=14:d=1', os.path.join(d, 'preview', name + '_15s.mp3')])
    cards.append({'name': name, 'dur': round(len(x) / sr, 1), 'bpm': b.get('bpm'), 'climax_15s_start': round(start, 1), 'loudest_sec': round(peak, 1), 'accents': (b.get('accents') or b.get('strong') or [])[:6]})
json.dump(cards, open(os.path.join(d, 'cards.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
for c in cards: print(c)

rows = ''.join(f"""<div class=c><b>{i+1:02d} · {c['name'].replace('_',' ')}</b><div class=m>{c['bpm']} BPM · {int(c['dur']//60)}:{int(c['dur']%60):02d} · 高潮约 {c['climax_15s_start']}s</div>
<div class=a><label>高潮 15 秒</label><audio controls preload=none src="preview/{c['name']}_15s.mp3"></audio></div><div class=a><label>完整</label><audio controls preload=none src="{c['name']}.mp3"></audio></div></div>""" for i, c in enumerate(cards))
open(os.path.join(d, 'index.html'), 'w', encoding='utf8').write(f"""<!doctype html><meta charset=utf-8><title>配乐候选试听</title><style>body{{background:#0d0f14;color:#e8e8ee;font:15px sans-serif;max-width:900px;margin:30px auto;padding:0 16px}}.c{{background:#161a22;border-radius:12px;padding:14px 18px;margin:12px 0}}.m{{color:#8a93a6;font-size:13px;margin:6px 0}}.a{{display:flex;gap:10px;align-items:center}}.a label{{width:80px;color:#9aa}}audio{{flex:1}}</style><h1>配乐候选试听</h1>{rows}""")
print('试听页：', os.path.join(d, 'index.html'))
