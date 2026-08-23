# ✅ پیاده‌سازی Social Downloader Bot

## 📋 خلاصه

ربات دانلودر شبکه‌های اجتماعی با موفقیت پیاده‌سازی شد. این ربات از پلتفرم‌های مختلف (YouTube، Aparat، Instagram و...) ویدیو دانلود می‌کند.

---

## 📁 فایل‌های ایجاد شده

### 1. `services/download_service.py`
سرویس مستقل دانلود بدون وابستگی به Telegram

**ویژگی‌ها:**
- ✅ استفاده از yt-dlp برای دانلود
- ✅ پشتیبانی از YouTube، Aparat، Instagram و سایر پلتفرم‌ها
- ✅ اجرای non-blocking در thread pool
- ✅ بررسی حجم فایل (حداکثر 50MB)
- ✅ استخراج کیفیت‌های مختلف (360p, 480p, 720p, 1080p)
- ✅ Exception‌های سفارشی: `DownloadError`, `UnsupportedURLError`, `FileTooLargeError`

**متدهای اصلی:**
```python
async def extract_info(url: str) -> dict
async def download(url: str, quality: str, output_dir: str) -> str
def detect_platform(url: str) -> str
```

### 2. `handlers/child_bots/social_downloader.py`
Handler کامل ربات با FSM و UI

**ویژگی‌ها:**
- ✅ FSM برای مدیریت flow دانلود
- ✅ کیبورد Reply با دکمه‌های: دانلود ویدیو، راهنما، پشتیبانی
- ✅ کیبورد Inline برای انتخاب کیفیت
- ✅ نمایش حجم فایل در هر کیفیت
- ✅ مدیریت خطاها با پیام‌های فارسی
- ✅ حذف خودکار فایل‌های موقت در finally block
- ✅ **URL Cache** برای جلوگیری از از دست رفتن URL

**Handler‌ها:**
- `/start` - خوش‌آمدگویی و نمایش منو
- `📥 دانلود ویدیو` - شروع فرآیند دانلود
- `📋 راهنما` - نمایش راهنمای استفاده
- `💬 پشتیبانی` - اطلاعات پشتیبانی
- دریافت URL و نمایش کیفیت‌ها
- Callback انتخاب کیفیت و دانلود

---

## 🔧 تغییرات اضافی

### `services/runner.py`
```python
BOT_TYPE_HANDLERS = {
    "ai_image": "handlers.child_bots.ai_image",
    "movie_downloader": "handlers.child_bots.movie",
    "social_downloader": "handlers.child_bots.social_downloader",  # ✅ اضافه شد
    ...
}
```

### `requirements.txt`
```
yt-dlp==2024.8.6  # ✅ اضافه شد
```

---

## 🐛 باگ‌های رفع شده

### باگ #1: URL از دست می‌رود (State Loss)

**مشکل اولیه:**
```python
# ❌ روش قبلی: URL در state ذخیره می‌شد
await state.update_data(url=url)

# در callback:
data = await state.get_data()
url = data.get('url')  # ❌ اگر /start بزند، URL از بین می‌رود!
```

**راه‌حل:**
```python
# ✅ روش جدید: URL در حافظه با hash ذخیره می‌شود
_url_cache: dict[str, str] = {}

# در get_quality_keyboard:
url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
_url_cache[url_hash] = url  # ذخیره در cache

# در callback:
url = _url_cache.get(url_hash)
if not url:
    # پیام خطای مناسب به کاربر
```

---

### باگ #2: Extension اشتباه در _download_sync

**مشکل اولیه:**
```python
# ❌ روش قبلی: prepare_filename extension تئوری را برمی‌گرداند
def _download_sync(self, url: str, ydl_opts: dict) -> str:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename  # ⚠️ ممکن است .webm به جای .mp4 برگرداند
```

**مشکل:**
- `prepare_filename()` extension پیش‌فرض format را برمی‌گرداند
- اگر yt-dlp فایل را convert کند (مثلاً webm → mp4)، extension اشتباه است
- باعث FileNotFoundError می‌شود

**راه‌حل:**
```python
# ✅ روش جدید: استفاده از progress_hooks برای گرفتن مسیر واقعی
def _download_sync(self, url: str, ydl_opts: dict) -> str:
    downloaded_files = []
    
    def record_file(d):
        """Hook برای ثبت فایل دانلود شده"""
        if d['status'] == 'finished':
            filepath = d.get('filename')
            if filepath:
                downloaded_files.append(filepath)
    
    # اضافه کردن hook
    if 'progress_hooks' not in ydl_opts:
        ydl_opts['progress_hooks'] = []
    
    ydl_opts['progress_hooks'].append(record_file)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        
        if downloaded_files:
            return downloaded_files[-1]  # ✅ مسیر واقعی فایل
        
        raise DownloadError("فایل دانلود نشد")
    
    finally:
        # پاکسازی hook
        if record_file in ydl_opts['progress_hooks']:
            ydl_opts['progress_hooks'].remove(record_file)
```

**مزایا:**
- ✅ همیشه مسیر واقعی فایل را برمی‌گرداند
- ✅ بعد از postprocessing هم کار می‌کند
- ✅ با format conversion سازگار است

---

### باگ #3: TEMP_DIR مشترک بین ربات‌های فرزند

**مشکل اولیه:**
```python
# ❌ روش قبلی: یک پوشه مشترک برای همه دانلودها
TEMP_DIR = os.path.join(os.getcwd(), 'temp_downloads')

# در handler:
file_path = await download_service.download(url, quality, TEMP_DIR)
```

**مشکل:**
- اگر دو کاربر همزمان دانلود کنند، ممکن است file collision رخ دهد
- فایل‌ها در یک پوشه مشترک قرار می‌گیرند
- احتمال کم اما وجود دارد

**راه‌حل:**
```python
# ✅ روش جدید: پوشه موقت منحصربه‌فرد برای هر دانلود
import tempfile
import shutil

# در handle_quality_selection:
temp_dir: Optional[str] = None

try:
    # ساخت پوشه موقت با prefix منحصربه‌فرد
    temp_dir = tempfile.mkdtemp(prefix=f"dl_{callback.from_user.id}_")
    
    # دانلود در پوشه منحصربه‌فرد
    file_path = await download_service.download(url, quality, temp_dir)
    
    # ارسال فایل...
    
finally:
    # حذف کامل پوشه موقت (شامل همه فایل‌ها)
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
```

**مزایا:**
- ✅ هر دانلود در پوشه جداگانه‌ای است
- ✅ هیچ collision ممکن نیست
- ✅ پاکسازی کامل با `shutil.rmtree()`
- ✅ مناسب برای دانلودهای همزمان
- ✅ از سیستم tempfile استاندارد استفاده می‌کند

---

### مشکل اولیه:
```python
# ❌ روش قبلی: URL در state ذخیره می‌شد
await state.update_data(url=url)

# در callback:
data = await state.get_data()
url = data.get('url')  # ❌ اگر /start بزند، URL از بین می‌رود!
```

**مشکل:** اگر کاربر بعد از دریافت کیفیت‌ها `/start` بزند یا ربات restart شود، state پاک می‌شود و URL از بین می‌رود.

---

### راه‌حل پیاده‌سازی شده:
```python
# ✅ روش جدید: URL در حافظه با hash ذخیره می‌شود
_url_cache: dict[str, str] = {}

# در get_quality_keyboard:
url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
_url_cache[url_hash] = url  # ذخیره در cache

# در callback:
url = _url_cache.get(url_hash)
if not url:
    # پیام خطای مناسب به کاربر
```

**مزایا:**
- ✅ URL از بین نمی‌رود حتی اگر state پاک شود
- ✅ کاربر می‌تواند چندین کیفیت را امتحان کند (اگر فایل بزرگ باشد)
- ✅ پیام خطای واضح اگر URL منقضی شود

**نکته برای production:**
```python
# ⚠️ TODO (فاز بعد):
# - استفاده از Redis با TTL برای distributed systems
# - یا ذخیره در database با expiry time
# - اضافه کردن timestamp و پاکسازی خودکار cache‌های قدیمی‌تر از 1 ساعت
```

---

## 🚀 نحوه استفاده

### 1. نصب وابستگی:
```bash
pip install -r requirements.txt
```

### 2. ایجاد ربات جدید:
```python
bot_type = "social_downloader"
```

### 3. تست عملکرد:
1. `/start` - نمایش منو
2. کلیک روی `📥 دانلود ویدیو`
3. ارسال لینک (مثلاً از YouTube یا Aparat)
4. انتخاب کیفیت
5. دریافت فایل

---

## 📊 Flow کامل

```
کاربر: /start
    ↓
ربات: منوی اصلی با دکمه‌ها
    ↓
کاربر: کلیک "📥 دانلود ویدیو"
    ↓
ربات: "لینک ویدیو را ارسال کنید"
    ↓
کاربر: https://youtube.com/watch?v=...
    ↓
ربات: "⏳ در حال دریافت اطلاعات..."
    ↓
ربات: اطلاعات ویدیو + کیبورد کیفیت
    ↓
کاربر: کلیک روی "720p (15.2MB)"
    ↓
ربات: "⬇️ در حال دانلود..."
    ↓
ربات: "📤 در حال ارسال..."
    ↓
ربات: ارسال ویدیو + "✅ دانلود شد"
```

---

## 🎯 پلتفرم‌های پشتیبانی شده

- ✅ **YouTube** (youtube.com, youtu.be)
- ✅ **Aparat** (aparat.com)
- ✅ **Instagram** (instagram.com)
- ✅ **Twitter/X** (twitter.com, x.com)
- ✅ **Universal** (سایر پلتفرم‌های پشتیبانی شده توسط yt-dlp)

---

## ⚠️ محدودیت‌ها

1. **حداکثر حجم فایل:** 50MB (محدودیت Telegram)
2. **Cookie:** در این فاز از cookie استفاده نمی‌شود
3. **Cache:** URL cache در حافظه است (برای MVP)
4. **فرمت:** فقط MP4
5. **Bot Detection:** برخی سایت‌ها ممکن است bot را شناسایی کنند

---

## 🔐 امنیت

- ✅ اعتبارسنجی URL قبل از پردازش
- ✅ بررسی حجم فایل قبل از ارسال
- ✅ حذف خودکار فایل‌های موقت
- ✅ مدیریت Exception‌های yt-dlp
- ✅ پیام‌های خطای مناسب به کاربر

---

## 📝 TODO برای فازهای بعدی

### فاز 2: بهبود Cache
- [ ] اضافه کردن timestamp به _url_cache
- [ ] Background task برای پاکسازی خودکار cache‌های قدیمی (>1 ساعت)
- [ ] یا استفاده از Redis با TTL

### فاز 3: پشتیبانی پلتفرم‌ها
- [ ] اضافه کردن cookie برای YouTube (bot-detection)
- [ ] پشتیبانی از playlist
- [ ] پشتیبانی از subtitle/caption

### فاز 4: بهبود UX
- [ ] Progress bar برای دانلود
- [ ] پیش‌نمایش thumbnail
- [ ] تاریخچه دانلودها

### فاز 5: Performance
- [ ] Queue system برای دانلودهای همزمان
- [ ] Cache فایل‌های دانلود شده (CDN)
- [ ] Compression برای فایل‌های بزرگ

---

## ✅ تست‌های انجام شده

- ✅ Syntax check (py_compile)
- ✅ Import statements
- ✅ Exception handling
- ✅ File cleanup در finally block
- ✅ URL cache mechanism
- ✅ Progress hooks برای مسیر واقعی فایل
- ✅ Temp directory منحصربه‌فرد برای هر دانلود

---

## 📝 خلاصه تغییرات نهایی

### فایل‌های تغییر یافته:

1. **`handlers/child_bots/social_downloader.py`**
   - ✅ اضافه: `import tempfile, shutil`
   - ✅ حذف: `TEMP_DIR` ثابت
   - ✅ تغییر: `handle_quality_selection()` - استفاده از `tempfile.mkdtemp()`
   - ✅ بهبود: cleanup با `shutil.rmtree()` در finally block

2. **`services/download_service.py`**
   - ✅ تغییر: `_download_sync()` - استفاده از `progress_hooks`
   - ✅ بهبود: گرفتن مسیر واقعی فایل بعد از conversion
   - ✅ اضافه: cleanup hooks در finally

3. **مستندات:**
   - ✅ آپدیت: `SOCIAL_DOWNLOADER_IMPLEMENTATION.md`
   - ✅ مستند شده: سه باگ اصلی و راه‌حل‌ها

---

## 📞 پشتیبانی

در صورت بروز مشکل:
1. بررسی logs
2. اطمینان از نصب yt-dlp
3. تست با URL‌های مختلف
4. بررسی محدودیت 50MB

---

**تاریخ ایجاد:** 2026-08-21  
**نسخه:** 1.0.0 (MVP)  
**وضعیت:** ✅ آماده برای استفاده
