"""给成片加封面，不重渲正片：封面场景接在片头，用溶接过渡；音乐和音效整体后移，再写入封面缩略图。
用法（在项目目录）：
  python -X utf8 <技能目录>/tools/addcover.py --cover frames/cover --frames frames/full --out out/成片_含封面.mp4
        [--xfade 0.4] [--bgm bgm.json --cues out/cues.json] [--music out/music.wav]
  --cover：封面的逐帧图目录（f%05d.jpg，建议 2–3 秒，**第 0 帧就是完整封面**，抖音取第一帧当封面），也可以是一个视频文件；
  --frames：正片的**原始逐帧图**目录。一定从原始帧重新编码，别拿压好的成片再压一遍（实测码率从 11.7 掉到 8.9 Mbps，画质二次损失）；
  声音二选一：--bgm + --cues（推荐：配乐起点前移、cues 后移，再用 mixbgm 重混，片头不会有一段空白）；
              --music（已混好的 wav，前面补静音）。
编码：先试 h264_nvenc（需 NVIDIA 驱动 ≥ 610），不行自动回退 libx264 crf 17。封面第 0 帧另存 jpg，作为 attached_pic 写进 mp4。
"""
import json, os, subprocess, sys, tempfile

FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))


def opt(a, k, d=None):
    return a[a.index('--' + k) + 1] if '--' + k in a else d


def read_json(p):
    return json.loads(open(p, encoding='utf-8-sig').read())   # utf-8-sig：兼容 PowerShell 写的 BOM


def count_frames(d):
    fs = sorted(f for f in os.listdir(d) if f.startswith('f') and f.endswith('.jpg'))
    return int(fs[0][1:6]), len(fs)


def ff(*args):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)


def nvenc_ok():
    r = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=s=256x256:d=0.1', '-c:v', 'h264_nvenc', '-f', 'null', '-'], capture_output=True)
    return r.returncode == 0


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a = sys.argv[1:]
    if '--cover' not in a or '--frames' not in a or '--out' not in a:
        print(__doc__); return
    cover, frames, out = opt(a, 'cover'), opt(a, 'frames'), opt(a, 'out')
    xf = float(opt(a, 'xfade', 0.4))
    tmp = tempfile.mkdtemp()

    # ---- 视频输入 ----
    if os.path.isdir(cover):
        c0, cn = count_frames(cover)
        cin = ['-framerate', str(FPS), '-start_number', str(c0), '-i', os.path.join(cover, 'f%05d.jpg')]
        first = os.path.join(cover, f'f{c0:05d}.jpg')
    else:
        r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', cover], capture_output=True, text=True)
        cn = round(float(r.stdout) * FPS); cin = ['-i', cover]
        first = os.path.join(tmp, 'first.jpg'); ff('-i', cover, '-frames:v', '1', '-q:v', '2', first)
    cdur = cn / FPS
    m0, mn = count_frames(frames)
    shift = cdur - xf
    print(f'封面 {cdur:.2f}s + 溶接 {xf}s，正片 {mn / FPS:.2f}s → 成片 {shift + mn / FPS:.2f}s（正片整体后移 {shift:.2f}s）')

    # ---- 声音 ----
    wav = os.path.join(tmp, 'music.wav')
    if '--bgm' in a:
        bgm = read_json(opt(a, 'bgm')); cues = read_json(opt(a, 'cues', 'out/cues.json'))
        e0 = bgm.get('edit', [[0, None]])
        if e0[0][0] - shift < 0:
            print(f'⚠ 配乐起点 {e0[0][0]}s 不够前移 {shift:.2f}s，片头前 {shift - e0[0][0]:.2f}s 会是静音')
        start = max(0, e0[0][0] - shift)
        bgm['edit'] = [[start, e0[0][1]]] + e0[1:]
        bgm['total'] = bgm['total'] + shift
        bgm['music'] = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(opt(a, 'bgm'))), bgm['music']))
        bp, cp = os.path.join(tmp, 'bgm.json'), os.path.join(tmp, 'cues.json')
        json.dump(bgm, open(bp, 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump([{**c, 't': round(c['t'] + shift, 3)} for c in cues], open(cp, 'w', encoding='utf-8'))
        subprocess.run([sys.executable, '-X', 'utf8', os.path.join(HERE, 'mixbgm.py'), bp, cp, wav], check=True)
    elif '--music' in a:
        ms = int(shift * 1000)
        ff('-i', opt(a, 'music'), '-af', f'adelay={ms}|{ms}', wav)
    else:
        sys.exit('声音要么给 --bgm + --cues，要么给 --music')

    # ---- 编码：封面 + 正片原始帧，一次编码 ----
    enc = ['-c:v', 'h264_nvenc', '-preset', 'p7', '-cq', '17', '-b:v', '0'] if nvenc_ok() else ['-c:v', 'libx264', '-preset', 'slow', '-crf', '17']
    print('编码器：' + enc[1])
    body = os.path.join(tmp, 'body.mp4')
    ff(*cin, '-framerate', str(FPS), '-start_number', str(m0), '-i', os.path.join(frames, 'f%05d.jpg'), '-i', wav,
       '-filter_complex', f'[0:v]settb=AVTB,fps={FPS},format=yuv420p[c];[1:v]settb=AVTB,fps={FPS},format=yuv420p[m];[c][m]xfade=transition=fade:duration={xf}:offset={shift:.3f}[v]',
       '-map', '[v]', '-map', '2:a', *enc, '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-shortest', body)
    # ---- 写入封面缩略图（流复制，不再压缩） ----
    ff('-i', body, '-i', first, '-map', '0', '-map', '1', '-c', 'copy', '-c:v:1', 'mjpeg', '-disposition:v:1', 'attached_pic', '-movflags', '+faststart', out)
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,bit_rate', '-of', 'csv=p=0', out], capture_output=True, text=True)
    d, br = r.stdout.strip().split(',')
    print(f'✔ {out}  {float(d):.1f}s  {int(br) / 1e6:.1f} Mbps')


if __name__ == '__main__':
    main()
