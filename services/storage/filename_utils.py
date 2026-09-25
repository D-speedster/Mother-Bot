"""
Filename Utilities for Storage

مسئولیت: ساخت نام‌های امن و unique برای فایل‌ها در storage

Security:
- جلوگیری از path traversal (../)
- جلوگیری از absolute paths
- جلوگیری از کاراکترهای غیرمجاز
- جلوگیری از collision
"""
import os
import re
import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional


class FilenameGenerator:
    """
    ساخت نام‌های امن و unique برای فایل‌ها
    
    Strategy:
    - استفاده از UUID برای uniqueness
    - حفظ extension اصلی
    - حذف کاراکترهای unsafe
    - جلوگیری از path traversal
    
    Example:
    original: "my video.mp4"
    stored: "8f31c2a1_my_video.mp4"
    """
    
    # کاراکترهای مجاز در نام فایل
    SAFE_CHARS = re.compile(r'[^a-zA-Z0-9._-]')
    
    # حداکثر طول نام فایل
    MAX_FILENAME_LENGTH = 200
    
    @classmethod
    def generate_safe_filename(
        cls,
        original_filename: str,
        prefix: Optional[str] = None
    ) -> str:
        """
        ساخت نام فایل امن و unique
        
        Args:
            original_filename: نام اصلی فایل
            prefix: پیشوند اختیاری (مثل date)
            
        Returns:
            نام فایل امن و unique
            
        Example:
            generate_safe_filename("my video.mp4")
            → "8f31c2a1_my_video.mp4"
        """
        # استخراج extension
        original_path = Path(original_filename)
        extension = original_path.suffix.lower()
        base_name = original_path.stem
        
        # حذف کاراکترهای unsafe از base name
        safe_base = cls._sanitize_filename(base_name)
        
        # ساخت unique ID
        unique_id = cls._generate_unique_id()
        
        # ترکیب
        if prefix:
            safe_prefix = cls._sanitize_filename(prefix)
            parts = [safe_prefix, unique_id, safe_base]
        else:
            parts = [unique_id, safe_base]
        
        # فیلتر کردن parts خالی
        parts = [p for p in parts if p]
        
        # ساخت نام نهایی
        if parts:
            filename = "_".join(parts)
        else:
            filename = unique_id
        
        # اضافه کردن extension
        if extension:
            filename = f"{filename}{extension}"
        
        # محدود کردن طول
        filename = cls._truncate_filename(filename, extension)
        
        return filename
    
    @classmethod
    def _sanitize_filename(cls, name: str) -> str:
        """
        حذف کاراکترهای غیرمجاز از نام فایل
        
        Args:
            name: نام برای تمیز کردن
            
        Returns:
            نام تمیز شده
        """
        # حذف فاصله‌های ابتدا و انتها
        name = name.strip()
        
        # جایگزینی فاصله با underscore
        name = name.replace(' ', '_')
        
        # حذف کاراکترهای غیرمجاز
        name = cls.SAFE_CHARS.sub('', name)
        
        # حذف نقطه‌های متوالی و در ابتدا/انتها
        name = re.sub(r'\.{2,}', '.', name)
        name = name.strip('.')
        
        # حذف underscore‌های متوالی
        name = re.sub(r'_{2,}', '_', name)
        name = name.strip('_')
        
        return name
    
    @classmethod
    def _generate_unique_id(cls) -> str:
        """
        ساخت ID منحصر به فرد
        
        Returns:
            8-character unique ID
        """
        # استفاده از UUID4 برای randomness
        unique = uuid.uuid4().hex[:8]
        return unique
    
    @classmethod
    def _truncate_filename(cls, filename: str, extension: str) -> str:
        """
        محدود کردن طول نام فایل
        
        Args:
            filename: نام فایل
            extension: پسوند فایل
            
        Returns:
            نام فایل truncate شده (با حفظ extension)
        """
        if len(filename) <= cls.MAX_FILENAME_LENGTH:
            return filename
        
        # محاسبه حداکثر طول base name
        max_base_length = cls.MAX_FILENAME_LENGTH - len(extension)
        
        if max_base_length <= 0:
            # extension خیلی طولانی است!
            return filename[:cls.MAX_FILENAME_LENGTH]
        
        # Truncate base name
        base = filename[:-len(extension)] if extension else filename
        base = base[:max_base_length]
        
        return f"{base}{extension}"
    
    @classmethod
    def validate_filename(cls, filename: str) -> bool:
        """
        اعتبارسنجی نام فایل برای امنیت
        
        Args:
            filename: نام فایل برای بررسی
            
        Returns:
            True اگر نام فایل امن باشد
        """
        # بررسی خالی نبودن
        if not filename or not filename.strip():
            return False
        
        # بررسی path traversal
        if '..' in filename:
            return False
        
        # بررسی absolute path
        if filename.startswith('/') or filename.startswith('\\'):
            return False
        
        # بررسی drive letter (Windows)
        if len(filename) >= 2 and filename[1] == ':':
            return False
        
        # بررسی طول
        if len(filename) > cls.MAX_FILENAME_LENGTH:
            return False
        
        return True
    
    @classmethod
    def get_metadata_filename(cls, stored_filename: str) -> str:
        """
        ساخت نام فایل metadata برای فایل ذخیره شده
        
        Args:
            stored_filename: نام فایل در storage
            
        Returns:
            نام فایل metadata (مثل "abc123_video.mp4.meta")
        """
        return f"{stored_filename}.meta"
    
    @classmethod
    def extract_timestamp_from_filename(cls, filename: str) -> Optional[datetime]:
        """
        استخراج timestamp از نام فایل (اگر موجود باشد)
        
        Args:
            filename: نام فایل
            
        Returns:
            datetime object یا None
        """
        # Pattern: YYYYMMDD_HHMMSS_
        pattern = r'^(\d{8})_(\d{6})_'
        match = re.match(pattern, filename)
        
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            
            try:
                return datetime.strptime(
                    f"{date_str}{time_str}",
                    "%Y%m%d%H%M%S"
                )
            except ValueError:
                pass
        
        return None
