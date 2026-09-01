"""
Filename Detector Utility

مسئولیت: تشخیص صحیح نام و پسوند فایل از URL و Response Headers

Priority:
1. Content-Disposition response header
2. Filename در redirect نهایی / URL نهایی
3. Filename در URL اولیه
4. تشخیص extension بر اساس Content-Type
5. نام امن بدون extension جعلی
"""
import re
import logging
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Optional, Dict

logger = logging.getLogger(__name__)


# MIME Type to Extension mapping
MIME_TO_EXT = {
    # Images
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/bmp': '.bmp',
    'image/svg+xml': '.svg',
    
    # Videos
    'video/mp4': '.mp4',
    'video/mpeg': '.mpeg',
    'video/quicktime': '.mov',
    'video/x-msvideo': '.avi',
    'video/x-matroska': '.mkv',
    'video/webm': '.webm',
    'video/x-flv': '.flv',
    
    # Audio
    'audio/mpeg': '.mp3',
    'audio/mp3': '.mp3',
    'audio/wav': '.wav',
    'audio/wave': '.wav',
    'audio/ogg': '.ogg',
    'audio/aac': '.aac',
    'audio/flac': '.flac',
    'audio/x-m4a': '.m4a',
    
    # Documents
    'application/pdf': '.pdf',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/vnd.ms-powerpoint': '.ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
    'text/plain': '.txt',
    'text/csv': '.csv',
    'text/html': '.html',
    'application/xml': '.xml',
    'application/json': '.json',
    
    # Archives
    'application/zip': '.zip',
    'application/x-rar-compressed': '.rar',
    'application/x-rar': '.rar',
    'application/x-7z-compressed': '.7z',
    'application/x-tar': '.tar',
    'application/gzip': '.gz',
    'application/x-bzip2': '.bz2',
    
    # Executables
    'application/x-msdownload': '.exe',
    'application/x-msdos-program': '.exe',
    'application/vnd.microsoft.portable-executable': '.exe',
    'application/x-deb': '.deb',
    'application/x-rpm': '.rpm',
    'application/vnd.android.package-archive': '.apk',
    
    # Other
    'application/octet-stream': '',  # Generic binary - no extension
}


class FilenameDetector:
    """
    Detector برای تشخیص صحیح نام و پسوند فایل
    
    این کلاس از اولویت‌های مشخص شده استفاده می‌کند:
    1. Content-Disposition header
    2. Final URL (بعد از redirectها)
    3. Original URL
    4. Content-Type header
    5. Safe default name
    """
    
    @staticmethod
    def detect_filename(
        url: str,
        headers: Optional[Dict[str, str]] = None,
        final_url: Optional[str] = None
    ) -> str:
        """
        تشخیص نام فایل بر اساس اولویت‌های مشخص شده
        
        Args:
            url: URL اولیه
            headers: Response headers (شامل Content-Disposition و Content-Type)
            final_url: URL نهایی بعد از redirectها
            
        Returns:
            نام فایل تشخیص داده شده
        """
        if headers is None:
            headers = {}
        
        # Priority 1: Content-Disposition header
        if 'content-disposition' in headers:
            filename = FilenameDetector._extract_from_content_disposition(
                headers['content-disposition']
            )
            if filename:
                logger.info(f"✅ Filename از Content-Disposition: {filename}")
                return FilenameDetector._sanitize_filename(filename)
        
        # Priority 2: Final URL (بعد از redirectها)
        if final_url:
            filename = FilenameDetector._extract_from_url(final_url)
            if filename and FilenameDetector._has_extension(filename):
                logger.info(f"✅ Filename از Final URL: {filename}")
                return FilenameDetector._sanitize_filename(filename)
        
        # Priority 3: Original URL
        filename = FilenameDetector._extract_from_url(url)
        if filename and FilenameDetector._has_extension(filename):
            logger.info(f"✅ Filename از Original URL: {filename}")
            return FilenameDetector._sanitize_filename(filename)
        
        # Priority 4: Content-Type header
        if 'content-type' in headers:
            base_name = filename or "file"
            extension = FilenameDetector._get_extension_from_content_type(
                headers['content-type']
            )
            if extension:
                result = f"{base_name}{extension}"
                logger.info(f"✅ Filename از Content-Type: {result}")
                return FilenameDetector._sanitize_filename(result)
        
        # Priority 5: Safe default (بدون extension جعلی)
        default_name = filename or "downloaded_file"
        logger.warning(
            f"⚠️ نام فایل تشخیص داده نشد، استفاده از default: {default_name}"
        )
        return FilenameDetector._sanitize_filename(default_name)
    
    @staticmethod
    def _extract_from_content_disposition(header_value: str) -> Optional[str]:
        """
        استخراج نام فایل از Content-Disposition header
        
        Examples:
        - attachment; filename="example.zip"
        - attachment; filename*=UTF-8''example%20file.zip
        - inline; filename="document.pdf"
        
        Args:
            header_value: مقدار Content-Disposition header
            
        Returns:
            نام فایل یا None
        """
        try:
            # Pattern 1: filename="..."
            match = re.search(r'filename="([^"]+)"', header_value)
            if match:
                return unquote(match.group(1))
            
            # Pattern 2: filename=... (بدون quotes)
            match = re.search(r'filename=([^\s;]+)', header_value)
            if match:
                return unquote(match.group(1))
            
            # Pattern 3: filename*=UTF-8''... (RFC 5987)
            match = re.search(r"filename\*=UTF-8''([^\s;]+)", header_value)
            if match:
                return unquote(match.group(1))
            
            # Pattern 4: filename*=... (other encodings)
            match = re.search(r"filename\*=[^']*'[^']*'([^\s;]+)", header_value)
            if match:
                return unquote(match.group(1))
        
        except Exception as e:
            logger.error(
                f"❌ خطا در parse Content-Disposition: {type(e).__name__}",
                exc_info=True
            )
        
        return None
    
    @staticmethod
    def _extract_from_url(url: str) -> Optional[str]:
        """
        استخراج نام فایل از URL
        
        Args:
            url: URL برای parse
            
        Returns:
            نام فایل یا None
        """
        try:
            parsed = urlparse(url)
            path = unquote(parsed.path)
            
            # استخراج نام فایل از path
            filename = Path(path).name
            
            # فیلتر کردن نام‌های نامعتبر
            if filename and filename not in ['.', '..', '']:
                return filename
        
        except Exception as e:
            logger.error(
                f"❌ خطا در parse URL: {type(e).__name__}",
                exc_info=True
            )
        
        return None
    
    @staticmethod
    def _get_extension_from_content_type(content_type: str) -> Optional[str]:
        """
        تشخیص extension از Content-Type header
        
        Args:
            content_type: مقدار Content-Type header (مثل "image/jpeg; charset=utf-8")
            
        Returns:
            Extension (مثل ".jpg") یا None
        """
        try:
            # حذف parameters (مثل charset)
            mime_type = content_type.split(';')[0].strip().lower()
            
            # جستجو در mapping
            return MIME_TO_EXT.get(mime_type)
        
        except Exception as e:
            logger.error(
                f"❌ خطا در parse Content-Type: {type(e).__name__}",
                exc_info=True
            )
        
        return None
    
    @staticmethod
    def _has_extension(filename: str) -> bool:
        """
        بررسی اینکه فایل extension دارد یا خیر
        
        Args:
            filename: نام فایل
            
        Returns:
            True اگر extension داشته باشد
        """
        return bool(Path(filename).suffix)
    
    @staticmethod
    def _sanitize_filename(filename: str, max_length: int = 255) -> str:
        """
        تمیز کردن نام فایل (حذف کاراکترهای غیرمجاز)
        
        Args:
            filename: نام فایل اولیه
            max_length: حداکثر طول نام فایل
            
        Returns:
            نام فایل تمیز شده
        """
        # حذف کاراکترهای غیرمجاز در Windows/Linux
        # مجاز: حروف، اعداد، نقطه، خط تیره، underscore، فاصله
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
        
        # حذف فاصله‌های اضافی
        sanitized = ' '.join(sanitized.split())
        
        # محدود کردن طول
        if len(sanitized) > max_length:
            # حفظ extension
            path = Path(sanitized)
            name = path.stem[:max_length - len(path.suffix) - 3] + "..."
            sanitized = name + path.suffix
        
        return sanitized
