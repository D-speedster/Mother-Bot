# 🔍 گزارش بررسی پروژه Mother Bot

**تاریخ بررسی:** ۲۵ سپتامبر ۲۰۲۶  
**ریپو:** [github.com/D-speedster/Mother-Bot](https://github.com/D-speedster/Mother-Bot)  
**زبان:** Python 3.9+  
**فریمورک:** aiogram 3.15.0  
**حجم کد:** ~۱۷٬۵۰۰ خط Python در ۱۱۳ فایل

---

## 📋 خلاصه کلی

Mother Bot یک پلتفرم مدیریت ربات‌های تلگرام (Telegram Bot Manager) است که به کاربران اجازه می‌دهد از طریق یک ربات مادر، ربات‌های فرزند با قابلیت‌های مختلف بسازند و مدیریت کنند. پروژه از معماری لایه‌بندی تمیز (Handler → Service → Repository → Database) پیروی می‌کند و نکات امنیتی خوبی مثل رمزنگاری توکن‌ها با Fernet (AES-128) و Token Masking در لاگ‌ها دارد.

### انواع ربات‌های قابل ساخت:
| نوع | توضیح | وضعیت پیاده‌سازی |
|-----|--------|-------------------|
| AI Image | 🎨 ربات هوش مصنوعی و ویرایش عکس | ✅ Product-ready (با Mock Provider) |
| Movie Downloader | 🎬 دانلود فیلم و سریال | ⚠️ فقط UI/Mock Data |
| Social Downloader | 📱 دانلود از YouTube/Instagram | ✅ پیاده‌سازی واقعی با yt-dlp |
| File Transfer | 📁 فایل ↔ لینک | ✅ پیاده‌سازی واقعی |
| VPN Seller | 🔐 فروش فیلترشکن | ⚠️ از همان Handler دانلودر استفاده می‌کند (Placeholder) |

---

## ✅ نقاط قوت پروژه

### ۱. معماری و ساختار
- **معماری لایه‌بندی تمیز:** جداسازی کامل Handler / Service / Repository / Database
- **Dependency Injection:** سرویس‌ها از طریق `dp.workflow_data` به handlerها تزریق می‌شوند
- **Router Factory Pattern:** هر ربات فرزند Router اختصاصی خود را دارد (جلوگیری از تداخل)
- **مدیریت lifecycle ربات‌های فرزند:** اجرای همزمان چند ربات با asyncio و مدیریت taskهای جداگانه

### ۲. امنیت
- **رمزنگاری توکن‌ها:** با Fernet (AES-128) و کلید محیطی
- **Token Masking در لاگ‌ها:** فیلتر regex برای مخفی کردن توکن‌ها در لاگ
- **بررسی ownership:** توکن فقط به صاحب ربات برگردانده می‌شود
- **عدم افشای توکن در لیست‌ها:** `token_encrypted` در SELECT لیست ربات‌ها نمی‌آید
- **مدیریت Race Condition:** با IntegrityError در SQLite
- **بستار امن:** `bot.session.close()` و `database.disconnect()` در `finally`

### ۳. مدیریت خطا
- Exceptionهای سفارشی (`TokenAlreadyRegisteredError`, `InvalidTokenError`, `TelegramRateLimitError`)
- Crash یک ربات فرزند روی ربات مادر تأثیر ندارد (ایزوله بودن taskها)
- Rollback خودکار ربات در صورت کسر ناموفق از کیف پول

### ۴. پنل ادمین و کیف پول
- سیستم کیف پول کامل با واریز/برداشت و تاریخچه تراکنش‌ها
- پنل ادمین با آمار کلی، مدیریت ادمین‌ها و بررسی فیش‌های واریزی
- AdminCheckMiddleware برای کاهش DB query

### ۵. مستندات
- بیش از ۳۰ فایل مستندات در پوشه `docs/`
- README کامل با راه‌اندازی گام‌به‌گام
- گزارش‌های معماری و امنیتی

---

## ⚠️ مشکلات و نواقص

### 🔴 بحرانی (Critical)

#### ۱. فایل دیتابیس در Git commit شده
```
mother_bot.db-shm  ← در ریپو وجود دارد
mother_bot.db-wal  ← در ریپو وجود دارد
```
اگرچه `.gitignore` شامل `*.db` است، ولی `*.db-shm` و `*.db-wal` پوشش داده نشده‌اند. این فایل‌های WAL ممکن است حاوی داده‌های حساس (توکن‌های رمزشده، اطلاعات کاربران) باشند.

**راه‌حل:**
```gitignore
# اضافه کن:
*.db-shm
*.db-wal
*.db-journal
```
و حذف از تاریخچه Git:
```bash
git filter-repo --path mother_bot.db-shm --path mother_bot.db-wal --invert-paths
```

#### ۲. اطلاعات بانکی Hardcoded
```python
# config.py خط ۵۳-۵۵
BANK_CARD_NUMBER = os.getenv('BANK_CARD_NUMBER', '6037-9977-1234-5678')
BANK_CARD_HOLDER = os.getenv('BANK_CARD_HOLDER', 'علی احمدی')
BANK_NAME = os.getenv('BANK_NAME', 'بانک ملی ایران')
```
شماره کارت و نام دارنده کارت به‌عنوان default value در کد هاردکد شده‌اند. اگر `.env` تنظیم نشود، این مقادیر نمایش داده می‌شوند که ممکن است اطلاعات شخصی واقعی نباشند ولی بهتر است به‌جای default value، خطای عدم تنظیم شدن برگردانده شود.

**راه‌حل:**
```python
BANK_CARD_NUMBER = os.getenv('BANK_CARD_NUMBER')
if not BANK_CARD_NUMBER:
    raise ValueError("BANK_CARD_NUMBER در .env تنظیم نشده است")
```

### 🟠 مهم (Major)

#### ۳. ADMIN_USER_ID هاردکد شده
```python
# config.py خط ۴۷
ADMIN_USER_ID = 79049016
```
آیدی تلگرام ادمین اصلی مستقیماً در کد نوشته شده. این باعث می‌شود تغییر ادمین نیازمند تغییر کد باشد.

**راه‌حل:**
```python
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))
if not ADMIN_USER_ID:
    raise ValueError("ADMIN_USER_ID در .env تنظیم نشده است")
```

#### ۴. Placeholder در لینک دعوت
```python
# handlers/start.py خط ۷۵
referral_link = f"https://t.me/YOUR_BOT_USERNAME?start={user.id}"
```
لینک دعوت با `YOUR_BOT_USERNAME` جایگزین نشده است. سیستم کسب درآمد (referral) عملاً غیرفعال است.

**راه‌حل:** یوزرنیم ربات را به‌صورت داینامیک از `bot.me()` بگیر:
```python
bot_info = await message.bot.me()
referral_link = f"https://t.me/{bot_info.username}?start={user.id}"
```

#### ۵. استفاده گسترده از `except:` خالی (Bare Except)
۱۴ مورد `except:` بدون نوع خطا پیدا شد:
- `handlers/child_bots/social_downloader.py` — ۹ مورد
- `handlers/wallet.py` — ۳ مورد
- `handlers/bot_maker.py` — ۱ مورد
- `services/download_service.py` — ۱ مورد

این الگو تمام exceptionها (از جمله `KeyboardInterrupt` و `SystemExit`) را می‌گیرد و می‌تواند باگ‌های پنهان ایجاد کند.

**راه‌حل:** همیشه نوع exception را مشخص کن:
```python
# به‌جای:
except:
    pass

# بنویس:
except Exception as e:
    logger.error(f"خطا: {e}", exc_info=True)
```

#### ۶. VPN Seller از Handler اشتباه استفاده می‌کند
```python
# services/runner.py خط ۴۷
"vpn_seller": "handlers.child_bots.downloader",
```
ربات فروش VPN از همان Handler ربات دانلودر استفاده می‌کند. این یعنی اگر کاربر ربات VPN Seller بسازد، در عمل یک ربات دانلود فیلم/سریال دریافت می‌کند که ربطی به VPN ندارد.

**راه‌حل:** یا یک Handler اختصاصی برای VPN Seller بساز، یا این نوع ربات را از `BOT_TYPES` حذف کن تا کاربران سردرگم نشوند.

#### ۷. URL Cache بدون TTL در حافظه
```python
# handlers/child_bots/social_downloader.py خط ۴۲
_url_cache: dict[str, str] = {}
```
کش URL در حافظه نگهداری می‌شود بدون پاکسازی خودکار. اگر ربات طولانی‌مدت کار کند، این کش رشد می‌کند و memory leak ایجاد می‌کند.

**راه‌حل:** از `cachetools.TTLCache` استفاده کن یا پاکسازی دوره‌ای اضافه کن:
```python
from cachetools import TTLCache
_url_cache = TTLCache(maxsize=1000, ttl=3600)  # ۱ ساعت TTL
```

### 🟡 متوسط (Medium)

#### ۸. MemoryStorage برای FSM
```python
# bot.py خط ۱۱۲
storage = MemoryStorage()
```
FSM در حافظه نگهداری می‌شود. اگر ربات restart شود، تمام stateهای کاربران از دست می‌رود. برای production بهتر است از `RedisStorage` استفاده شود.

#### ۹. عدم وجود `.env.example`
`.gitignore` به `!.env.example` اشاره دارد ولی این فایل در ریپو وجود ندارد. کاربران جدید نمی‌دانند چه متغیرهای محیطی نیاز است.

#### ۱۰. تست‌های محدود
فقط ۲ فایل تست وجود دارد (`tests/test_local_api_config.py` و `tests/test_health_check.py`) که پوشش کاملی برای منطق اصلی ندارند. هیچ تست برای `BotService`, `WalletService`, یا `BotRepository` وجود ندارد.

#### ۱۱. `datetime.utcnow()` منسوخ شده
```python
# repository.py و wallet_service.py
now = datetime.utcnow().isoformat()
```
`datetime.utcnow()` در Python 3.12+ منسوخ شده است.

**راه‌حل:**
```python
from datetime import datetime, timezone
now = datetime.now(timezone.utc).isoformat()
```

#### ۱۲. VPN Seller در BOT_TYPES ولی در config تعریف نشده
در `config.py`، `BOT_TYPES` شامل `vpn_seller` است ولی در `runner.py`، `vpn_seller` به `downloader` نگاشت شده که منطق متفاوتی دارد.

---

## 🏗️ ساختار پروژه

```
Mother-Bot/
├── bot.py                    # نقطه ورود + Token Masking + startup
├── config.py                 # تنظیمات (توکن، کلید رمزنگاری، هزینه‌ها)
├── generate_key.py           # ابزار تولید کلید Fernet
├── requirements.txt           # وابستگی‌ها (۷ پکیج)
│
├── database/
│   ├── db.py                 # اتصال SQLite + WAL + Schema
│   └── repository.py         # CRUD ربات‌ها + بررسی ownership
│
├── services/
│   ├── bot_service.py        # ثبت/اعتبارسنجی ربات
│   ├── encryption.py         # رمزنگاری Fernet
│   ├── runner.py             # اجرای child botها با asyncio
│   ├── wallet_service.py     # کیف پول + تراکنش‌ها
│   ├── admin_service.py      # پنل ادمین + آمار
│   ├── deposit_service.py    # مدیریت فیش‌های واریزی
│   ├── download_service.py   # دانلود با yt-dlp
│   ├── file_transfer_service.py  # آپلود/دانلود فایل
│   ├── telegram_client.py    # کلاینت Telegram API
│   ├── exceptions.py         # خطاهای سفارشی
│   ├── progress_tracker.py   # ردیابی پیشرفت
│   ├── ai_image/             # سرویس‌های AI Image (generation, admin, broadcast)
│   └── telegram/             # پشتیبانی Local Bot API
│
├── handlers/
│   ├── start.py              # منوی اصلی
│   ├── bot_maker.py          # ساخت ربات با FSM
│   ├── wallet.py             # کیف پول + ثبت فیش
│   ├── admin.py              # پنل ادمین
│   └── child_bots/           # Handlerهای ربات‌های فرزند
│       ├── ai_image.py       # ربات AI Image (۹۴۰ خط)
│       ├── ai_image_admin.py # پنل ادمین AI Image
│       ├── movie.py          # ربات فیلم (Mock Data)
│       ├── social_downloader.py  # ربات دانلودر (yt-dlp)
│       ├── downloader.py     # ربات دانلود فیلم/سریال (Placeholder)
│       └── file_transfer.py  # ربات انتقال فایل
│
├── keyboards/                # کیبوردهای inline و reply
├── middlewares/              # AdminCheckMiddleware
├── data/                     # Mock Data فیلم
├── utils/                    # ابزارهای کمکی
├── tests/                    # تست‌ها (محدود)
└── docs/                     # ۳۰+ فایل مستندات
```

---

## 📊 ارزیابی نهایی

| معیار | امتیاز | توضیح |
|-------|--------|--------|
| معماری | ⭐⭐⭐⭐⭐ | لایه‌بندی عالی، DI، Router Factory |
| امنیت | ⭐⭐⭐⭐ | رمزنگاری خوب، ولی هاردکد کردن اطلاعات حساس |
| کیفیت کد | ⭐⭐⭐⭐ | خوانا و مستند، ولی bare except زیاد |
| تست‌پذیری | ⭐⭐ | تست‌های محدود، پوشش پایین |
| مستندات | ⭐⭐⭐⭐⭐ | بسیار کامل و گام‌به‌گام |
| آماده production | ⭐⭐⭐ | نیاز به رفع مشکلات بحرانی دارد |

---

## 🎯 اولویت‌های پیشنهادی برای بهبود

1. **فوری:** پاک کردن فایل‌های `*.db-shm` و `*.db-wal` از Git و اضافه کردن به `.gitignore`
2. **فوری:** هاردکد کردن `ADMIN_USER_ID` و اطلاعات بانکی را به `.env` منتقل کن
3. **مهم:** تمام `except:` خالی را به `except Exception as e:` تبدیل کن
4. **مهم:** لینک دعوت (`YOUR_BOT_USERNAME`) را داینامیک کن
5. **مهم:** Handler اختصاصی VPN Seller بساز یا آن را حذف کن
6. **متوسط:** `.env.example` بساز
7. **متوسط:** `MemoryStorage` را به `RedisStorage` ارتقا بده
8. **متوسط:** تست‌های واحد برای Serviceها و Repository اضافه کن
9. **پیشنهادی:** `datetime.utcnow()` را به `datetime.now(timezone.utc)` تغییر بده
10. **پیشنهادی:** TTLCache برای URL Cache استفاده کن
