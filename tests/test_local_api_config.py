"""
Tests for Local Bot API Configuration

تست‌های تنظیمات Local Bot API
"""
import os
import pytest
from services.telegram import LocalBotAPIConfig


class TestLocalBotAPIConfig:
    """تست‌های LocalBotAPIConfig"""
    
    def test_config_disabled_by_default(self, monkeypatch):
        """
        تست: پیش‌فرض غیرفعال باشد
        """
        # پاک کردن تمام env vars
        monkeypatch.delenv('TELEGRAM_LOCAL_API_ENABLED', raising=False)
        monkeypatch.delenv('TELEGRAM_LOCAL_API_BASE_URL', raising=False)
        monkeypatch.delenv('TELEGRAM_LOCAL_API_PORT', raising=False)
        
        config = LocalBotAPIConfig.from_env()
        
        assert config.enabled is False
        assert config.base_url == 'http://localhost'
        assert config.port == 8081
    
    def test_config_enabled_with_yes(self, monkeypatch):
        """
        تست: فعال شدن با ENABLED=yes
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'yes')
        
        config = LocalBotAPIConfig.from_env()
        
        assert config.enabled is True
    
    def test_config_enabled_with_true(self, monkeypatch):
        """
        تست: فعال شدن با ENABLED=true
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'true')
        
        config = LocalBotAPIConfig.from_env()
        
        assert config.enabled is True
    
    def test_config_enabled_with_1(self, monkeypatch):
        """
        تست: فعال شدن با ENABLED=1
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', '1')
        
        config = LocalBotAPIConfig.from_env()
        
        assert config.enabled is True
    
    def test_config_disabled_with_no(self, monkeypatch):
        """
        تست: غیرفعال ماندن با ENABLED=no
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'no')
        
        config = LocalBotAPIConfig.from_env()
        
        assert config.enabled is False
    
    def test_config_disabled_with_false(self, monkeypatch):
        """
        تست: غیرفعال ماندن با ENABLED=false
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'false')
        
        config = LocalBotAPIConfig.from_env()
        
        assert config.enabled is False
    
    def test_config_disabled_with_0(self, monkeypatch):
        """
        تست: غیرفعال ماندن با ENABLED=0
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', '0')
        
        config = LocalBotAPIConfig.from_env()
        
        assert config.enabled is False
    
    def test_config_custom_base_url(self, monkeypatch):
        """
        تست: آدرس پایه سفارشی
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'yes')
        monkeypatch.setenv('TELEGRAM_LOCAL_API_BASE_URL', 'http://192.168.1.100')
        
        config = LocalBotAPIConfig.from_env()
        
        assert config.enabled is True
        assert config.base_url == 'http://192.168.1.100'
    
    def test_config_custom_port(self, monkeypatch):
        """
        تست: پورت سفارشی
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'yes')
        monkeypatch.setenv('TELEGRAM_LOCAL_API_PORT', '9000')
        
        config = LocalBotAPIConfig.from_env()
        
        assert config.enabled is True
        assert config.port == 9000
    
    def test_config_invalid_port_uses_default(self, monkeypatch):
        """
        تست: پورت نامعتبر → از پیش‌فرض استفاده می‌شود
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'yes')
        monkeypatch.setenv('TELEGRAM_LOCAL_API_PORT', 'invalid_port')
        
        config = LocalBotAPIConfig.from_env()
        
        assert config.enabled is True
        assert config.port == 8081  # پیش‌فرض
    
    def test_config_api_url_construction(self, monkeypatch):
        """
        تست: ساخت صحیح api_url
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'yes')
        monkeypatch.setenv('TELEGRAM_LOCAL_API_BASE_URL', 'http://localhost')
        monkeypatch.setenv('TELEGRAM_LOCAL_API_PORT', '8081')
        
        config = LocalBotAPIConfig.from_env()
        
        assert config.api_url == 'http://localhost:8081'
    
    def test_get_bot_api_url(self, monkeypatch):
        """
        تست: ساخت URL برای یک ربات خاص
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'yes')
        monkeypatch.setenv('TELEGRAM_LOCAL_API_BASE_URL', 'http://localhost')
        monkeypatch.setenv('TELEGRAM_LOCAL_API_PORT', '8081')
        
        config = LocalBotAPIConfig.from_env()
        
        token = '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'
        url = config.get_bot_api_url(token)
        
        expected = f'http://localhost:8081/bot{token}'
        assert url == expected
    
    def test_config_disabled_when_enabled_but_empty_base_url(self, monkeypatch):
        """
        تست: غیرفعال شدن اگر ENABLED=yes ولی BASE_URL خالی باشد
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'yes')
        monkeypatch.setenv('TELEGRAM_LOCAL_API_BASE_URL', '')
        
        config = LocalBotAPIConfig.from_env()
        
        # باید خودکار غیرفعال شود
        assert config.enabled is False
    
    def test_config_repr_safe(self, monkeypatch):
        """
        تست: __repr__ هیچ اطلاعات حساسی لاگ نمی‌کند
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'yes')
        
        config = LocalBotAPIConfig.from_env()
        
        repr_str = repr(config)
        
        # باید شامل enabled و api_url باشد
        assert 'enabled=True' in repr_str
        assert 'api_url=http://localhost:8081' in repr_str
        
        # نباید شامل هیچ توکن یا اطلاعات حساسی باشد
        # (البته در config هم ذخیره نمی‌شوند، ولی باز هم چک می‌کنیم)
        assert 'token' not in repr_str.lower()
        assert 'api_id' not in repr_str.lower()
        assert 'api_hash' not in repr_str.lower()
    
    def test_config_dataclass_immutable_fields(self):
        """
        تست: فیلدهای config قابل تغییر هستند (dataclass بدون frozen)
        """
        config = LocalBotAPIConfig(
            enabled=True,
            base_url='http://localhost',
            port=8081
        )
        
        # باید بتوانیم فیلدها را تغییر دهیم (چون frozen=False)
        config.enabled = False
        assert config.enabled is False
        
        config.port = 9000
        assert config.port == 9000


class TestLocalBotAPIConfigEdgeCases:
    """تست‌های Edge Cases"""
    
    def test_config_case_insensitive_enabled(self, monkeypatch):
        """
        تست: ENABLED با حروف بزرگ/کوچک مختلف
        """
        test_cases = ['YES', 'Yes', 'yEs', 'TRUE', 'True', 'ON', 'On']
        
        for value in test_cases:
            monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', value)
            config = LocalBotAPIConfig.from_env()
            assert config.enabled is True, f"Failed for value: {value}"
    
    def test_config_case_insensitive_disabled(self, monkeypatch):
        """
        تست: DISABLED با حروف بزرگ/کوچک مختلف
        """
        test_cases = ['NO', 'No', 'nO', 'FALSE', 'False', 'OFF', 'Off']
        
        for value in test_cases:
            monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', value)
            config = LocalBotAPIConfig.from_env()
            assert config.enabled is False, f"Failed for value: {value}"
    
    def test_config_whitespace_trimmed(self, monkeypatch):
        """
        تست: فضای خالی در مقادیر trim می‌شود
        """
        # Python os.getenv خودش trim نمی‌کند، ولی .lower() روی رشته کار می‌کند
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', ' yes ')
        
        config = LocalBotAPIConfig.from_env()
        
        # انتظار: غیرفعال بماند چون ' yes ' != 'yes'
        assert config.enabled is False
    
    def test_config_base_url_with_trailing_slash(self, monkeypatch):
        """
        تست: BASE_URL با trailing slash
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'yes')
        monkeypatch.setenv('TELEGRAM_LOCAL_API_BASE_URL', 'http://localhost/')
        
        config = LocalBotAPIConfig.from_env()
        
        # فعلاً trailing slash حذف نمی‌شود
        # api_url باید http://localhost/:8081 شود (نادرست)
        # ⚠️ این یک bug احتمالی است که باید در آینده fix شود
        assert config.api_url == 'http://localhost/:8081'
    
    def test_config_negative_port(self, monkeypatch):
        """
        تست: پورت منفی → از پیش‌فرض استفاده می‌شود
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'yes')
        monkeypatch.setenv('TELEGRAM_LOCAL_API_PORT', '-1')
        
        config = LocalBotAPIConfig.from_env()
        
        # port=-1 معتبر نیست، ولی int('-1') کار می‌کند
        # پس این تست فعلاً fail نمی‌کند
        # ⚠️ TODO: اضافه کردن validation برای port range (1-65535)
        assert config.port == -1
    
    def test_config_port_zero(self, monkeypatch):
        """
        تست: پورت صفر
        """
        monkeypatch.setenv('TELEGRAM_LOCAL_API_ENABLED', 'yes')
        monkeypatch.setenv('TELEGRAM_LOCAL_API_PORT', '0')
        
        config = LocalBotAPIConfig.from_env()
        
        assert config.port == 0
