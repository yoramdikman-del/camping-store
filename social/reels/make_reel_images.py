#!/usr/bin/env python3
"""רילס 15 שניות 1080x1920 מ-3 תמונות מוצר, בסגנון רילס הקמפינג.
שימוש: python3 reel.py <repo> <out.mp4> <product_id> <imgs a,b,c> <music.m4a> "<headline>" "<expl line1|line2>"
"""
import sys, os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

repo, out, pid, imgs, music, headline, expl = sys.argv[1:8]
W, H, FPS = 1080, 1920, 30
BG, TX, AC = (0x1E, 0x15, 0x10), (0xF4, 0xE3, 0xC3), (0xEC, 0x6A, 0x3D)
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Heebo.ttf')
BOX, BX, BY = 900, 90, 610
MAIN, END, FADE = 12.4, 2.6, 0.5
EXPL_T = 2.2


def font(size, wght=800):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([wght])
    return f


def ctext(d, y, text, size, col, wght=800, gap=1.15, dr='rtl'):
    f = font(size, wght)
    for i, line in enumerate(text.split('|')):
        w = d.textlength(line, font=f, direction=dr)
        d.text(((W - w) / 2, y + i * size * gap), line, font=f, fill=col, direction=dr)


def logo(im, cx, cy, size):
    lg = Image.open(os.path.join(repo, 'logo.png')).convert('RGBA').resize((size, size), Image.LANCZOS)
    m = Image.new('L', (size, size), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size, size), fill=255)
    im.paste(lg, (cx - size // 2, cy - size // 2), m)


tmp = tempfile.mkdtemp()
# שכבת בסיס: רקע, לוגו, כותרת, קו מבטא, ידית. אזור התיבה שקוף!
base = Image.new('RGBA', (W, H), BG + (255,))
d = ImageDraw.Draw(base)
logo(base, W // 2, 150, 210)
ctext(d, 300, headline, 92, TX, 800)
d.rectangle((BX, BY, BX + BOX, BY + BOX), fill=(0, 0, 0, 0))
d.rectangle((140, BY + BOX + 45, W - 140, BY + BOX + 51), fill=AC)
ctext(d, H - 110, '@camping.store.il', 40, TX, 600, dr='ltr')
base.save(f'{tmp}/base.png')
# שכבת הסבר: מופיעה משנייה 2.2
ex = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ctext(ImageDraw.Draw(ex), BY + BOX + 90, expl, 58, TX, 700, 1.3)
ex.save(f'{tmp}/expl.png')
# כרטיס סיום
end = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(end)
logo(end, W // 2, 640, 320)
ctext(d, 880, 'הקישור לרכישה', 96, TX, 800)
ctext(d, 990, 'באינסטגרם ובפייסבוק', 96, AC, 800)
ctext(d, 1170, 'מוצרים לקמפינג וטיולים', 64, TX, 700)
ctext(d, 1280, '@camping.store.il', 48, TX, 600, dr='ltr')
end.save(f'{tmp}/end.png')


def run(c):
    subprocess.run(c, check=True)


# קטעי תמונות 900x900 עם זום איטי
ks = [int(k) for k in imgs.split(',')]
n = len(ks)
seg = (MAIN + FADE * (n - 1)) / n
fr = int(round(seg * FPS))
clips = []
for i, k in enumerate(ks):
    src = os.path.join(repo, 'media', pid, f'img_{k:02d}.jpg')
    sq = f'{tmp}/sq{i}.png'
    im = Image.open(src).convert('RGB')
    s = min(im.size)
    im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2)).resize((1800, 1800), Image.LANCZOS)
    im.save(sq)
    z = f"1+0.10*on/{fr}" if i % 2 == 0 else f"1.10-0.10*on/{fr}"
    c = f'{tmp}/c{i}.mp4'
    run(['ffmpeg', '-v', 'error', '-y', '-i', sq, '-vf',
         f"zoompan=z='{z}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={fr}:s={BOX}x{BOX}:fps={FPS},format=yuv420p",
         '-frames:v', str(fr), '-c:v', 'libx264', '-crf', '16', '-preset', 'veryfast', c])
    clips.append(c)
chain, last, off = '', '[0:v]', 0.0
for i in range(1, n):
    off += seg - FADE
    chain += f"{last}[{i}:v]xfade=transition=fade:duration={FADE}:offset={off:.3f}[x{i}];"
    last = f'[x{i}]'
inp = sum((['-i', c] for c in clips), [])
inp += ['-i', f'{tmp}/base.png', '-loop', '1', '-framerate', str(FPS), '-t', str(MAIN), '-i', f'{tmp}/expl.png']
b, e = n, n + 1
fc = (chain + f"color=c=0x1E1510:s={W}x{H}:r={FPS}:d={MAIN}[bg];[bg]{last}overlay={BX}:{BY}[m1];"
      f"[m1][{b}:v]overlay=0:0[m2];[{e}:v]format=rgba,fade=in:st={EXPL_T}:d=0.4:alpha=1[ex];"
      f"[m2][ex]overlay=0:0,trim=0:{MAIN},format=yuv420p[o]")
main = f'{tmp}/main.mp4'
run(['ffmpeg', '-v', 'error', '-y'] + inp + ['-filter_complex', fc, '-map', '[o]', '-r', str(FPS),
     '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', main])
endv = f'{tmp}/end.mp4'
run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', f'{tmp}/end.png', '-vf',
     f'format=yuv420p,loop=-1:1,trim=duration={END},fade=in:st=0:d=0.3', '-r', str(FPS),
     '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', endv])
lst = f'{tmp}/l.txt'
open(lst, 'w').write(f"file '{main}'\nfile '{endv}'\n")
silent = f'{tmp}/v.mp4'
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent])
part = out[:-4] + '.part.mp4'
run(['ffmpeg', '-v', 'error', '-y', '-i', silent, '-i', music, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
     '-c:a', 'aac', '-b:a', '160k', '-af', f'afade=out:st={MAIN + END - 1.2}:d=1.2', '-t', str(MAIN + END),
     '-movflags', '+faststart', part])
os.replace(part, out)
print(out)
