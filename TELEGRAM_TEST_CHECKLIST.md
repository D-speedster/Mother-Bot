# Real Telegram Test Checklist

این Checklist برای تست واقعی Admin Panel در Telegram است.

---

## 🔧 Pre-Test Setup

### ☐ Step 1: نصب Dependencies
```bash
pip install psutil==5.9.8
```

### ☐ Step 2: تنظیم Admin ID
در `.env`:
```env
AI_IMAGE_ADMIN_IDS=YOUR_TELEGRAM_USER_ID
```

💡 **چطور User ID خودم را پیدا کنم؟**
- به [@userinfobot](https://t.me/userinfobot) پیام بده
- یا از Mother Bot دستور `/me` بزن (اگر وجود دارد)

### ☐ Step 3: Start Mother Bot
```bash
python bot.py
```

### ☐ Step 4: ساخت AI Image Bot
1. به Mother Bot پیام `/newbot` بده
2. انتخاب کن: `🎨 ربات هوش مصنوعی و ویرایش عکس`
3. Token بده
4. Username بده
5. Bot باید خودکار start شود

### ☐ Step 5: بررسی Log
در Console Mother Bot باید ببینی:
```
✅ Admin Router برای ai_image لود و ترکیب شد
✅ ربات X (@username) شروع شد
```

---

## 🧪 Test Scenarios

### Test 1: ☐ Unauthorized Access

**هدف**: کاربر غیرمجاز نباید به Admin Panel دسترسی داشته باشد

**Steps**:
1. با یک اکانت Telegram که در `AI_IMAGE_ADMIN_IDS` نیست، به AI Image Bot بزن
2. Send: `/admin`

**Expected Result**:
```
⛔ دسترسی غیرمجاز.

این بخش فقط برای مدیران است.
```

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

**Notes**: _____________

---

### Test 2: ☐ Admin Panel Access

**هدف**: Admin باید به Panel دسترسی داشته باشد

**Steps**:
1. با اکانت Admin (که در `.env` است) به AI Image Bot بزن
2. Send: `/admin`

**Expected Result**:
- پیام خوش‌آمدگویی Admin Panel
- Reply Keyboard با 6 دکمه:
  - 📊 مدیریت
  - 📢 ارتباط
  - 🧠 AI
  - 📚 محتوا
  - ⚙️ سیستم
  - ⬅️ بازگشت

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

**Screenshot**: ☐ Taken

---

### Test 3: ☐ Management - User Stats

**Steps**:
1. `/admin`
2. Click: `📊 مدیریت`
3. Click: `👥 آمار کاربران` (Inline)

**Expected Result**:
```
👥 آمار کاربران

📊 کل کاربران: 0
🟢 فعال امروز: 0
📅 فعال این هفته: 0

➕ کاربر جدید امروز: 0
...
```

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 4: ☐ Management - Generation Stats

**Steps**:
1. Admin Panel → `📊 مدیریت`
2. Click: `🖼 آمار Generation`

**Expected Result**:
```
🖼 آمار Generation

📊 کل: 0
✅ موفق: 0
❌ ناموفق: 0
...
```

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 5: ☐ Communication - Broadcast

**هدف**: تست Broadcast flow با Confirmation

**Steps**:
1. Admin Panel → `📢 ارتباط`
2. Click: `📨 ارسال همگانی`
3. Type: "این یک تست ارسال همگانی است"
4. Click: `👥 همه کاربران`
5. بررسی Preview
6. Click: `✅ ارسال به X کاربر`

**Expected Result**:
- Preview نمایش داده شود
- Confirmation خواسته شود
- Broadcast ارسال شود (یا error برای 0 کاربر)

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

**Notes**: _____________

---

### Test 6: ☐ Communication - Sponsor Settings

**Steps**:
1. Admin Panel → `📢 ارتباط`
2. Click: `⭐ مدیریت Sponsor`
3. Click: `🟢 فعال کردن`
4. Click: `✏️ تغییر متن`
5. Type: "اسپانسر تستی"
6. Check result

**Expected Result**:
- Sponsor toggle شود
- متن update شود
- Confirmation نمایش داده شود

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 7: ☐ AI Settings - Provider Status

**Steps**:
1. Admin Panel → `🧠 AI`
2. Click: `🔌 Provider / API`

**Expected Result**:
```
🔌 Provider / API

Provider: mock
Model: default
وضعیت: ❌ not_configured

⚠️ توجه: API Key هرگز در Telegram نمایش داده نمی‌شود.
```

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 8: ☐ AI Settings - Styles Management

**Steps**:
1. Admin Panel → `🧠 AI`
2. Click: `🎨 Style Settings`
3. Click on: `✅ واقع‌گرایانه`
4. Click: `🔴 غیرفعال کردن`
5. Check result

**Expected Result**:
- Style disabled شود
- Status به `❌` تغییر کند
- Confirmation نمایش داده شود

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 9: ☐ Content - FAQ Creation

**Steps**:
1. Admin Panel → `📚 محتوا`
2. Click: `❓ FAQ`
3. Click: `➕ افزودن FAQ جدید`
4. Type question: "چطور تصویر بسازم؟"
5. Type answer: "روی دکمه ساخت تصویر کلیک کنید"
6. Check FAQ list

**Expected Result**:
- FAQ ساخته شود
- در لیست نمایش داده شود

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 10: ☐ Content - FAQ Delete with Confirmation

**Steps**:
1. Admin Panel → `📚 محتوا` → `❓ FAQ`
2. Click on FAQ
3. Click: `🗑️ حذف`
4. Check confirmation message

**Expected Result**:
```
🗑️ حذف FAQ

⚠️ آیا مطمئن هستید؟
این عملیات قابل بازگشت نیست.

[✅ بله، حذف شود] [❌ خیر]
```

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 11: ☐ Content - System Messages

**Steps**:
1. Admin Panel → `📚 محتوا`
2. Click: `💬 پیام‌های سیستم`
3. Click: `👋 خوش‌آمدگویی`
4. Type new message: "سلام! به ربات تست خوش آمدید"
5. Check result

**Expected Result**:
- پیام update شود
- Confirmation نمایش داده شود

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 12: ☐ System - Server Status

**Steps**:
1. Admin Panel → `⚙️ سیستم`
2. Click: `🖥 وضعیت Server`

**Expected Result**:
```
🖥 وضعیت Server

Status: running
Uptime: Xh Ym

CPU: X.X%
RAM: X.X% (XMB / XMB)

Python: 3.x.x
Platform: win32
```

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 13: ☐ System - Maintenance Mode ON

**هدف**: تست Maintenance Mode با Confirmation

**Steps**:
1. Admin Panel → `⚙️ سیستم`
2. Click: `🔧 Maintenance Mode`
3. Click: `🔴 روشن کردن Maintenance`
4. Check confirmation
5. Confirm

**Expected Result**:
```
🔴 روشن کردن Maintenance Mode

⚠️ توجه: با فعال کردن Maintenance Mode:
• کاربران نمی‌توانند تصویر تولید کنند
• پیام Maintenance به کاربران نمایش داده می‌شود

آیا مطمئن هستید؟

[✅ بله، روشن شود] [❌ خیر]
```

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 14: ☐ User Flow During Maintenance

**هدف**: کاربر عادی نباید بتواند تصویر بسازد

**Steps**:
1. با User غیر Admin به AI Image Bot بزن
2. Send: `/start`
3. Click: `🖼️ ساخت تصویر`

**Expected Result**:
```
🔧 سیستم در حال تعمیر و نگهداری است

لطفاً بعداً مراجعه کنید.
```

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 15: ☐ System - Maintenance Mode OFF

**Steps**:
1. Admin Panel → `⚙️ سیستم`
2. Click: `🔧 Maintenance Mode`
3. Click: `🟢 خاموش کردن Maintenance`
4. Confirm

**Expected Result**:
- Maintenance disabled شود
- User بتواند دوباره تصویر بسازد

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 16: ☐ User Flow - Normal Generation

**هدف**: User Flow نباید تغییر کرده باشد

**Steps**:
1. با User غیر Admin به AI Image Bot بزن
2. Send: `/start`
3. Click: `🖼️ ساخت تصویر`
4. Type prompt: "a cat"
5. Select Style: `🎨 واقع‌گرایانه`
6. Select Ratio: `1:1`
7. Select Quality: `⚡ استاندارد`
8. Select Count: `1`
9. Confirm generation

**Expected Result**:
- Wizard کامل کار کند
- تصویر mock تولید شود
- هیچ Admin option نمایش داده نشود

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

**Screenshot**: ☐ Taken

---

### Test 17: ☐ Movie Bot - Not Affected

**هدف**: Movie Bot نباید Admin Panel داشته باشد

**Steps**:
1. یک Movie Bot بساز (اگر وجود ندارد)
2. به Movie Bot بزن
3. Send: `/admin`

**Expected Result**:
- Command شناخته نشود
- یا: "این دستور وجود ندارد"
- Movie Bot normal کار کند

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 18: ☐ Error Handling - Safe Messages

**هدف**: خطاها امن باشند (بدون Stack Trace)

**Steps**:
1. با Admin به AI Image Bot بزن
2. Admin Panel → هر بخش
3. عملیات مختلف انجام بده
4. بررسی کن که اگر خطایی رخ داد، Stack Trace نمایش داده نشود

**Expected Result**:
- فقط پیام‌های کاربرپسند مثل:
  - "❌ خطا رخ داد"
  - "❌ عملیات انجام نشد"
- هیچ Stack Trace یا Internal Error

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 19: ☐ Navigation - Reply Keyboard

**هدف**: Reply Keyboard برای Navigation اصلی

**Steps**:
1. `/admin`
2. Click: `📊 مدیریت`
3. Click: `⬅️ بازگشت`
4. Check که به Admin Main برگشته

**Expected Result**:
- Navigation با Reply Keyboard کار کند
- بازگشت به Main Panel

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

### Test 20: ☐ Long Session Test

**هدف**: Admin Panel در Session طولانی کار کند

**Steps**:
1. وارد Admin Panel شو
2. بین بخش‌های مختلف navigate کن
3. عملیات مختلف انجام بده
4. 10+ دقیقه در Panel بمان
5. دوباره عملیاتی انجام بده

**Expected Result**:
- Panel responsive بماند
- FSM State حفظ شود (یا timeout منطقی)

**Actual Result**: _____________

**Status**: ☐ Pass ☐ Fail

---

## 📊 Test Summary

**Total Tests**: 20

**Passed**: ___ / 20

**Failed**: ___ / 20

**Critical Failures**: ___

**Notes**: 
_________________________________
_________________________________
_________________________________

---

## ✅ Sign-off

**Tester**: _____________

**Date**: _____________

**Environment**: 
- Python Version: _____________
- aiogram Version: _____________
- OS: _____________

**Overall Status**: ☐ Ready for Production ☐ Needs Fixes

**Next Steps**:
_________________________________
_________________________________
_________________________________
