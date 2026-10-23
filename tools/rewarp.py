"""换配乐不重渲：把已渲染的帧和音效 cues 按锚点分段线性变速，对齐到新配乐。
用法（在项目目录）：
  python -X utf8 <技能目录>/tools/rewarp.py anchors.json frames/full frames/warp [--cues out/cues.json out/cues2.json] [--fps 30]
anchors.json：[[旧片时间, 新片时间], ...]，从 [0, 0] 开始，到 [旧片总长, 新片总长] 结束。
  锚点放在片名、落空、Drop、静默、最终段这些关键时刻，新片时间取新配乐的强起音（beats.py 的 accents / onsets）。
  每段速度（新段长/旧段长）尽量控制在 0.9–1.1，超出 0.85–1.2 会提示。
之后：重混 python mixbgm.py bgm.json out/cues2.json out/music.wav，再用 ffmpeg 把 frames/warp 和 music.wav 编码成片。
非整数帧位置用相邻两帧按比例 blend（离整数帧很近时直接复制，避免发糊）。
偏好提醒：可哥喜欢整首连续的配乐，能不剪曲就不剪，优先用这个变速去贴音乐。
"""
import json, os, shutil, sys
from PIL import Image


def opt(a, k, n=1):
    if '--' + k not in a: return None
    i = a.index('--' + k); return a[i + 1:i + 1 + n]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__); return
    A = [tuple(x) for x in json.load(open(a[0], encoding='utf-8'))]
    src, dst = a[1], a[2]
    fps = float((opt(a, 'fps') or [30])[0])
    for (a0, b0), (a1, b1) in zip(A, A[1:]):
        r = (b1 - b0) / (a1 - a0)
        print(f'  {a0:7.2f}–{a1:7.2f}s → {b0:7.2f}–{b1:7.2f}s  速度 ×{1 / r:.3f}' + ('  ⚠ 变速偏大' if not 0.85 <= 1 / r <= 1.2 else ''))

    def back(t):   # 新片时间 → 旧片时间
        for (a0, b0), (a1, b1) in zip(A, A[1:]):
            if t <= b1: return a0 + (a1 - a0) * (t - b0) / (b1 - b0)
        return A[-1][0]

    def fwd(t):    # 旧片时间 → 新片时间（cues 用）
        for (a0, b0), (a1, b1) in zip(A, A[1:]):
            if t <= a1: return b0 + (b1 - b0) * (t - a0) / (a1 - a0)
        return A[-1][1]

    cues = opt(a, 'cues', 2)
    if cues:
        cs = json.load(open(cues[0], encoding='utf-8'))
        json.dump([{**c, 't': round(fwd(c['t']), 3)} for c in cs], open(cues[1], 'w', encoding='utf-8'))
        print(f'cues {len(cs)} 条 → {cues[1]}')

    names = sorted(f for f in os.listdir(src) if f.startswith('f') and f.endswith('.jpg'))
    first, last = int(names[0][1:6]), int(names[-1][1:6])
    shutil.rmtree(dst, ignore_errors=True); os.makedirs(dst)
    N = round(A[-1][1] * fps)
    for k in range(N):
        x = back(k / fps) * fps; i = max(first, min(int(x), last)); f = x - int(x)
        out = f'{dst}/f{k:05d}.jpg'
        fi = lambda j: f'{src}/f{max(first, min(j, last)):05d}.jpg'
        if f < 0.15 or i >= last: shutil.copyfile(fi(i), out)
        elif f > 0.85: shutil.copyfile(fi(i + 1), out)
        else: Image.blend(Image.open(fi(i)), Image.open(fi(i + 1)), f).save(out, quality=94)
        if k % 300 == 0: print(f'\r  {k}/{N}', end='')
    print(f'\n✔ {N} 帧 → {dst}')


if __name__ == '__main__':
    main()
