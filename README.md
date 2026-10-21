# מוצרים לקמפינג וטיולים – חנות ציוד שטח

אתר סטטי (GitHub Pages) שמציג ציוד קמפינג, טיולים ופיקניק מחנויות רשמיות באלי אקספרס, עם קישורי שותפים (מזהה מעקב campsite).
נבנה מאותה תבנית כמו photo-store (חנות "צילום בכל גיל").

- `index.html` – האתר. קורא את המוצרים מ-`data/products.json`.
- `data/products.json` – כל המוצרים והאוספים. מוצר עם `status: pending` מוסתר באתר עד שיורם מאשר.
- `scripts/make_links.py` + `make-links.yml` – יצירת קישורי שותפים (campsite) למוצרים ממתינים. מריצים ידנית מלשונית Actions.
- `scripts/refresh.py` + `refresh.yml` – בדיקה שבועית מול אלי אקספרס (מחיר, דירוג, מוצרים שנעלמו). התוצאה נפתחת כבקשת שינוי שמחכה לאישור.
- `scripts/fetch_media.py` – הורדת תמונות מוצרים לפי `media/requests.txt`.
- `scripts/search.py` – חיפוש מחקר לפי `search/queries.txt` (לא משנה את האתר).
- הסוד של ה-API נשמר רק ב-Settings → Secrets → Actions בשם `ALI_APP_SECRET`.

## כללים
- חנויות מותג רשמיות בלבד (Naturehike, Fire-Maple, Widesea, FLEXTAIL, AONIJIE, NITECORE, Sofirn ועוד).
- בלי סכינים, בלי בלוני גז ואביזרי מילוי גז, בלי ביגוד ונעליים.
- מחיר "החל מ-", או גרסה מומלצת (variant) עם מחיר שנבדק ידנית.
- כותרות: שם המותג באנגלית, כל השאר בעברית.
