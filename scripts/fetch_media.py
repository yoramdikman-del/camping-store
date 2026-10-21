# מוריד תמונות (וסרטון אם יש) של מוצרים מאלי אקספרס לתיקיית media/<מספר מוצר>/
# רץ ב-GitHub Actions כשמתעדכן הקובץ media/requests.txt (מספר מוצר בכל שורה).
# התמונות נשמרות כ-JPG אמיתי, כדי ש-Metricool ואינסטגרם יקבלו אותן.
import os, sys, io, time, hmac, hashlib, requests
from PIL import Image

APP_KEY = os.environ.get('ALI_APP_KEY', '553904')
APP_SECRET = os.environ.get('ALI_APP_SECRET', '').strip()
if not APP_SECRET:
    sys.exit('חסר הסוד ALI_APP_SECRET')
MAX_IMAGES = 8

def call(method, **params):
    for attempt in range(4):
        p = {'app_key': APP_KEY, 'method': method, 'sign_method': 'sha256', 'timestamp': str(int(time.time() * 1000))}
        p.update({k: str(v) for k, v in params.items()})
        p['sign'] = hmac.new(APP_SECRET.encode(), ''.join(k + p[k] for k in sorted(p)).encode(), hashlib.sha256).hexdigest().upper()
        res = requests.post('https://api-sg.aliexpress.com/sync', data=p, timeout=30).json()
        if 'ApiCallLimit' in str(res)[:300]:
            time.sleep(2 + attempt * 2); continue
        return res
    return res

ids = [l.split('#')[0].strip() for l in open('media/requests.txt', encoding='utf-8')]
ids = [i for i in ids if i.isdigit() and not os.path.exists(f'media/{i}/done.txt')]
report = []
for pid in ids:
    res = call('aliexpress.affiliate.productdetail.get', product_ids=pid, target_currency='USD',
               target_language='EN', country='IL', tracking_id='campsite')
    root = res.get('aliexpress_affiliate_productdetail_get_response', {}).get('resp_result', {})
    prods = ((root.get('result') or {}).get('products') or {}).get('product', [])
    if not prods:
        report.append(f'{pid}: לא נמצא (אולי לא בתוכנית השותפים)'); continue
    x = prods[0]
    urls = [x.get('product_main_image_url')] + list(((x.get('product_small_image_urls') or {}).get('string')) or [])
    urls = [u for i, u in enumerate(urls) if u and u not in urls[:i]][:MAX_IMAGES]
    os.makedirs(f'media/{pid}', exist_ok=True)
    n = 0
    for u in urls:
        try:
            r = requests.get(u, timeout=60)
            im = Image.open(io.BytesIO(r.content)).convert('RGB')
            n += 1
            im.save(f'media/{pid}/img_{n:02d}.jpg', 'JPEG', quality=90)
        except Exception as e:
            print('תמונה נכשלה', u, e)
    vid = 'אין'
    if x.get('product_video_url'):
        try:
            r = requests.get(x['product_video_url'], timeout=120)
            if r.ok and len(r.content) < 40_000_000:
                open(f'media/{pid}/video.mp4', 'wb').write(r.content); vid = 'כן'
        except Exception as e:
            print('סרטון נכשל', e)
    open(f'media/{pid}/done.txt', 'w', encoding='utf-8').write(f"{x.get('product_title','')}\n")
    report.append(f'{pid}: {n} תמונות, סרטון: {vid}')
    time.sleep(0.5)
print('\n'.join(report) or 'אין בקשות חדשות')
