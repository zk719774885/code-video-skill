"""图像/视频素材：搜索 → 出预览联系表挑选 → 下载进项目，并记账（来源、作者、授权）。
用法（在项目目录）：
  python -X utf8 <技能目录>/tools/assets.py search commons "Antikythera mechanism" [--n 12]
  python -X utf8 <技能目录>/tools/assets.py search pexels "underwater shipwreck" [--video] [--portrait]
  python -X utf8 <技能目录>/tools/assets.py search pixabay "ink mountain" [--video]
  python -X utf8 <技能目录>/tools/assets.py get <编号...>          # 下载上次搜索结果里的第几张，如 get 1 4 7
  python -X utf8 <技能目录>/tools/assets.py get-title "File:xxx.jpg" ...      # 按 Commons 精确文件名下载
  python -X utf8 <技能目录>/tools/assets.py grade duo|ink|warm assets/a.jpg ...  # 统一调色 → assets/proc/
来源：commons = Wikimedia Commons（公有领域名画/文物/历史照片，免 key，只保留 PD/CC0/CC BY/CC BY-SA）
      pexels  = 写实照片/视频（环境变量 PEXELS_API_KEY），pixabay = 照片/视频/插画（PIXABAY_API_KEY）
产物：assets/_search.json（上次结果）、assets/_preview.jpg（带编号的联系表，用 Read 看图挑）、
      assets/<来源>_<id>.<ext>、assets/ASSETS.json（账本：交付时据此写素材署名）。
"""
import json, os, re, subprocess, sys, tempfile, urllib.parse, urllib.request

UA = 'code-video-skill/1.0 (https://github.com/zk719774885/code-video-skill)'
A = 'assets'


def env(name):
    v = os.environ.get(name)
    if not v and os.name == 'nt':  # setx 写的用户变量，当前进程可能还没继承
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as k:
                v = winreg.QueryValueEx(k, name)[0]
        except OSError:
            v = None
    if not v:
        sys.exit(f'缺少环境变量 {name}（见 references/assets.md 的注册步骤）')
    return v


def get_json(url, headers=None):
    req = urllib.request.Request(url, headers={'User-Agent': UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def download(url, path, headers=None):
    req = urllib.request.Request(url, headers={'User-Agent': UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, 'wb') as f:
        while chunk := r.read(1 << 16):
            f.write(chunk)


def strip_html(s):
    return re.sub(r'<[^>]+>', '', s or '').strip()


def search_commons(q, n, video):
    p = {'action': 'query', 'format': 'json', 'generator': 'search', 'gsrnamespace': 6, 'gsrlimit': n * 3,
         'gsrsearch': q + (' filetype:video' if video else ' filetype:bitmap'),
         'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata', 'iiurlwidth': 480}
    d = get_json('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(p))
    out = []
    for pg in sorted(d.get('query', {}).get('pages', {}).values(), key=lambda x: x.get('index', 0)):
        it = commons_item(pg)
        if not it or not FREE.search(it['license']):
            continue
        if not video and it['w'] < 1200:
            continue
        out.append(it)
        if len(out) >= n:
            break
    return out


FREE = re.compile(r'public domain|^pd|cc0|cc by', re.I)


def commons_item(pg):
    if 'imageinfo' not in pg:
        return None
    ii = pg['imageinfo'][0]
    md = ii.get('extmetadata', {})
    return {'source': 'commons', 'id': str(pg['pageid']), 'title': pg['title'].removeprefix('File:'),
            'w': ii['width'], 'h': ii['height'], 'thumb': ii.get('thumburl', ii['url']), 'url': ii['url'],
            'author': strip_html(md.get('Artist', {}).get('value')), 'license': md.get('LicenseShortName', {}).get('value', ''),
            'page': ii['descriptionurl']}


def commons_titles(titles):
    """按精确文件名取（搜不出来但知道文件名时用），如 "File:Sholes typewriter patent.png"。"""
    titles = ['File:' + t.removeprefix('File:') for t in titles]
    p = {'action': 'query', 'format': 'json', 'titles': '|'.join(titles), 'prop': 'imageinfo',
         'iiprop': 'url|size|mime|extmetadata', 'iiurlwidth': 480}
    d = get_json('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(p))
    out = []
    for pg in d.get('query', {}).get('pages', {}).values():
        it = commons_item(pg)
        if it:
            out.append(it)
        else:
            print('找不到：' + pg.get('title', '?'))
    return out


def search_pexels(q, n, video, portrait):
    key = env('PEXELS_API_KEY')
    o = 'portrait' if portrait else 'landscape'
    base = 'https://api.pexels.com/videos/search' if video else 'https://api.pexels.com/v1/search'
    d = get_json(f'{base}?' + urllib.parse.urlencode({'query': q, 'per_page': n, 'orientation': o}), {'Authorization': key})
    out = []
    for it in d.get('videos' if video else 'photos', []):
        if video:
            files = sorted([f for f in it['video_files'] if f.get('file_type') == 'video/mp4' and f.get('width')], key=lambda f: -f['width'])
            best = next((f for f in files if f['width'] <= 1920 or f['height'] <= 1920), files[0] if files else None)
            if not best:
                continue
            out.append({'source': 'pexels', 'id': str(it['id']), 'title': q, 'w': best['width'], 'h': best['height'], 'thumb': it['image'],
                        'url': best['link'], 'author': it['user']['name'], 'license': 'Pexels License', 'page': it['url'], 'video': True, 'dur': it['duration']})
        else:
            out.append({'source': 'pexels', 'id': str(it['id']), 'title': it.get('alt') or q, 'w': it['width'], 'h': it['height'],
                        'thumb': it['src']['medium'], 'url': it['src']['original'], 'author': it['photographer'],
                        'license': 'Pexels License', 'page': it['url']})
    return out


def search_pixabay(q, n, video, portrait):
    key = env('PIXABAY_API_KEY')
    p = {'key': key, 'q': q, 'per_page': max(3, n), 'safesearch': 'true'}
    if not video:
        p.update(image_type='all', orientation='vertical' if portrait else 'horizontal', min_width=1600)
    d = get_json(('https://pixabay.com/api/videos/?' if video else 'https://pixabay.com/api/?') + urllib.parse.urlencode(p))
    out = []
    for it in d.get('hits', []):
        if video:
            v = it['videos'].get('large') or it['videos']['medium']
            out.append({'source': 'pixabay', 'id': str(it['id']), 'title': it['tags'], 'w': v['width'], 'h': v['height'],
                        'thumb': v.get('thumbnail') or it['videos']['tiny'].get('thumbnail'), 'url': v['url'], 'author': it['user'],
                        'license': 'Pixabay Content License', 'page': it['pageURL'], 'video': True, 'dur': it['duration']})
        else:
            out.append({'source': 'pixabay', 'id': str(it['id']), 'title': it['tags'], 'w': it['imageWidth'], 'h': it['imageHeight'],
                        'thumb': it['webformatURL'], 'url': it.get('largeImageURL') or it['webformatURL'], 'author': it['user'],
                        'license': 'Pixabay Content License', 'page': it['pageURL']})
    return out[:n]


def contact_sheet(items, out_jpg):
    """下载缩略图，左上角标编号，拼成 4 列联系表供挑选。"""
    tmp = tempfile.mkdtemp()
    files = []
    for i, it in enumerate(items, 1):
        f = os.path.join(tmp, f'{i:02d}.jpg')
        try:
            download(it['thumb'], f)
            files.append((i, f))
        except Exception as e:
            print(f'  预览 {i} 下载失败：{e}')
    if not files:
        return
    cols = 4
    args, flt = [], []
    font = 'C\\:/Windows/Fonts/arial.ttf' if os.name == 'nt' else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    for k, (i, f) in enumerate(files):
        args += ['-i', f]
        flt.append(f"[{k}]scale=400:225:force_original_aspect_ratio=decrease,crop='min(iw,400)':'min(ih,225)',pad=400:225:(ow-iw)/2:(oh-ih)/2:color=0x222222,"
                   f"drawtext=fontfile='{font}':text='{i}':x=8:y=6:fontsize=30:fontcolor=yellow:box=1:boxcolor=black@0.7[v{k}]")
    while len(files) % cols:
        k = len(files)
        args += ['-f', 'lavfi', '-i', 'color=c=0x111111:s=400x225:d=1']
        flt.append(f'[{k}]null[v{k}]')
        files.append((None, None))
    rows = len(files) // cols
    layout = '|'.join(f'{(k % cols) * 400}_{(k // cols) * 225}' for k in range(len(files)))
    flt.append(''.join(f'[v{k}]' for k in range(len(files))) + f'xstack=inputs={len(files)}:layout={layout}' if len(files) > 1 else '[v0]null')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *args, '-filter_complex', ';'.join(flt), '-frames:v', '1', out_jpg], check=True)


GRADES = ('duo', 'ink', 'warm')


def grade_img(src, dst, mode, maxside=2400):
    """统一调色，让不同来源的图放在一起像同一部片子。
    duo：深棕→奶油双色调（档案感，最常用）；ink：线稿/版画转墨色米纸（专利图、手稿、古籍）；
    warm：降饱和偏暖、压高光（彩色照片和其他素材混用时）。"""
    import numpy as np
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    im.thumbnail((maxside, maxside), Image.LANCZOS)
    x = np.asarray(im).astype(np.float32) / 255
    lum = x @ np.array([0.299, 0.587, 0.114], np.float32)
    lo, hi = np.percentile(lum, 1), np.percentile(lum, 99)
    lum = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1)
    if mode == 'duo':
        dark, light = np.array([0.10, 0.07, 0.05]), np.array([0.93, 0.86, 0.72])
        y = dark + (light - dark) * lum[..., None] ** 0.9
    elif mode == 'ink':
        ink, paper = np.array([0.13, 0.10, 0.08]), np.array([0.92, 0.87, 0.76])
        y = ink + (paper - ink) * (np.clip((lum - 0.15) / 0.7, 0, 1) ** 1.4)[..., None]
    elif mode == 'warm':
        y = (x * 0.55 + lum[..., None] * 0.45) * np.array([1.06, 1.0, 0.88])
        y = np.where(y > 0.8, 0.8 + (y - 0.8) * 0.5, y)
    else:
        sys.exit('调色模式只有：' + ' / '.join(GRADES))
    Image.fromarray((np.clip(y, 0, 1) * 255).astype(np.uint8)).save(dst, quality=93)


def write_ledger(items):
    """下载并记账（同名文件覆盖旧记录）。"""
    ledger_p = f'{A}/ASSETS.json'
    ledger = json.load(open(ledger_p, encoding='utf-8')) if os.path.exists(ledger_p) else []
    for it in items:
        ext = os.path.splitext(urllib.parse.urlparse(it['url']).path)[1].lower() or ('.mp4' if it.get('video') else '.jpg')
        name = f"{it['source']}_{it['id']}{ext}"
        download(it['url'], f'{A}/{name}')
        ledger = [x for x in ledger if x['file'] != name] + [{'file': name, **{k: it[k] for k in ('source', 'title', 'author', 'license', 'page', 'url', 'w', 'h')}}]
        print(f'✔ {A}/{name}  {it["w"]}x{it["h"]}  {it["license"]}')
    json.dump(ledger, open(ledger_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    os.makedirs(A, exist_ok=True)
    flag = lambda k: k in a
    if a[0] == 'search':
        src, q = a[1], a[2]
        n = int(a[a.index('--n') + 1]) if '--n' in a else 12
        video, portrait = flag('--video'), flag('--portrait')
        items = {'commons': lambda: search_commons(q, n, video), 'pexels': lambda: search_pexels(q, n, video, portrait),
                 'pixabay': lambda: search_pixabay(q, n, video, portrait)}[src]()
        json.dump(items, open(f'{A}/_search.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        if os.path.exists(f'{A}/_preview.jpg'):
            os.remove(f'{A}/_preview.jpg')      # 防止搜不到时误看上一次的联系表
        if not items:
            print('没有结果（换英文关键词，或用 get-title 按文件名取）')
            return
        for i, it in enumerate(items, 1):
            extra = f" {it['dur']}s" if it.get('video') else ''
            print(f"{i:2d}. {it['w']}x{it['h']}{extra}  {it['title'][:60]}  — {it['author'][:30]} [{it['license']}]")
        contact_sheet(items, f'{A}/_preview.jpg')
        print(f'预览联系表：{A}/_preview.jpg（Read 看图后用 get 编号 下载）')
    elif a[0] == 'get':
        items = json.load(open(f'{A}/_search.json', encoding='utf-8'))
        write_ledger([items[int(k) - 1] for k in a[1:]])
    elif a[0] == 'get-title':
        items = commons_titles(a[1:])
        for it in items:
            if not FREE.search(it['license']):
                print(f"⚠ {it['title']} 的授权是「{it['license']}」，用之前确认能不能用")
        write_ledger(items)
    elif a[0] == 'grade':
        os.makedirs(f'{A}/proc', exist_ok=True)
        for f in a[2:]:
            dst = f'{A}/proc/' + os.path.splitext(os.path.basename(f))[0] + '.jpg'
            grade_img(f, dst, a[1])
            print(f'✔ {dst}  [{a[1]}]')
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
