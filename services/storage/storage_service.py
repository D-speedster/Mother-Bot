"""
Storage Service

مسئولیت: واسط اصلی برای استفاده از storage در File Transfer Bot

این service abstraction layer بین File Transfer Bot و storage provider است.
"""
import logging
from typing import Optional, Callable

from .base import StorageProvider, StoredFile
from .config import storage_config
from .exceptions import StorageDisabledError
from .ftp_provider import FTPStorageProvider

logger = logging.getLogger(__name__)


class StorageService:
    """
    Storage Service - واسط اصلی برای File Transfer Bot
    
    این service:
    - storage provider مناسب را انتخاب می‌کند
    - disabled state را handle می‌کند
    - API ساده برای File Transfer Bot فراهم می‌کند
    
    Usage:
        storage = StorageService()
        
        if storage.is_enabled:
            stored_file = await storage.upload(local_path, original_name)
            print(stored_file.public_url)
    """
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.config = storage_config
        self.provider: Optional[StorageProvider] = None
        
        if self.config.is_configured:
            # انتخاب provider (فعلاً فقط FTP)
            self.provider = FTPStorageProvider()
            logger.info("✅ Storage Service: ENABLED (FTP)")
        else:
            logger.info("ℹ️ Storage Service: DISABLED")
    
    @property
    def is_enabled(self) -> bool:
        """بررسی فعال بودن storage"""
        return self.provider is not None
    
    def _ensure_enabled(self):
        """اطمینان از فعال بودن storage"""
        if not self.is_enabled:
            raise StorageDisabledError()
    
    async def upload(
        self,
        local_path: str,
        original_filename: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> StoredFile:
        """
        آپلود فایل به storage
        
        Args:
            local_path: مسیر فایل محلی
            original_filename: نام اصلی فایل
            progress_callback: Callback برای Progress
            
        Returns:
            StoredFile با اطلاعات فایل
            
        Raises:
            StorageDisabledError: storage غیرفعال است
            StorageUploadError: خطا در آپلود
        """
        self._ensure_enabled()
        
        return await self.provider.upload_file(
            local_path,
            original_filename,
            progress_callback
        )
    
    async def delete(self, filename: str) -> bool:
        """
        حذف فایل از storage
        
        Args:
            filename: نام فایل
            
        Returns:
            True اگر حذف شد
            
        Raises:
            StorageDisabledError: storage غیرفعال است
        """
        self._ensure_enabled()
        
        return await self.provider.delete_file(filename)
    
    async def exists(self, filename: str) -> bool:
        """
        بررسی وجود فایل
        
        Args:
            filename: نام فایل
            
        Returns:
            True اگر فایل وجود دارد
        """
        if not self.is_enabled:
            return False
        
        return await self.provider.file_exists(filename)
    
    def get_public_url(self, filename: str) -> str:
        """
        دریافت URL عمومی فایل
        
        Args:
            filename: نام فایل
            
        Returns:
            URL عمومی
            
        Raises:
            StorageDisabledError: storage غیرفعال است
        """
        self._ensure_enabled()
        
        return self.provider.generate_public_url(filename)
    
    async def cleanup_expired(self) -> int:
        """
        حذف فایل‌های منقضی شده
        
        Returns:
            تعداد فایل‌های حذف شده
            
        Raises:
            StorageDisabledError: storage غیرفعال است
        """
        self._ensure_enabled()
        
        return await self.provider.cleanup_expired_files()
    
    async def list_all(self) -> list[StoredFile]:
        """
        لیست تمام فایل‌های ذخیره شده
        
        Returns:
            لیست StoredFile
            
        Raises:
            StorageDisabledError: storage غیرفعال است
        """
        self._ensure_enabled()
        
        return await self.provider.list_files()
    
    def get_max_file_size(self) -> int:
        """
        دریافت حداکثر حجم مجاز فایل
        
        Returns:
            حداکثر حجم (bytes)
        """
        if self.is_enabled:
            return self.config.max_file_size_bytes
        return 0
    
    def get_ttl_seconds(self) -> int:
        """
        دریافت TTL فایل‌ها
        
        Returns:
            TTL (seconds)
        """
        if self.is_enabled:
            return self.config.ttl_seconds
        return 0
