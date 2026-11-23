#!/usr/bin/env python3
"""רילס 9:16 ל-UGREEN Smart Tag: סרטון הספק במרכז, כיתוב בעברית מעל ומתחת. בלי שינוי בתוכן הספק."""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FONT = '/home/claude/camping-store/social/reels/Heebo.ttf'
SRC, OUT = sys.argv[1], sys.argv[2]
GOLD, GREEN = (233, 162, 59, 255), (24, 46, 33, 235)


def font(size, weight):
    f = ImageFont.truetype(FONT, size, layout_engine=ImageFont.Layout.RAQM)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def center(d, y, text, f, fill, shadow=True):
    w = d.textlength(text, font=f, direction='rtl')
    x = (W - w) / 2
    if shadow:
        d.text((x + 3, y + 4), text, font=f, fill=(0, 0, 0, 150), direction='rtl')
    d.text((x, y), text, font=f, fill=fill, direction='rtl')


def overlay(path, kick, head1, head2):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fk = font(46, 700)
    kw = d.textlength(kick, font=fk, direction='rtl')
    d.rounded_rectangle(((W - kw) / 2 - 34, 150, (W + kw) / 2 + 34, 226), 38, fill=GOLD)
    d.text(((W - kw) / 2, 158), kick, font=fk, fill=(29, 42, 32, 255), direction='rtl')
    fh = font(88, 900)
    center(d, 270, head1, fh, (255, 255, 255, 255))
    center(d, 380, head2, fh, (255, 255, 255, 255))
    # כרטיס מוצר
    d.rounded_rectangle((90, 1330, W - 90, 1640), 34, fill=GREEN, outline=GOLD, width=3)
    fb = font(44, 700)
    d.text((W - 130, 1360), 'UGREEN', font=fb, fill=GOLD, anchor='ra')
    d.text((W - 130, 1425), 'תג איתור חכם למפתחות ולמזוודה', font=font(50, 700), fill='white', anchor='ra', direction='rtl')
    d.text((W - 130, 1505), 'עובד עם אייפון (Find My) · חנות רשמית', font=font(42, 500), fill='white', anchor='ra', direction='rtl')
    d.text((W - 130, 1565), 'צפצוף למציאה מהירה בבית', font=font(42, 500), fill=(255, 255, 255, 220), anchor='ra', direction='rtl')
    center(d, 1720, 'הקישור בתגובה הראשונה 👇'.replace(' 👇', ''), font(50, 700), (255, 255, 255, 255))
    im.save(path)


overlay('/home/claude/vid/ov1.png', 'נוסעים לחו"ל?', 'המזוודה בשדה,', 'ואתם כבר בדרך?')
overlay('/home/claude/vid/ov2.png', 'הפתרון', 'רואים במפה', 'איפה היא עכשיו')
fc = ("[0:v]fps=30,split[v1][v2];"
      f"[v1]scale=-2:{H},crop={W}:{H},boxblur=30:2,eq=brightness=-0.2[bg];"
      f"[v2]scale={W}:-2[fg];[bg][fg]overlay=0:(H-h)/2+20[m];"
      "[m][1:v]overlay=0:0:enable='lt(t,12)'[m2];[m2][2:v]overlay=0:0:enable='gte(t,12)',format=yuv420p[out]")
tmp = OUT[:-4] + '.tmp.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-i', '/home/claude/vid/ov1.png', '-i', '/home/claude/vid/ov2.png',
                '-filter_complex', fc, '-map', '[out]', '-map', '0:a?', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                '-r', '30', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', tmp], check=True)
import os
os.replace(tmp, OUT)
print(OUT)
