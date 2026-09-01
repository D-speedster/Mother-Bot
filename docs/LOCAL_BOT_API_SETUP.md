# Local Bot API Setup Guide

راهنمای راه‌اندازی Telegram Local Bot API Server برای پشتیبانی از فایل‌های بزرگ

---

## چرا Local Bot API؟

Telegram Bot API استاندارد محدودیت‌هایی برای اندازه فایل دارد:
- **Download**: حداکثر 20 MB
- **Upload**: حداکثر 50 MB

**Telegram Local Bot API Server** این محدودیت‌ها را برمی‌دارد:
- **Download**: نامحدود
- **Upload**: تا **2000 MB (≈2 GB)**
- **Local File Paths**: امکان کار با مسیرهای محلی فایل

این برای **File Transfer Child Bot** ضروری است که قرار است فایل‌های بزرگ را مدیریت کند.

---

## معماری

```
Mother Bot (Python + aiogram)
    |
    +-- Child Bot #1 (AI Image)
    +-- Child Bot #2 (Movie)
    +-- Child Bot #3 (File Transfer) ───┐
    +-- Child Bot #N (...)              │
                                         │
                                         ▼
                        ┌─────────────────────────────┐
                        │ Shared Local Bot API Server │
                        │   (One Instance for All)    │
                        │   Port: 8081 (default)      │
                        └─────────────────────────────┘
                                         │
                                         ▼
                              Telegram Backend
```

**مهم**: یک Local Bot API Server برای همه Child Bot‌ها مشترک است، نه یک instance برای هر Bot.

---

## نصب Local Bot API Server (Windows)

### پیش‌نیازها

1. **Visual Studio 2019/2022** (با C++ build tools)
2. **CMake** (برای build)
3. **Git** (برای دانلود source)
4. **vcpkg** (برای dependency management)

### مراحل Build از Source

```powershell
# 1. Clone repository
git clone --recursive https://github.com/tdlib/telegram-bot-api.git
cd telegram-bot-api

# 2. Build با CMake
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . --config Release

# 3. فایل اجرایی در:
# telegram-bot-api\build\Release\telegram-bot-api.exe
```

### دریافت api_id و api_hash

**⚠️ CRITICAL**: Local Bot API Server نیاز به `api_id` و `api_hash` دارد.

1. به https://my.telegram.org وارد شوید
2. به بخش "API development tools" بروید
3. یک Application جدید ایجاد کنید
4. `api_id` (عدد) و `api_hash` (رشته) را یادداشت کنید

**🔐 SECURITY**:
- هیچ‌وقت `api_id` و `api_hash` را در git commit نکنید
- این اطلاعات حساس هستند و نباید public شوند
- در environment variable یا فایل خصوصی نگه دارید

---

## راه‌اندازی Local Bot API Server

### حالت Local Mode (توصیه شده)

```powershell
telegram-bot-api.exe --api-id=YOUR_API_ID --api-hash=YOUR_API_HASH --local
```

**پارامترهای مهم**:
- `--api-id`: API ID شما از my.telegram.org
- `--api-hash`: API Hash شما
- `--local`: فعال کردن حالت local (بدون محدودیت download، تا 2000MB upload)
- `--http-port=8081`: تغییر پورت (پیش‌فرض: 8081)

### اجرای پس‌زمینه

برای اجرای دائمی:

**Option 1**: Windows Service (پیشنهاد برای Production)
- از NSSM یا Windows Service Wrapper استفاده کنید

**Option 2**: Startup Script
- اسکریپت PowerShell با تنظیم Task Scheduler

**Option 3**: Screen/Tmux (برای Development)
- ترمینال جداگانه با keep-alive

---

## تنظیمات Mother-Bot

### 1. Environment Variables

فایل `.env` را ویرایش کنید:

```env
# فعال کردن Local Bot API
TELEGRAM_LOCAL_API_ENABLED=yes

# آدرس Local Server
TELEGRAM_LOCAL_API_BASE_URL=http://localhost

# پورت Local Server
TELEGRAM_LOCAL_API_PORT=8081

# توکن تست برای Health Check (اختیاری)
TELEGRAM_LOCAL_API_TEST_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 2. Health Check

پس از راه‌اندازی Local Server، سلامت آن را بررسی کنید:

```python
from services.telegram import LocalBotAPIConfig, HealthCheckService

config = LocalBotAPIConfig.from_env()
if config.enabled:
    service = HealthCheckService(config)
    result = await service.check_health(test_token)
    
    if result.success:
        print("✅ Local API Server سالم است")
    else:
        print(f"❌ خطا: {result.message}")
```

---

## تست 2GB Transfer (Manual)

**⚠️ این تست MANUAL است و باید دستی انجام شود.**

### فاز A: Basic Connectivity

```python
# Test getMe
bot_info = await client.get_me(token)
print(f"Bot ID: {bot_info['id']}, Username: @{bot_info['username']}")
```

**Checklist**:
- [ ] getMe موفق
- [ ] پاسخ JSON معتبر
- [ ] Bot ID صحیح

---

### فاز B: Small File Upload (~1 MB)

```python
# Upload a small test file
with open('test_1mb.bin', 'rb') as f:
    await bot.send_document(chat_id=TEST_CHAT_ID, document=f)
```

**Checklist**:
- [ ] آپلود موفق
- [ ] فایل در Telegram قابل مشاهده است
- [ ] دانلود از Telegram کار می‌کند

**Metrics**:
- Upload Duration: ______ ثانیه
- Download Duration: ______ ثانیه
- Throughput: ______ MB/s

---

### فاز C: Medium File (~100 MB)

```python
# Upload 100MB file
with open('test_100mb.bin', 'rb') as f:
    await bot.send_document(chat_id=TEST_CHAT_ID, document=f)
```

**Checklist**:
- [ ] آپلود موفق
- [ ] Peak RAM Usage: ______ MB
- [ ] CPU Usage: ______ %

**Metrics**:
- Upload Duration: ______ ثانیه
- Download Duration: ______ ثانیه
- Throughput: ______ MB/s

---

### فاز D: Large File (~500 MB)

```python
# Upload 500MB file
with open('test_500mb.bin', 'rb') as f:
    await bot.send_document(chat_id=TEST_CHAT_ID, document=f)
```

**Checklist**:
- [ ] آپلود موفق
- [ ] Peak RAM Usage: ______ MB
- [ ] Disk Usage: ______ MB (temp files)

**Metrics**:
- Upload Duration: ______ دقیقه
- Download Duration: ______ دقیقه
- Throughput: ______ MB/s
- Retry Count: ______

---

### فاز E: Very Large File (~1 GB)

```python
# Upload 1GB file
with open('test_1gb.bin', 'rb') as f:
    await bot.send_document(chat_id=TEST_CHAT_ID, document=f)
```

**Checklist**:
- [ ] آپلود موفق
- [ ] Peak RAM Usage: ______ MB
- [ ] Network Stability: ______
- [ ] Retry/Resume behavior: ______

**Metrics**:
- Upload Duration: ______ دقیقه
- Download Duration: ______ دقیقه
- Throughput: ______ MB/s
- Errors/Retries: ______

---

### فاز F: Maximum File (~2 GB)

**⚠️ CRITICAL**: این تست نیاز به:
- اتصال اینترنت پایدار
- فضای دیسک کافی (حداقل 5GB free)
- RAM کافی (حداقل 4GB free)
- زمان کافی (ممکن است 30+ دقیقه طول بکشد)

```python
# Upload near-max file (1.9 GB)
with open('test_1900mb.bin', 'rb') as f:
    await bot.send_document(chat_id=TEST_CHAT_ID, document=f)
```

**Checklist**:
- [ ] آپلود موفق
- [ ] Peak RAM Usage: ______ GB
- [ ] Peak Disk Usage: ______ GB
- [ ] Network Errors: ______
- [ ] Timeout handling: ______

**Metrics**:
- Upload Duration: ______ دقیقه
- Download Duration: ______ دقیقه
- Throughput: ______ MB/s
- Chunk Size: ______ MB
- Retry Count: ______
- Error Types: ______

---

### ساخت فایل‌های تست

```powershell
# Windows PowerShell
# 1 MB
fsutil file createnew test_1mb.bin 1048576

# 100 MB
fsutil file createnew test_100mb.bin 104857600

# 500 MB
fsutil file createnew test_500mb.bin 524288000

# 1 GB
fsutil file createnew test_1gb.bin 1073741824

# 1.9 GB (near max)
fsutil file createnew test_1900mb.bin 2040109465
```

---

## Production Considerations

### 1. Server Stability

- **Monitoring**: نظارت بر uptime و health check دوره‌ای
- **Auto-Restart**: در صورت crash خودکار restart شود
- **Logging**: لاگ‌های Local Server را ذخیره و بررسی کنید

### 2. Resource Management

- **RAM**: حداقل 2GB برای هر ترانسفر بزرگ
- **Disk**: فضای کافی برای temp files
- **Network**: پهنای باند کافی (حداقل 10 Mbps)

### 3. Security

- **Firewall**: Local Server را در معرض اینترنت قرار ندهید
- **localhost only**: فقط 127.0.0.1 bind کنید
- **No Public Access**: Local Server فقط برای Mother Bot قابل دسترسی باشد

### 4. Backup Strategy

- **Configuration**: backup از تنظیمات Local Server
- **api_id/api_hash**: در محل امن نگهداری
- **Temp Files**: پاک‌سازی دوره‌ای

---

## Troubleshooting

### خطا: Connection Refused

**علت**: Local Server اجرا نمی‌شود

**راه‌حل**:
1. چک کنید که `telegram-bot-api.exe` در حال اجراست
2. پورت 8081 باز باشد
3. Firewall آن را block نکرده باشد

---

### خطا: 401 Unauthorized

**علت**: `api_id` یا `api_hash` اشتباه است

**راه‌حل**:
1. دوباره از my.telegram.org بررسی کنید
2. مطمئن شوید که space اضافی ندارد
3. Server را با پارامترهای صحیح restart کنید

---

### خطا: Timeout

**علت**: File خیلی بزرگ یا Network کند است

**راه‌حل**:
1. Timeout را افزایش دهید
2. Chunk size را کاهش دهید
3. Retry logic اضافه کنید

---

### خطا: Out of Memory

**علت**: RAM کافی برای فایل بزرگ نیست

**راه‌حل**:
1. RAM سیستم را افزایش دهید
2. از streaming upload استفاده کنید
3. فایل را به chunks کوچک‌تر تقسیم کنید

---

## FAQ

### آیا می‌توانم چند Local Server داشته باشم؟

بله، ولی معمولاً نیازی نیست. یک instance برای همه Bot‌ها کافی است.

---

### آیا Local API بر روی Child Bot‌های دیگر تأثیر می‌گذارد؟

خیر، Child Bot‌های دیگر (AI Image, Movie, etc.) همچنان از Standard API استفاده می‌کنند.
فقط File Transfer Bot از Local API استفاده خواهد کرد.

---

### آیا Local Server باید همیشه روشن باشد؟

برای File Transfer Bot: بله.
برای سایر Bot‌ها: خیر، تأثیری ندارد.

---

### چگونه می‌توانم Log‌های Local Server را ببینم?

```powershell
# Redirect stdout/stderr to file
telegram-bot-api.exe --api-id=... --api-hash=... --local > server.log 2>&1
```

---

### آیا می‌توانم Local Server را در Docker اجرا کنم؟

بله، ولی برای Windows Development توصیه نمی‌شود.
برای Production می‌توانید از Docker استفاده کنید.

---

## Next Steps

این راهنما فقط **infrastructure preparation** است.

**File Transfer Bot** هنوز implement نشده است.

پس از اتمام تست‌های manual و اطمینان از سلامت Local API:
- Phase 2: File Transfer Bot Architecture
- Phase 3: Upload/Download Service
- Phase 4: Storage Service
- Phase 5: Queue System

---

## References

- [Telegram Bot API Source](https://github.com/tdlib/telegram-bot-api)
- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [Local Bot API Features](https://core.telegram.org/bots/api#using-a-local-bot-api-server)

---

**تاریخ ایجاد**: 2024
**نسخه**: 1.0 (Infrastructure PoC)
**وضعیت**: آماده برای تست Manual
