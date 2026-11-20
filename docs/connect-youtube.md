# ربط يوتيوب (رفع تلقائي)

1. ادخل https://console.cloud.google.com ← اعمل مشروع جديد.
2. APIs & Services ← Library ← فعّل **YouTube Data API v3**.
3. OAuth consent screen ← External ← ضيف إيميلك في Test users.
4. Credentials ← Create credentials ← OAuth client ID ← نوع **Desktop app** ← خد `Client ID` و `Client secret`.
5. هات الـ Refresh Token بأسهل طريقة:
   - افتح https://developers.google.com/oauthplayground
   - من الترس ⚙️ علّم «Use your own OAuth credentials» وحط الـ ID والـ Secret.
   - في الخانة اكتب `https://www.googleapis.com/auth/youtube.upload` ← Authorize ← سجل دخول بحساب القناة.
   - Exchange authorization code for tokens ← انسخ **Refresh token**.
   - (لازم تضيف `https://developers.google.com/oauthplayground` في Authorized redirect URIs للـ client.)
6. في لوحة المصنع ← الربط ← إضافة «يوتيوب» ← حط الثلاثة ← الخصوصية `private` في الأول ← اختبار.

> ملاحظة: مشاريع جوجل الجديدة غير المراجَعة بترفع الفيديوهات «خاصة» لحد ما تعمل مراجعة للتطبيق. ارفع private وراجع ثم انشر.

# تيك توك
محتاج تطبيق على https://developers.tiktok.com بصلاحية `video.publish` و Access Token للحساب. التطبيقات غير المعتمدة تنشر `SELF_ONLY` بس.

# فيسبوك
Page ID + Page Access Token (صلاحيات `pages_manage_posts` و `pages_read_engagement`) من Graph API Explorer.

# إنستجرام / أي تطبيق مش موجود
استخدم رابط **Webhook** مع n8n أو Make أو Zapier: المصنع يبعتلهم بيانات الفيديو (أو الملف نفسه) وهما يكمّلوا لأي منصة (إنستجرام ريلز، جوجل درايف، شيت، إلخ).

# الموبايل
- **تيليجرام**: اعمل بوت من @BotFather. نفس البوت ينفع للتحكم (`/video` و `/auto`) ولاستلام الفيديوهات.
- **ntfy**: نزّل تطبيق ntfy واشترك في اسم قناة صعب التخمين → إشعار أول ما الفيديو يخلص.
- **أندرويد بالكابل**: رابط «أمر على الحاسوب» مع `adb push {short} /sdcard/Movies/`.
- **جوجل درايف/دروبوكس**: رابط «أمر» مع `rclone copy {video} gdrive:Videos` أو انسخ لمجلد دروبوكس.
