# 📋 توضیحات آپدیت V2 - دکمه ساخت ربات و دریافت توکن

## 🆕 تغییرات جدید در این نسخه

---

## 1️⃣ تغییر ساختار منوی اصلی (Reply Keyboard)

### قبل:
```python
keyboard = [
    [KeyboardButton("🛒 خرید اشتراک"), KeyboardButton("📋 قوانین")],
    [KeyboardButton("👤 حساب کاربری"), KeyboardButton("💰 کسب درآمد")],
    [KeyboardButton("🤖 مدیریت ربات‌ها"), KeyboardButton("💬 پشتیبانی")]
]
```

### بعد:
```python
keyboard = [
    [KeyboardButton("🤖 ساخت ربات")],  # دکمه تک‌سطری - جدید!
    [KeyboardButton("👤 حساب کاربری"), KeyboardButton("💰 کسب درآمد")],
    [KeyboardButton("🤖 مدیریت ربات‌ها"), KeyboardButton("💬 پشتیبانی")],
    [KeyboardButton("📋 قوانین")]
]
```

### 📝 تغییرات:
- ❌ دکمه "🛒 خرید اشتراک" حذف شد
- ✅ دکمه "🤖 ساخت ربات" اضافه شد (تک‌سطری)
- 📋 دکمه "قوانین" به انتهای منو منتقل شد

### 💡 چرا تک‌سطری؟
- برجسته‌تر است
- توجه کاربر را جلب می‌کند
- اولین اکشن کاربر ساخت ربات است (CTA - Call To Action)

---

## 2️⃣ تابع جدید: show_bot_types_menu()

```python
async def show_bot_types_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback: bool = False):
    """نمایش منوی انتخاب نوع ربات - قابل استفاده از هر دو مسیر"""
    keyboard = [
        [InlineKeyboardButton("🛒 ربات فروشگاهی", callback_data="bot_type_shop")],
        [InlineKeyboardButton("📥 ربات دانلودر", callback_data="bot_type_downloader")],
        ...
    ]
    
    if is_callback:
        # اگر از طریق Inline Button آمده
        query = update.callback_query
        await query.edit_message_text(message, reply_markup=reply_markup)
    else:
        # اگر از طریق دکمه منوی اصلی آمده
        await update.message.reply_text(message, reply_markup=reply_markup)
```

### 🎯 هدف:
این تابع از **دو مسیر مختلف** قابل فراخوانی است:

#### مسیر 1: از دکمه "🤖 ساخت ربات" (Reply Keyboard)
```
کاربر روی "🤖 ساخت ربات" کلیک می‌کند
    ↓
handle_message() فراخوانی می‌شود
    ↓
show_bot_types_menu(update, context, is_callback=False)
    ↓
پیام جدید با Inline Buttons ارسال می‌شود
```

#### مسیر 2: از دکمه "➕ ساخت ربات جدید" (Inline Keyboard)
```
کاربر روی "➕ ساخت ربات جدید" کلیک می‌کند
    ↓
button_callback() فراخوانی می‌شود
    ↓
show_bot_types_menu(update, context, is_callback=True)
    ↓
پیام قبلی ویرایش می‌شود (edit)
```

### 💡 مزیت:
- **DRY principle** (Don't Repeat Yourself)
- یک تابع برای دو مسیر
- کد تمیزتر و قابل نگهداری‌تر

---

## 3️⃣ تابع جدید: validate_bot_token()

```python
async def validate_bot_token(token: str) -> bool:
    """اعتبارسنجی ساده توکن ربات"""
    # چک کردن فرمت کلی توکن تلگرام: NUMBER:STRING
    if ':' not in token:
        return False
    
    parts = token.split(':')
    if len(parts) != 2:
        return False
    
    # بخش اول باید عدد باشد (Bot ID)
    if not parts[0].isdigit():
        return False
    
    # بخش دوم باید حداقل 30 کاراکتر باشد
    if len(parts[1]) < 30:
        return False
    
    return True
```

### 📋 قوانین اعتبارسنجی:

1. **حاوی `:` باشد**
   - توکن تلگرام: `123456789:ABCdefGHI...`

2. **فقط 2 بخش داشته باشد**
   - قبل از `:` → Bot ID
   - بعد از `:` → Secret Token

3. **بخش اول عدد باشد**
   - مثال: `123456789`

4. **بخش دوم حداقل 30 کاراکتر باشد**
   - مثال: `ABCdefGHIjklMNOpqrsTUVwxyz...`

### ❌ توکن‌های نامعتبر:
```python
"123456789"                    # بدون :
"123456789:ABC"                # کوتاه (کمتر از 30 کاراکتر)
"abc:ABCdefGHI..."             # بخش اول عدد نیست
"123:456:ABC..."               # بیشتر از 2 بخش
```

### ✅ توکن معتبر:
```python
"123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890"
```

---

## 4️⃣ تغییر اساسی در handle_message()

### بخش جدید: دریافت توکن (خطوط اول تابع)

```python
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # بررسی اینکه آیا کاربر در حال ورود توکن است
    if context.user_data.get('waiting_for_token', False):
        # دریافت توکن از کاربر
        token = text.strip()
        
        # اعتبارسنجی توکن
        if not await validate_bot_token(token):
            await update.message.reply_text("❌ توکن نامعتبر است!")
            return
        
        # توکن معتبر است - ذخیره و پیام موفقیت
        ...
```

### 🔄 جریان کار:

#### حالت 1: کاربر در حالت انتظار توکن است
```
کاربر متن می‌فرستد
    ↓
چک می‌کنیم: waiting_for_token == True?
    ↓
بله! پس این متن توکن است
    ↓
اعتبارسنجی توکن
    ↓
معتبر؟
  ├─ بله → ذخیره + پیام موفقیت
  └─ خیر → پیام خطا + درخواست مجدد
```

#### حالت 2: کاربر در حالت عادی است
```
کاربر متن می‌فرستد
    ↓
چک می‌کنیم: waiting_for_token == True?
    ↓
خیر! پس دکمه منو است
    ↓
if/elif برای تشخیص دکمه
```

### 💾 ذخیره توکن:

```python
# ذخیره توکن (فعلاً در context، بعداً در دیتابیس)
if 'user_bots' not in context.user_data:
    context.user_data['user_bots'] = []

context.user_data['user_bots'].append({
    'type': bot_type,
    'token': token,
    'created_at': 'اکنون'
})
```

**ساختار داده:**
```python
user_bots = [
    {
        'type': 'shop',
        'token': '123456789:ABC...',
        'created_at': 'اکنون'
    },
    {
        'type': 'downloader',
        'token': '987654321:XYZ...',
        'created_at': 'اکنون'
    }
]
```

---

## 5️⃣ بهبود نمایش لیست ربات‌ها (my_bots)

### قبل:
```python
message = "شما هنوز هیچ رباتی نساخته‌اید."
```

### بعد:
```python
if not user_bots:
    message = "شما هنوز هیچ رباتی نساخته‌اید."
else:
    # نمایش لیست ربات‌ها
    bots_list = "\n\n".join([
        f"🤖 {bot_types_names.get(bot['type'], 'ربات')}\n"
        f"⏰ زمان ساخت: {bot.get('created_at', 'نامشخص')}\n"
        f"✅ وضعیت: فعال"
        for bot in user_bots
    ])
    
    message = f"""
📋 ربات‌های من

تعداد ربات‌ها: {len(user_bots)} عدد

{bots_list}
    """
```

### 📊 نمونه خروجی:

```
📋 ربات‌های من

تعداد ربات‌ها: 2 عدد

🤖 🛒 ربات فروشگاهی
⏰ زمان ساخت: اکنون
✅ وضعیت: فعال

🤖 📥 ربات دانلودر
⏰ زمان ساخت: اکنون
✅ وضعیت: فعال
```

---

## 6️⃣ مسیر دکمه "🤖 ساخت ربات"

### کد:
```python
if text == "🤖 ساخت ربات":
    # هدایت مستقیم به منوی انتخاب نوع ربات
    await show_bot_types_menu(update, context, is_callback=False)
```

### 🔄 جریان کامل:

```
کاربر /start می‌زند
    ↓
منوی اصلی نمایش داده می‌شود
    ↓
کاربر روی "🤖 ساخت ربات" کلیک می‌کند
    ↓
show_bot_types_menu() با is_callback=False فراخوانی می‌شود
    ↓
6 نوع ربات نمایش داده می‌شود
    ↓
کاربر روی یک نوع کلیک می‌کند (مثلاً "🛒 ربات فروشگاهی")
    ↓
button_callback() با data="bot_type_shop" فراخوانی می‌شود
    ↓
پیام تایید + دکمه "✅ ادامه ساخت ربات"
    ↓
کاربر روی "✅ ادامه" کلیک می‌کند
    ↓
button_callback() با data="continue_create_shop" فراخوانی می‌شود
    ↓
راهنمای BotFather + waiting_for_token = True
    ↓
کاربر توکن را می‌فرستد
    ↓
handle_message() توکن را دریافت می‌کند
    ↓
validate_bot_token() اعتبارسنجی می‌کند
    ↓
ذخیره در context.user_data['user_bots']
    ↓
پیام موفقیت + دکمه‌های بازگشت
```

---

## 🎯 نکات مهم:

### 1. State Management (مدیریت وضعیت)
```python
context.user_data['waiting_for_token'] = True   # فعال کردن حالت دریافت توکن
context.user_data['creating_bot_type'] = 'shop' # ذخیره نوع ربات
```

### 2. Priority در handle_message
```python
# ترتیب اولویت:
1. چک کردن waiting_for_token (اول از همه)
2. چک کردن دکمه‌های منو
```

**چرا؟**
- اگر کاربر در حال ورود توکن باشد، نباید با دکمه‌های منو تداخل کند

### 3. پاک کردن وضعیت
```python
context.user_data['waiting_for_token'] = False
context.user_data['creating_bot_type'] = None
```

**چرا؟**
- بعد از دریافت موفق توکن، باید حالت را ریست کنیم
- وگرنه هر پیام بعدی را هم توکن می‌پندارد!

---

## 📊 مقایسه قبل و بعد:

| ویژگی | قبل | بعد |
|-------|-----|-----|
| دکمه ساخت ربات | ❌ نداشت | ✅ تک‌سطری در منوی اصلی |
| دریافت توکن | ❌ نداشت | ✅ با اعتبارسنجی |
| ذخیره ربات‌ها | ❌ نداشت | ✅ در context.user_data |
| لیست ربات‌ها | ❌ خالی | ✅ نمایش لیست واقعی |
| State Management | ❌ نداشت | ✅ waiting_for_token |

---

## 🚀 آماده برای تست:

```bash
python bot.py
```

### مسیر تست:
1. ✅ /start → منوی اصلی
2. ✅ کلیک روی "🤖 ساخت ربات"
3. ✅ انتخاب نوع ربات (مثلاً "🛒 ربات فروشگاهی")
4. ✅ کلیک روی "✅ ادامه ساخت ربات"
5. ✅ ارسال توکن (معتبر یا نامعتبر)
6. ✅ مشاهده پیام موفقیت
7. ✅ رفتن به "📋 ربات‌های من" و مشاهده لیست

---

## 💡 نکته نهایی:

**context.user_data موقت است!**

- وقتی ربات restart شود، تمام داده‌ها پاک می‌شوند
- برای ذخیره دائمی باید از **دیتابیس** استفاده کنید:
  - SQLite (ساده)
  - PostgreSQL (حرفه‌ای)
  - MongoDB (NoSQL)

---

سوالی داری؟ 😊
