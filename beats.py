"""音乐卡点分析：测 BPM、拍点、重拍（强起音）时间，输出 JSON 给场景代码用。
用法：python -P beats.py music.mp3 [out.json]
依赖：numpy、scipy、ffmpeg（先用 ffmpeg 解成 22050Hz 单声道）。
输出：{bpm, beat_period, beats[], downbeats[], accents[]}，时间单位秒。
- beats：每一拍（画面小动作可踩这里）
- downbeats：每小节第一拍（4/4 拍，画面切换/换镜头踩这里）
- accents：能量最强的起音点（片名、钩子时刻、关键音效踩这里）
"""
import json, subprocess, sys
import numpy as np
from scipy.signal import find_peaks

SR, HOP = 22050, 512


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def onset_env(x):
    n = 2048
    frames = np.lib.stride_tricks.sliding_window_view(np.pad(x, (n // 2, n // 2)), n)[::HOP] * np.hanning(n)
    mag = np.abs(np.fft.rfft(frames, axis=1))
    # 对数梅尔近似：按频率分 40 段求和后取对数
    edges = np.unique(np.geomspace(1, mag.shape[1] - 1, 41).astype(int))
    bands = np.log1p(np.add.reduceat(mag, edges, axis=1) * 10)
    flux = np.maximum(0, np.diff(bands, axis=0)).sum(1)
    flux = np.concatenate([[0], flux])
    flux -= np.convolve(flux, np.ones(16) / 16, 'same')  # 去局部均值
    return np.maximum(flux, 0)


def tempo(env, lo=70, hi=180):
    fps = SR / HOP
    ac = np.correlate(env, env, 'full')[len(env) - 1:]
    lags = np.arange(len(ac))
    bpms = 60 * fps / np.maximum(lags, 1)
    ok = (bpms >= lo) & (bpms <= hi)
    # 偏好 120 附近（对数高斯权重），避免倍频/半频误判
    w = np.exp(-0.5 * (np.log2(bpms / 120) / 0.9) ** 2)
    score = np.where(ok, ac * w, 0)
    lag = int(np.argmax(score))
    # 抛物线插值求亚帧精度
    if 1 <= lag < len(score) - 1:
        a, b, c = score[lag - 1:lag + 2]
        lag = lag + 0.5 * (a - c) / (a - 2 * b + c + 1e-9)
    return 60 * fps / lag


def track(env, bpm):
    fps = SR / HOP
    period = 60 / bpm * fps
    # 找最佳相位：拍格上 onset 能量之和最大
    phases = np.arange(0, period, 0.25)
    idx = lambda ph: np.round(np.arange(ph, len(env) - 1, period)).astype(int)
    best = max(phases, key=lambda ph: env[idx(ph)].sum())
    beats = idx(best)
    # 每拍在 ±10% 周期内吸附到最近的局部峰
    r = max(1, int(period * 0.1))
    snapped = [b - r + int(np.argmax(env[max(0, b - r):b + r + 1])) if b - r >= 0 else b for b in beats]
    beats_t = np.array(snapped) / fps
    # 小节第一拍：4 个相位里重音能量最大的那个
    strength = env[np.array(snapped)]
    k = int(np.argmax([strength[i::4].mean() for i in range(4)]))
    return beats_t, beats_t[k::4]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    path = sys.argv[1]
    x = load(path)
    env = onset_env(x)
    bpm = tempo(env)
    beats, downs = track(env, bpm)
    fps = SR / HOP
    pk, _ = find_peaks(env, distance=int(0.4 * fps), prominence=np.percentile(env, 99) * 0.5)
    acc = pk[np.argsort(env[pk])[::-1][:12]]
    out = {
        'file': path, 'duration': round(len(x) / SR, 3), 'bpm': round(float(bpm), 2),
        'beat_period': round(60 / float(bpm), 4),
        'beats': [round(float(t), 3) for t in beats],
        'downbeats': [round(float(t), 3) for t in downs],
        'accents': sorted(round(float(t), 3) for t in acc / fps),
    }
    s = json.dumps(out, ensure_ascii=False, indent=1)
    if len(sys.argv) > 2:
        open(sys.argv[2], 'w', encoding='utf-8').write(s)
    print(f"BPM {out['bpm']}  拍长 {out['beat_period']}s  拍数 {len(out['beats'])}  小节首拍 {out['downbeats'][:6]}...  重音 {out['accents'][:8]}")


if __name__ == '__main__':
    main()
