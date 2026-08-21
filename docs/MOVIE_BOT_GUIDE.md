# راهنمای Movie Bot

## 📋 خلاصه

Movie Bot یک **UI Prototype** برای ربات فیلم و سریال است که به عنوان یکی از انواع Child Bot روی Runtime فعلی پروژه اجرا می‌شود.

⚠️ **مهم:** این فقط یک Prototype است و شامل موارد زیر **نمی‌شود**:
- دیتابیس واقعی فیلم و سریال
- آرشیو واقعی
- لینک دانلود واقعی
- API خارجی (TMDB، IMDb و غیره)
- سیستم اشتراک واقعی
- سرور دانلود
- CDN یا Storage

## 🏗️ معماری

```
Mother Bot
    ↓
BotRuntimeManager (services/runner.py)
    ↓
bot_type = "movie_downloader"
    ↓
handlers/child_bots/movie.py
    ↓
get_router() → Router جدید
    ↓
Movie Bot Handlers
```

## 📁 ساختار فایل‌ها

```
handlers/
    └─ child_bots/
        └─ movie.py              # Main handler (Router Factory)
        
data/
    └─ movie_mock_data.py        # Mock data (فیلم‌ها، سریال‌ها، ژانرها)
    
keyboards/
    └─ movie_keyboards.py        # Inline keyboards
    
services/
    └─ runner.py                 # تغییر mapping: movie_downloader → movie.py
```

## ✅ تغییرات اعمال شده

### 1. ساخت Mock Data
**فایل:** `data/movie_mock_data.py`

- 5 فیلم نمونه
- 5 سریال نمونه
- 8 ژانر
- توابع helper برای جستجو، فیلتر و مرتب‌سازی

### 2. ساخت Keyboards
**فایل:** `keyboards/movie_keyboards.py`

کیبوردهای جدا از Handler:
- Main Menu
- Movies List
- Series List
- Movie Detail
- Series Detail
- Genres
- Search Results
- Profile
- Favorites

### 3. ساخت Movie Handler
**فایل:** `handlers/child_bots/movie.py`

ویژگی‌ها:
- ✅ Router Factory Pattern (`get_router()`)
- ✅ FSM برای جستجو
- ✅ Inline Navigation
- ✅ Mock Data جدا از Handler
- ✅ هیچ Runtime مستقل ایجاد نمی‌کند
- ✅ از همان Lifecycle Manager فعلی استفاده می‌کند

### 4. تغییر Runner Mapping
**فایل:** `services/runner.py`

فقط یک خط تغییر یافت:
```python
"movie_downloader": "handlers.child_bots.movie",  # قبلاً: downloader
```

سایر bot_type mappingها **دست‌نخورده** باقی ماندند:
- `"ai_image": "handlers.child_bots.downloader"`
- `"social_downloader": "handlers.child_bots.downloader"`
- `"vpn_seller": "handlers.child_bots.downloader"`
- `"downloader": "handlers.child_bots.downloader"`

## 🎬 UI/UX فعلی

### صفحه اصلی
```
🎬 به ربات فیلم و سریال خوش آمدید!

🔎 جستجو
🎬 فیلم‌ها  |  📺 سریال‌ها
🔥 محبوب‌ترین‌ها  |  🆕 جدیدترین‌ها
🎭 ژانرها
👤 پروفایل
```

### Movie Card نمونه
```
🎬 Inception
تلقین

⭐ امتیاز: 8.8/10
📅 سال: 2010
🌍 کشور: USA
🎭 ژانر: Action • Sci-Fi • Thriller
⏱️ مدت: 148 دقیقه
🎬 کارگردان: Christopher Nolan

📝 درباره فیلم:
یک دزد ماهر که در هنر استخراج اسرار...

[▶️ تماشا] [⬇️ دانلود]
[❤️ افزودن به علاقه‌مندی‌ها]
[⬅️ بازگشت]
```

## 🔧 نحوه استفاده

### برای کاربر نهایی:
1. در Mother Bot نوع ربات را انتخاب کنید: **🎬 ربات دانلود فیلم و سریال**
2. توکن BotFather را وارد کنید
3. ربات شما با UI جدید Movie Bot روشن می‌شود

### برای توسعه‌دهنده:
هیچ تنظیم اضافی لازم نیست. فقط کافیست:
```python
# در config.py از قبل تعریف شده:
BOT_TYPES = {
    "movie_downloader": "🎬 ربات دانلود فیلم و سریال",
    ...
}
```

## 🚀 چگونه کار می‌کند؟

1. **کاربر ربات می‌سازد:**
   - Mother Bot → `bot_type='movie_downloader'` در DB ذخیره می‌شود

2. **Runtime ربات را شروع می‌کند:**
   - `BotRunner.start_bot(bot_id, owner_id)`
   - Runner از DB می‌خواند: `bot_type='movie_downloader'`
   - `_get_router_for_bot_type('movie_downloader')`
   - Lazy import: `handlers.child_bots.movie`
   - صدا زدن: `movie.get_router()`
   - Router جدید به Dispatcher اضافه می‌شود

3. **Child Bot اجرا می‌شود:**
   - هر ربات در یک `asyncio.Task` جداگانه
   - Lifecycle توسط `BotRunner` مدیریت می‌شود
   - Stop/Start/Restart همه کار می‌کنند

## 🧪 تست

### تست دستی:
1. ربات Mother را اجرا کنید: `python bot.py`
2. یک ربات movie_downloader بسازید
3. چک کنید که UI جدید نمایش داده می‌شود
4. Navigation را تست کنید
5. جستجو را تست کنید
6. Stop/Start ربات را تست کنید

### چک‌لیست:
- [ ] Child Bot‌های قبلی (downloader) همچنان کار می‌کنند
- [ ] Movie Bot با UI جدید روشن می‌شود
- [ ] Navigation کار می‌کند (بدون پیام‌های اضافی)
- [ ] جستجو کار می‌کند
- [ ] Stop ربات کار می‌کند
- [ ] Start مجدد کار می‌کند
- [ ] هیچ خطایی در logs نیست

## ⚠️ محدودیت‌های فعلی (به عمد)

1. **هیچ Database:** همه داده‌ها Mock هستند
2. **هیچ API خارجی:** TMDB، IMDb استفاده نمی‌شوند
3. **هیچ دانلود واقعی:** دکمه‌های Watch/Download فقط UI هستند
4. **هیچ سیستم Favorite واقعی:** فقط پیام Mock
5. **هیچ سیستم اشتراک:** این قابلیت فعلاً scope نیست

## 🔮 مراحل بعدی (خارج از Scope فعلی)

اگر در آینده بخواهید این Prototype را به سرویس واقعی تبدیل کنید:

1. **Database Schema:**
   - جدول `movies`
   - جدول `series`
   - جدول `genres`
   - جدول `user_favorites`

2. **Storage:**
   - سرور دانلود / CDN
   - مدیریت فایل‌ها

3. **API Integration:**
   - TMDB برای metadata
   - Subtitle APIs

4. **Payment:**
   - سیستم اشتراک
   - گیت‌وی پرداخت

5. **Admin Panel:**
   - آپلود محتوا
   - مدیریت کاربران

## 📝 نکات توسعه

### اضافه کردن فیلم/سریال جدید:
فایل `data/movie_mock_data.py` را ویرایش کنید:
```python
MOCK_MOVIES.append({
    "id": 6,
    "title": "The Matrix",
    "title_fa": "ماتریکس",
    "year": 1999,
    # ...
})
```

### اضافه کردن Handler جدید:
در `movie.py`:
```python
async def my_new_handler(callback: CallbackQuery):
    # ...

# در get_router():
router.callback_query.register(my_new_handler, F.data == "my_action")
```

### اضافه کردن Keyboard جدید:
در `movie_keyboards.py`:
```python
def get_my_keyboard() -> InlineKeyboardMarkup:
    # ...
```

## 🐛 عیب‌یابی

### ربات روشن نمی‌شود:
1. چک کنید logs را: `python bot.py`
2. بررسی کنید که `handlers/child_bots/movie.py` وجود دارد
3. چک کنید که `data/movie_mock_data.py` import می‌شود

### خطای Import:
اطمینان حاصل کنید که:
- `data/__init__.py` وجود دارد (خالی باشد)
- `keyboards/__init__.py` وجود دارد (خالی باشد)

### Navigation کار نمی‌کند:
- چک کنید callback_data ها یکتا هستند
- بررسی کنید که handler‌ها در `get_router()` ثبت شده‌اند

## 📞 پشتیبانی

برای سوال یا مشکل:
1. لاگ‌های `python bot.py` را بررسی کنید
2. فایل `services/runner.py` را چک کنید
3. مطمئن شوید که `bot_type` در config درست تعریف شده

---

**نسخه:** 1.0.0  
**تاریخ:** 2024  
**وضعیت:** ✅ UI Prototype کامل
