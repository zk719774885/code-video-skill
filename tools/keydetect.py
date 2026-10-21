"""测配乐的调：python keydetect.py music.mp3  → 例如 C minor（Krumhansl 调式轮廓匹配，色度来自 FFT）"""
import subprocess, sys
import numpy as np
sr = 22050
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', sys.argv[1], '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True).stdout
x = np.frombuffer(raw, np.float32); N, hop = 8192, 4096; chroma = np.zeros(12)
f = np.fft.rfftfreq(N, 1 / sr); v = (f > 60) & (f < 2000); pc = np.round(69 + 12 * np.log2(f[v] / 440)).astype(int) % 12; w = np.hanning(N)
for i in range(0, len(x) - N, hop): np.add.at(chroma, pc, np.abs(np.fft.rfft(x[i:i + N] * w))[v] ** 2)
names = 'C C# D Eb E F F# G Ab A Bb B'.split()
maj = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]); mnr = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
res = sorted([(np.corrcoef(chroma, np.roll(maj, k))[0, 1], f'{names[k]} major') for k in range(12)] + [(np.corrcoef(chroma, np.roll(mnr, k))[0, 1], f'{names[k]} minor') for k in range(12)], reverse=True)
print(res[0][1], f'(r={res[0][0]:.2f}；次选 {res[1][1]} r={res[1][0]:.2f})')
