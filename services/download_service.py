"""
سرویس دانلود ویدیو از پلتفرم‌های مختلف با استفاده از yt-dlp

این سرویس هیچ وابستگی به aiogram یا Telegram ندارد و می‌تواند
به صورت مستقل در هر پروژه‌ای استفاده شود.

پلتفرم‌های پشتیبانی شده:
- YouTube (youtube.com, youtu.be)
- Aparat (aparat.com)
- Universal (سایر پلتفرم‌های پشتیبانی شده توسط yt-dlp)

محدودیت‌ها:
- حداکثر حجم فایل: 50MB (محدودیت Telegram)
- در این فاز از cookie استفاده نمی‌شود
"""
import os
import re
import asyncio
import logging
from typing import Dict, Optional
from pathlib import Path

import yt_dlp

logger = logging.getLogger(__name__)


# ========== Exception‌های سفارشی ==========
class DownloadError(Exception):
    """خطای عمومی در فرآیند دانلود"""
    pass


class UnsupportedURLError(DownloadError):
    """URL پشتیبانی نمی‌شود"""
    pass


class FileTooLargeError(DownloadError):
    """فایل بیشتر از 50MB است"""
    pass


# ========== DownloadService ==========
class DownloadService:
    """
    سرویس دانلود ویدیو با yt-dlp
    
    این کلاس منطق دانلود و استخراج اطلاعات ویدیو را مدیریت می‌کند.
    
    ⚠️ مهم:
    - yt-dlp blocking است و باید در thread pool اجرا شود
    - همه عملیات yt-dlp از طریق _run_in_executor اجرا می‌شوند
    - خطاهای yt-dlp به DownloadError تبدیل می‌شوند
    """
    
    # محدودیت حجم فایل (50MB برای Telegram)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
    
    def __init__(self):
        """مقداردهی اولیه سرویس"""
        pass
    
    async def extract_info(self, url: str) -> dict:
        """
        استخراج اطلاعات ویدیو از URL
        
        Args:
            url: آدرس ویدیو
            
        Returns:
            dict با ساختار:
            {
                'title': str,           # عنوان ویدیو
                'duration': int,        # طول ویدیو (ثانیه)
                'thumbnail': str,       # URL تصویر بندانگشتی
                'uploader': str,        # نام آپلودر
                'platform': str,        # نام پلتفرم (youtube, aparat, ...)
                'qualities': {          # کیفیت‌های موجود
                    '360': {
                        'format_id': str,
                        'filesize': int,
                        'ext': str
                    },
                    '720': {...},
                    ...
                }
            }
            
        Raises:
            UnsupportedURLError: اگر URL پشتیبانی نشود
            DownloadError: اگر استخراج اطلاعات ناموفق باشد
        """
        try:
            # اعتبارسنجی URL
            if not self._is_valid_url(url):
                raise UnsupportedURLError("URL نامعتبر است")
            
            # تشخیص پلتفرم
            platform = self.detect_platform(url)
            
            logger.info(f"استخراج اطلاعات ویدیو از {platform}: {url}")
            
            # تنظیمات yt-dlp برای استخراج اطلاعات
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            # استخراج اطلاعات در thread pool
            info = await self._run_in_executor(
                lambda: self._extract_info_sync(url, ydl_opts)
            )
            
            # پردازش و ساختاردهی اطلاعات
            result = {
                'title': info.get('title', 'بدون عنوان'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'نامشخص'),
                'platform': platform,
                'qualities': self._extract_qualities(info)
            }
            
            logger.info(
                f"اطلاعات استخراج شد: {result['title']} "
                f"({len(result['qualities'])} کیفیت)"
            )
            
            return result
        
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if "Unsupported URL" in error_msg or "not supported" in error_msg:
                raise UnsupportedURLError(f"این URL پشتیبانی نمی‌شود")
            raise DownloadError(f"خطا در استخراج اطلاعات: {error_msg}")
        
        except UnsupportedURLError:
            raise
        
        except Exception as e:
            logger.error(f"خطای غیرمنتظره در extract_info: {type(e).__name__}", exc_info=True)
            raise DownloadError(f"خطای داخلی: {type(e).__name__}")
    
    async def download(self, url: str, quality: str, output_dir: str) -> str:
        """
        دانلود ویدیو با کیفیت مشخص
        
        Args:
            url: آدرس ویدیو
            quality: کیفیت انتخابی ('360', '720', 'best', ...)
            output_dir: پوشه خروجی
            
        Returns:
            مسیر کامل فایل دانلود شده
            
        Raises:
            DownloadError: اگر دانلود ناموفق باشد
            FileTooLargeError: اگر فایل بیشتر از 50MB باشد
        """
        try:
            # ساخت پوشه output اگر وجود ندارد
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            logger.info(f"شروع دانلود با کیفیت {quality}: {url}")
            
            # تنظیمات yt-dlp
            ydl_opts = self._get_ydl_opts(quality, output_dir)
            
            # دانلود در thread pool
            file_path = await self._run_in_executor(
                lambda: self._download_sync(url, ydl_opts)
            )
            
            # بررسی حجم فایل
            file_size = os.path.getsize(file_path)
            
            if file_size > self.MAX_FILE_SIZE:
                # حذف فایل
                try:
                    os.remove(file_path)
                except:
                    pass
                
                raise FileTooLargeError(
                    f"فایل بیشتر از 50MB است ({file_size / (1024*1024):.1f}MB)"
                )
            
            logger.info(
                f"دانلود موفق: {file_path} "
                f"({file_size / (1024*1024):.1f}MB)"
            )
            
            return file_path
        
        except FileTooLargeError:
            raise
        
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            logger.error(f"خطای yt-dlp در دانلود: {error_msg}")
            raise DownloadError(f"دانلود ناموفق: {error_msg}")
        
        except Exception as e:
            logger.error(f"خطای غیرمنتظره در download: {type(e).__name__}", exc_info=True)
            raise DownloadError(f"خطای داخلی: {type(e).__name__}")
    
    def detect_platform(self, url: str) -> str:
        """
        تشخیص پلتفرم از URL
        
        Args:
            url: آدرس ویدیو
            
        Returns:
            نام پلتفرم: 'youtube', 'aparat', 'instagram', 'universal'
        """
        url_lower = url.lower()
        
        # YouTube
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        
        # Aparat
        if 'aparat.com' in url_lower:
            return 'aparat'
        
        # Instagram
        if 'instagram.com' in url_lower:
            return 'instagram'
        
        # Twitter/X
        if 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        
        # سایر پلتفرم‌ها
        return 'universal'
    
    def _get_ydl_opts(self, quality: str, output_dir: str) -> dict:
        """
        ساخت تنظیمات yt-dlp بر اساس کیفیت
        
        Args:
            quality: کیفیت انتخابی
            output_dir: پوشه خروجی
            
        Returns:
            dict تنظیمات yt-dlp
        """
        # الگوی نام فایل خروجی
        output_template = os.path.join(output_dir, '%(id)s.%(ext)s')
        
        # انتخاب format بر اساس کیفیت
        if quality == 'best':
            format_selector = 'best[ext=mp4]/best'
        elif quality == '360':
            format_selector = 'best[height<=360][ext=mp4]/best[height<=360]'
        elif quality == '480':
            format_selector = 'best[height<=480][ext=mp4]/best[height<=480]'
        elif quality == '720':
            format_selector = 'best[height<=720][ext=mp4]/best[height<=720]'
        elif quality == '1080':
            format_selector = 'best[height<=1080][ext=mp4]/best[height<=1080]'
        else:
            # پیش‌فرض
            format_selector = 'best[ext=mp4]/best'
        
        opts = {
            'format': format_selector,
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            # بدون cookie در این فاز
            # 'cookiefile': None,
        }
        
        return opts
    
    def _is_valid_url(self, url: str) -> bool:
        """
        اعتبارسنجی ساده URL
        
        Args:
            url: آدرس برای بررسی
            
        Returns:
            True اگر URL معتبر باشد
        """
        # بررسی ساده با regex
        pattern = r'^https?://.+'
        return bool(re.match(pattern, url))
    
    def _extract_qualities(self, info: dict) -> Dict[str, dict]:
        """
        استخراج کیفیت‌های موجود از اطلاعات ویدیو
        
        Args:
            info: اطلاعات خام yt-dlp
            
        Returns:
            dict کیفیت‌ها با ساختار:
            {
                '360': {'format_id': str, 'filesize': int, 'ext': str},
                '720': {...},
                ...
            }
        """
        qualities = {}
        formats = info.get('formats', [])
        
        # ارتفاع‌های استاندارد
        standard_heights = [360, 480, 720, 1080]
        
        for height in standard_heights:
            # جستجوی بهترین format برای این ارتفاع
            best_format = None
            
            for fmt in formats:
                fmt_height = fmt.get('height')
                
                if fmt_height and fmt_height <= height:
                    if not best_format or fmt_height > best_format.get('height', 0):
                        best_format = fmt
            
            # اضافه کردن به نتیجه
            if best_format:
                key = str(height)
                qualities[key] = {
                    'format_id': best_format.get('format_id', ''),
                    'filesize': best_format.get('filesize', 0) or 0,
                    'ext': best_format.get('ext', 'mp4')
                }
        
        # اگر هیچ کیفیتی پیدا نشد، حداقل 'best' را اضافه کن
        if not qualities:
            qualities['best'] = {
                'format_id': 'best',
                'filesize': 0,
                'ext': 'mp4'
            }
        
        return qualities
    
    def _extract_info_sync(self, url: str, ydl_opts: dict) -> dict:
        """
        استخراج اطلاعات (نسخه همگام - برای thread pool)
        
        Args:
            url: آدرس ویدیو
            ydl_opts: تنظیمات yt-dlp
            
        Returns:
            dict اطلاعات خام yt-dlp
        """
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    
    def _download_sync(self, url: str, ydl_opts: dict) -> str:
        """
        دانلود ویدیو (نسخه همگام - برای thread pool)
        
        Args:
            url: آدرس ویدیو
            ydl_opts: تنظیمات yt-dlp
            
        Returns:
            مسیر فایل دانلود شده
            
        ⚠️ FIX: استفاده از progress_hooks برای گرفتن مسیر واقعی فایل
        به جای prepare_filename که extension اشتباه برمی‌گرداند
        """
        downloaded_files = []
        
        # ذخیره post_hooks قبلی (اگر وجود دارد)
        original_post_hooks = ydl_opts.get('postprocessor_hooks', [])
        
        # تابع برای ثبت فایل دانلود شده
        def record_file(d):
            """
            Hook برای ثبت فایل‌های دانلود شده
            
            این hook بعد از تکمیل دانلود صدا زده می‌شود
            و مسیر واقعی فایل را به ما می‌دهد
            """
            if d['status'] == 'finished':
                # مسیر فایل نهایی (بعد از postprocessing)
                filepath = d.get('filename')
                if filepath:
                    downloaded_files.append(filepath)
        
        # اضافه کردن progress_hooks برای ثبت فایل
        if 'progress_hooks' not in ydl_opts:
            ydl_opts['progress_hooks'] = []
        
        ydl_opts['progress_hooks'].append(record_file)
        ydl_opts['postprocessor_hooks'] = original_post_hooks
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
            
            # برگرداندن آخرین فایل دانلود شده
            if downloaded_files:
                return downloaded_files[-1]
            
            # اگر هیچ فایلی ثبت نشد، سعی کن با prepare_filename
            # (fallback برای حالت‌های خاص)
            raise DownloadError("فایل دانلود نشد - هیچ فایلی در progress_hooks ثبت نشد")
        
        except yt_dlp.utils.DownloadError as e:
            raise DownloadError(f"خطا در دانلود: {str(e)}")
        
        finally:
            # پاکسازی hooks از ydl_opts (اگر دوباره استفاده شود)
            if 'progress_hooks' in ydl_opts and record_file in ydl_opts['progress_hooks']:
                ydl_opts['progress_hooks'].remove(record_file)
    
    async def _run_in_executor(self, func):
        """
        اجرای تابع blocking در thread pool
        
        Args:
            func: تابع همگام برای اجرا
            
        Returns:
            نتیجه تابع
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func)
