"""视频联系表：每 N 秒一帧、左上角带时间码，拼成一张大图（Read 看图用；省额度）。
用法：python -X utf8 contact.py 视频.mp4 [--every 4] [--cols 6] [--w 320] [--from 0] [--to 结尾] [--out sheet.jpg]
一张最多 cols×8 格，超出自动分成 sheet_1.jpg、sheet_2.jpg…
注意：Windows 上 winget 装的 ffmpeg 没有 fontconfig，drawtext 不指定 fontfile 会直接段错误，这里已写死字体路径。
"""
import os, subprocess, sys


def opt(a, k, d):
    return a[a.index('--' + k) + 1] if '--' + k in a else d


def duration(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    src = a[0]
    every, cols, w = float(opt(a, 'every', 4)), int(opt(a, 'cols', 6)), int(opt(a, 'w', 320))
    t0 = float(opt(a, 'from', 0)); t1 = float(opt(a, 'to', duration(src)))
    out = opt(a, 'out', os.path.splitext(src)[0] + '_sheet.jpg')
    font = 'C\\:/Windows/Fonts/arial.ttf' if os.name == 'nt' else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    per = cols * 8
    n = max(1, -int(-(t1 - t0) // every))   # 帧时刻 t0, t0+every, … 都小于 t1
    pages = max(1, -(-n // per))
    for k in range(pages):
        s = t0 + k * per * every
        cnt = min(per, n - k * per)
        rows = -(-cnt // cols)
        dst = out if pages == 1 else out.replace('.jpg', f'_{k + 1}.jpg')
        vf = (f"fps=1/{every},scale={w}:-2,drawtext=fontfile='{font}':text='%{{pts\\:hms\\:{s}}}':x=6:y=6:fontsize={max(12, w // 18)}:"
              f"fontcolor=yellow:box=1:boxcolor=black@0.6,tile={cols}x{rows}:padding=3:color=black")
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(s), '-t', str(cnt * every), '-i', src, '-vf', vf, '-frames:v', '1', dst], check=True)
        print('✔', dst, f'{s:.0f}–{s + cnt * every:.0f}s')


if __name__ == '__main__':
    main()
