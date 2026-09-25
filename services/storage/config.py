"""
Storage Configuration Module

مسئولیت: مدیریت تنظیمات storage از environment variables

Security:
- هیچ credential در code نیست
- همه تنظیمات از environment variables
- validation در startup
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی
load_dotenv()


class StorageConfig:
    """
    تنظیمات Storage از Environment Variables
    
    Environment Variables:
    - FILE_STORAGE_ENABLED: فعال/غیرفعال بودن storage (true/false)
    - FILE_STORAGE_FTP_HOST: آدرس FTP server
    - FILE_STORAGE_FTP_PORT: پورت FTP (پیش‌فرض: 21)
    - FILE_STORAGE_FTP_USERNAME: نام کاربری FTP
    - FILE_STORAGE_FTP_PASSWORD: رمز عبور FTP
    - FILE_STORAGE_FTP_BASE_PATH: مسیر پایه در FTP (مثل /public_html/files)
    - FILE_STORAGE_PUBLIC_BASE_URL: آدرس عمومی فایل‌ها (مثل https://example.ir/files)
    - FILE_STORAGE_TTL_SECONDS: مدت زمان نگهداری فایل (پیش‌فرض: 21600 = 6 ساعت)
    - FILE_STORAGE_MAX_FILE_SIZE_MB: حداکثر حجم فایل به MB (پیش‌فرض: 2048)
    """
    
    def __init__(self):
        """خواندن و اعتبارسنجی تنظیمات"""
        # Enabled flag
        self.enabled = self._parse_bool(
            os.getenv('FILE_STORAGE_ENABLED', 'false')
        )
        
        if not self.enabled:
            logger.info("📦 File Storage: DISABLED")
            return
        
        # FTP Configuration
        self.ftp_host = os.getenv('FILE_STORAGE_FTP_HOST')
        self.ftp_port = int(os.getenv('FILE_STORAGE_FTP_PORT', '21'))
        self.ftp_username = os.getenv('FILE_STORAGE_FTP_USERNAME')
        self.ftp_password = os.getenv('FILE_STORAGE_FTP_PASSWORD')
        self.ftp_base_path = os.getenv('FILE_STORAGE_FTP_BASE_PATH', '')
        
        # Public URL Configuration
        self.public_base_url = os.getenv('FILE_STORAGE_PUBLIC_BASE_URL')
        
        # File Management
        self.ttl_seconds = int(os.getenv('FILE_STORAGE_TTL_SECONDS', '21600'))
        self.max_file_size_mb = int(
            os.getenv('FILE_STORAGE_MAX_FILE_SIZE_MB', '2048')
        )
        self.max_file_size_bytes = self.max_file_size_mb * 1024 * 1024
        
        # Validation
        self._validate()
        
        logger.info("📦 File Storage: ENABLED")
        logger.info(f"📡 FTP Host: {self.ftp_host}:{self.ftp_port}")
        logger.info(f"👤 FTP User: {self.ftp_username}")
        logger.info(f"📁 Base Path: {self.ftp_base_path or '/'}")
        logger.info(f"🌐 Public URL: {self.public_base_url}")
        logger.info(f"⏰ TTL: {self.ttl_seconds}s ({self.ttl_seconds // 3600}h)")
        logger.info(f"📊 Max Size: {self.max_file_size_mb}MB")
    
    def _parse_bool(self, value: str) -> bool:
        """تبدیل رشته به boolean"""
        return value.lower() in ('true', 'yes', '1', 'on')
    
    def _validate(self):
        """اعتبارسنجی تنظیمات"""
        errors = []
        
        if not self.ftp_host:
            errors.append("FILE_STORAGE_FTP_HOST is required")
        
        if not self.ftp_username:
            errors.append("FILE_STORAGE_FTP_USERNAME is required")
        
        if not self.ftp_password:
            errors.append("FILE_STORAGE_FTP_PASSWORD is required")
        
        if not self.public_base_url:
            errors.append("FILE_STORAGE_PUBLIC_BASE_URL is required")
        
        if self.ttl_seconds <= 0:
            errors.append("FILE_STORAGE_TTL_SECONDS must be positive")
        
        if self.max_file_size_mb <= 0:
            errors.append("FILE_STORAGE_MAX_FILE_SIZE_MB must be positive")
        
        if errors:
            error_msg = (
                "❌ File Storage Configuration Errors:\n" +
                "\n".join(f"  • {err}" for err in errors)
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    @property
    def is_configured(self) -> bool:
        """بررسی اینکه storage به درستی تنظیم شده است"""
        return self.enabled


# Global instance
storage_config = StorageConfig()
