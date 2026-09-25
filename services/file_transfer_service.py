"""
File Transfer Service - دانلود و آپلود فایل‌ها

این سرویس مسئول:
۱. آپلود فایل به هاست و ساخت لینک مستقیم
۲. دانلود فایل از لینک مستقیم

Features:
- تشخیص صحیح نام و پسوند فایل
- مدیریت redirectها
- نمایش Progress برای دانلود
- مدیریت robust خطاها

⚠️ هیچ وابستگی به aiogram ندارد - Pure Python Service
"""
import os
import logging
import aiohttp
import asyncio
from pathlib import Path
from typing import Optional, Callable
from urllib.parse import urlparse

from utils.filename_detector import FilenameDetector

logger = logging.getLogger(__name__)


# ========== Constants ==========
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
BLOCKED_DOMAINS = [
    'youtube.com', 'youtu.be',
    'instagram.com', 'instagr.am',
    'aparat.com',
    'twitter.com', 't.co',
    'facebook.com', 'fb.com',
    'tiktok.com',
]


# ========== Exceptions ==========
class FileTransferError(Exception):
    """خطای عمومی File Transfer"""
    pass


class HostNotConfiguredError(FileTransferError):
    """خطا: هاست برای آپلود تنظیم نشده است"""
    pass


class InvalidURLError(FileTransferError):
    """خطا: URL نامعتبر یا از دامنه‌های مسدود شده است"""
    pass


class FileTooLargeError(FileTransferError):
    """خطا: فایل بزرگتر از حد مجاز است"""
    
    def __init__(self, size: int, max_size: int):
        self.size = size
        self.max_size = max_size
        super().__init__(
            f"حجم فایل ({self._format_size(size)}) "
            f"بیشتر از حداکثر مجاز ({self._format_size(max_size)}) است"
        )
    
    @staticmethod
    def _format_size(size: int) -> str:
        """تبدیل bytes به واحد خوانا"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"


class DownloadError(FileTransferError):
    """خطا: دانلود فایل ناموفق بود"""
    pass


# ========== Service ==========
class FileTransferService:
    """
    سرویس انتقال فایل
    
    Features:
    - آپلود فایل به هاست (آینده)
    - دانلود فایل از URL
    - اعتبارسنجی URL
    - مدیریت حجم فایل
    
    Security:
    - محدودیت حجم فایل (2GB)
    - مسدود کردن دامنه‌های شبکه اجتماعی
    - Timeout برای دانلود
    """
    
    def __init__(self, timeout: int = 300):
        """
        Args:
            timeout: Timeout برای دانلود (ثانیه) - پیش‌فرض: 5 دقیقه
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
    
    async def upload_to_host(
        self,
        telegram_file_path: str,
        original_filename: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        آپلود فایل به هاست و دریافت لینک مستقیم
        
        Args:
            telegram_file_path: مسیر فایل دانلود شده از Telegram
            original_filename: نام اصلی فایل
            progress_callback: Callback برای Progress upload
            
        Returns:
            لینک مستقیم دانلود
            
        Raises:
            HostNotConfiguredError: storage هنوز تنظیم نشده است
            StorageError: خطا در آپلود
        """
        from services.storage import StorageService, StorageDisabledError
        
        storage = StorageService()
        
        if not storage.is_enabled:
            logger.warning("⚠️ Storage is disabled")
            raise HostNotConfiguredError(
                "⏳ این قابلیت به زودی فعال می‌شود\n\n"
                "فعلاً می‌توانید از قابلیت «لینک به فایل» استفاده کنید."
            )
        
        try:
            logger.info(f"📤 Uploading to storage: {original_filename}")
            
            # آپلود به storage
            stored_file = await storage.upload(
                telegram_file_path,
                original_filename,
                progress_callback
            )
            
            logger.info(f"✅ Upload successful: {stored_file.public_url}")
            
            return stored_file.public_url
        
        except StorageDisabledError:
            raise HostNotConfiguredError(
                "⏳ این قابلیت به زودی فعال می‌شود\n\n"
                "فعلاً می‌توانید از قابلیت «لینک به فایل» استفاده کنید."
            )
        
        except Exception as e:
            logger.error(
                f"❌ Upload to storage failed: {type(e).__name__}",
                exc_info=True
            )
            raise
    
    async def download_from_url(
        self,
        url: str,
        output_dir: str,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None
    ) -> str:
        """
        دانلود فایل از لینک مستقیم با Progress
        
        Args:
            url: لینک مستقیم فایل
            output_dir: پوشه موقت برای ذخیره فایل
            progress_callback: Callback برای نمایش Progress (current, total)
            
        Returns:
            مسیر کامل فایل دانلود شده
            
        Raises:
            InvalidURLError: URL نامعتبر یا مسدود شده
            FileTooLargeError: حجم فایل بیش از 2GB
            DownloadError: خطا در دانلود
            
        Note:
        - فایل در پوشه موقت ذخیره می‌شود
        - نام فایل به صورت هوشمند تشخیص داده می‌شود
        - Progress به صورت throttled گزارش می‌شود
        - مسئولیت حذف فایل بعد از استفاده با فراخواننده است
        """
        # اعتبارسنجی URL
        if not self.is_valid_direct_url(url):
            logger.warning(f"⚠️ URL نامعتبر یا مسدود: {url}")
            raise InvalidURLError(
                "لینک نامعتبر است یا از دامنه‌های شبکه اجتماعی است.\n"
                "لطفاً یک لینک مستقیم ارسال کنید."
            )
        
        # ساخت پوشه خروجی
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"🔽 شروع دانلود از URL: {url}")
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # مرحله ۱: بررسی اطلاعات فایل با HEAD request
                headers = {}
                final_url = url
                total_size = None
                
                try:
                    async with session.head(url, allow_redirects=True) as response:
                        if response.status == 200:
                            # ذخیره headers برای تشخیص نام فایل
                            headers = {k.lower(): v for k, v in response.headers.items()}
                            final_url = str(response.url)
                            
                            # دریافت حجم فایل
                            content_length = headers.get('content-length')
                            if content_length:
                                total_size = int(content_length)
                                
                                # بررسی محدودیت حجم
                                if total_size > MAX_FILE_SIZE:
                                    logger.warning(
                                        f"⚠️ فایل بزرگتر از 2GB: {total_size} bytes"
                                    )
                                    raise FileTooLargeError(total_size, MAX_FILE_SIZE)
                                
                                logger.info(
                                    f"ℹ️ حجم فایل: {self._format_size(total_size)}"
                                )
                
                except aiohttp.ClientError as e:
                    logger.warning(
                        f"⚠️ HEAD request ناموفق: {type(e).__name__} - "
                        f"ادامه با GET"
                    )
                
                # مرحله ۲: دانلود فایل با GET request
                async with session.get(url, allow_redirects=True) as response:
                    if response.status != 200:
                        raise DownloadError(
                            f"سرور خطای {response.status} برگرداند"
                        )
                    
                    # بروزرسانی headers و URL نهایی
                    headers = {k.lower(): v for k, v in response.headers.items()}
                    final_url = str(response.url)
                    
                    # بررسی مجدد حجم (اگر در HEAD نبود)
                    if not total_size:
                        content_length = headers.get('content-length')
                        if content_length:
                            total_size = int(content_length)
                            if total_size > MAX_FILE_SIZE:
                                raise FileTooLargeError(total_size, MAX_FILE_SIZE)
                    
                    # تشخیص نام فایل
                    filename = FilenameDetector.detect_filename(
                        url=url,
                        headers=headers,
                        final_url=final_url
                    )
                    output_path = os.path.join(output_dir, filename)
                    
                    logger.info(f"📝 نام فایل تشخیص داده شده: {filename}")
                    
                    # دانلود و ذخیره فایل با Progress
                    downloaded_size = 0
                    chunk_size = 8192
                    
                    with open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                
                                # بررسی محدودیت حجم در حین دانلود
                                if downloaded_size > MAX_FILE_SIZE:
                                    # حذف فایل ناقص
                                    f.close()
                                    os.remove(output_path)
                                    raise FileTooLargeError(
                                        downloaded_size, MAX_FILE_SIZE
                                    )
                                
                                # گزارش Progress
                                if progress_callback:
                                    try:
                                        await progress_callback(downloaded_size, total_size)
                                    except Exception as e:
                                        # خطای Progress نباید دانلود را fail کند
                                        logger.warning(
                                            f"⚠️ خطا در Progress callback (ignored): "
                                            f"{type(e).__name__}"
                                        )
                    
                    logger.info(
                        f"✅ دانلود موفق: {filename} "
                        f"({self._format_size(downloaded_size)})"
                    )
                    
                    return output_path
        
        except (InvalidURLError, FileTooLargeError):
            # این خطاها را مستقیماً raise می‌کنیم
            raise
        
        except aiohttp.ClientError as e:
            logger.error(
                f"❌ خطای شبکه در دانلود: {type(e).__name__}",
                exc_info=True
            )
            raise DownloadError(
                f"خطا در اتصال به سرور: {type(e).__name__}"
            )
        
        except asyncio.TimeoutError:
            logger.error("❌ Timeout در دانلود فایل")
            raise DownloadError(
                "زمان دانلود به پایان رسید. لطفاً دوباره تلاش کنید."
            )
        
        except Exception as e:
            logger.error(
                f"❌ خطای غیرمنتظره در دانلود: {type(e).__name__}",
                exc_info=True
            )
            raise DownloadError(f"خطا در دانلود فایل: {type(e).__name__}")
    
    def get_file_info(self, file_path: str) -> dict:
        """
        دریافت اطلاعات فایل
        
        Args:
            file_path: مسیر فایل
            
        Returns:
            Dict شامل:
            {
                'name': str,        # نام فایل
                'size': int,        # حجم (bytes)
                'size_str': str,    # حجم قابل خواندن
                'extension': str,   # پسوند
                'mime_type': str    # نوع MIME (تقریبی)
            }
            
        Raises:
            FileNotFoundError: اگر فایل وجود نداشته باشد
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"فایل یافت نشد: {file_path}")
        
        path_obj = Path(file_path)
        file_size = os.path.getsize(file_path)
        
        # تشخیص MIME type ساده بر اساس پسوند
        mime_types = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
            '.gif': 'image/gif', '.webp': 'image/webp',
            '.mp4': 'video/mp4', '.mkv': 'video/x-matroska', '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime', '.webm': 'video/webm',
            '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg',
            '.pdf': 'application/pdf', '.zip': 'application/zip',
            '.rar': 'application/x-rar-compressed',
            '.7z': 'application/x-7z-compressed',
            '.txt': 'text/plain', '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }
        
        extension = path_obj.suffix.lower()
        mime_type = mime_types.get(extension, 'application/octet-stream')
        
        return {
            'name': path_obj.name,
            'size': file_size,
            'size_str': self._format_size(file_size),
            'extension': extension,
            'mime_type': mime_type
        }
    
    def is_valid_direct_url(self, url: str) -> bool:
        """
        بررسی معتبر بودن URL مستقیم
        
        URL مستقیم: لینکی که مستقیماً به فایل اشاره دارد
        URL نامعتبر: لینک‌های YouTube، Instagram، Aparat و...
        
        Args:
            url: URL برای بررسی
            
        Returns:
            True اگر URL معتبر باشد
        """
        try:
            # بررسی شروع URL
            if not url.startswith(('http://', 'https://')):
                return False
            
            # Parse URL
            parsed = urlparse(url)
            
            # بررسی domain
            domain = parsed.netloc.lower()
            
            # حذف www. از ابتدا
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # بررسی دامنه‌های مسدود شده
            for blocked in BLOCKED_DOMAINS:
                if blocked in domain:
                    logger.warning(
                        f"⚠️ دامنه مسدود شده: {domain} (حاوی {blocked})"
                    )
                    return False
            
            return True
        
        except Exception as e:
            logger.error(
                f"❌ خطا در اعتبارسنجی URL: {type(e).__name__}"
            )
            return False
    
    @staticmethod
    def _format_size(size: int) -> str:
        """
        تبدیل bytes به واحد خوانا
        
        Args:
            size: حجم به bytes
            
        Returns:
            رشته قابل خواندن مثل "25.3 MB"
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
