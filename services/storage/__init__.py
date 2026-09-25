"""
Storage Module

مسئولیت: مدیریت storage برای File Transfer Bot

Architecture:
    File Transfer Bot
        ↓
    Storage Service
        ↓
    Storage Provider (FTP, S3, Local, etc)
        ↓
    Physical Storage

Usage:
    from services.storage import StorageService, StorageDisabledError
    
    storage = StorageService()
    
    if storage.is_enabled:
        stored_file = await storage.upload(local_path, "file.pdf")
        print(stored_file.public_url)
"""
from .storage_service import StorageService
from .exceptions import (
    StorageError,
    StorageConfigurationError,
    StorageConnectionError,
    StorageUploadError,
    StorageDeleteError,
    StorageFileTooLargeError,
    StorageDisabledError
)
from .base import StoredFile

__all__ = [
    'StorageService',
    'StoredFile',
    'StorageError',
    'StorageConfigurationError',
    'StorageConnectionError',
    'StorageUploadError',
    'StorageDeleteError',
    'StorageFileTooLargeError',
    'StorageDisabledError',
]
