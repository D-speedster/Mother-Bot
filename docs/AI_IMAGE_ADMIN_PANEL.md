# AI Image Bot - Admin Panel

## نمای کلی

این Admin Panel مستقل برای AI Image Bot ساخته شده و کاملاً جدا از Mother Bot است.

## ویژگی‌ها

### 📊 مدیریت
- **آمار کاربران**: تعداد کل، فعال امروز، کاربران جدید
- **کاربران فعال**: لیست کاربران فعال ۷ روز اخیر
- **آمار Generation**: کل، موفق، ناموفق، امروز، این هفته، این ماه
- **درآمد / مصرف**: اعتبار مصرف‌شده، میانگین هزینه، درآمد

### 📢 ارتباط
- **ارسال همگانی**: ارسال پیام به همه کاربران یا کاربران فعال
- **پیام‌های آفلاین**: مشاهده پیام‌های دریافتی در زمان Maintenance
- **Sponsor**: فعال/غیرفعال، تنظیم متن و لینک
- **تبلیغات**: فعال/غیرفعال، تنظیم متن، لینک و فرکانس نمایش

### 🧠 AI
- **Provider / API**: مشاهده وضعیت Provider و API
- **Model**: مشاهده Model فعال
- **Default Settings**: سبک، نسبت، کیفیت و تعداد پیش‌فرض
- **Prompt Settings**: System Prompt, Prefix, Suffix, Negative Prompt
- **Style Settings**: مدیریت Styleها (فعال/غیرفعال، نام، توضیحات، Modifier)
- **Generation Limits**: محدودیت روزانه، Rate Limit، Cooldown

### 📚 محتوا
- **راهنمای ربات**: مشاهده و ویرایش راهنمای کامل
- **FAQ**: CRUD کامل (Create, Read, Update, Delete)
- **پیام‌های سیستم**: تنظیم پیام‌های سیستم (خوش‌آمدگویی، خطا، محدودیت، etc.)

### ⚙️ سیستم
- **وضعیت Server**: Status, Uptime, CPU, RAM, Python Version
- **صف انتظار**: Pending, Processing, Completed, Failed
- **آمار خطا**: تعداد خطاها، خطاهای Generation، خطاهای Provider
- **Maintenance Mode**: فعال/غیرفعال با Confirmation

## معماری

```
handlers/child_bots/
├── ai_image.py                 # User Handler (موجود)
└── ai_image_admin.py           # Admin Handler (جدید)

keyboards/
├── ai_image_keyboards.py       # User Keyboards (موجود)
└── ai_image_admin_keyboards.py # Admin Keyboards (جدید)

services/ai_image/
├── generation_service.py       # Generation Logic (موجود)
├── models.py                   # Data Models (موجود)
├── mock_provider.py            # Mock Provider (موجود)
├── admin_service.py            # Admin Operations (جدید)
├── config_service.py           # Configuration Management (جدید)
├── content_service.py          # Content Management (جدید)
├── broadcast_service.py        # Broadcast & Ads (جدید)
└── mother_bot_gateway.py       # Mother Bot Connection (جدید)
```

## Admin Authorization

### تنظیم Admin IDs

در فایل `.env` متغیر زیر را اضافه کنید:

```env
AI_IMAGE_ADMIN_IDS=123456789,987654321
```

- چند Admin ID می‌توانید با کاما جدا کنید
- فقط این User IDها به Admin Panel دسترسی دارند
- کاربران غیرمجاز هیچ اطلاعاتی دریافت نمی‌کنند

### بررسی دسترسی

```python
from handlers.child_bots.ai_image_admin import is_admin

if is_admin(user_id):
    # Admin است
    pass
```

## استفاده

### فعال‌سازی Admin Panel

Admin Panel از طریق دستور `/admin` قابل دسترسی است:

```
/admin
```

### Navigation

- **Reply Keyboard** برای Navigation اصلی بین بخش‌ها
- **Inline Keyboard** فقط برای Actions داخلی

### مثال Workflow: ارسال همگانی

1. `/admin` → ورود به Admin Panel
2. کلیک روی `📢 ارتباط`
3. کلیک روی `📨 ارسال همگانی`
4. نوشتن پیام
5. انتخاب مخاطبان (همه / فعال)
6. Preview و تأیید
7. ارسال

### مثال Workflow: تغییر Style

1. `/admin` → ورود به Admin Panel
2. کلیک روی `🧠 AI`
3. کلیک روی `🎨 Style Settings`
4. انتخاب Style موردنظر
5. `🔴 غیرفعال کردن` یا ویرایش تنظیمات

## Mother Bot Gateway

### نقش Gateway

`MotherBotGateway` یک Abstraction Layer است که AI Image Bot را به Mother Bot متصل می‌کند.

### فعلاً Mock است

```python
from services.ai_image import get_mother_bot_gateway

gateway = get_mother_bot_gateway(mock_mode=True)

# در آینده:
# gateway = get_mother_bot_gateway(mock_mode=False)
```

### قابلیت‌های آینده

- دریافت اطلاعات کاربر از Mother Bot
- کسر هزینه از Wallet
- گزارش استفاده (Analytics)
- بررسی اشتراک
- دریافت پلن کاربر

## Persistence

### وضعیت فعلی

تمام داده‌ها فعلاً در حافظه (In-Memory) نگهداری می‌شوند:

- Admin Service: Cache آمار
- Config Service: تنظیمات AI و Maintenance
- Content Service: Guide, FAQ, System Messages
- Broadcast Service: Broadcasts, Sponsor, Ads

### Database آینده

در آینده این موارد باید Persistent شوند:

```sql
-- پیشنهادی: جداول زیر به Database اضافه شوند

CREATE TABLE ai_image_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP
);

CREATE TABLE ai_image_faqs (
    id TEXT PRIMARY KEY,
    question TEXT,
    answer TEXT,
    enabled BOOLEAN,
    order_index INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE ai_image_broadcasts (
    id TEXT PRIMARY KEY,
    text TEXT,
    created_by INTEGER,
    status TEXT,
    sent_count INTEGER,
    failed_count INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE ai_image_offline_messages (
    id TEXT PRIMARY KEY,
    user_id INTEGER,
    message_text TEXT,
    handled BOOLEAN,
    created_at TIMESTAMP
);
```

## Security

### Error Handling

- ❌ هیچ Stack Trace به Telegram ارسال نمی‌شود
- ❌ API Keys هرگز نمایش داده نمی‌شوند
- ✅ فقط پیام‌های کاربرپسند نمایش داده می‌شوند
- ✅ تمام Exceptions در Logger ثبت می‌شوند

### Confirmation

عملیات‌های حساس نیاز به تأیید دارند:

- ✅ Broadcast (قبل از ارسال)
- ✅ Maintenance Mode (روشن/خاموش)
- ✅ حذف FAQ

## Integration با Runner

⚠️ **مهم**: Admin Router باید به AI Image Bot اضافه شود.

در `services/runner.py` یا هر جایی که Bot Runtime مدیریت می‌شود:

```python
from handlers.child_bots.ai_image import get_router
from handlers.child_bots.ai_image_admin import get_admin_router

# ساخت Bot
bot = Bot(token=bot_token)
dp = Dispatcher()

# اضافه کردن User Router
user_router = get_router()
dp.include_router(user_router)

# اضافه کردن Admin Router
admin_router = get_admin_router()
dp.include_router(admin_router)

# Start Polling
await dp.start_polling(bot)
```

## Testing

### Import Test

```bash
python test_ai_admin_imports.py
```

این تست بررسی می‌کند:
- ✅ Service Imports
- ✅ Keyboard Imports
- ✅ Handler Imports
- ✅ Service Instantiation
- ✅ Config Operations
- ✅ Content Operations
- ✅ Gateway Operations
- ✅ Existing Handler

## Known Issues

### محدودیت‌های فعلی

1. **Broadcast**: فعلاً Synchronous اجرا می‌شود. باید به Background Task منتقل شود.
2. **Offline Messages**: فعلاً Persistence ندارد.
3. **User List**: `get_all_user_ids()` فعلاً لیست خالی برمی‌گرداند.
4. **Statistics**: فعلاً Mock/Session-based است.
5. **Queue Management**: پیاده‌سازی نشده.

## Technical Debt

### 1. Background Tasks

Broadcast باید در background اجرا شود:

```python
# فعلاً:
result = await broadcast_service.execute_broadcast(...)

# باید:
task = asyncio.create_task(broadcast_service.execute_broadcast(...))
```

### 2. Database Integration

Repository Pattern برای Persistence:

```python
class AIImageRepository:
    async def save_config(self, key, value):
        pass
    
    async def get_config(self, key):
        pass
    
    async def save_faq(self, faq):
        pass
```

### 3. Pagination

FAQs و Broadcasts باید Pagination داشته باشند.

### 4. Search & Filter

Admin باید بتواند:
- جستجو در FAQs
- فیلتر کردن Broadcasts
- فیلتر کردن کاربران

## Next Steps

### Phase 1: Database Integration
1. ایجاد جداول Database
2. پیاده‌سازی Repository Pattern
3. Migration از In-Memory به Database

### Phase 2: Mother Bot Connection
1. پیاده‌سازی Real Gateway
2. اتصال به Wallet System
3. اتصال به User Management

### Phase 3: Advanced Features
1. Scheduled Broadcasts
2. A/B Testing for Ads
3. Advanced Analytics
4. Export/Import Configuration

## Compatibility

### Mother Bot

- ✅ **هیچ تغییری در Mother Bot ایجاد نشده**
- ✅ **هیچ فایل مشترکی تغییر نکرده**
- ✅ Movie Bot و Downloader Bot دست‌نخورده هستند
- ✅ Runner بدون تغییر باقی مانده

### AI Image User Flow

- ✅ **User Handler (`ai_image.py`) دست‌نخورده**
- ✅ **همه FSM Stateها کار می‌کنند**
- ✅ **Generation Service بدون تغییر**
- ✅ **User Experience تغییر نکرده**

## Credits

این Admin Panel بر اساس معماری AI Image Bot ساخته شده و کاملاً مستقل از Mother Bot است.

**Architecture:**
- Reply Keyboard for Main Navigation
- Inline Keyboard for Actions
- FSM for Input Flows
- Service Layer for Business Logic
- Mock Implementation for Future Integration
