"""把 narr.py 返回的逐字时间戳对齐到台词表，生成画面用的 voice.json：每句 t0/t1、字幕卡（分行）和逐字出现时间。
用法：python -X utf8 align.py 台词.json 旁白.wav voice.json [--offset 秒] [--width 13] [--rows 2]
  --offset：旁白在成片里的起点（如开头有 1 秒封面就写 1）；--width：每行最多几个字（竖屏 11–13，横屏 16–20）；--rows：每张字幕卡最多几行。
只按台词原文逐字匹配：提示词里引号关键词造成的「假词」（每字约 40ms，音频里没念）会被丢掉。
画面里的时间全部挂在 voice.json 上（「第 i 句第 n 个字」），换一条配音只要重跑这一步，分镜不用改。
"""
import json, sys

P = set('，。：；、！？—…「」《》“”（）·,.!?:;')


def opt(a, k, d):
    return a[a.index('--' + k) + 1] if '--' + k in a else d


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__); return
    lines_f, wav, out = a[:3]
    off, width, max_rows = float(opt(a, 'offset', 0)), int(opt(a, 'width', 13)), int(opt(a, 'rows', 2))
    cfg = json.load(open(lines_f, encoding='utf-8-sig'))
    sub = json.load(open(wav + '.sub.json', encoding='utf-8'))['sentences']
    words = [(w['text'], w['start_time'] / 1000, w['end_time'] / 1000) for s in sub for w in s['words'] if w['text'] not in P and w['text'].strip()]
    res, j, miss = [], 0, 0
    for li, (_, _, _, text) in enumerate(cfg['lines']):
        times = []
        for ch in text:
            if ch in P: times.append(None); continue
            k = j
            while k < len(words) and words[k][0] != ch: k += 1
            if k < len(words) and k - j < 12: times.append((words[k][1], words[k][2])); j = k + 1
            else: times.append(None); miss += 1; print(f'  未对齐：第 {li} 句「{ch}」')
        got = [x for x in times if x]
        if not got:
            print(f'⚠ 第 {li} 句整句没对上，跳过：{text}'); continue
        t0, t1 = got[0][0] + off, got[-1][1] + off
        # 字幕：按标点切成短语，打包成字幕卡（每卡最多 max_rows 行、每行最多 width 字），卡按时间先后出现
        ph, cur, curT = [], '', None
        for ch, tt in zip(text, times):
            if ch in '，。：；、？！—':
                if ch in '？！': cur += ch
                if cur: ph.append((cur, curT)); cur, curT = '', None
                continue
            if curT is None and tt: curT = tt[0] + off
            cur += ch
        if cur: ph.append((cur, curT))
        caps = []
        for p, pt in ph:
            c = caps[-1] if caps else None
            if c and len(c['rows'][-1]) + len(p) + 1 <= width: c['rows'][-1] += '　' + p
            elif c and len(c['rows']) < max_rows and len(p) <= width: c['rows'].append(p)
            else: caps.append({'rows': [p], 't0': pt if pt is not None else t0})
        seq = [(ch, tt[0] + off) for ch, tt in zip(text, times) if tt]; q = 0
        for c in caps:
            wl, last = [], c['t0']
            for ch in ''.join(c['rows']):
                if ch != '　' and ch not in '？！…':
                    while q < len(seq) and seq[q][0] != ch: q += 1
                    if q < len(seq): last = seq[q][1]; q += 1
                wl.append({'ch': ch, 't': round(last, 3)})
            c['words'] = wl; c['t0'] = round(c['t0'], 3)
        res.append({'i': li, 't0': round(t0, 3), 't1': round(t1, 3), 'text': text, 'caps': caps})
        print(f'{li:2d} {t0:6.2f}–{t1:6.2f}  ' + '  ||  '.join(' / '.join(c['rows']) for c in caps))
    json.dump({'wav': wav, 'offset': off, 'lines': res}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'✔ {out}  {len(res)} 句' + (f'，{miss} 个字没对上（看上面的「未对齐」）' if miss else ''))


if __name__ == '__main__':
    main()
