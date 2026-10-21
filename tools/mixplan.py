"""通用配乐：python mixplan.py music.json cues.json out.wav
music.json = {"total":60, "sections":[{"kind":"18","start":0,"dur":60,"music_gain":1}], "note":"guzheng|piano|marimba|bell|epiano|toy"}
cues 里 sfx=='note' 的按 music.json 的 note 乐器发音。"""
import json, sys, os
sys.path.insert(0, os.path.join(os.environ.get('SY_STYLES') or os.path.join(os.environ.get('VIDEO_HOME') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'), 'sy-styles-20'), 'audio'))
import synth as S
from synth import nm
INST = {
    'guzheng': lambda m: S.ks(m, 1.6, 0.6, 0.997) * 0.9,
    'piano': lambda m: S.piano(m, 1.6),
    'marimba': lambda m: S.marimba(m, 0.8) * 1.2,
    'bell': lambda m: S.bell(m, 1.4, 0.9),
    'epiano': lambda m: S.epiano(m, 1.4),
    'toy': lambda m: S.toy(m, 1.0),
}
def main():
    mp = json.load(open(sys.argv[1], encoding='utf8')); cues = json.load(open(sys.argv[2], encoding='utf8'))
    total = mp['total']; inst = INST[mp.get('note', 'bell')]
    secs = [dict(s, cues=[]) for s in mp['sections']]
    g = []
    for c in cues:
        c = dict(c)
        if c['t'] >= total: continue
        if c['sfx'] == 'note':
            key = 'n_' + mp.get('note', 'bell') + '_' + c['note']
            if key not in S.SFX: S.SFX[key] = (lambda m=nm(c['note']): inst(m))
            c['sfx'] = key
        c.setdefault('send', 0.25)
        g.append(c)
    S.render({'sections': secs, 'global_cues': g}, sys.argv[3])
if __name__ == '__main__':
    main()
