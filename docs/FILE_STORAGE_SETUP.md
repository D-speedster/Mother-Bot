# File Storage Setup Guide

راهنمای راه‌اندازی سیستم ذخیره‌سازی فایل برای File Transfer Bot

## 📋 نیازمندی‌ها

### 1. FTP Host

شما نیاز به یک FTP host ایرانی دارید که:
- از FTP passive mode پشتیبانی کند
- دسترسی public HTTPS برای دانلود فایل‌ها فراهم کند
- حداقل 50GB فضای ذخیره‌سازی داشته باشد (برای فایل‌های موقت)

### 2. Environment Variables

تنظیمات زیر را در فایل `.env` قرار دهید:

```env
# فعال‌سازی storage
FILE_STORAGE_ENABLED=true

# اطلاعات FTP server
FILE_STORAGE_FTP_HOST=ftp.yourdomain.ir
FILE_STORAGE_FTP_PORT=21
FILE_STORAGE_FTP_USERNAME=your_ftp_username
FILE_STORAGE_FTP_PASSWORD=your_ftp_password

# مسیر پایه در FTP
# مثال: /public_html/files یا /htdocs/files
FILE_STORAGE_FTP_BASE_PATH=/public_html/files

# آدرس عمومی برای دانلود
# این آدرس باید به همان directory که در FTP تنظیم کردید اشاره کند
FILE_STORAGE_PUBLIC_BASE_URL=https://yourdomain.ir/files

# مدت زمان نگهداری فایل (ثانیه)
# 21600 = 6 ساعت
FILE_STORAGE_TTL_SECONDS=21600

# حداکثر حجم فایل (MB)
# 2048 = 2GB
FILE_STORAGE_MAX_FILE_SIZE_MB=2048
```

## 🚀 راه‌اندازی

### مرحله 1: ساخت Directory در FTP

1. به FTP server خود متصل شوید
2. directory مورد نظر را بسازید (مثلاً `/public_html/files`)
3. مطمئن شوید که directory قابل نوشتن (writable) است

```bash
# Example با FileZilla یا FTP client
mkdir /public_html/files
chmod 755 /public_html/files
```

### مرحله 2: تنظیم Web Server

مطمئن شوید که directory شما از طریق HTTPS قابل دسترسی است:

```
https://yourdomain.ir/files
```

#### برای cPanel:

1. به File Manager بروید
2. directory `files` را در `public_html` بسازید
3. مطمئن شوید که permissions روی 755 است

#### برای Nginx:

```nginx
location /files {
    alias /path/to/public_html/files;
    autoindex off;
}
```

#### برای Apache:

```apache
<Directory /path/to/public_html/files>
    Options -Indexes
    AllowOverride None
    Require all granted
</Directory>
```

### مرحله 3: تنظیم Environment Variables

فایل `.env` را ویرایش کنید و تنظیمات را وارد کنید.

**⚠️ هشدار امنیتی:**
- هیچ‌وقت فایل `.env` را commit نکنید
- از FTP password قوی استفاده کنید
- فقط دسترسی لازم را به FTP user بدهید

### مرحله 4: تست اتصال

```python
from services.storage import StorageService

storage = StorageService()

if storage.is_enabled:
    print("✅ Storage is enabled and configured")
else:
    print("❌ Storage is disabled or misconfigured")
```

## 🧪 تست

### تست دستی:

```python
import asyncio
from services.storage import StorageService

async def test_upload():
    storage = StorageService()
    
    if not storage.is_enabled:
        print("Storage is disabled")
        return
    
    # آپلود یک فایل تست
    stored_file = await storage.upload(
        local_path="test.txt",
        original_filename="test.txt"
    )
    
    print(f"✅ Uploaded: {stored_file.public_url}")
    print(f"📦 Size: {stored_file.size} bytes")
    print(f"⏰ Expires: {stored_file.expires_at}")

# اجرا
asyncio.run(test_upload())
```

### تست cleanup:

```python
async def test_cleanup():
    storage = StorageService()
    
    deleted_count = await storage.cleanup_expired()
    print(f"🗑 Deleted {deleted_count} expired files")

asyncio.run(test_cleanup())
```

## 🔄 Cleanup خودکار

فایل‌های منقضی شده باید به صورت خودکار حذف شوند.

### روش 1: Cron Job (توصیه می‌شود)

یک script Python بسازید:

```python
# cleanup_storage.py
import asyncio
import logging
from services.storage import StorageService

logging.basicConfig(level=logging.INFO)

async def main():
    storage = StorageService()
    
    if not storage.is_enabled:
        print("Storage is disabled")
        return
    
    deleted_count = await storage.cleanup_expired()
    print(f"Cleanup complete: {deleted_count} files deleted")

if __name__ == '__main__':
    asyncio.run(main())
```

سپس cron job اضافه کنید:

```bash
# هر 1 ساعت یکبار cleanup
0 * * * * cd /path/to/mother-bot && python cleanup_storage.py >> cleanup.log 2>&1
```

### روش 2: Background Task در Bot

```python
# در bot.py یا runner
import asyncio
from services.storage import StorageService

async def cleanup_task():
    storage = StorageService()
    
    while True:
        await asyncio.sleep(3600)  # هر 1 ساعت
        
        if storage.is_enabled:
            try:
                deleted = await storage.cleanup_expired()
                logger.info(f"Cleanup: {deleted} files deleted")
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
```

## 📊 Monitoring

### بررسی وضعیت:

```python
async def check_status():
    storage = StorageService()
    
    if not storage.is_enabled:
        print("❌ Storage disabled")
        return
    
    files = await storage.list_all()
    
    total_size = sum(f.size for f in files)
    expired = sum(1 for f in files if f.is_expired)
    
    print(f"📁 Total files: {len(files)}")
    print(f"📊 Total size: {total_size / (1024**3):.2f} GB")
    print(f"⏰ Expired: {expired}")
```

## 🔒 امنیت

### بهترین شیوه‌ها:

1. **FTP Credentials:**
   - از password قوی استفاده کنید
   - FTP user را محدود به directory مشخص کنید
   - هیچ‌وقت credentials را commit نکنید

2. **Directory Permissions:**
   - 755 برای directories
   - 644 برای فایل‌ها
   - Directory listing را غیرفعال کنید

3. **Public Access:**
   - فقط از HTTPS استفاده کنید
   - Hotlink protection را فعال کنید (اختیاری)
   - Rate limiting برای دانلود (اختیاری)

4. **File Names:**
   - سیستم به صورت خودکار نام‌های unique و امن می‌سازد
   - هیچ user input مستقیماً در نام فایل استفاده نمی‌شود

## 🐛 عیب‌یابی

### Storage غیرفعال است:

```
❌ Storage Service: DISABLED
```

**راه حل:**
- بررسی `FILE_STORAGE_ENABLED=true` در `.env`
- بررسی تمام environment variables لازم

### خطای اتصال FTP:

```
StorageConnectionError: Failed to connect to FTP server
```

**راه حل:**
- بررسی `FILE_STORAGE_FTP_HOST`
- بررسی `FILE_STORAGE_FTP_PORT` (معمولاً 21)
- بررسی credentials
- بررسی firewall

### خطای Permission:

```
FTP Permission Error
```

**راه حل:**
- بررسی FTP username/password
- بررسی permissions directory
- بررسی اینکه FTP user دسترسی write دارد

### فایل آپلود می‌شود ولی لینک کار نمی‌کند:

**راه حل:**
- بررسی `FILE_STORAGE_PUBLIC_BASE_URL`
- مطمئن شوید که directory از طریق web accessible است
- بررسی web server configuration

## 📝 نکات مهم

1. **TTL:**
   - فایل‌ها فقط برای مدت TTL نگهداری می‌شوند
   - بعد از انقضا، cleanup خودکار آنها را حذف می‌کند
   - Default: 6 ساعت

2. **File Size:**
   - حداکثر 2GB (قابل تنظیم)
   - بررسی قبل از آپلود
   - Streaming upload (بدون load کامل در RAM)

3. **Cleanup:**
   - باید به صورت خودکار اجرا شود
   - Safe to repeat
   - خطای یک فایل عملیات را متوقف نمی‌کند

4. **Progress:**
   - Upload progress به Telegram نمایش داده می‌شود
   - Throttled updates (هر 3 ثانیه)
   - خطای Progress عملیات را fail نمی‌کند

## 🔗 مثال کامل

```env
# .env
FILE_STORAGE_ENABLED=true
FILE_STORAGE_FTP_HOST=ftp.example.ir
FILE_STORAGE_FTP_PORT=21
FILE_STORAGE_FTP_USERNAME=botfiles
FILE_STORAGE_FTP_PASSWORD=strong_password_here
FILE_STORAGE_FTP_BASE_PATH=/public_html/botfiles
FILE_STORAGE_PUBLIC_BASE_URL=https://example.ir/botfiles
FILE_STORAGE_TTL_SECONDS=21600
FILE_STORAGE_MAX_FILE_SIZE_MB=2048
```

با این تنظیمات:
- فایل‌ها به `/public_html/botfiles` آپلود می‌شوند
- لینک عمومی: `https://example.ir/botfiles/abc123_file.pdf`
- فایل‌ها بعد از 6 ساعت حذف می‌شوند
- حداکثر حجم: 2GB

## ✅ Checklist

- [ ] FTP account ساخته شده
- [ ] Directory در FTP ساخته شده
- [ ] Permissions تنظیم شده (755)
- [ ] Web server برای دسترسی HTTPS تنظیم شده
- [ ] Environment variables در `.env` تنظیم شده
- [ ] تست آپلود انجام شده
- [ ] تست دانلود از لینک عمومی انجام شده
- [ ] Cleanup cron job تنظیم شده
- [ ] Monitoring راه‌اندازی شده

---

**آخرین بروزرسانی:** 2026-09-01  
**نسخه:** 1.0
