# מעדכן את שער הדולר-שקל לקובץ data/rate.json, פעם ביום.
# מקור ראשי: השער היציג של בנק ישראל. גיבוי: Frankfurter (הבנק האירופי המרכזי).
import json, datetime, requests

def boi():
    r = requests.get('https://boi.org.il/PublicApi/GetExchangeRate?key=USD', timeout=30).json()
    return float(r['currentExchangeRate']), str(r.get('lastUpdate', ''))[:10], 'בנק ישראל (שער יציג)'

def frankfurter():
    r = requests.get('https://api.frankfurter.dev/v1/latest?from=USD&to=ILS', timeout=30).json()
    return float(r['rates']['ILS']), r['date'], 'Frankfurter (ECB)'

for src in (boi, frankfurter):
    try:
        rate, date, name = src()
        if 2 < rate < 6:
            break
    except Exception as e:
        print('מקור נכשל:', src.__name__, e)
else:
    raise SystemExit('לא התקבל שער')

out = {'usd_ils': round(rate, 4), 'date': date or datetime.date.today().isoformat(), 'source': name}
json.dump(out, open('data/rate.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(out)
