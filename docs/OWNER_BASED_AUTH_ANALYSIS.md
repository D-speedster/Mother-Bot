# Owner-Based Authorization Analysis and Design

## تاریخ: 2026-08-22
## وضعیت: طراحی اولیه

---

## 📋 خلاصه اجرایی

این سند طراحی سیستم **Owner-Based Authorization** برای Child Bot Platform است که جایگزین رویکرد نادرست `AI_IMAGE_ADMIN_IDS` می‌شود.

### هدف اصلی
تبدیل AI Image Admin Panel از سیستم Admin ID سراسری به سیستم **Bot Instance Ownership** که در آن:
- هر کاربری که Bot می‌سازد، **Owner** آن Bot است
- فقط Owner می‌تواند Admin Panel مربوط به Bot خودش را ببیند
- Owner یک Bot نمی‌تواند Admin Panel Bot دیگری را ببیند
- دسترسی غیرمجاز **Silent** است (هیچ اطلاعاتی فاش نمی‌شود)

---

## 🔍 تحلیل وضعیت فعلی

### 1. ساختار Database

**جدول: `bots`**
```sql
CREATE TABLE bots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,              -- ✅ فیلد مالکیت موجود است
    bot_telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    bot_type TEXT NOT NULL,
    token_encrypted TEXT NOT NULL,
    status TEXT DEFAULT 'inactive',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**✅ یافته کلیدی:** فیلد `owner_id` از قبل موجود است و در تمام Repository methods استفاده می‌شود.

### 2. Repository Ownership Checks

تمام متدهای Repository از قبل ownership را بررسی می‌کنند:

```python
# مثال‌ها از repository.py:
async def get_bot_by_id(bot_id: int, owner_id: int) -> Optional[Dict]
async def get_bot_token_encrypted(bot_id: int, owner_id: int) -> Optional[str]
async def update_bot_status(bot_id: int, owner_id: int, status: str) -> bool
async def delete_bot(bot_id: int, owner_id: int) -> bool
```

**✅ یافته کلیدی:** لایه Database از قبل ownership-aware است.

### 3. Bot Creation Flow

```python
# از bot_maker.py:
await bot_service.register_bot(
    owner_id=user_id,        # ✅ owner_id ذخیره می‌شود
    token=token,
    bot_type=bot_type
)
```

**✅ یافته کلیدی:** هنگام ساخت Bot، `owner_id` به درستی ذخیره می‌شود.

### 4. Bot Runtime Structure

**مشکل اصلی کشف شده:**

```python
# runner.py - _run_bot_task():
async def _run_bot_task(self, bot_id: int, token: str, bot_type: str) -> None:
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    router = _get_router_for_bot_type(bot_type)
    dp.include_router(router)
    await dp.start_polling(bot)
```

**❌ مشکل:** Child Bot در Runtime نمی‌داند که `bot_id` و `owner_id` خودش چیست.

**Router Handlers** فقط دسترسی به این اطلاعات دارند:
- `message.from_user.id` (شناسه کاربری که پیام ارسال کرده)
- `message.bot` (Bot instance تلگرام)

**نمی‌دانند:**
- این Bot کدام `bot_id` از Database است؟
- `owner_id` این Bot چه کسی است؟

---

## 🎯 راه‌حل طراحی‌شده

### گام 1: Context Storage in Bot Instance

از `bot.set()` برای ذخیره bot context استفاده می‌کنیم:

```python
# runner.py - _run_bot_task():
async def _run_bot_task(self, bot_id: int, token: str, bot_type: str, owner_id: int) -> None:
    bot = Bot(token=token)
    
    # ✅ ذخیره bot context در Bot instance
    bot["bot_context"] = {
        "bot_id": bot_id,
        "owner_id": owner_id,
        "bot_type": bot_type
    }
    
    dp = Dispatcher(storage=MemoryStorage())
    router = _get_router_for_bot_type(bot_type)
    dp.include_router(router)
    await dp.start_polling(bot)
```

### گام 2: Context Access in Handlers

```python
# handlers/child_bots/ai_image_admin.py:
async def cmd_admin(message: Message, state: FSMContext):
    """Handler دستور /admin - نمایش Admin Panel"""
    
    # ✅ دریافت bot context
    bot_context = message.bot.get("bot_context", {})
    bot_owner_id = bot_context.get("owner_id")
    
    # ✅ بررسی ownership
    user_id = message.from_user.id
    if user_id != bot_owner_id:
        # ⚠️ Silent failure - هیچ پاسخی ارسال نمی‌شود
        logger.warning(
            f"Unauthorized admin access: user {user_id} tried to access "
            f"bot owned by {bot_owner_id}"
        )
        return
    
    # ادامه نمایش Admin Panel...
```

### گام 3: Mother Bot Gateway Update

```python
# services/ai_image/mother_bot_gateway.py:
class MotherBotGateway:
    """
    Gateway برای دسترسی Child Bot به اطلاعات Mother Bot
    """
    
    def __init__(self, bot_context: dict):
        """
        Args:
            bot_context: شامل bot_id و owner_id
        """
        self._bot_id = bot_context.get("bot_id")
        self._owner_id = bot_context.get("owner_id")
    
    def get_owner_id(self) -> int:
        """
        دریافت owner_id این Bot
        
        Returns:
            ID صاحب این Bot
        """
        return self._owner_id
    
    def is_owner(self, user_id: int) -> bool:
        """
        بررسی اینکه آیا user_id مالک این Bot است
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            True اگر مالک باشد
        """
        return user_id == self._owner_id
```

### گام 4: Service Initialization with Context

```python
# handlers/child_bots/ai_image_admin.py:
def get_admin_router() -> Router:
    """
    ساخت و برگرداندن Admin Router
    
    ⚠️ Services باید در اولین استفاده با bot_context مقداردهی شوند
    """
    router = Router(name="ai_image_admin")
    
    # Handler registration...
    
    return router


async def cmd_admin(message: Message, state: FSMContext):
    """Handler دستور /admin"""
    
    # ✅ دریافت bot context
    bot_context = message.bot.get("bot_context", {})
    
    # ✅ بررسی ownership
    if not is_owner(message.from_user.id, bot_context):
        return  # Silent failure
    
    # ✅ Initialize services با bot_context (اگر لازم باشد)
    # admin_service, config_service, etc. می‌توانند bot_context دریافت کنند
    
    await state.clear()
    # نمایش Admin Panel...
```

---

## 📝 تغییرات مورد نیاز

### فایل‌های Modified

#### 1. `services/runner.py`

**تغییرات:**
- اضافه کردن `owner_id` به signature متد `_run_bot_task()`
- ذخیره bot context در Bot instance با `bot.set()`
- Pass کردن `owner_id` به `start_bot()` و `start_bot_system()`

**خطوط تغییر:**
- خط ~144: signature متد `_run_bot_task`
- خط ~160: اضافه کردن `bot["bot_context"] = {...}`
- خط ~109: Pass کردن owner_id از bot_info

#### 2. `handlers/child_bots/ai_image_admin.py`

**تغییرات:**
- **حذف کامل `get_admin_ids()` و `is_admin()` functions**
- اضافه کردن `is_owner()` function
- تغییر `check_admin_access()` به `check_owner_access()`
- دریافت bot_context در همه handlers
- بررسی ownership به جای admin IDs

**خطوط حذف:**
- خط 44-67: `get_admin_ids()` و `is_admin()` functions
- خط 191-221: `check_admin_access()` function

**خطوط اضافه/تغییر:**
- تابع جدید `is_owner(user_id, bot_context)` 
- تابع جدید `check_owner_access(message_or_callback)`
- تمام handlers: اضافه کردن دریافت bot_context

#### 3. `services/ai_image/mother_bot_gateway.py`

**تغییرات:**
- اضافه کردن `__init__(bot_context)`
- اضافه کردن `get_owner_id()`
- اضافه کردن `is_owner(user_id)`
- حذف Mock implementation برای ownership methods

**خطوط اضافه:**
- Constructor با bot_context
- متدهای ownership

#### 4. `.env.example` و `.env`

**تغییرات:**
- **حذف کامل `AI_IMAGE_ADMIN_IDS`**
- اضافه کردن کامنت توضیحی درباره owner-based auth

#### 5. `test_admin_security_fix.py`

**تغییرات:**
- بازنویسی کامل
- تست ownership به جای admin IDs
- تست scenarios:
  - Owner access → Success
  - Non-owner access → Silent
  - Multiple bots → Isolation

---

## 🔒 Security Considerations

### 1. Silent Failure
- کاربر غیرمجاز نباید بفهمد Admin Panel وجود دارد
- `/admin` برای non-owner: هیچ پاسخی ارسال نمی‌شود
- Callback handlers برای non-owner: فقط dismiss می‌شوند

### 2. Information Disclosure Prevention
- هیچ اطلاعاتی درباره owner در پیام خطا فاش نمی‌شود
- لاگ‌ها فقط برای debugging داخلی هستند
- کاربر فقط می‌بیند که "چیزی اتفاق نیفتاد"

### 3. Context Security
- `bot_context` فقط در Bot instance ذخیره می‌شود (ایزوله)
- هر Bot instance جدا از بقیه است
- هیچ global state یا shared memory نیست

### 4. Owner Verification
- Owner check در **هر handler** انجام می‌شود
- نه فقط `/admin` command
- تمام callback handlers
- تمام FSM message handlers

---

## 🧪 Test Scenarios

### Scenario 1: Owner Access (Positive)
```
User 79049016 → ساخت AI Image Bot #17
User 79049016 → /admin در Bot #17
→ ✅ Admin Panel نمایش داده می‌شود
```

### Scenario 2: Non-Owner Access (Negative)
```
User 79049016 → ساخت AI Image Bot #17
User 12345678 → /admin در Bot #17
→ ⚠️ هیچ پاسخی ارسال نمی‌شود (Silent)
→ Log: "Unauthorized access attempt"
```

### Scenario 3: Multiple Bots Isolation
```
User A → ساخت Bot #17
User B → ساخت Bot #18

User A → /admin در Bot #17 → ✅ Admin Panel Bot #17
User B → /admin در Bot #17 → ⚠️ Silent (نه Owner)

User A → /admin در Bot #18 → ⚠️ Silent (نه Owner)
User B → /admin در Bot #18 → ✅ Admin Panel Bot #18
```

### Scenario 4: Callback Handlers
```
User A (Owner) → /admin در Bot خودش → ✅ Panel
User A → Click "📊 مدیریت" → ✅ Works
User A → Click "admin:mgmt:users" → ✅ Stats نمایش داده می‌شود

User B (Non-Owner) → Somehow trigger callback → ⚠️ Silent dismiss
```

### Scenario 5: FSM Handlers
```
User A (Owner) → شروع Broadcast FSM → ✅ Works
User A → ارسال پیام Broadcast → ✅ Processed

User B (Non-Owner) → تلاش برای ارسال در FSM → ⚠️ Ignored
```

---

## 📊 Implementation Checklist

### Phase 1: Core Changes
- [ ] تغییر `runner.py` برای Pass کردن bot_context
- [ ] اضافه کردن bot_context storage در Bot instance
- [ ] تست manual: آیا bot_context در handlers قابل دسترسی است؟

### Phase 2: Authorization Rewrite
- [ ] حذف `get_admin_ids()` و `is_admin()`
- [ ] اضافه کردن `is_owner()` و `get_bot_context()`
- [ ] بازنویسی `check_admin_access()` → `check_owner_access()`

### Phase 3: Handler Updates
- [ ] به‌روزرسانی `cmd_admin`
- [ ] به‌روزرسانی همه Reply Keyboard handlers
- [ ] به‌روزرسانی همه Callback handlers
- [ ] به‌روزرسانی همه FSM message handlers

### Phase 4: Service Integration
- [ ] به‌روزرسانی `MotherBotGateway`
- [ ] اگر لازم باشد، pass کردن bot_context به services

### Phase 5: Cleanup
- [ ] حذف `AI_IMAGE_ADMIN_IDS` از `.env.example`
- [ ] حذف `AI_IMAGE_ADMIN_IDS` از `.env`
- [ ] حذف reference‌های قدیمی در documentation

### Phase 6: Testing
- [ ] بازنویسی `test_admin_security_fix.py`
- [ ] اضافه کردن integration test
- [ ] تست با 2 user و 2 bot مختلف
- [ ] تست callback isolation
- [ ] تست FSM isolation

### Phase 7: Regression
- [ ] تست User Flow عادی AI Image Bot
- [ ] تست Movie Bot (نباید تغییر کرده باشد)
- [ ] تست Downloader Bot (نباید تغییر کرده باشد)
- [ ] تست Bot Creation Flow

---

## 🚀 Migration Path

### استراتژی بدون Downtime

1. **تغییرات بدون Breaking:**
   - فیلد `owner_id` از قبل موجود است
   - Repository methods از قبل ownership-aware هستند
   - فقط لایه Authorization تغییر می‌کند

2. **Backward Compatibility:**
   - اگر `bot_context` موجود نباشد، silent failure
   - log warning اما crash نمی‌کند

3. **Rollback Plan:**
   - اگر مشکلی پیش آمد، می‌توان به `AI_IMAGE_ADMIN_IDS` برگشت
   - فقط handler files را revert کنیم

---

## 🔮 Future Enhancements

### Permission Levels (فاز آینده)
```python
# جدول جدید: bot_permissions
CREATE TABLE bot_permissions (
    bot_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,  -- 'owner', 'admin', 'moderator'
    granted_at TEXT NOT NULL,
    granted_by INTEGER,
    PRIMARY KEY (bot_id, user_id)
);
```

### Multi-Owner Support (فاز آینده)
- Owner می‌تواند Admin اضافه کند
- Admin محدودتر از Owner (نمی‌تواند Bot را حذف کند)

### Audit Log (فاز آینده)
- لاگ تمام Admin actions
- چه کسی چه کاری انجام داده

---

## ❓ Q&A

### Q1: آیا باید Database Schema تغییر کند؟
**A:** خیر. فیلد `owner_id` از قبل موجود است.

### Q2: آیا Mother Bot تغییر می‌کند؟
**A:** خیر. فقط `runner.py` یک خط کد اضافه می‌شود برای Pass کردن owner_id.

### Q3: آیا Movie Bot تحت تأثیر قرار می‌گیرد؟
**A:** خیر. این تغییرات فقط AI Image Admin Panel است.

### Q4: Performance Impact چقدر است?
**A:** صفر. فقط یک dict lookup در memory (bot_context).

### Q5: چطور می‌توانیم Owner را تغییر دهیم؟
**A:** فعلاً امکانش نیست. در آینده با جدول `bot_permissions` اضافه می‌شود.

---

## 📚 References

- [Aiogram Bot Storage](https://docs.aiogram.dev/en/latest/dispatcher/storage.html)
- Database Schema: `database/db.py`
- Repository Implementation: `database/repository.py`
- Bot Runner: `services/runner.py`
- Admin Handler: `handlers/child_bots/ai_image_admin.py`

---

## ✅ Approval Required

قبل از شروع Implementation، این موارد را تأیید کنید:

1. ✅ طراحی bot_context storage مناسب است؟
2. ✅ Silent failure approach امنیت کافی دارد؟
3. ✅ تغییرات minimal هستند؟
4. ✅ Rollback plan واضح است؟
5. ✅ Test scenarios کامل هستند؟

**اگر تأیید شد، implementation آغاز می‌شود.**
