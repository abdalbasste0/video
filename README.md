# بوت أتمتة يوتيوب عبر ديسكورد 🤖📺

تعطي الأوامر في ديسكورد، فينفّذها البوت على قنوات يوتيوب المربوطة: رفع فيديو، جدولة النشر، تعديل البيانات، الصور المصغرة، الحذف، والرد على التعليقات. يمكن ربط أكثر من قناة.

## الأوامر

| الأمر | الوظيفة |
|---|---|
| `/channels` | عرض القنوات المربوطة |
| `/stats channel` | إحصائيات القناة (مشتركين، مشاهدات، عدد الفيديوهات) |
| `/videos channel [count]` | آخر الفيديوهات مع إحصائياتها |
| `/upload channel title file\|url [description] [tags] [privacy] [schedule] [thumbnail]` | رفع فيديو من ملف مرفق أو رابط، مع جدولة اختيارية |
| `/edit channel video [title] [description] [tags]` | تعديل بيانات الفيديو |
| `/privacy channel video [privacy] [schedule]` | تغيير الخصوصية أو جدولة النشر |
| `/thumbnail channel video image` | تغيير الصورة المصغرة |
| `/delete channel video` | حذف فيديو (يطلب تأكيداً) |
| `/comments channel video [count]` | آخر التعليقات |
| `/reply channel comment_id text` | الرد على تعليق |

- `video` يقبل الرابط الكامل أو المعرف (مثل `dQw4w9WgXcQ`).
- `schedule` بصيغة `2026-11-10 18:30` حسب المنطقة الزمنية في `TIMEZONE`.
- فقط المستخدمون في `ALLOWED_USER_IDS` يمكنهم إعطاء الأوامر.

## الإعداد

### 1) تثبيت المتطلبات
```bash
python -m venv .venv
source .venv/bin/activate        # على ويندوز: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 2) إنشاء بوت ديسكورد
1. ادخل إلى https://discord.com/developers/applications ← **New Application**.
2. من **Bot** اضغط **Reset Token** وانسخ التوكن إلى `DISCORD_TOKEN` في `.env`.
3. من **OAuth2 → URL Generator** اختر `bot` و `applications.commands`، ومن الصلاحيات `Send Messages` و `Embed Links` و `Attach Files`، ثم افتح الرابط وأضف البوت لسيرفرك.
4. فعّل **Developer Mode** في ديسكورد (Settings → Advanced)، ثم انقر بزر الفأرة الأيمن على اسمك ← **Copy User ID** وضعه في `ALLOWED_USER_IDS`. وانسخ معرف السيرفر إلى `DISCORD_GUILD_ID` لتظهر الأوامر فوراً.

### 3) تفعيل YouTube API
1. ادخل إلى https://console.cloud.google.com وأنشئ مشروعاً.
2. **APIs & Services → Library** ← فعّل **YouTube Data API v3**.
3. **OAuth consent screen** ← اختر External، وأضف بريدك في **Test users**.
4. **Credentials → Create Credentials → OAuth client ID** ← النوع **Desktop app**.
5. حمّل ملف JSON وضعه بجانب البوت باسم `client_secret.json`.

### 4) ربط قنوات يوتيوب
لكل قناة شغّل (على جهاز فيه متصفح):
```bash
python auth.py main
python auth.py gaming
```
سجّل الدخول واختر القناة. يُحفظ التوكن في `tokens/<الاسم>.json`.
> إذا كان البوت على سيرفر بدون متصفح: شغّل `auth.py` على جهازك ثم انسخ مجلد `tokens/` إلى السيرفر.

### 5) التشغيل
```bash
python bot.py
```
ثم اكتب `/help` في ديسكورد.

## ملاحظات مهمة
- **حصة يوتيوب (Quota):** الحصة المجانية 10,000 وحدة يومياً؛ رفع فيديو واحد يستهلك نحو 1,600 وحدة (≈ 6 فيديوهات يومياً). يمكن طلب زيادة من Google.
- **مشاريع غير موثّقة:** الفيديوهات المرفوعة عبر API من مشروع لم يجتز تدقيق Google قد تُقفل كـ"خاص". للنشر العام قدّم طلب [Audit](https://support.google.com/youtube/contact/yt_api_form).
- **وضع الاختبار:** ما دامت شاشة الموافقة في وضع Testing، تنتهي صلاحية التوكن بعد 7 أيام. انشر التطبيق (Publish app) لتجنب إعادة الربط.
- **حجم الملفات:** ملفات ديسكورد المرفقة محدودة الحجم؛ للفيديوهات الكبيرة استخدم خيار `url` برابط تحميل مباشر.
- لا ترفع `.env` أو `client_secret.json` أو `tokens/` إلى GitHub (موجودة في `.gitignore`).
