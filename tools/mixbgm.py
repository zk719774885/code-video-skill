"""成品配乐 + 动效音效 混音（通用版）：python mixbgm.py bgm.json cues.json out.wav
bgm.json：{"music": "配乐.mp3", "edit": [[2.1, null]], "total": 95.6, "key": "C minor", "sfx_db": -6, "fade_in": 0.5, "fade_out": 4}
  - edit：默认只写一段 [[起点, null]]＝整首连续、只选起点偏移（可哥偏好，听着不断）；
    按小节拼接 [[0, 15.02], [7.59, 15.02], [15.02, null]] 只作不得已的选项，一次最多一个接口；
  - fade_in / fade_out：开头淡入、结尾淡出秒数（默认 0 / 1.2；整首连续时结尾建议 4 秒左右）；
  - lufs：成片目标响度（默认 -15）。末端是"整体测响度 → 一次性静态增益 → 限幅"，不用 loudnorm（它是动态增益，音乐会忽大忽小）；
  - key：配乐的调（tools/bgmcard.py 或 references/bgm-workflow.md 里的测调脚本可测），所有有音高的音效都吸附到该调的五声音阶并降一个八度；
  - sfx_db：音效总线相对音乐的电平（推荐 -5 ~ -9）。
音效来自 cues（sy-styles-20 的 SFX 名称 + note/boom/riser），一律低通去刺、加短混响。"""
import json, os, subprocess, sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.environ.get('SY_STYLES') or os.path.join(HERE, '..', 'engines', 'sy-styles-20'), 'audio'))
import synth as S

SR = S.SR
CFG = json.load(open(sys.argv[1], encoding='utf8'))
MUSIC = CFG['music']
EDIT = [tuple(e) for e in CFG.get('edit', [[0, None]])]
XF = 0.06
TOTAL = CFG['total']
KEY = CFG.get('key', 'C minor')
SFX_DB = CFG.get('sfx_db', -5)
FADE_IN, FADE_OUT = CFG.get('fade_in', 0), CFG.get('fade_out', 1.2)
LUFS = CFG.get('lufs', -15)
rng = np.random.default_rng(11)

def n(t): return int(round(t * SR))
def lp(x, fc, o=4): return signal.sosfilt(signal.butter(o, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc, o=2): return signal.sosfilt(signal.butter(o, fc, 'high', fs=SR, output='sos'), x)
def env(N, a, d): t = np.arange(N) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
NM = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
def note(s):  # 'Eb5' -> midi
    name, octv = s[:-1], int(s[-1]); return 12 * (octv + 1) + NM[name]

def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)

# ---------- 有音高的音色：柔和拨弦（基音 + 少量泛音 + 低八度垫底，快速衰减，低通） ----------
def pluck(m, dur=0.9, bright=1.0):
    N = n(dur); t = np.arange(N) / SR; f = mtof(m)
    y = (np.sin(2 * np.pi * f * t) * env(N, 0.003, 0.32)
         + 0.28 * np.sin(2 * np.pi * 2 * f * t) * env(N, 0.002, 0.12) * bright
         + 0.08 * np.sin(2 * np.pi * 3 * f * t) * env(N, 0.001, 0.05) * bright
         + 0.35 * np.sin(2 * np.pi * f / 2 * t) * env(N, 0.006, 0.4))
    return lp(y, 3500) * 0.6
def pad_key(dur=1.6):   # 配乐调的主和弦铺底（替代原 A 小调 swell）
    N = n(dur); t = np.arange(N) / SR; r = 60 + _root
    y = sum(np.sin(2 * np.pi * mtof(m) * t + 0.3 * np.sin(2 * np.pi * 0.3 * t)) for m in ((r, r + 5, r + 7, r + 12) if _sus else (r, r + 3, r + 7, r + 10) if _minor else (r, r + 4, r + 7, r + 11)))
    return lp(y, 2400) * np.sin(np.pi * t / dur) * 0.22
def mixs(*xs):
    out = np.zeros(max(len(x) for x in xs))
    for x in xs: out[:len(x)] += x
    return out
def arp(ms, gap=0.06, dur=0.8):
    out = np.zeros(n(gap * len(ms) + dur))
    for i, m in enumerate(ms): y = pluck(m, dur); k = n(i * gap); out[k:k + len(y)] += y
    return out

# ---------- 有音高的音效：吸附到配乐调式的五声音阶，并降一个八度 ----------
_root = NM[KEY.split()[0]]; _minor = 'minor' in KEY; _sus = 'sus' in KEY     # sus：大小调拿不准时只用两种调式共有的音（1 2 4 5）
PENTA = [(_root + d) % 12 for d in ((0, 2, 5, 7) if _sus else (0, 3, 5, 7, 10) if _minor else (0, 2, 4, 7, 9))]
def snap(m):
    cands = [o * 12 + pc for o in range(1, 9) for pc in PENTA]
    return min(cands, key=lambda c: (abs(c - m), c)) - 12
def deg(i, octv=5):   # 调内第 i 个五声音级（可跨八度）
    o, k = divmod(i, len(PENTA)); return 12 * (octv + 1 + o) + PENTA[k] + (12 if PENTA[k] < PENTA[0] else 0)
def tonal(name, c):
    if name == 'note': return pluck(snap(note(c.get('note', 'A5'))))
    if name == 'beep': return pluck(deg(3), 0.35, 0.6) * 0.6
    if name == 'ding': return pluck(deg(5), 0.7, 0.7) * 0.7
    if name == 'lock': return mixs(arp([deg(3, 4), deg(0)], 0.07, 0.6) * 0.8, lp(S.SFX['lock'](), 3000) * 0.25)
    if name == 'chime': return arp([deg(0), deg(3), deg(5)], 0.05, 1.2) * 0.7
    if name == 'sparkle': return arp([deg(3), deg(4), deg(6), deg(8)], 0.05, 0.6) * 0.35
    if name == 'coin': return arp([deg(3), deg(5)], 0.06, 0.4) * 0.5
    if name == 'swell': return pad_key(1.6)
    if name in ('powerup', 'levelup'): return arp([deg(0), deg(1), deg(3), deg(5)], 0.07, 0.5) * 0.6
    return None

def boom(g):
    N = n(2.2); t = np.arange(N) / SR
    f = 32 + 58 * np.exp(-t / 0.18); sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(N, 0.004, 0.55)
    body = lp(rng.standard_normal(N), 260) * env(N, 0.002, 0.12) * 0.8
    return (sub + body) * g
def riser(g, dur=3.7):
    N = n(dur); t = np.arange(N) / SR; x = rng.standard_normal(N); out = np.zeros(N)
    for i in range(0, N, 2400): out[i:i + 2400] = lp(x[i:i + 2400], 200 + 4000 * (i / N) ** 2, 2)
    tone = np.sin(2 * np.pi * np.cumsum(mtof(36 + _root) * 2 ** (2 * (t / dur) ** 2)) / SR) * 0.15   # C3 上滑两个八度
    return (out * 0.6 + tone) * (t / dur) ** 2.2 * g

# 每类的音量与低通（原版音量 × 系数）
CAT = {
    'boot': (0.7, 6000), 'whoosh': (0.8, 6000), 'whoosh_up': (0.7, 6000), 'zoom': (0.7, 5500), 'glitch': (0.6, 5000),
    'impact': (0.9, 7000), 'impact_soft': (0.8, 6500), 'data': (0.55, 5000), 'ticks': (0.5, 4500), 'tick': (0.5, 4000),
    'type': (0.5, 4000), 'pop': (0.6, 3500), 'stamp': (0.8, 5000), 'suck': (0.7, 5000), 'expand': (0.7, 5000),
    'riser_short': (0.6, 5000), 'bonk': (0.6, 3000), 'tail': (0.6, 5000),
}

def render_cue(c):
    name, g = c['sfx'], c.get('gain', 0.6)
    if name == 'boom': return boom(g), 0.15
    if name == 'riser': return riser(g, c.get('dur', 3.7)), 0.2
    y = tonal(name, c)
    if y is not None: return y * g * 1.1, 0.35          # 音高类：多一点混响
    f = S.SFX.get(name)
    if f is None: print('skip', name); return None, 0
    k, fc = CAT.get(name, (0.6, 5000))
    return lp(f(), fc) * g * k, 0.22

def main():
    cues = json.load(open(sys.argv[2], encoding='utf8'))
    m = load(MUSIC); xf = n(XF); parts = []
    for a, b in EDIT:
        seg = m[n(a): (n(b) + xf) if b is not None else len(m)]
        parts.append(seg.copy())
    music = parts[0]
    for seg in parts[1:]:
        fade = np.linspace(0, 1, xf)[:, None]
        music = np.concatenate([music[:-xf], music[-xf:] * (1 - fade) + seg[:xf] * fade, seg[xf:]])
    L = n(TOTAL); music = music[:L] if len(music) >= L else np.pad(music, ((0, L - len(music)), (0, 0)))
    check_hits(music, cues)     # 在淡入淡出之前测：淡入本身会被当成一个巨大的起音
    if FADE_IN > 0: music[:n(FADE_IN)] *= np.linspace(0, 1, n(FADE_IN))[:, None] ** 2
    music[-n(FADE_OUT):] *= np.linspace(1, 0, n(FADE_OUT))[:, None] ** 2
    dry = np.zeros((L + n(4), 2)); wet = np.zeros((L + n(4), 2))
    for c in cues:
        y, send = render_cue(c)
        if y is None: continue
        y = hp(y, 30); k = n(c['t']); pan = (rng.random() - 0.5) * 0.5
        for ch, pg in ((0, 1 - pan), (1, 1 + pan)):
            seg = y[: len(dry) - k] * pg; dry[k:k + len(seg), ch] += seg; wet[k:k + len(seg), ch] += seg * send
    ir = S.reverb_ir(1.6, 0.45)
    verb = np.stack([signal.fftconvolve(wet[:, i], ir[:, i])[: len(wet)] for i in range(2)], 1)
    fx = (dry + verb * 0.6)[:L]
    rm = np.sqrt((music ** 2).mean()); rf = np.sqrt((fx ** 2).mean()) + 1e-9
    fx *= rm / rf * 10 ** (SFX_DB / 20)
    pk = np.abs(fx).max(); print('fx peak', round(float(pk), 3))
    if pk > 1.2: fx = np.tanh(fx / 1.2) * 1.2      # 只软削极少数尖峰，不再整体压低
    mix = music + fx
    tmp = sys.argv[3] + '.pre.wav'
    wavfile.write(tmp, SR, mix.astype(np.float32))
    # 静态增益：整体测一次响度，整条乘同一个增益，再用限幅器只挡真峰值（不改变音乐的起伏）
    meas = subprocess.run(['ffmpeg', '-hide_banner', '-i', tmp, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='ignore').stderr
    I = float(meas.rsplit('I:', 1)[1].split('LUFS')[0])
    gain = LUFS - I + 0.3      # 限幅会吃掉一点，略多给
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', tmp, '-af', f'volume={gain:.2f}dB,alimiter=limit=0.84:attack=1:release=80:level=disabled',
                    '-c:a', 'pcm_s16le', '-ar', str(SR), sys.argv[3]], check=True)
    os.remove(tmp)
    print('wrote', sys.argv[3], f'{TOTAL}s', f'原始 {I:.1f} LUFS → 增益 {gain:+.1f} dB')


HEAVY = {'impact', 'impact_soft', 'boom', 'stamp', 'bonk', 'tail'}


def check_hits(music, cues):
    """重击音效附近 ±0.4 秒有音乐强起音、但没对齐（差 > 30ms）→ 会听成"双响"，提示该挪多少。"""
    sys.path.insert(0, os.path.join(HERE, '..'))
    import beats as B
    mono = signal.resample_poly(music.mean(1), B.SR, SR).astype(np.float32)
    ons = [t for t, s in B.onsets_fine(mono, top=80) if s >= 0.25]
    bad = 0
    for c in cues:
        if c['sfx'] not in HEAVY or c.get('gain', 0.6) < 0.4: continue
        near = [o for o in ons if abs(o - c['t']) <= 0.4]
        if not near: continue
        o = min(near, key=lambda o: abs(o - c['t']))
        if abs(o - c['t']) > 0.03:
            bad += 1; print(f"⚠ 双响风险：{c['sfx']} @ {c['t']:.3f}s，音乐重拍在 {o:.3f}s（差 {(c['t'] - o) * 1000:+.0f} ms）→ 把这个 cue 挪到 {o:.3f}")
    if not bad: print('✔ 重击音效与音乐重拍对齐检查通过')

if __name__ == '__main__':
    main()
