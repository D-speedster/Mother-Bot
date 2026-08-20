# 🔧 راهنمای لایه Service و اعتبارسنجی واقعی توکن

## ✅ تغییرات اعمال شده در مرحله 5

---

## 📊 خلاصه تغییرات

### 🆕 موارد اضافه شده:
1. ✅ پوشه `services/` با لایه Business Logic
2. ✅ فایل `services/bot_service.py` با اعتبارسنجی واقعی توکن
3. ✅ اتصال به Telegram Bot API (`getMe`)
4. ✅ دریافت اطلاعات واقعی ربات (نام، یوزرنیم، ID)
5. ✅ نمایش اطلاعات ربات در پیام موفقیت و لیست ربات‌ها
6. ✅ مدیریت خطاها با Exception سفارشی

---

## 🗂️ ساختار جدید پروژه

```
mother-bot/
├── bot.py
├── config.py
├── .env
├── requirements.txt          # ✨ اضافه شد: aiohttp
│
├── handlers/
│   ├── __init__.py
│   ├── start.py
│   └── bot_maker.py          # ✨ آپدیت شد
│
└── services/                 # ✨ جدید!
    ├── __init__.py
    └── bot_service.py        # ✨ جدید!
```

---

## 📁 فایل‌های جدید و تغییرات

### 1️⃣ `services/__init__.py`

```python
"""
پکیج services - شامل لایه business logic و external API calls
"""
from .bot_service import validate_bot_token, BotValidationError

__all__ = ['validate_bot_token', 'BotValidationError']
```

**نقش:**
- Export کردن توابع اصلی برای استفاده در handlerها

---

### 2️⃣ `services/bot_service.py` (فایل اصلی لایه Service)

#### 🔸 Exception سفارشی:

```python
class BotValidationError(Exception):
    """خطای سفارشی برای اعتبارسنجی توکن"""
    pass
```

**چرا؟**
- برای تفکیک خطاهای اعتبارسنجی از خطاهای عمومی
- مدیریت بهتر خطاها در handler

---

#### 🔸 تابع اصلی: `validate_bot_token()`

```python
async def validate_bot_token(token: str) -> Dict[str, Any]:
    """
    اعتبارسنجی توکن ربات با استفاده از Telegram Bot API
    
    Returns:
        {
            'id': int,
            'username': str,
            'first_name': str,
            'is_bot': bool
        }
        
    Raises:
        BotValidationError: اگر توکن نامعتبر باشد
    """
```

**جریان کار:**

```
1. بررسی فرمت ساده توکن (قبل از درخواست API)
   ├─ حاوی ':' باشد
   ├─ 2 بخش داشته باشد
   ├─ بخش اول عدد باشد
   └─ بخش دوم حداقل 30 کاراکتر باشد
   
2. ساخت URL درخواست:
   https://api.telegram.org/bot{token}/getMe
   
3. ارسال درخواست GET با aiohttp
   └─ timeout: 10 ثانیه
   
4. بررسی پاسخ JSON:
   ├─ ok == true? ✅ توکن معتبر
   │  ├─ استخراج id, username, first_name
   │  ├─ بررسی is_bot == true
   │  └─ برگرداندن dict اطلاعات
   │
   └─ ok == false? ❌ توکن نامعتبر
      └─ raise BotValidationError
```

---

#### 🔸 مثال درخواست و پاسخ API

**درخواست:**
```
GET https://api.telegram.org/bot123456789:ABCdef.../getMe
```

**پاسخ موفق:**
```json
{
  "ok": true,
  "result": {
    "id": 123456789,
    "is_bot": true,
    "first_name": "My Bot",
    "username": "my_bot",
    "can_join_groups": true,
    "can_read_all_group_messages": false,
    "supports_inline_queries": false
  }
}
```

**پاسخ نامعتبر:**
```json
{
  "ok": false,
  "error_code": 401,
  "description": "Unauthorized"
}
```

---

### 3️⃣ تغییرات در `handlers/bot_maker.py`

#### 🔸 Import های جدید:

```python
import logging
from services import validate_bot_token, BotValidationError

logger = logging.getLogger(__name__)
```

---

#### 🔸 حذف تابع `validate_bot_token()` قدیمی:

```python
# ❌ حذف شد - تابع ساده قدیمی
def validate_bot_token(token: str) -> bool:
    if ':' not in token:
        return False
    ...
```

✅ **جایگزین:** استفاده از `validate_bot_token()` از `services/`

---

#### 🔸 آپدیت `handle_token_input()`:

**قبل:**
```python
# اعتبارسنجی ساده
if not validate_bot_token(token):
    await message.answer("❌ توکن نامعتبر است!")
    return
```

**بعد:**
```python
# نمایش پیام در حال بررسی
processing_msg = await message.answer("⏳ در حال بررسی توکن...")

try:
    # اعتبارسنجی واقعی با API تلگرام
    bot_info = await validate_bot_token(token)
    
    # ذخیره اطلاعات واقعی ربات
    user_bots.append({
        'type': bot_type,
        'token': token,
        'bot_id': bot_info['id'],              # 🆕
        'bot_username': bot_info['username'],  # 🆕
        'bot_name': bot_info['first_name'],    # 🆕
        'created_at': 'اکنون'
    })
    
    # نمایش اطلاعات واقعی در پیام موفقیت
    success_message = f"""
✅ توکن با موفقیت تایید شد!

نوع ربات: {selected_bot}
🤖 نام ربات: {bot_info['first_name']}        # 🆕
👤 یوزرنیم: @{bot_info['username']}          # 🆕
🆔 شناسه: {bot_info['id']}                    # 🆕
وضعیت: ✅ فعال و آماده استفاده
    """
    
except BotValidationError as e:
    # مدیریت خطای اعتبارسنجی
    await message.answer(f"❌ توکن نامعتبر است!\n\nخطا: {str(e)}")
```

---

#### 🔸 آپدیت `callback_my_bots()`:

**قبل:**
```python
bots_list = "\n\n".join([
    f"🤖 {BOT_TYPES.get(bot['type'], 'ربات')}\n"
    f"⏰ زمان ساخت: {bot.get('created_at', 'نامشخص')}\n"
    f"✅ وضعیت: فعال"
    for bot in user_bots
])
```

**بعد:**
```python
bots_list = "\n\n".join([
    f"🤖 {BOT_TYPES.get(bot['type'], 'ربات')}\n"
    f"📛 نام: {bot.get('bot_name', 'نامشخص')}\n"           # 🆕
    f"👤 یوزرنیم: @{bot.get('bot_username', 'نامشخص')}\n" # 🆕
    f"🆔 شناسه: {bot.get('bot_id', 'نامشخص')}\n"          # 🆕
    f"⏰ زمان ساخت: {bot.get('created_at', 'نامشخص')}\n"
    f"✅ وضعیت: فعال"
    for bot in user_bots
])
```

---

### 4️⃣ آپدیت `requirements.txt`

```diff
aiogram==3.15.0
python-dotenv==1.0.0
+ aiohttp==3.10.11
```

---

## 🔄 جریان کامل اعتبارسنجی

```
کاربر توکن را می‌فرستد
    ↓
handle_token_input() فراخوانی می‌شود
    ↓
نمایش پیام: "⏳ در حال بررسی توکن..."
    ↓
فراخوانی validate_bot_token(token) از services/
    ↓
┌─────────────────────────────────────────┐
│ bot_service.validate_bot_token()        │
│                                         │
│ 1. بررسی فرمت ساده                     │
│    ├─ نامعتبر? → raise BotValidationError
│    └─ معتبر? → ادامه                   │
│                                         │
│ 2. ساخت URL API                        │
│    https://api.telegram.org/bot{token}/getMe
│                                         │
│ 3. ارسال درخواست GET با aiohttp        │
│    ├─ timeout: 10s                     │
│    └─ دریافت JSON                      │
│                                         │
│ 4. بررسی پاسخ                          │
│    ├─ ok: true                         │
│    │   ├─ is_bot: true? ✅             │
│    │   └─ return bot_info              │
│    │                                   │
│    └─ ok: false                        │
│        └─ raise BotValidationError     │
└─────────────────────────────────────────┘
    ↓
برگشت به handle_token_input()
    ↓
try/except:
    ├─ موفق (bot_info دریافت شد)
    │   ├─ ذخیره اطلاعات واقعی در state
    │   ├─ حذف پیام "در حال بررسی"
    │   └─ نمایش پیام موفقیت با اطلاعات ربات
    │
    └─ ناموفق (BotValidationError)
        ├─ حذف پیام "در حال بررسی"
        └─ نمایش پیام خطا + درخواست مجدد
```

---

## 💡 مزایای لایه Service

### 1. تفکیک نگرانی‌ها (Separation of Concerns)
```
handlers/    → UI Logic (تعامل با کاربر)
services/    → Business Logic (منطق کسب‌وکار)
config.py    → Configuration
```

### 2. قابلیت تست (Testability)
```python
# می‌توان به صورت مستقل تست کرد
import pytest
from services import validate_bot_token, BotValidationError

async def test_valid_token():
    result = await validate_bot_token("123:ABC...")
    assert result['is_bot'] == True

async def test_invalid_token():
    with pytest.raises(BotValidationError):
        await validate_bot_token("invalid")
```

### 3. قابلیت استفاده مجدد (Reusability)
```python
# می‌توان از همان تابع در جاهای مختلف استفاده کرد
from services import validate_bot_token

# در handler دیگر
async def another_handler(message: Message):
    bot_info = await validate_bot_token(token)
```

### 4. مدیریت بهتر خطاها
```python
try:
    bot_info = await validate_bot_token(token)
except BotValidationError as e:
    # خطای اعتبارسنجی
    logger.warning(f"Invalid token: {e}")
except Exception as e:
    # خطای غیرمنتظره
    logger.error(f"Unexpected error: {e}")
```

---

## 🎯 داده‌های ذخیره شده

### قبل:
```python
{
    'type': 'shop',
    'token': '123:ABC...',
    'created_at': 'اکنون'
}
```

### بعد:
```python
{
    'type': 'shop',
    'token': '123:ABC...',
    'bot_id': 123456789,              # 🆕 ID واقعی ربات
    'bot_username': 'my_shop_bot',    # 🆕 یوزرنیم واقعی
    'bot_name': 'فروشگاه من',         # 🆕 نام واقعی
    'created_at': 'اکنون'
}
```

---

## 🧪 تست

### 1. تست توکن معتبر:
```
ارسال: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567890

نتیجه:
✅ توکن با موفقیت تایید شد!
🤖 نام ربات: My Bot
👤 یوزرنیم: @my_bot
🆔 شناسه: 123456789
```

### 2. تست توکن نامعتبر:
```
ارسال: 123456789

نتیجه:
❌ توکن نامعتبر است!
خطا: فرمت توکن نامعتبر است. توکن باید شامل ':' باشد.
```

### 3. تست توکن منقضی شده:
```
ارسال: 999999999:InvalidTokenHere12345678901234567890

نتیجه:
❌ توکن نامعتبر است!
خطا: توکن نامعتبر: Unauthorized
```

---

## 📈 مقایسه قبل و بعد

| ویژگی | قبل | بعد |
|-------|-----|-----|
| **اعتبارسنجی** | فرمت ساده | API واقعی تلگرام |
| **اطلاعات ربات** | ❌ ندارد | ✅ نام، یوزرنیم، ID |
| **مدیریت خطا** | یک پیام عمومی | خطاهای دقیق و واضح |
| **لایه‌بندی** | Monolithic | Service Layer |
| **قابلیت تست** | محدود | بالا |
| **UX** | متوسط | عالی (با spinner) |

---

## 🔮 توسعه‌های بعدی

### 1. Cache کردن نتایج
```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def validate_bot_token_cached(token: str):
    return await validate_bot_token(token)
```

### 2. ذخیره در دیتابیس
```python
# به جای state
await db.save_bot(
    user_id=message.from_user.id,
    bot_info=bot_info
)
```

### 3. راه‌اندازی واقعی ربات
```python
async def start_user_bot(token: str, bot_type: str):
    """راه‌اندازی ربات کاربر با توکن دریافتی"""
    bot = Bot(token=token)
    # منطق راه‌اندازی بر اساس bot_type
```

---

## 🎊 نتیجه

✅ لایه Service اضافه شد  
✅ اعتبارسنجی واقعی با API تلگرام  
✅ دریافت اطلاعات واقعی ربات  
✅ مدیریت خطاهای دقیق  
✅ UX بهتر (spinner + اطلاعات کامل)  
✅ کد تمیزتر و ماژولارتر  

---

**پروژه حالا حرفه‌ای‌تر شده است! 🚀**
