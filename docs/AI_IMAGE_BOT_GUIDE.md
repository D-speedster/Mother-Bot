# راهنمای AI Image Bot

## 📋 خلاصه

AI Image Bot دومین **Child Bot واقعی** پروژه است که به عنوان یک **UI Prototype** برای تولید تصویر با هوش مصنوعی پیاده‌سازی شده است.

⚠️ **مهم:** این فقط یک Prototype است و شامل موارد زیر **نمی‌شود**:
- تولید واقعی تصویر
- Stable Diffusion یا Midjourney
- OpenAI Image API
- GPU Processing
- Queue واقعی
- سیستم پرداخت
- History واقعی
- Database مخصوص تصاویر
- Cloud Storage

## 🏗️ معماری

```
Mother Bot
    ↓
BotRuntimeManager (services/runner.py)
    ↓
bot_type = "ai_image"
    ↓
handlers/child_bots/ai_image.py
    ↓
get_router() → Router جدید
    ↓
AI Image Bot Handlers
```

**ویژگی کلیدی:** AI Image Bot و Movie Bot **همزمان** و **مستقل** روی Runtime مشترک اجرا می‌شوند.

## 📁 ساختار فایل‌ها

```
handlers/
    └─ child_bots/
        ├─ ai_image.py           # Main handler (Router Factory)
        ├─ movie.py              # Movie Bot (دست‌نخورده)
        └─ downloader.py         # Downloader (دست‌نخورده)
        
keyboards/
    ├─ ai_image_keyboards.py     # AI Image keyboards
    └─ movie_keyboards.py        # Movie keyboards (دست‌نخورده)
    
data/
    └─ movie_mock_data.py        # Movie data (دست‌نخورده)
    
services/
    └─ runner.py                 # تغییر mapping: ai_image → ai_image.py
```

## ✅ تغییرات اعمال شده

### 1. ساخت AI Image Keyboards
**فایل:** `keyboards/ai_image_keyboards.py`

ویژگی‌ها:
- ✅ Namespace: تمام callback_data ها با `ai:` شروع می‌شوند
- ✅ جلوگیری از Collision با Movie Bot
- ✅ کیبوردهای جدا از Handler

کیبوردها:
- Main Menu
- Cancel (برای FSM)
- Result (بعد از Mock)
- Gallery
- Profile
- Help

### 2. ساخت AI Image Handler
**فایل:** `handlers/child_bots/ai_image.py`

ویژگی‌ها:
- ✅ Router Factory Pattern (`get_router()`)
- ✅ FSM برای دریافت Prompt
- ✅ Callback Namespace: `ai:*`
- ✅ State Management با `state.clear()`
- ✅ Mock Result
- ✅ هیچ Runtime مستقل ایجاد نمی‌کند
- ✅ از همان Lifecycle Manager فعلی استفاده می‌کند

Handler‌ها:
- `/start` - صفحه اصلی
- `/help` - راهنما
- `ai:home` - بازگشت به خانه
- `ai:create` - شروع ساخت تصویر (FSM)
- `ai:gallery` - گالری (Mock)
- `ai:profile` - پروفایل (Mock)
- `ai:help` - راهنما
- `ai:cancel` - لغو FSM
- Message handler برای Prompt

### 3. تغییر Runner Mapping
**فایل:** `services/runner.py`

فقط یک خط تغییر یافت:
```python
"ai_image": "handlers.child_bots.ai_image",  # قبلاً: downloader
```

سایر bot_type mappingها **دست‌نخورده** باقی ماندند:
- `"movie_downloader": "handlers.child_bots.movie"` ✅
- `"social_downloader": "handlers.child_bots.downloader"` ✅
- `"vpn_seller": "handlers.child_bots.downloader"` ✅
- `"downloader": "handlers.child_bots.downloader"` ✅

## 🎨 UI/UX فعلی

### صفحه اصلی
```
🖼️ به AI Image Bot خوش آمدید!

✨ استودیو تولید تصویر با هوش مصنوعی

💡 در این نسخه می‌توانید:
• رابط کاربری تولید تصویر را مشاهده کنید
• Flow کامل را تجربه کنید

⚠️ توجه: این نسخه Prototype است

[✨ ساخت تصویر]
[🖼️ گالری من]
[📖 راهنما] [👤 حساب کاربری]
```

### Flow ساخت تصویر
```
کاربر: ✨ ساخت تصویر
    ↓
Bot: 📝 توضیح تصویر را وارد کنید
    [❌ لغو]
    ↓
کاربر: a futuristic city at night
    ↓
Bot: 🎨 درخواست شما دریافت شد
     Prompt: a futuristic city at night
     ⏳ وضعیت: Prototype
     ⚠️ تولید تصویر در این نسخه فعال نیست
     
     [🔄 درخواست جدید] [⬅️ بازگشت]
```

### گالری
```
🖼️ گالری من

👤 کاربر: ...

📊 آمار:
• تصاویر تولیدشده: 0
• درخواست‌های انجام‌شده: 0

❌ هنوز تصویری تولید نکرده‌اید

[✨ ساخت تصویر] [⬅️ بازگشت]
```

### پروفایل
```
👤 حساب کاربری

نام: ...
شناسه: ...
یوزرنیم: @...

📊 آمار استفاده:
🖼️ تصاویر تولیدشده: 0
✨ درخواست‌های انجام‌شده: 0

💡 این اطلاعات در نسخه Prototype Mock هستند
```

## 🔧 نحوه استفاده

### برای کاربر نهایی:
1. در Mother Bot نوع ربات را انتخاب کنید: **🎨 ربات هوش مصنوعی و ویرایش عکس**
2. توکن BotFather را وارد کنید
3. ربات شما با UI جدید AI Image Bot روشن می‌شود

### برای توسعه‌دهنده:
هیچ تنظیم اضافی لازم نیست:
```python
# در config.py از قبل تعریف شده:
BOT_TYPES = {
    "ai_image": "🎨 ربات هوش مصنوعی و ویرایش عکس",
    ...
}
```

## 🚀 چگونه کار می‌کند؟

1. **کاربر ربات می‌سازد:**
   - Mother Bot → `bot_type='ai_image'` در DB ذخیره می‌شود

2. **Runtime ربات را شروع می‌کند:**
   - `BotRunner.start_bot(bot_id, owner_id)`
   - Runner از DB می‌خواند: `bot_type='ai_image'`
   - `_get_router_for_bot_type('ai_image')`
   - Lazy import: `handlers.child_bots.ai_image`
   - صدا زدن: `ai_image.get_router()`
   - Router جدید به Dispatcher اضافه می‌شود

3. **Child Bot اجرا می‌شود:**
   - هر ربات در یک `asyncio.Task` جداگانه
   - Lifecycle توسط `BotRunner` مدیریت می‌شود
   - Stop/Start/Restart همه کار می‌کنند

## 🧪 تست‌های مورد نیاز

### Test 1: استقلال UI
```
Mother Bot
    ├── Movie Bot 🟢 → /start → Movie UI
    └── AI Image Bot 🟢 → /start → AI Image UI
```

### Test 2: عملکرد همزمان
```
AI Image: ✨ ساخت تصویر → Prompt → Mock Result
Movie Bot: همزمان باید کار کند
```

### Test 3: Stop Isolation
```
Mother Bot → Stop AI Image Bot
    ├── AI Image Bot 🔴 متوقف شود
    └── Movie Bot 🟢 همچنان Online
```

### Test 4: Start مجدد
```
Mother Bot → Start AI Image Bot
    ├── AI Image Bot 🟢 آنلاین شود
    └── Movie Bot 🟢 همچنان Online
```

### Test 5: FSM Isolation
```
AI Image: waiting_for_prompt
Movie Bot: باید بدون مشکل کار کند
```

## 🔐 Callback Namespace

### AI Image Bot:
```
ai:home
ai:create
ai:gallery
ai:help
ai:profile
ai:cancel
```

### Movie Bot (دست‌نخورده):
```
movie_home
movie_list
movie_search
movie_detail_*
series_detail_*
genre_*
...
```

**نتیجه:** هیچ Collision بین دو Bot وجود ندارد ✅

## ⚠️ محدودیت‌های فعلی (به عمد)

1. **هیچ تولید تصویر:** همه Mock است
2. **هیچ API خارجی:** بدون OpenAI، Stable Diffusion
3. **هیچ Queue:** بدون سیستم صف واقعی
4. **هیچ Database:** بدون ذخیره تصاویر
5. **هیچ Storage:** بدون Cloud یا CDN
6. **هیچ پرداخت:** این قابلیت فعلاً scope نیست

## 🔮 مراحل بعدی (خارج از Scope فعلی)

اگر در آینده بخواهید این Prototype را به سرویس واقعی تبدیل کنید:

1. **AI Backend:**
   - Stable Diffusion Server
   - OpenAI Integration
   - Midjourney API

2. **Queue System:**
   - Redis Queue
   - Worker Processes
   - Progress Updates

3. **Storage:**
   - Cloud Storage (S3, GCS)
   - CDN
   - Thumbnail Generation

4. **Database:**
   - جدول `images`
   - جدول `user_prompts`
   - جدول `generation_history`

5. **Payment:**
   - سیستم اعتبار
   - پلن‌های مختلف
   - گیت‌وی پرداخت

## 📝 نکات توسعه

### اضافه کردن Handler جدید:
در `ai_image.py`:
```python
async def my_new_handler(callback: CallbackQuery):
    # ...

# در get_router():
router.callback_query.register(my_new_handler, F.data == "ai:my_action")
```

### اضافه کردن Keyboard جدید:
در `ai_image_keyboards.py`:
```python
def get_my_keyboard() -> InlineKeyboardMarkup:
    # ...
```

### اضافه کردن State جدید:
در `ai_image.py`:
```python
class AIImageStates(StatesGroup):
    waiting_for_prompt = State()
    waiting_for_style = State()  # جدید
```

## 🐛 عیب‌یابی

### ربات روشن نمی‌شود:
1. چک کنید logs را: `python bot.py`
2. بررسی کنید که `handlers/child_bots/ai_image.py` وجود دارد
3. چک کنید mapping در runner.py

### خطای Callback:
- اطمینان حاصل کنید تمام callback ها با `ai:` شروع می‌شوند
- بررسی کنید که handler در `get_router()` ثبت شده

### FSM کار نمی‌کند:
- چک کنید State به درستی set شده: `await state.set_state(...)`
- بعد از پایان حتماً: `await state.clear()`

## 📊 مقایسه با Movie Bot

| ویژگی | Movie Bot | AI Image Bot |
|------|-----------|--------------|
| **Namespace** | `movie_*` | `ai:*` |
| **Router Name** | `movie_bot` | `ai_image_bot` |
| **FSM States** | `MovieBotStates` | `AIImageStates` |
| **Main Data** | Mock movies/series | Mock prompts |
| **Runtime** | Shared ✅ | Shared ✅ |
| **Independent** | Yes ✅ | Yes ✅ |

## 🎯 Definition of Done

- [x] ✅ ai_image به Child Bot مستقل متصل شد
- [x] ✅ downloader.py حذف یا خراب نشد
- [x] ✅ سایر Bot Typeها تغییر نکردند
- [x] ✅ Runtime جدید ساخته نشد
- [x] ✅ Event Loop جدید ساخته نشد
- [x] ✅ Router Factory Pattern رعایت شد
- [x] ✅ AI Image Router از Movie Router مستقل است
- [x] ✅ Callbackها Namespace دارند (`ai:*`)
- [x] ✅ FSM برای Prompt پیاده‌سازی شد
- [x] ✅ Cancel State وجود دارد
- [x] ✅ State بعد از پایان پاک می‌شود
- [x] ✅ UI اصلی ساخته شد
- [x] ✅ Gallery UI ساخته شد
- [x] ✅ Profile UI ساخته شد
- [x] ✅ Help UI ساخته شد
- [x] ✅ Mock Result ساخته شد
- [x] ✅ هیچ API خارجی استفاده نشد
- [x] ✅ هیچ تصویر واقعی تولید نشد
- [x] ✅ هیچ Database جدیدی ایجاد نشد
- [x] ✅ Movie Bot بدون تغییر باقی ماند
- [ ] ⏳ Movie Bot و AI Image Bot همزمان قابل اجرا هستند
- [ ] ⏳ Stop/Start یکی روی دیگری اثر نمی‌گذارد

---

**نسخه:** 1.0.0  
**تاریخ:** 2024  
**وضعیت:** ✅ UI Prototype آماده تست
