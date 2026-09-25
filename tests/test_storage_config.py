"""
Tests for Storage Configuration

تست‌های تنظیمات storage
"""
import pytest
import os
from unittest.mock import patch


def test_storage_disabled_by_default():
    """تست: storage به صورت پیش‌فرض غیرفعال است"""
    with patch.dict(os.environ, {}, clear=True):
        from services.storage.config import StorageConfig
        config = StorageConfig()
        assert config.enabled is False


def test_storage_enabled():
    """تست: فعال کردن storage"""
    env = {
        'FILE_STORAGE_ENABLED': 'true',
        'FILE_STORAGE_FTP_HOST': 'ftp.example.com',
        'FILE_STORAGE_FTP_USERNAME': 'testuser',
        'FILE_STORAGE_FTP_PASSWORD': 'testpass',
        'FILE_STORAGE_PUBLIC_BASE_URL': 'https://example.com/files'
    }
    
    with patch.dict(os.environ, env, clear=True):
        from services.storage.config import StorageConfig
        config = StorageConfig()
        assert config.enabled is True
        assert config.ftp_host == 'ftp.example.com'


def test_storage_config_validation_missing_host():
    """تست: خطای validation برای host خالی"""
    env = {
        'FILE_STORAGE_ENABLED': 'true',
        'FILE_STORAGE_FTP_USERNAME': 'testuser',
        'FILE_STORAGE_FTP_PASSWORD': 'testpass',
        'FILE_STORAGE_PUBLIC_BASE_URL': 'https://example.com/files'
    }
    
    with patch.dict(os.environ, env, clear=True):
        from services.storage.config import StorageConfig
        with pytest.raises(ValueError, match="FTP_HOST"):
            StorageConfig()


def test_storage_config_defaults():
    """تست: مقادیر پیش‌فرض"""
    env = {
        'FILE_STORAGE_ENABLED': 'true',
        'FILE_STORAGE_FTP_HOST': 'ftp.example.com',
        'FILE_STORAGE_FTP_USERNAME': 'testuser',
        'FILE_STORAGE_FTP_PASSWORD': 'testpass',
        'FILE_STORAGE_PUBLIC_BASE_URL': 'https://example.com/files'
    }
    
    with patch.dict(os.environ, env, clear=True):
        from services.storage.config import StorageConfig
        config = StorageConfig()
        assert config.ftp_port == 21
        assert config.ttl_seconds == 21600
        assert config.max_file_size_mb == 2048


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
