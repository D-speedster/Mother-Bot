# 📋 توضیحات آپدیت جدید - بخش مدیریت ربات‌ها

## 🆕 تغییرات اعمال شده

### 1. Import های جدید (خط 7-8)

```python
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler
```

**توضیح:**
- `InlineKeyboardMarkup`: برای ساخت دکمه‌های شیشه‌ای زیر پیام
- `InlineKeyboardButton`: هر دکمه شیشه‌ای
- `CallbackQueryHandler`: برای مدیریت کلیک روی دکمه‌های Inline

---

### 2. تابع مدیریت ربات‌ها بازنویسی شد (خط 121-135)

```python
async def handle_bot_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ ساخت ربات جدید", callback_data="create_new_bot")],
        [InlineKeyboardButton("📋 ربات‌های من", callback_data="my_bots")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
```

**تفاوت با قبل:**
- ✅ حالا دکمه‌های **Inline** نشان می‌دهد (زیر پیام، شیشه‌ای)
- ✅ دکمه‌ها callback_data دارند (شناسه منحصر به فرد)
- ❌ قبلاً فقط یک متن ثابت بود

**callback_data چیست؟**
وقتی کاربر روی دکمه کلیک کند، این مقدار به ربات ارسال می‌شود تا بفهمد کدام دکمه زده شده.

---

### 3. تابع جدید: button_callback (خط 198-315)

این تابع **قلب اصلی سیستم Inline Keyboards** است!

#### بخش اول: دریافت کلیک (خط 200-204)
```python
query = update.callback_query
await query.answer()  # حذف loading از دکمه
data = query.data  # دریافت callback_data
```

---

#### بخش دوم: ساخت ربات جدید (خط 206-222)
```python
if data == "create_new_bot":
    keyboard = [
        [InlineKeyboardButton("🛒 ربات فروشگاهی", callback_data="bot_type_shop")],
        [InlineKeyboardButton("📥 ربات دانلودر", callback_data="bot_type_downloader")],
        ...
    ]
```

**چه اتفاقی می‌افتد:**
1. کاربر روی "➕ ساخت ربات جدید" کلیک می‌کند
2. `callback_data="create_new_bot"` ارسال می‌شود
3. ربات 6 نوع ربات را به صورت دکمه نشان می‌دهد
4. از `query.edit_message_text()` استفاده می‌کند (پیام قبلی ویرایش می‌شود)

---

#### بخش سوم: ربات‌های من (خط 224-238)
```python
elif data == "my_bots":
    message = "شما هنوز هیچ رباتی نساخته‌اید."
```

**چه اتفاقی می‌افتد:**
- کاربر روی "📋 ربات‌های من" کلیک می‌کند
- فعلاً لیست خالی نشان می‌دهد
- بعداً می‌توانید از دیتابیس ربات‌های کاربر را بخوانید

---

#### بخش چهارم: بازگشت به منوی اصلی (خط 240-249)
```python
elif data == "back_to_main":
    await query.edit_message_text(message)
    await query.message.reply_text(
        "به منوی اصلی بازگشتید:",
        reply_markup=get_main_keyboard()
    )
```

**چه اتفاقی می‌افتد:**
- دکمه‌های Inline پاک می‌شوند
- کیبورد اصلی (دکمه‌های بزرگ) دوباره نمایش داده می‌شود

---

#### بخش پنجم: بازگشت به مدیریت ربات‌ها (خط 251-265)
```python
elif data == "back_to_bot_management":
    # منوی اصلی مدیریت ربات‌ها را دوباره نشان می‌دهد
```

---

#### بخش ششم: انتخاب نوع ربات (خط 267-291)
```python
elif data.startswith("bot_type_"):
    bot_type = data.replace("bot_type_", "")
    
    bot_types = {
        "shop": "🛒 ربات فروشگاهی",
        "downloader": "📥 ربات دانلودر",
        ...
    }
    
    selected_bot = bot_types.get(bot_type, "ربات")
```

**چه اتفاقی می‌افتد:**
1. کاربر روی یکی از 6 نوع ربات کلیک می‌کند (مثلاً "🛒 ربات فروشگاهی")
2. `callback_data="bot_type_shop"` ارسال می‌شود
3. با `startswith("bot_type_")` چک می‌کنیم که از نوع‌های ربات است
4. با `replace` نوع ربات را استخراج می‌کنیم (shop)
5. از dictionary نام فارسی را پیدا می‌کنیم
6. پیام تایید با دکمه "✅ ادامه ساخت ربات" نشان می‌دهیم

**نکته مهم:**
- `startswith()`: چک می‌کند که callback_data با "bot_type_" شروع شود
- **چرا؟** چون 6 تا نوع ربات داریم، نمی‌خواهیم 6 بار `elif` بنویسیم!

---

#### بخش هفتم: ادامه ساخت ربات (خط 293-315)
```python
elif data.startswith("continue_create_"):
    bot_type = data.replace("continue_create_", "")
    
    # ذخیره نوع ربات در context
    context.user_data['creating_bot_type'] = bot_type
    
    message = """
🔑 دریافت توکن ربات
...
5️⃣ توکن را در همین چت برای من ارسال کنید
    """
    
    # تنظیم وضعیت کاربر
    context.user_data['waiting_for_token'] = True
```

**چه اتفاقی می‌افتد:**
1. کاربر روی "✅ ادامه ساخت ربات" کلیک می‌کند
2. `callback_data="continue_create_shop"` ارسال می‌شود
3. نوع ربات در `context.user_data` ذخیره می‌شود
4. راهنمای گرفتن توکن از BotFather نشان داده می‌شود
5. فلگ `waiting_for_token = True` فعال می‌شود

**context.user_data چیست؟**
- یک دیکشنری (dictionary) موقت برای هر کاربر
- وقتی ربات restart شود، پاک می‌شود
- برای ذخیره دائمی باید از دیتابیس استفاده کنید

---

### 4. تغییر در تابع main (خط 319-329)

```python
application.add_handler(CallbackQueryHandler(button_callback))
```

**توضیح:**
- این handler تمام کلیک‌های روی دکمه‌های Inline را می‌گیرد
- باید **قبل از MessageHandler** اضافه شود (اولویت بالاتر)

---

## 🔄 جریان کامل کار:

```
کاربر: روی دکمه "🤖 مدیریت ربات‌ها" کلیک می‌کند
    ↓
handle_bot_management() فراخوانی می‌شود
    ↓
3 دکمه Inline نمایش داده می‌شود:
  - ➕ ساخت ربات جدید
  - 📋 ربات‌های من
  - 🔙 بازگشت به منوی اصلی
    ↓
کاربر: روی "➕ ساخت ربات جدید" کلیک می‌کند
    ↓
button_callback() با data="create_new_bot" فراخوانی می‌شود
    ↓
6 نوع ربات به صورت دکمه نمایش داده می‌شود
    ↓
کاربر: روی "🛒 ربات فروشگاهی" کلیک می‌کند
    ↓
button_callback() با data="bot_type_shop" فراخوانی می‌شود
    ↓
پیام تایید + دکمه "✅ ادامه ساخت ربات" نمایش داده می‌شود
    ↓
کاربر: روی "✅ ادامه ساخت ربات" کلیک می‌کند
    ↓
button_callback() با data="continue_create_shop" فراخوانی می‌شود
    ↓
راهنمای گرفتن توکن از BotFather نمایش داده می‌شود
context.user_data['waiting_for_token'] = True
context.user_data['creating_bot_type'] = 'shop'
```

---

## 🎯 تفاوت‌های کلیدی Inline Keyboard vs Reply Keyboard

| ویژگی | Inline Keyboard | Reply Keyboard |
|-------|----------------|----------------|
| محل نمایش | زیر پیام (شیشه‌ای) | پایین صفحه (جایگزین کیبورد) |
| ویرایش | می‌شود (با edit_message) | نمی‌شود |
| callback | callback_data | text message |
| استفاده | منوها، تاییدیه‌ها | منوی اصلی |
| مثال | دکمه‌های "ساخت ربات جدید" | دکمه "🤖 مدیریت ربات‌ها" |

---

## 💡 نکات مهم:

1. **query.answer()**: حتماً باید فراخوانی شود، وگرنه کاربر loading می‌بیند
2. **query.edit_message_text()**: پیام قبلی را ویرایش می‌کند (بدون پیام جدید)
3. **callback_data**: حداکثر 64 بایت می‌تواند باشد
4. **context.user_data**: فقط تا زمانی که ربات روشن است، ذخیره می‌ماند

---

## 🚀 مراحل بعدی (اختیاری):

1. **دریافت و اعتبارسنجی توکن**: وقتی کاربر توکن را می‌فرستد، چک کنیم معتبر است
2. **ذخیره در دیتابیس**: توکن و نوع ربات را در SQLite یا PostgreSQL ذخیره کنیم
3. **راه‌اندازی ربات کاربر**: با توکن دریافتی، ربات کاربر را فعال کنیم
4. **لیست ربات‌ها**: در بخش "📋 ربات‌های من" لیست واقعی نشان دهیم

---

## ✅ تست کنید:

1. ربات را اجرا کنید: `python bot.py`
2. روی "🤖 مدیریت ربات‌ها" کلیک کنید
3. روی "➕ ساخت ربات جدید" کلیک کنید
4. یکی از 6 نوع ربات را انتخاب کنید
5. روی "✅ ادامه ساخت ربات" کلیک کنید
6. راهنمای دریافت توکن را ببینید

---

**سوالی دارید؟ 😊**
