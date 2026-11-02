"""旁白生成（火山引擎 seed-audio-1.0）：一次生成整段，提示词里写音色人设、整体情绪曲线、逐句时间和语气，返回带逐字时间戳的字幕。
用法：python -X utf8 narr.py 台词.json 输出.wav [--dry]        --dry 只打印提示词，不调接口（不花钱）
台词.json：
  {"theme": "这是一部……短片的旁白。整体情绪曲线：开头……；结尾……",
   "voice": "旁白是一位三十岁左右的女性，普通话标准，声音温润、沉静……",   # 可省，默认用下面的 VOICE
   "speaker": "zh_female_xxx",                                         # 可省：指定音色 ID
   "dur": 108,
   "lines": [[0.5, 4.5, "好奇的提问，语调上扬", "为什么古人画地图，南在上，北在下？"], ...]}
key：环境变量 VOLC_API_KEY，或从台词文件所在目录往上找 `.volc.env`（一行 VOLC_API_KEY=…）。key 只放项目里，**不进技能目录**。
输出：输出.wav（48k）+ 输出.wav.sub.json（逐句、逐字时间戳）。接着用 align.py 对齐到台词，生成画面用的 voice.json。
坑（详见 references/voice.md）：
  · 语气描述里别用引号写关键词（如「整个世界」放慢），返回的字幕会混进这些「假词」（每字只有 40ms，音频里没念）；align.py 会按原文过滤；
  · 最后一句之后常有 3–10 秒多余的重复或呢喃，混音时截到最后一句结束 +0.35 秒（mixbgm.py 给了 voice_json 就会自动截）；
  · 同时请求超过 3 条会 429（并发配额），多条 take 排队跑。
"""
import base64, json, os, sys, time, urllib.error, urllib.request, uuid

VOICE = ('旁白是一位三十岁左右的女性，普通话标准，声音温润、沉静、通透，有书卷气，像人文纪录片的旁白，'
         '亲切但不甜腻、不播音腔，咬字清晰，气息稳定，语速偏慢，句与句之间自然留白。')
URL = 'https://openspeech.bytedance.com/api/v3/tts/create'


def find_key(start):
    if os.environ.get('VOLC_API_KEY'):
        return os.environ['VOLC_API_KEY']
    d = os.path.abspath(start)
    while True:
        p = os.path.join(d, '.volc.env')
        if os.path.exists(p):
            env = dict(l.strip().split('=', 1) for l in open(p, encoding='utf-8-sig') if '=' in l)
            if env.get('VOLC_API_KEY'): return env['VOLC_API_KEY']
        up = os.path.dirname(d)
        if up == d: break
        d = up
    sys.exit('找不到 VOLC_API_KEY：设环境变量，或在项目目录放 .volc.env（一行 VOLC_API_KEY=…）')


def build(cfg):
    p = '全程只有人声，不要背景音乐、不要音效、不要环境声。' + cfg.get('theme', '') + cfg.get('voice', VOICE) + f"音频总时长约 {cfg['dur']} 秒。"
    for a, b, emo, text in cfg['lines']:
        if any(q in emo for q in '「」“”"'):
            print(f'⚠ 第 {a}s 那句的语气描述里有引号，返回的字幕可能混进假词：{emo}')
        p += f'在[{a}s:{b}s]，{emo}，说：“{text}”'
    return p


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__); return
    cfg = json.load(open(a[0], encoding='utf-8-sig'))
    prompt = build(cfg)
    if '--dry' in a:
        print(prompt); print(f'\n（{len(prompt)} 字，{len(cfg["lines"])} 句）'); return
    body = {'model': 'seed-audio-1.0', 'text_prompt': prompt, 'audio_config': {'format': 'wav', 'sample_rate': 48000, 'enable_subtitle': True}}
    if cfg.get('speaker'):
        body['references'] = [{'speaker': cfg['speaker']}]
    req = urllib.request.Request(URL, data=json.dumps(body, ensure_ascii=False).encode(),
                                 headers={'X-Api-Key': find_key(os.path.dirname(os.path.abspath(a[0]))), 'X-Api-Request-Id': str(uuid.uuid4()), 'Content-Type': 'application/json'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            j = json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors='ignore')[:400]
        sys.exit(f'HTTP {e.code}{"（并发超额：同时最多 3 条，排队重试）" if e.code == 429 else ""}：{msg}')
    if not j.get('audio'):
        sys.exit(json.dumps(j, ensure_ascii=False)[:400])
    out = a[1]
    open(out, 'wb').write(base64.b64decode(j['audio']))
    sub = j.get('subtitle') or {}
    json.dump(sub, open(out + '.sub.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'✔ {out}  时长 {j.get("duration")}  用时 {time.time() - t0:.0f}s')
    for s in sub.get('sentences', []):
        print(f"   {s['start_time'] / 1000:6.2f}–{s['end_time'] / 1000:6.2f}  {s['text']}")


if __name__ == '__main__':
    main()
