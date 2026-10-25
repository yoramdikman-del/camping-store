#!/usr/bin/env python3
"""יוצר רילס 9:16 (1080x1920) למוצר: מתמונות המוצר או מקטעי וידאו, עם כיתוב בעברית.

שימוש:
  python3 social/reels/make_reel.py spec.json
spec.json:
  {"id": "...", "out": "social/reels/reel-x.mp4",
   "top": "שורה עליונה קטנה", "headline": "כותרת גדולה",
   "images": [1,2,5,6]                # או:
   "video_segments": [[2,12],[14,23]],
   "price_note": "החל מ־$21"           # לא חובה, ברירת מחדל מתוך products.json
  }
"""
import json, os, subprocess, sys, tempfile, html

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W, H = 1080, 1920
IMG_DUR, FADE = 3.2, 0.4


def product(pid):
    d = json.load(open(os.path.join(ROOT, 'data/products.json')))
    return next(p for p in d['products'] if p['id'] == pid)


def overlay(spec, p, png):
    import math
    price = spec.get('price_note') or f"החל מ־${math.ceil(p['price'])}"
    rating = f"{p['rating']:.1f}".rstrip('0').rstrip('.')
    page = f"""<!doctype html><html dir="rtl"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@500;700;900&display=swap" rel="stylesheet">
<style>
html,body{{margin:0;width:{W}px;height:{H}px;background:transparent;font-family:'Heebo',sans-serif}}
.top{{position:absolute;top:110px;left:70px;right:70px;text-align:center}}
.kick{{display:inline-block;background:#e9a23b;color:#1d2a20;font-weight:700;font-size:44px;
 padding:8px 30px;border-radius:40px}}
.head{{margin-top:22px;color:#fff;font-weight:900;font-size:86px;line-height:1.1;
 text-shadow:0 4px 18px rgba(0,0,0,.55)}}
.card{{position:absolute;top:1395px;left:90px;right:150px;background:rgba(24,46,33,.92);
 border:3px solid #e9a23b;border-radius:34px;padding:30px 40px;color:#fff;text-align:right}}
.brand{{font-family:Arial,sans-serif;font-weight:700;font-size:40px;color:#e9a23b;letter-spacing:1px}}
.title{{font-weight:700;font-size:46px;margin-top:4px;line-height:1.2}}
.meta{{font-weight:500;font-size:40px;margin-top:10px}}
.cta{{position:absolute;top:1745px;left:90px;right:150px;text-align:center;color:#fff;
 font-weight:700;font-size:42px;text-shadow:0 3px 12px rgba(0,0,0,.7)}}
</style></head><body>
<div class="top"><span class="kick">{html.escape(spec['top'])}</span>
<div class="head">{html.escape(spec['headline'])}</div></div>
<div class="card"><div class="brand">{html.escape(p['brand'])}</div>
<div class="title">{html.escape(p['title'])}</div>
<div class="meta">{html.escape(price)} · דירוג {rating}% · חנות רשמית</div></div>
<div class="cta">הקישור בביו · מוצרים לקמפינג וטיולים</div>
</body></html>"""
    from playwright.sync_api import sync_playwright
    hp = png + '.html'
    open(hp, 'w').write(page)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': W, 'height': H})
        pg.goto('file://' + hp)
        pg.wait_for_load_state('networkidle')
        pg.evaluate('document.fonts.ready')
        pg.wait_for_timeout(500)
        pg.screenshot(path=png, omit_background=True)
        b.close()


def run(cmd):
    subprocess.run(cmd, check=True)


def main(spec_path):
    spec = json.load(open(spec_path))
    p = product(spec['id'])
    out = os.path.join(ROOT, spec['out'])
    tmp = tempfile.mkdtemp()
    ov = os.path.join(tmp, 'ov.png')
    overlay(spec, p, ov)
    media = os.path.join(ROOT, 'media', spec['id'])
    fg_y = '(H-h)/2-60'
    if 'video_segments' in spec:
        src = os.path.join(media, 'video.mp4')
        parts = ''.join(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[s{i}];" for i, (a, b) in enumerate(spec['video_segments']))
        n = len(spec['video_segments'])
        fc = (parts + ''.join(f"[s{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,fps=30,split[v1][v2];"
              f"[v1]scale=-2:{H},crop={W}:{H},boxblur=30:2,eq=brightness=-0.15[bg];"
              f"[v2]scale={W}:-2[fg];[bg][fg]overlay=0:{fg_y}[m];[m][1:v]overlay=0:0,format=yuv420p[out]")
        run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-i', ov, '-filter_complex', fc, '-map', '[out]',
             '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-r', '30', '-movflags', '+faststart', '-an', out])
    else:
        clips = []
        frames = int(IMG_DUR * 30)
        for i, k in enumerate(spec['images']):
            img = os.path.join(media, f'img_{k:02d}.jpg')
            c = os.path.join(tmp, f'c{i}.mp4')
            zin = i % 2 == 0
            z = "1+0.08*on/{f}".format(f=frames) if zin else "1.08-0.08*on/{f}".format(f=frames)
            fc = (f"[0:v]scale={W}:{W},setsar=1,split[a][b];"
                  f"[a]scale=-2:{H},crop={W}:{H},boxblur=40:2,eq=brightness=-0.18[bg];"
                  f"[b]scale=2160:2160,zoompan=z='{z}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s=900x900:fps=30[fg];"
                  f"[bg]loop={frames}:1:0,setpts=N/30/TB[bgl];[bgl][fg]overlay=90:455,trim=0:{IMG_DUR},format=yuv420p[o]")
            run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', img, '-filter_complex', fc, '-map', '[o]',
                 '-t', str(IMG_DUR), '-r', '30', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', c])
            clips.append(c)
        inputs = sum((['-i', c] for c in clips), [])
        chain, last, off = '', '[0:v]', 0.0
        for i in range(1, len(clips)):
            off += IMG_DUR - FADE
            chain += f"{last}[{i}:v]xfade=transition=fade:duration={FADE}:offset={off:.2f}[x{i}];"
            last = f"[x{i}]"
        chain += f"{last}[{len(clips)}:v]overlay=0:0,format=yuv420p[out]"
        run(['ffmpeg', '-v', 'error', '-y'] + inputs + ['-i', ov, '-filter_complex', chain, '-map', '[out]',
             '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-r', '30', '-movflags', '+faststart', '-an', out])
    run(['ffmpeg', '-v', 'error', '-y', '-ss', '2', '-i', out, '-frames:v', '1', '-q:v', '2', out.replace('.mp4', '-cover.jpg')])
    print(out)


if __name__ == '__main__':
    main(sys.argv[1])
