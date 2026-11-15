# AnyPS5 → Discord (الصورة الأصلية)

هذا المستودع يرسل صورة التقدم المنشورة من مشروع AnyPS5 إلى روم Discord كل ساعتين.
الصورة تُحمّل من صفحة المشروع بصيغة SVG ثم تُحوّل إلى PNG حتى تظهر كصورة مرفقة داخل Discord. لا يعاد رسمها أو تعديل تصميمها.

## 1) أنشئ مستودع GitHub

1. افتح GitHub وأنشئ Repository جديداً.
2. اجعله Public أو Private حسب رغبتك.
3. ارفع محتويات هذا المجلد إلى جذر المستودع، مع الحفاظ على المسار:
   `.github/workflows/anyps5-progress.yml`

## 2) أنشئ Discord Webhook

1. افتح إعدادات الروم المطلوب في Discord.
2. ادخل إلى **Integrations → Webhooks**.
3. أنشئ Webhook جديداً، واختر الروم الصحيح.
4. انسخ Webhook URL. لا تنشره ولا تضعه داخل ملف workflow.

## 3) خزّن الرابط كسِرّ في GitHub

داخل مستودعك:
**Settings → Secrets and variables → Actions → New repository secret**

- Name: `DISCORD_WEBHOOK_URL`
- Secret: الصق رابط Webhook الذي نسخته من Discord.

احفظ السر.

## 4) جرّب الإرسال فوراً

1. افتح تبويب **Actions** في مستودعك.
2. اختر **AnyPS5 progress image to Discord**.
3. اضغط **Run workflow** ثم أكّد التشغيل.
4. إذا نجح التشغيل، ستصل الصورة إلى الروم المحدد.

بعدها سيعمل تلقائياً كل ساعتين حسب توقيت UTC. قد يتأخر GitHub Actions أحياناً عن الموعد المحدد.

## الملفات

- `.github/workflows/anyps5-progress.yml`: ينزّل الصورة الأصلية، يحوّلها إلى PNG، ثم يرسلها إلى Discord.

## ملاحظات

- رابط صورة المشروع المستخدم:
  `https://boykopovar.github.io/AnyPS5/progress.svg`
- الصورة المرسلة هي نفس رسم SVG المنشور من AnyPS5، وليست إعادة تصميم. التحويل إلى PNG هدفه ضمان ظهورها كمرفق في Discord.
- إذا غيّر المشروع رابط الصورة أو أوقف نشرها، سيفشل التشغيل بدلاً من إرسال صورة قديمة.
- لا تضع Webhook URL في ملفات المستودع؛ استخدم GitHub Actions Secret فقط.
