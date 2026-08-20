# راهنمای راه‌اندازی پایگاه داده و رمزنگاری

## 📋 مقدمه

این سند راهنمای کامل راه‌اندازی پایگاه داده SQLite و سیستم رمزنگاری توکن‌ها را شرح می‌دهد.

## 🔧 پیش‌نیازها

### نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

وابستگی‌های اضافه‌شده:
- `aiosqlite==0.20.0` - کتابخانه آسنکرون SQLite
- `cryptography==42.0.5` - کتابخانه رمزنگاری Fernet

## 🔑 مرحله ۱: تولید کلید رمزنگاری

برای امنیت توکن‌های ربات‌ها، باید یک کلید رمزنگاری Fernet تولید کنید:

### روش ۱: استفاده از اسکریپت

```bash
python generate_key.py
```

خروجی:
```
============================================================
🔑 کلید رمزنگاری Fernet جدید:
============================================================
kQw7hJ_9XvL2nR4tYpM8bZ1cV5xS6uA3dG0fH4iK7jN=
============================================================
```

### روش ۲: تولید دستی

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## ⚙️ مرحله ۲: تنظیم متغیرهای محیطی

فایل `.env` خود را ویرایش کنید:

```env
# توکن ربات اصلی (Mother Bot)
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# کلید رمزنگاری (از مرحله ۱)
FERNET_KEY=kQw7hJ_9XvL2nR4tYpM8bZ1cV5xS6uA3dG0fH4iK7jN=

# مسیر پایگاه داده (اختیاری)
DATABASE_PATH=mother_bot.db
```

### ⚠️ هشدارهای امنیتی

1. **هرگز** کلید `FERNET_KEY` را به Git commit نکنید
2. کلید را در جای امنی backup کنید
3. اگر کلید را گم کنید، توکن‌های رمزشده قابل بازیابی نیستند
4. در محیط Production از Key Management Service استفاده کنید

## 🗄️ مرحله ۳: معماری پایگاه داده

### ساختار جدول `bots`

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `id` | INTEGER PK | شناسه یکتا در دیتابیس |
| `owner_id` | INTEGER NOT NULL | ID کاربر تلگرام (صاحب ربات) |
| `bot_telegram_id` | INTEGER UNIQUE NOT NULL | ID تلگرام ربات |
| `username` | TEXT | نام کاربری ربات (@bot_name) |
| `first_name` | TEXT | نام نمایشی ربات |
| `bot_type` | TEXT NOT NULL | نوع ربات (shop, downloader, ...) |
| `token_encrypted` | TEXT NOT NULL | توکن رمزشده |
| `status` | TEXT NOT NULL | وضعیت (active/inactive) |
| `created_at` | DATETIME NOT NULL | زمان ایجاد |
| `updated_at` | DATETIME NOT NULL | زمان به‌روزرسانی |

### Indexes برای بهبود عملکرد

```sql
CREATE INDEX idx_bots_owner_id ON bots(owner_id);
CREATE INDEX idx_bots_status ON bots(status);
```

### PRAGMA Settings

```sql
PRAGMA journal_mode = WAL;  -- Write-Ahead Logging
PRAGMA foreign_keys = ON;   -- یکپارچگی داده
```

## 🏗️ معماری لایه‌بندی

```
┌─────────────────────────────────────────┐
│           Handler Layer                 │
│     (handlers/bot_maker.py)             │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Service Layer                   │
│    (services/bot_service.py)            │
│  - اعتبارسنجی توکن                      │
│  - رمزنگاری/رمزگشایی                    │
│  - منطق کسب‌وکار                        │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│       Repository Layer                  │
│   (database/repository.py)              │
│  - CRUD operations                      │
│  - مدیریت Race Condition                │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│        Database Layer                   │
│      (database/db.py)                   │
│  - مدیریت اتصال                         │
│  - Schema management                    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
            ┌──────────┐
            │  SQLite  │
            └──────────┘
```

## 🔐 جریان ثبت ربات جدید

```
1. کاربر توکن را ارسال می‌کند
         ↓
2. Handler → BotService.register_bot()
         ↓
3. اعتبارسنجی با Telegram API (getMe)
         ↓
4. بررسی عدم تکراری بودن
         ↓
5. رمزنگاری توکن با Fernet
         ↓
6. ذخیره در Repository
         ↓
7. Commit به SQLite
         ↓
8. بازگشت نتیجه به کاربر
```

## 🛡️ مدیریت Race Condition

برای جلوگیری از ثبت مجدد یک ربات توسط چند کاربر همزمان:

```python
try:
    await repository.create_bot(...)
except aiosqlite.IntegrityError:
    # UNIQUE constraint failed on bot_telegram_id
    raise TokenAlreadyRegisteredError(...)
```

SQLite با UNIQUE constraint روی `bot_telegram_id` از ثبت تکراری جلوگیری می‌کند.

## 📊 استفاده از API

### ثبت ربات جدید

```python
from services import BotService, TokenEncryptionService
from database import Database, BotRepository

# راه‌اندازی
db = Database("mother_bot.db")
await db.connect()

encryption = TokenEncryptionService()
repository = BotRepository(db.connection)
bot_service = BotService(repository, encryption)

# ثبت ربات
result = await bot_service.register_bot(
    owner_id=123456789,
    token="1234567890:ABCdefGHI...",
    bot_type="shop"
)

# خروجی:
# {
#     'bot_id': 1,
#     'telegram_id': 987654321,
#     'username': 'my_shop_bot',
#     'first_name': 'My Shop Bot',
#     'bot_type': 'shop'
# }
```

### دریافت لیست ربات‌های کاربر

```python
bots = await bot_service.get_user_bots(owner_id=123456789)

# خروجی:
# [
#     {
#         'bot_id': 1,
#         'telegram_id': 987654321,
#         'username': 'my_shop_bot',
#         'first_name': 'My Shop Bot',
#         'bot_type': 'shop',
#         'status': 'active',
#         'created_at': '2024-01-15T10:30:00'
#     },
#     ...
# ]
```

### دریافت توکن رمزگشایی‌شده

```python
token = await bot_service.get_bot_token(bot_telegram_id=987654321)
# توکن خام برای استفاده: "1234567890:ABCdefGHI..."
```

## 🧪 تست سیستم

### تست رمزنگاری

```python
from services import TokenEncryptionService

encryption = TokenEncryptionService()

# رمزنگاری
token = "1234567890:ABCdefGHI..."
encrypted = encryption.encrypt(token)
print(f"Encrypted: {encrypted}")

# رمزگشایی
decrypted = encryption.decrypt(encrypted)
assert decrypted == token
print("✅ Test passed!")
```

### تست پایگاه داده

```python
from database import Database, BotRepository

async def test_database():
    db = Database("test.db")
    await db.connect()
    
    repo = BotRepository(db.connection)
    
    # ثبت ربات
    bot_id = await repo.create_bot(
        owner_id=123,
        bot_telegram_id=456,
        username="test_bot",
        first_name="Test Bot",
        bot_type="shop",
        token_encrypted="encrypted_token_here"
    )
    
    # جستجو
    bot = await repo.get_bot_by_telegram_id(456)
    assert bot['username'] == "test_bot"
    
    print("✅ Database test passed!")
    
    await db.disconnect()
```

## 🔄 Migration در آینده

برای تغییرات Schema در آینده:

1. فایل migration جدید در `database/migrations/` بسازید
2. نسخه Schema را در `Database` ردیابی کنید
3. در هر اتصال، migration‌های pending را اجرا کنید

## 📝 Checklist راه‌اندازی

- [ ] نصب وابستگی‌ها (`pip install -r requirements.txt`)
- [ ] تولید کلید رمزنگاری (`python generate_key.py`)
- [ ] تنظیم `.env` (BOT_TOKEN + FERNET_KEY)
- [ ] اجرای ربات (`python bot.py`)
- [ ] تست ثبت ربات جدید از طریق تلگرام
- [ ] بررسی لاگ‌ها برای اطمینان از اتصال به دیتابیس
- [ ] تست Race Condition (ارسال همزمان یک توکن)

## 🆘 عیب‌یابی

### خطا: FERNET_KEY not found

```bash
ValueError: 🔴 خطا: کلید رمزنگاری (FERNET_KEY) یافت نشد!
```

**حل:** کلید را در `.env` تنظیم کنید (مرحله ۲)

### خطا: Invalid Fernet key

```bash
ValueError: کلید رمزنگاری نامعتبر است
```

**حل:** کلید باید base64 معتبر باشد. از `generate_key.py` استفاده کنید

### خطا: TokenAlreadyRegisteredError

```bash
TokenAlreadyRegisteredError: این ربات قبلاً ثبت شده است
```

**عادی است!** یک ربات فقط یک بار قابل ثبت است.

### خطا: Database locked

```bash
sqlite3.OperationalError: database is locked
```

**حل:** از WAL mode استفاده می‌شود. اطمینان حاصل کنید فقط یک instance از ربات اجرا است.

## 📚 منابع بیشتر

- [SQLite WAL Mode](https://www.sqlite.org/wal.html)
- [Fernet Documentation](https://cryptography.io/en/latest/fernet/)
- [aiosqlite Documentation](https://aiosqlite.omnilib.dev/)

---

**تاریخ آخرین به‌روزرسانی:** 2024
**نسخه:** 1.0.0
