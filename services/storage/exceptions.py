"""
Storage Exceptions

مسئولیت: تعریف خطاهای سطح application برای storage

Security:
- هیچ credential در exception messages نیست
- هیچ sensitive data در traceback نیست
"""


class StorageError(Exception):
    """خطای عمومی Storage"""
    pass


class StorageConfigurationError(StorageError):
    """خطا: تنظیمات storage نادرست یا ناقص است"""
    pass


class StorageConnectionError(StorageError):
    """خطا: اتصال به storage ناموفق بود"""
    pass


class StorageUploadError(StorageError):
    """خطا: آپلود فایل ناموفق بود"""
    pass


class StorageDeleteError(StorageError):
    """خطا: حذف فایل ناموفق بود"""
    pass


class StorageFileTooLargeError(StorageError):
    """خطا: فایل بزرگتر از حد مجاز است"""
    
    def __init__(self, file_size: int, max_size: int):
        self.file_size = file_size
        self.max_size = max_size
        super().__init__(
            f"File size ({file_size} bytes) exceeds maximum "
            f"allowed size ({max_size} bytes)"
        )


class StorageDisabledError(StorageError):
    """خطا: storage غیرفعال است"""
    
    def __init__(self):
        super().__init__(
            "File storage is disabled. "
            "Set FILE_STORAGE_ENABLED=true to enable it."
        )
