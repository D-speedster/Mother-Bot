"""
Storage Base Interface

مسئولیت: تعریف interface برای storage providers

این abstraction اجازه می‌دهد که در آینده provider دیگری (S3, Local, etc)
بدون تغییر File Transfer Bot اضافه شود.
"""
from abc import ABC, abstractmethod
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StoredFile:
    """
    اطلاعات یک فایل ذخیره شده
    
    Attributes:
        filename: نام فایل در storage (unique)
        original_filename: نام اصلی فایل
        public_url: آدرس عمومی دانلود
        size: حجم فایل (bytes)
        uploaded_at: زمان آپلود
        expires_at: زمان انقضا
    """
    filename: str
    original_filename: str
    public_url: str
    size: int
    uploaded_at: datetime
    expires_at: datetime
    
    @property
    def is_expired(self) -> bool:
        """بررسی اینکه فایل منقضی شده است یا خیر"""
        return datetime.utcnow() > self.expires_at


class StorageProvider(ABC):
    """
    Interface برای storage providers
    
    هر provider (FTP, S3, Local, etc) باید این interface را پیاده‌سازی کند
    """
    
    @abstractmethod
    async def upload_file(
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
            progress_callback: Callback برای گزارش Progress (current, total)
            
        Returns:
            StoredFile با اطلاعات فایل آپلود شده
            
        Raises:
            StorageUploadError: خطا در آپلود
            StorageFileTooLargeError: فایل بزرگتر از حد مجاز
            StorageConnectionError: خطا در اتصال
        """
        pass
    
    @abstractmethod
    async def delete_file(self, filename: str) -> bool:
        """
        حذف فایل از storage
        
        Args:
            filename: نام فایل در storage
            
        Returns:
            True اگر فایل حذف شد، False اگر وجود نداشت
            
        Raises:
            StorageDeleteError: خطا در حذف
        """
        pass
    
    @abstractmethod
    async def file_exists(self, filename: str) -> bool:
        """
        بررسی وجود فایل در storage
        
        Args:
            filename: نام فایل
            
        Returns:
            True اگر فایل وجود دارد
        """
        pass
    
    @abstractmethod
    def generate_public_url(self, filename: str) -> str:
        """
        ساخت URL عمومی برای دانلود فایل
        
        Args:
            filename: نام فایل در storage
            
        Returns:
            URL عمومی
        """
        pass
    
    @abstractmethod
    async def cleanup_expired_files(self) -> int:
        """
        حذف فایل‌های منقضی شده
        
        Returns:
            تعداد فایل‌های حذف شده
            
        Note:
            این عملیات باید safe to repeat باشد
        """
        pass
    
    @abstractmethod
    async def list_files(self) -> list[StoredFile]:
        """
        لیست تمام فایل‌های ذخیره شده
        
        Returns:
            لیست StoredFile
        """
        pass
