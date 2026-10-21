# רענון שבועי של מוצרי החנות "צילום בכל גיל".
# רץ אוטומטית ב-GitHub Actions. לכל מוצר בודק באלי אקספרס: שהוא עדיין קיים ונשלח לישראל,
# ומעדכן מחיר, דירוג ומספר הזמנות. מוצר שלא נמצא מסומן "missing" ומוסתר באתר עד שיורם מאשר להסיר אותו.
# מוצרים בלי עמלה (no_commission) לא נעלמים אם ה-API לא מחזיר אותם, ובדוח מוצגות להם חלופות עם עמלה.
# מוצר חדש (status=pending) מוסתר באתר עד שנוצר לו קישור.
# כלום לא עולה לאתר בלי אישור: התוצאה נפתחת כבקשת שינוי (Pull Request) שמחכה לאישור.
# הסוד נקרא ממשתנה הסביבה ALI_APP_SECRET שנשמר ב-GitHub Secrets – לא בקוד.
import os, sys, json, time, hmac, hashlib, datetime, requests

APP_KEY = os.environ.get('ALI_APP_KEY', '553904')
APP_SECRET = os.environ.get('ALI_APP_SECRET', '').strip()
URL = 'https://api-sg.aliexpress.com/sync'
DATA = 'data/products.json'
REPORT = 'data/refresh_report.md'
PRICE_ALERT = 0.15   # שינוי מחיר של יותר מ-15% מופיע בדוח
TRACKING = 'campsite'

if not APP_SECRET:
    sys.exit('חסר הסוד ALI_APP_SECRET ב-GitHub Secrets')

def call(method, **params):
    res = {}
    for attempt in range(4):
        p = {'app_key': APP_KEY, 'method': method, 'sign_method': 'sha256',
             'timestamp': str(int(time.time() * 1000))}
        p.update({k: str(v) for k, v in params.items()})
        base = ''.join(k + p[k] for k in sorted(p))
        p['sign'] = hmac.new(APP_SECRET.encode(), base.encode(), hashlib.sha256).hexdigest().upper()
        try:
            res = requests.post(URL, data=p, timeout=30).json()
        except Exception as e:
            res = {'error': str(e)}
        if 'ApiCallLimit' in str(res)[:300]:
            time.sleep(2 + attempt * 2)
            continue
        return res
    return res

def num(s):
    try: return float(str(s).replace('%', ''))
    except Exception: return None

def gen_links(urls):
    res = call('aliexpress.affiliate.link.generate', promotion_link_type=0, source_values=','.join(urls), tracking_id=TRACKING)
    root = res.get('aliexpress_affiliate_link_generate_response', {}).get('resp_result', {})
    return {str(l.get('source_value', '')).split('?')[0]: l.get('promotion_link') for l in
            ((root.get('result') or {}).get('promotion_links') or {}).get('promotion_link', [])}

db = json.load(open(DATA, encoding='utf-8'))
prods = db['products']
ids = [p['id'] for p in prods]
found = {}
for i in range(0, len(ids), 20):
    res = call('aliexpress.affiliate.productdetail.get', product_ids=','.join(ids[i:i + 20]),
               target_currency='USD', target_language='EN', country='IL', tracking_id='linktree')
    if 'error_response' in res:
        sys.exit(f"שגיאת API: {res['error_response'].get('code')}")
    root = res.get('aliexpress_affiliate_productdetail_get_response', {}).get('resp_result', {})
    for x in ((root.get('result') or {}).get('products') or {}).get('product', []):
        found[str(x.get('product_id'))] = x
    time.sleep(0.5)

missing, price_moves, back, new_ok, new_wait = [], [], [], [], []
for p in prods:
    x = found.get(p['id'])
    if not x:
        if p.get('no_commission'):
            continue                      # לא מוחזר ב-API של השותפים – משאירים את הנתונים מהסריקה
        if p.get('status') == 'pending':
            continue
        if p.get('status') != 'missing':
            missing.append(p)
        p['status'] = 'missing'
        continue
    if p.get('status') == 'missing':
        back.append(p)
    if p.get('status') != 'pending':
        p.pop('status', None)
    new_price, new_rate, new_sold = num(x.get('target_sale_price')), num(x.get('evaluate_rate')), num(x.get('lastest_volume'))
    # מוצר עם "גרסה מומלצת" (variant): המחיר נקבע ידנית לגרסה המלאה, וה-API מחזיר את המחיר הנמוך ביותר
    # (לפעמים של חלק בלבד). לכן לא דורסים את המחיר שלו.
    if not p.get('variant'):
        if new_price and p.get('price') and abs(new_price - p['price']) / p['price'] > PRICE_ALERT:
            price_moves.append((p, p['price'], new_price))
        if new_price: p['price'] = round(new_price, 2)
    if new_rate: p['rating'] = new_rate
    if new_sold is not None: p['sold'] = int(new_sold)
    if x.get('product_main_image_url'): p['img'] = x['product_main_image_url']

# קישורי שותפים עם מזהה המעקב website לכל מוצר שעדיין אין לו
new_links = 0
todo = [p for p in prods if p.get('tid') != TRACKING and (p['id'] in found or p.get('no_commission') or p.get('status') == 'pending')]
src = lambda p: ((found.get(p['id']) or {}).get('product_detail_url') or f"https://www.aliexpress.com/item/{p['id']}.html").split('?')[0]
batch = [p for p in todo if not p.get('no_commission')]
for i in range(0, len(batch), 20):
    part = batch[i:i + 20]; urls = [src(p) for p in part]
    got = gen_links(urls)
    for p, u in zip(part, urls):
        if got.get(u):
            p['link'] = got[u]; p['tid'] = TRACKING; new_links += 1
    time.sleep(0.5)
for p in todo:                             # מוצרים בלי עמלה: אחד-אחד, כדי שכישלון לא יפיל אחרים
    if not p.get('no_commission') or p.get('tid') == TRACKING:
        continue
    u = src(p); got = gen_links([u])
    if got.get(u):
        p['link'] = got[u]; p['tid'] = TRACKING; new_links += 1
    else:
        p['link'] = u; p['tid'] = 'direct'      # קישור ישיר לדף המוצר (בלי מעקב)
    time.sleep(0.4)
for p in prods:
    if p.get('status') == 'pending' and p.get('tid') in (TRACKING, 'direct'):
        p.pop('status'); new_ok.append(p)
    elif p.get('status') == 'pending':
        new_wait.append(p)

# חלופות עם עמלה למוצרים בלי עמלה
alts = []
for q in sorted({p.get('alt_query') for p in prods if p.get('no_commission') and p.get('alt_query') and p.get('status') != 'missing'}):
    res = call('aliexpress.affiliate.product.query', keywords=q, ship_to_country='IL', target_currency='USD',
               target_language='EN', page_size=50, sort='LAST_VOLUME_DESC', tracking_id=TRACKING)
    root = res.get('aliexpress_affiliate_product_query_response', {}).get('resp_result', {})
    have = {p['id'] for p in prods}
    cand = []
    for x in ((root.get('result') or {}).get('products') or {}).get('product', []):
        c = num(x.get('hot_product_commission_rate')) or num(x.get('commission_rate')) or 0
        r = num(x.get('evaluate_rate')) or 0
        if c > 0 and r >= 90 and str(x.get('product_id')) not in have:
            cand.append((int(num(x.get('lastest_volume')) or 0), x, c, r))
    cand.sort(key=lambda t: -t[0])
    alts.append((q, cand[:3]))
    time.sleep(0.5)

today = datetime.date.today().isoformat()
db['updated'] = today
json.dump(db, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

name = lambda p: f"{p['brand']} – {p['title']} {p.get('code', '')}".strip()
nc = [p for p in prods if p.get('no_commission') and p.get('status') != 'missing']
lines = [f'# רענון מוצרים – {today}', '',
         f'נבדקו {len(prods)} מוצרים. נמצאו {len(found)}. קישורי website חדשים: {new_links}.', '']
lines += ['## מוצרים חדשים שעולים לאתר'] + ([f'- {name(p)} ({"קישור שותפים" if p["tid"] == TRACKING else "קישור ישיר, בלי מעקב"})' for p in new_ok] or ['- אין']) + ['']
if new_wait:
    lines += ['## מוצרים חדשים שעדיין מחכים לקישור'] + [f'- {name(p)} ({p["id"]})' for p in new_wait] + ['']
lines += ['## מוצרים שלא נמצאו (מוסתרים באתר עד החלטה)'] + ([f'- {name(p)} ({p["id"]})' for p in missing] or ['- אין']) + ['']
lines += ['## מוצרים שחזרו'] + ([f'- {name(p)}' for p in back] or ['- אין']) + ['']
lines += [f'## שינויי מחיר מעל {int(PRICE_ALERT * 100)}%'] + ([f'- {name(p)}: {a}$ → {b}$' for p, a, b in price_moves] or ['- אין']) + ['']
if nc:
    lines += [f'## מוצרים בלי עמלה ({len(nc)}) – חלופות עם עמלה לבדיקה']
    for q, cand in alts:
        lines.append(f'**{q}**')
        lines += [f'- {x.get("product_title", "")[:90]} | {x.get("shop_name", "")} | {x.get("target_sale_price")}$ | {r}% | {s} נמכרו | עמלה {c}% | {x.get("product_id")}'
                  for s, x, c, r in cand] or ['- לא נמצאה חלופה עם עמלה']
    lines.append('')
open(REPORT, 'w', encoding='utf-8').write('\n'.join(lines))
print('\n'.join(lines))
