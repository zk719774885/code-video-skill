"""成片构图量化：主体有多大、哪里是空场、字幕在屏幕上实际多高。规则见 references/composition.md。
用法：python -X utf8 frame_metrics.py 成片.mp4 [--step 0.25] [--sub 0.78:0.98] [--from 0 --to 结尾] [--csv out.csv]
  --sub a:b   字幕所在的竖直带（占帧高的比例，默认 0.78–0.98；竖屏字幕偏上时自己改，如 0.62:0.80）；--sub none 不测字幕
输出：
  · 主体尺度：每个采样帧里最大物体的「尺度」占帧高的比例。尺度 = max(高, min(宽, 4×高)/2.5)：
    方块看高度；一行大字这种宽而矮的物体按宽度折算一部分，免得整行标题被当成「小东西」。
  · 空场：主体尺度 < 10% 帧高、持续超过 1.5 秒的时段（< 7% 记为严重）。
  · 字幕字高：字幕带里文字行的像素高度。横屏要求 ≥ 5% 帧高（1080p 约 54px）；竖屏按缩到 480px 宽仍可读：≥ 60px（1080 宽）。测量误差约 ±15%，只当提示。
原理：灰度轻度模糊（压掉纸纹、颗粒）后求梯度，梯度强的地方是「有东西」，闭运算把轮廓和笔画连成块，再取连通块外框。
它只是量尺，不是审美：数字异常的地方抽帧看一眼再下结论（大面积纯色主体、整屏纹理背景会骗过它）。
"""
import subprocess, sys
import numpy as np
from scipy import ndimage as ndi

W = 480   # 分析分辨率（宽）


def opt(a, k, d=None):
    return a[a.index('--' + k) + 1] if '--' + k in a else d


def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration',
                        '-of', 'default=nw=1', path], capture_output=True, text=True).stdout
    d = dict(l.split('=') for l in r.split() if '=' in l)
    return int(d['width']), int(d['height']), float(d['duration'])


def frames(path, t0, t1, step, w, h):
    """按 step 秒取帧，缩到 W 宽的灰度图。"""
    hh = round(h * W / w / 2) * 2
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(t0), '-t', str(t1 - t0), '-i', path, '-vf', f'fps=1/{step},scale={W}:{hh},format=gray', '-f', 'rawvideo', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = W * hh
    i = 0
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n: break
        yield t0 + i * step, np.frombuffer(buf, np.uint8).reshape(hh, W).astype(np.float32)
        i += 1


def detail_mask(g):
    s = ndi.gaussian_filter(g, 1.5)
    mag = np.hypot(ndi.sobel(s, 0), ndi.sobel(s, 1)) / 8
    return mag > 6


def subject_scale(m):
    """最大物体的尺度（像素，分析分辨率下）和它的外框。"""
    H, Wd = m.shape
    c = ndi.binary_closing(m, np.ones((7, 7)), iterations=2)
    c = ndi.binary_closing(c, np.ones((1, 15)))          # 一行字的字与字连起来
    c = ndi.binary_fill_holes(c)
    lab, n = ndi.label(c)
    best, box = 0.0, None
    for sl in ndi.find_objects(lab):
        hgt, wid = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if hgt * wid < 0.0015 * H * Wd: continue
        if hgt > 0.97 * H and wid > 0.97 * Wd: continue   # 整屏边框、满屏纹理
        if hgt <= 2: continue                              # 细线（地平线、分隔线）
        sc = max(hgt, min(wid, 4 * hgt) / 2.5)
        if sc > best: best, box = sc, sl
    return best, box


def caption_height(m, band):
    """字幕带里最高的一行文字的高度（分析分辨率像素）。"""
    H = m.shape[0]
    a, b = int(band[0] * H), int(band[1] * H)
    sub = ndi.binary_closing(m[a:b], np.ones((1, 9)))     # 只横向连笔画，两行字幕不能粘成一行
    rows = sub.sum(1) > max(6, 0.01 * sub.shape[1])
    lab, n = ndi.label(rows)
    hs = [s[0].stop - s[0].start for s in ndi.find_objects(lab)]
    hs = [x for x in hs if x >= 3]
    return max(hs) if hs else 0


def spans(ts, flags, step, min_dur):
    out, start = [], None
    for t, f in zip(ts + [ts[-1] + step], flags + [False]):
        if f and start is None: start = t
        if not f and start is not None:
            if t - start > min_dur: out.append((start, t))
            start = None
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    path = a[0]
    w, h, dur = probe(path)
    step = float(opt(a, 'step', 0.25))
    t0, t1 = float(opt(a, 'from', 0)), float(opt(a, 'to', dur))
    sub = opt(a, 'sub', '0.78:0.98')
    band = None if sub == 'none' else tuple(float(x) for x in sub.split(':'))
    portrait = h > w
    scale_back = w / W          # 分析像素 → 原片像素
    ts, subj, caps = [], [], []
    for t, g in frames(path, t0, t1, step, w, h):
        m = detail_mask(g)
        body = m.copy()
        if band: body[int(band[0] * m.shape[0]):int(band[1] * m.shape[0])] = False   # 主体不算字幕
        sc, _ = subject_scale(body)
        ts.append(round(t, 2)); subj.append(sc * scale_back / h)
        caps.append(caption_height(m, band) * scale_back if band else 0)
    if not ts:
        sys.exit('没取到帧')
    subj_a = np.array(subj)
    print(f'{path}  {w}×{h}  {t0:.1f}–{t1:.1f}s  每 {step}s 采样，共 {len(ts)} 帧')
    print(f'主体尺度（占帧高）：中位数 {np.median(subj_a) * 100:.0f}%  ·  25 分位 {np.percentile(subj_a, 25) * 100:.0f}%  ·  ≥25% 的帧占 {np.mean(subj_a >= 0.25) * 100:.0f}%')
    sev = spans(ts, [s < 0.07 for s in subj], step, 1.5)
    mid = [s for s in spans(ts, [s < 0.10 for s in subj], step, 1.5) if not any(x[0] <= s[0] and s[1] <= x[1] for x in sev)]
    for lvl, ss in (('严重', sev), ('中', mid)):
        for s0, s1 in ss:
            print(f'  ⚠ 空场（{lvl}）{s0:.2f}–{s1:.2f}s（{s1 - s0:.1f}s）：最大物体不到帧高的 {7 if lvl == "严重" else 10}%')
    if not sev and not mid:
        print('  ✔ 没有超过 1.5 秒的空场')
    if band:
        need, aux = (60, 36) if portrait else (0.05 * h, 0.03 * h)   # 竖屏 1080 宽：缩到 480 宽约 27px 才算手机上看得清
        with_text = [(t, c) for t, c in zip(ts, caps) if c > 0]
        if with_text:
            cs = np.array([c for _, c in with_text])
            print(f'字幕字高：中位数 {np.median(cs):.0f}px、最小 {cs.min():.0f}px（要求 ≥ {need:.0f}px，{"竖屏按缩到 480 宽仍可读" if portrait else "5% 帧高"}）')
            small = [t for t, c in with_text if c < need * 0.9]
            if small:
                print(f'  ⚠ 字幕偏小的采样点 {len(small)} 个，例如 {", ".join(f"{t:.2f}s" for t in small[:8])}（抽这些帧看：是字幕太小，还是带里只有小字/装饰）')
            else:
                print('  ✔ 字幕字高达标')
        else:
            print('字幕字高：字幕带里没检测到文字（字幕不在这个位置？用 --sub 指定）')
    if '--csv' in a:
        with open(opt(a, 'csv'), 'w', encoding='utf-8') as f:
            f.write('t,subject_ratio,caption_px\n')
            for t, s, c in zip(ts, subj, caps): f.write(f'{t},{s:.4f},{c:.0f}\n')


if __name__ == '__main__':
    main()
