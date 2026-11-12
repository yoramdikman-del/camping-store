import sys
from PIL import Image,ImageDraw,ImageFont
from bidi.algorithm import get_display
repo=sys.argv[1]; out=sys.argv[2]
W=1080;bg='#1E1510';tx='#F4E3C3';ac='#EC6A3D'
im=Image.new('RGB',(W,W),bg);d=ImageDraw.Draw(im)
B='/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'
f=lambda s:ImageFont.truetype(B,s)
logo=Image.open(repo+'/logo.png').convert('RGBA');logo.thumbnail((150,150))
m=Image.new('L',logo.size,0);ImageDraw.Draw(m).ellipse((0,0)+logo.size,fill=255)
im.paste(logo,((W-logo.size[0])//2,40),m)
def c(t,y,s,col=tx):
    w=d.textlength(t,font=f(s),direction='rtl');d.text(((W-w)/2,y),t,font=f(s),fill=col,direction='rtl')
c('מבצע 11.11 באלי אקספרס',210,62,ac)
c('קודי ההנחה לישראל, עד 18.11 בשעה 22:59',295,36)
codes=[('ILAFF02',2,15),('ILAFF05',5,29),('ILAFF08',8,45),('ILAFF12',12,65),('ILAFF16',16,85),('ILAFF20',20,119),('ILAFF37',37,215),('ILAFF60',60,349)]
y=380
for i,(k,a,mn) in enumerate(codes):
    col=i%2; x0=90+col*470; yy=y+(i//2)*130
    d.rounded_rectangle((x0,yy,x0+430,yy+110),18,outline=ac,width=3)
    d.text((x0+405,yy+14),k,font=f(40),fill=ac,anchor='ra')
    s=f'{a} דולר הנחה מעל {mn} דולר'
    d.text((x0+405,yy+62),s,font=f(30),fill=tx,direction='rtl',anchor='ra')
c('בודקים את המחיר הסופי בקופה לפני התשלום',925,32)
c('myripo.com/camping-store',985,34,ac)
im.save(out,quality=92)
