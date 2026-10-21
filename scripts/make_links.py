# יוצר קישורי שותפים (מזהה מעקב website) למוצרים חדשים שממתינים לאישור (status=pending).
# המוצרים נשארים מוסתרים באתר. אחרי שיורם מאשר, מסירים את status והם עולים.
import os, sys, json, time, hmac, hashlib, requests
APP_KEY = os.environ.get('ALI_APP_KEY', '553904')
APP_SECRET = os.environ.get('ALI_APP_SECRET', '').strip()
URL = 'https://api-sg.aliexpress.com/sync'
if not APP_SECRET:
    sys.exit('חסר הסוד ALI_APP_SECRET')
def call(method, **params):
    p = {'app_key': APP_KEY, 'method': method, 'sign_method': 'sha256', 'timestamp': str(int(time.time() * 1000))}
    p.update({k: str(v) for k, v in params.items()})
    p['sign'] = hmac.new(APP_SECRET.encode(), ''.join(k + p[k] for k in sorted(p)).encode(), hashlib.sha256).hexdigest().upper()
    return requests.post(URL, data=p, timeout=30).json()
db = json.load(open('data/products.json', encoding='utf-8'))
todo = [p for p in db['products'] if p.get('status') == 'pending' and 's.click' not in (p.get('link') or '')]
src = lambda p: 'https://www.aliexpress.com/item/%s.html' % p['id']
done = 0
errors = []
for i in range(0, len(todo), 20):
    part = todo[i:i + 20]
    res = call('aliexpress.affiliate.link.generate', promotion_link_type=0, source_values=','.join(src(p) for p in part), tracking_id=os.environ.get('TRACKING','campsite'))
    root = res.get('aliexpress_affiliate_link_generate_response', {}).get('resp_result', {})
    if 'error_response' in res or root.get('resp_code') not in (200, None):
        errors.append(str(res.get('error_response') or {'resp_code': root.get('resp_code'), 'resp_msg': root.get('resp_msg')})[:300])
    got = {str(l.get('source_value', '')).split('?')[0]: l.get('promotion_link') for l in ((root.get('result') or {}).get('promotion_links') or {}).get('promotion_link', [])}
    for p in part:
        if got.get(src(p)):
            p['link'] = got[src(p)]; p['tid'] = os.environ.get('TRACKING','campsite'); done += 1
    time.sleep(0.5)
json.dump(db, open('data/products.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(done, 'links of', len(todo))
open('data/links_report.txt', 'w', encoding='utf-8').write(f"{done} links of {len(todo)}\ntracking: {os.environ.get('TRACKING','campsite')}\n" + '\n'.join(errors) + '\n')
