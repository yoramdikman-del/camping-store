# חיפוש מוצרים באלי אקספרס לפי מילות חיפוש, לצורך מחקר בלבד (לא משנה את האתר).
# קורא את search/queries.txt (שורה = חיפוש) וכותב את כל התוצאות ל-search/results.json.
# הסוד נקרא מ-ALI_APP_SECRET ב-GitHub Secrets.
import os, sys, json, time, hmac, hashlib, datetime, requests

APP_KEY = os.environ.get('ALI_APP_KEY', '553904')
APP_SECRET = os.environ.get('ALI_APP_SECRET', '').strip()
URL = 'https://api-sg.aliexpress.com/sync'
if not APP_SECRET:
    sys.exit('חסר הסוד ALI_APP_SECRET')

def call(method, **params):
    res = {}
    for attempt in range(4):
        p = {'app_key': APP_KEY, 'method': method, 'sign_method': 'sha256', 'timestamp': str(int(time.time() * 1000))}
        p.update({k: str(v) for k, v in params.items()})
        base = ''.join(k + p[k] for k in sorted(p))
        p['sign'] = hmac.new(APP_SECRET.encode(), base.encode(), hashlib.sha256).hexdigest().upper()
        try:
            res = requests.post(URL, data=p, timeout=30).json()
        except Exception as e:
            res = {'error': str(e)}
        if 'ApiCallLimit' in str(res)[:300]:
            time.sleep(2 + attempt * 2); continue
        return res
    return res

queries = [l.strip() for l in open('search/queries.txt', encoding='utf-8') if l.strip() and not l.startswith('#')]
pages = int(os.environ.get('PAGES', '2'))
found, errors = {}, []
for q in queries:
    for method in ('aliexpress.affiliate.product.query', 'aliexpress.affiliate.hotproduct.query'):
        for page in range(1, pages + 1):
            res = call(method, keywords=q, ship_to_country='IL', target_currency='USD', target_language='EN',
                       page_size=50, page_no=page, sort='LAST_VOLUME_DESC', tracking_id='campsite')
            key = method.replace('.', '_') + '_response'
            root = (res.get(key) or {}).get('resp_result') or {}
            if root.get('resp_code') != 200:
                errors.append({'q': q, 'method': method, 'page': page, 'res': str(res)[:200]}); break
            items = ((root.get('result') or {}).get('products') or {}).get('product', [])
            for x in items:
                pid = str(x.get('product_id'))
                r = found.setdefault(pid, {
                    'id': pid, 'title': x.get('product_title', ''), 'shop': x.get('shop_name', ''),
                    'shop_url': x.get('shop_url', ''), 'price': x.get('target_sale_price'),
                    'orig_price': x.get('target_original_price'), 'rating': x.get('evaluate_rate'),
                    'sold': x.get('lastest_volume'), 'img': x.get('product_main_image_url'),
                    'url': (x.get('product_detail_url') or '').split('?')[0],
                    'commission': max([x.get('hot_product_commission_rate'), x.get('commission_rate')], key=lambda v: float(str(v or 0).replace('%', '') or 0)),
                    'category': x.get('second_level_category_name') or x.get('first_level_category_name'),
                    'queries': []})
                if q not in r['queries']:
                    r['queries'].append(q)
            if len(items) < 50:
                break
            time.sleep(0.4)
out = {'date': datetime.datetime.utcnow().isoformat(timespec='minutes'), 'queries': queries,
       'count': len(found), 'errors': errors, 'products': list(found.values())}
json.dump(out, open('search/results.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(queries), 'queries,', len(found), 'products,', len(errors), 'errors')
