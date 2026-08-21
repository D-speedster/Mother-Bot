# اصلاحات Dependency Injection در BotRunner

## تاریخ: August 21, 2026
## وضعیت: ✅ اعمال شده و تست شده

---

## خلاصه تغییرات

این اصلاحات برای بهبود معماری و رعایت اصول SOLID (به‌ویژه Dependency Injection) انجام شده است.

---

## تغییر ۱: Injection کردن `encryption_service` به `BotRunner`

### مشکل قبلی:
در متد `start_bot_system()`, سرویس encryption به صورت local import و instantiate می‌شد:
```python
from services.encryption import TokenEncryptionService
encryption_service = TokenEncryptionService()
token = encryption_service.decrypt(token_encrypted)
```

این رویکرد مشکلاتی دارد:
- ❌ نقض اصل Dependency Injection
- ❌ مشکل در تست‌نویسی (نمی‌توان mock کرد)
- ❌ ایجاد instance جدید در هر call

### راه‌حل:
Injection کردن `encryption_service` به constructor:

#### فایل: `services/runner.py`

**Import اضافه شده:**
```python
from services.encryption import TokenEncryptionService
```

**تغییر در `__init__`:**
```python
def __init__(self, bot_service: BotService, encryption_service: TokenEncryptionService):
    """
    Args:
        bot_service: BotService instance برای دریافت اطلاعات ربات‌ها
        encryption_service: TokenEncryptionService instance برای دیکریپت کردن توکن‌ها
    """
    self._bot_service = bot_service
    self._encryption = encryption_service
    self._tasks: Dict[int, asyncio.Task] = {}
```

**تغییر در `start_bot_system()`:**
```python
# قبل:
from services.encryption import TokenEncryptionService
encryption_service = TokenEncryptionService()
token = encryption_service.decrypt(token_encrypted)

# بعد:
token = self._encryption.decrypt(token_encrypted)
```

### مزایا:
- ✅ رعایت اصل Dependency Injection
- ✅ قابل تست با mock
- ✅ استفاده از singleton instance
- ✅ کد تمیزتر و maintainable

---

## تغییر ۲: اضافه کردن `get_all_active_bots()` به Repository

### وضعیت:
✅ این متد **قبلاً در repository موجود بود** و نیازی به تغییر نداشت.

#### فایل: `database/repository.py`

متد موجود:
```python
async def get_all_active_bots(self) -> List[Dict[str, Any]]:
    """
    دریافت تمام ربات‌های فعال (status='active') برای استارت‌آپ سیستم
    
    Returns:
        لیست Dict‌های حاوی:
        - id, owner_id, bot_type, token_encrypted, username, first_name
    
    Security:
    - ⚠️ این متد token_encrypted برمی‌گرداند
    - فقط برای استفاده داخلی در startup
    """
    cursor = await self._conn.execute(
        """
        SELECT 
            id, owner_id, bot_type, token_encrypted, username, first_name
        FROM bots
        WHERE status = 'active'
        ORDER BY created_at ASC
        """
    )
    
    rows = await cursor.fetchall()
    
    return [
        {
            'id': row[0],
            'owner_id': row[1],
            'bot_type': row[2],
            'token_encrypted': row[3],
            'username': row[4],
            'first_name': row[5]
        }
        for row in rows
    ]
```

---

## تغییر ۳: اصلاح Instantiation در `bot.py`

### فایل: `bot.py`

**قبل:**
```python
encryption_service = TokenEncryptionService()
repository = BotRepository(database.connection)
bot_service = BotService(repository, encryption_service)
wallet_service = WalletService(database.connection)
bot_runner = BotRunner(bot_service)
```

**بعد:**
```python
encryption_service = TokenEncryptionService()
repository = BotRepository(database.connection)
bot_service = BotService(repository, encryption_service)
wallet_service = WalletService(database.connection)
bot_runner = BotRunner(
    bot_service=bot_service,
    encryption_service=encryption_service
)
```

### تغییرات:
- ✅ پاس دادن `encryption_service` به `BotRunner`
- ✅ استفاده از named arguments برای وضوح بیشتر

---

## تست‌های انجام شده

### ✅ Syntax Check:
```bash
python -m py_compile bot.py
python -m py_compile services\runner.py
python -m py_compile database\repository.py
```

همه فایل‌ها بدون خطا کامپایل شدند.

### ⏳ تست‌های عملکردی (در انتظار):
1. راه‌اندازی ربات مادر
2. ساخت ربات فرزند
3. ری‌استارت ربات مادر
4. بررسی راه‌اندازی خودکار ربات‌های فعال

---

## فایل‌های تغییر یافته

1. **`services/runner.py`**:
   - اضافه شدن import `TokenEncryptionService`
   - تغییر `__init__` برای دریافت `encryption_service`
   - حذف local import/instantiation در `start_bot_system()`

2. **`bot.py`**:
   - پاس دادن `encryption_service` به `BotRunner` constructor

3. **`database/repository.py`**:
   - بدون تغییر (متد `get_all_active_bots` قبلاً موجود بود)

---

## معماری نهایی

```
main (bot.py)
    ↓
    ├─ TokenEncryptionService (singleton)
    ├─ Database
    ├─ BotRepository (database.connection)
    ├─ BotService (repository, encryption_service)
    ├─ WalletService (database.connection)
    └─ BotRunner (bot_service, encryption_service) ← تزریق شد
```

### جریان Dependency Injection:
1. `TokenEncryptionService` ساخته می‌شود (singleton)
2. به `BotService` تزریق می‌شود
3. به `BotRunner` تزریق می‌شود
4. `BotRunner` از instance مشترک استفاده می‌کند

---

## مزایای معماری جدید

### 1. **Single Responsibility**
هر کلاس فقط یک مسئولیت دارد:
- `TokenEncryptionService`: فقط encryption/decryption
- `BotRunner`: فقط مدیریت lifecycle ربات‌ها
- `BotRepository`: فقط database operations

### 2. **Testability**
می‌توان `encryption_service` را mock کرد:
```python
mock_encryption = Mock(TokenEncryptionService)
mock_encryption.decrypt.return_value = "fake_token"
bot_runner = BotRunner(bot_service, mock_encryption)
```

### 3. **Maintainability**
- کد واضح‌تر و خواناتر
- dependencies صریح هستند (در constructor)
- تغییرات آینده آسان‌تر

### 4. **Performance**
- استفاده از instance مشترک (به جای ساخت instance جدید در هر call)
- کاهش overhead

---

## نکات امنیتی

### ⚠️ Token Security:
- توکن‌های decrypt‌شده هیچ‌جا log نمی‌شوند
- `token_encrypted` فقط در `get_all_active_bots()` برگردانده می‌شود
- دیکریپت فقط در `BotRunner` انجام می‌شود
- توکن‌ها به handler‌ها pass نمی‌شوند

### ⚠️ Ownership Security:
- متد `get_all_active_bots()` فقط در startup استفاده می‌شود
- handler‌ها باید از متدهای دارای ownership check استفاده کنند
- هیچ endpoint عمومی نباید `token_encrypted` برگرداند

---

## نتیجه‌گیری

✅ **تغییرات با موفقیت اعمال شدند**
✅ **کد syntax صحیح است**
✅ **معماری بهبود یافته است**
⏳ **منتظر تست عملکردی**

این اصلاحات باعث می‌شوند که:
- کد maintainable‌تر باشد
- تست‌نویسی آسان‌تر شود
- معماری تمیزتر و واضح‌تر باشد
- performance بهتر شود (singleton instance)
