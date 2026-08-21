# 🔐 سیستم مدیریت ادمین

## خلاصه
سیستم مدیریت ادمین امکان افزودن و حذف مدیران، مشاهده آمار کلی سیستم و بررسی فیش‌های در انتظار را فراهم می‌کند.

## ساختار

### 1. جدول پایگاه داده (`admins`)
```sql
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY,      -- شناسه کاربر تلگرام
    added_by INTEGER NOT NULL,        -- شناسه کسی که این ادمین را اضافه کرده
    created_at TEXT NOT NULL          -- تاریخ افزودن
);
```

### 2. سرویس مدیریت (`services/admin_service.py`)

#### کلاس `AdminService`
```python
class AdminService:
    def __init__(self, connection: aiosqlite.Connection, admin_user_id: int)
```

**متدها:**

- `async is_admin(user_id: int) -> bool`
  - بررسی اینکه آیا کاربر ادمین است یا خیر

- `async get_stats() -> Dict[str, int]`
  - دریافت آمار کلی سیستم
  - برمی‌گرداند:
    - `total_users`: تعداد کل کاربران
    - `total_bots`: تعداد کل ربات‌ها
    - `active_bots`: تعداد ربات‌های فعال
    - `total_revenue`: مجموع درآمد (تراکنش‌های debit)
    - `pending_receipts`: تعداد فیش‌های در انتظار

- `async get_all_admins() -> List[Dict]`
  - لیست تمام ادمین‌ها را برمی‌گرداند

- `async add_admin(user_id: int, added_by: int) -> bool`
  - افزودن ادمین جدید
  - برمی‌گرداند: `True` در صورت موفقیت، `False` اگر قبلاً وجود داشت

- `async remove_admin(user_id: int) -> bool`
  - حذف ادمین
  - ⚠️ ادمین اصلی (`ADMIN_USER_ID` از config) قابل حذف نیست
  - برمی‌گرداند: `True` در صورت موفقیت، `False` اگر ادمین اصلی بود

- `async ensure_main_admin_exists() -> None`
  - تضمین وجود ادمین اصلی در جدول
  - در `startup` ربات صدا زده می‌شود

### 3. Handler پنل ادمین (`handlers/admin.py`)

#### FSM States
```python
class AdminStates(StatesGroup):
    waiting_for_new_admin_id = State()
    waiting_for_remove_admin_id = State()
```

#### Keyboards
- `get_admin_keyboard()`: کیبورد اصلی پنل ادمین
- `get_admin_management_keyboard()`: کیبورد مدیریت ادمین‌ها
- `get_main_keyboard()`: کیبورد منوی اصلی

#### Handlers

| دستور/دکمه | عملکرد |
|-----------|--------|
| `/admin` یا `⚙️ پنل ادمین` | ورود به پنل مدیریت |
| `📊 آمار کلی` | نمایش آمار سیستم |
| `👥 مدیریت ادمین‌ها` | ورود به بخش مدیریت ادمین‌ها |
| `📋 لیست ادمین‌ها` | نمایش لیست تمام ادمین‌ها |
| `➕ افزودن ادمین` | افزودن ادمین جدید (با FSM) |
| `➖ حذف ادمین` | حذف ادمین (با FSM) |
| `📋 فیش‌های در انتظار` | هدایت به پنل بررسی فیش‌ها |
| `🔙 بازگشت به پنل ادمین` | بازگشت به کیبورد اصلی ادمین |
| `🔙 بازگشت به منوی اصلی` | بازگشت به منوی کاربر عادی |

### 4. تنظیمات (`config.py`)

```python
# آیدی ادمین اصلی سیستم (غیرقابل حذف)
ADMIN_USER_ID = 79049016

# لیست آیدی ادمین‌های اصلی (برای سازگاری با کدهای قبلی)
ADMIN_USER_IDS = [ADMIN_USER_ID]
```

## نحوه استفاده

### 1. دسترسی به پنل ادمین
- دستور `/admin` یا دکمه `⚙️ پنل ادمین` (فقط برای ادمین‌ها نمایش داده می‌شود)

### 2. مشاهده آمار
```
📊 آمار سیستم

👥 کاربران: 150
🤖 کل ربات‌ها: 45
✅ ربات‌های فعال: 38
💰 درآمد کل: 2,500,000 تومان
⏳ فیش‌های در انتظار: 3
```

### 3. افزودن ادمین جدید
1. کلیک روی `➕ افزودن ادمین`
2. ارسال User ID کاربر (مثل: `123456789`)
3. سیستم ادمین را اضافه می‌کند

### 4. حذف ادمین
1. کلیک روی `➖ حذف ادمین`
2. ارسال User ID ادمین مورد نظر
3. سیستم ادمین را حذف می‌کند (مگر ادمین اصلی)

## ویژگی‌های امنیتی

### 1. فیلتر دسترسی
تمام handler‌ها این چک را دارند:
```python
is_admin = await admin_service.is_admin(message.from_user.id)
if not is_admin:
    return  # بدون پیام، فقط ignore
```

### 2. محافظت از ادمین اصلی
```python
if user_id == self._admin_user_id:
    logger.warning(f"⚠️ تلاش برای حذف ادمین اصلی: {user_id}")
    return False
```

### 3. نمایش شرطی دکمه پنل ادمین
دکمه `⚙️ پنل ادمین` فقط برای کاربرانی که ادمین هستند در منوی اصلی نمایش داده می‌شود:

```python
async def get_main_keyboard(admin_service=None, user_id: int = None):
    keyboard = [...]
    
    if admin_service and user_id:
        is_admin = await admin_service.is_admin(user_id)
        if is_admin:
            keyboard.append([KeyboardButton(text="⚙️ پنل ادمین")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
```

## یکپارچگی با Bot

### راه‌اندازی در `bot.py`:

```python
from config import ADMIN_USER_ID
from services.admin_service import AdminService
from handlers import admin_router

# ساخت سرویس
admin_service = AdminService(database.connection, ADMIN_USER_ID)

# اضافه به middleware
dp.workflow_data.update({
    'admin_service': admin_service,
    ...
})

# ثبت router
dp.include_router(admin_router)

# تضمین ادمین اصلی در startup
@dp.startup()
async def on_startup():
    await admin_service.ensure_main_admin_exists()
```

## نکات مهم

1. **فقط ReplyKeyboard**: این پنل هیچ Inline Keyboard ندارد
2. **Silent Ignore**: اگر کاربر ادمین نباشد، بدون پیام خطا ignore می‌شود
3. **FSM برای Input**: برای دریافت User ID از FSM استفاده شده
4. **ادمین اصلی غیرقابل حذف**: `ADMIN_USER_ID` هرگز قابل حذف نیست
5. **Auto-initialization**: ادمین اصلی در startup به صورت خودکار ثبت می‌شود

## مثال استفاده در کد

```python
# در handler
@router.message(F.text == "...")
async def some_handler(message: Message, admin_service):
    # چک ادمین بودن
    if not await admin_service.is_admin(message.from_user.id):
        return
    
    # ادامه لاجیک برای ادمین...
```

## لاگ‌ها

```
✅ ادمین اصلی تضمین شد: 79049016
✅ ادمین جدید اضافه شد: 123456789 توسط 79049016
⚠️ تلاش برای حذف ادمین اصلی: 79049016
✅ ادمین حذف شد: 123456789
```

## فایل‌های مرتبط

- `database/db.py` - اضافه شدن جدول `admins`
- `services/admin_service.py` - لاجیک اصلی
- `handlers/admin.py` - UI و handlers
- `config.py` - تنظیم `ADMIN_USER_ID`
- `bot.py` - یکپارچگی و startup

---

✅ سیستم مدیریت ادمین به صورت کامل پیاده‌سازی شده و آماده استفاده است.
