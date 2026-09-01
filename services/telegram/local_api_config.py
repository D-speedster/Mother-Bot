"""
Local Bot API Configuration

مدیریت تنظیمات Telegram Local Bot API Server
"""
import os
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LocalBotAPIConfig:
    """
    تنظیمات Telegram Local Bot API Server
    
    Attributes:
        enabled: فعال/غیرفعال بودن Local API
        base_url: آدرس پایه Local API Server (مثال: http://localhost)
        port: پورت Local API Server (پیش‌فرض: 8081)
        api_url: URL کامل Local API (ساخته می‌شود از base_url + port)
    
    Security:
        - هیچ توکن، api_id، یا api_hash در این کلاس ذخیره نمی‌شود
        - تنها تنظیمات endpoint ذخیره می‌شود
    """
    
    enabled: bool
    base_url: str
    port: int
    
    @property
    def api_url(self) -> str:
        """
        ساخت URL کامل Local API
        
        Returns:
            URL کامل به فرمت: http://localhost:8081
        """
        return f"{self.base_url}:{self.port}"
    
    def get_bot_api_url(self, token: str) -> str:
        """
        ساخت URL کامل برای یک ربات خاص
        
        Args:
            token: توکن ربات (فقط برای ساخت URL، لاگ نمی‌شود)
            
        Returns:
            URL کامل برای API calls، مثال:
            http://localhost:8081/bot<token>/METHOD
            
        Security:
            - توکن در URL قرار می‌گیرد (مانند Standard API)
            - این متد توکن را لاگ نمی‌کند
        """
        return f"{self.api_url}/bot{token}"
    
    @classmethod
    def from_env(cls) -> 'LocalBotAPIConfig':
        """
        بارگذاری تنظیمات از environment variables
        
        Environment Variables:
            - TELEGRAM_LOCAL_API_ENABLED: فعال/غیرفعال (yes/no, true/false, 1/0)
            - TELEGRAM_LOCAL_API_BASE_URL: آدرس پایه (پیش‌فرض: http://localhost)
            - TELEGRAM_LOCAL_API_PORT: پورت (پیش‌فرض: 8081)
        
        Returns:
            LocalBotAPIConfig instance
            
        Security:
            - تنظیمات حساس (api_id, api_hash) در این کلاس ذخیره نمی‌شوند
            - فقط endpoint configuration بارگذاری می‌شود
        """
        # خواندن ENABLED
        enabled_str = os.getenv('TELEGRAM_LOCAL_API_ENABLED', 'no').lower()
        enabled = enabled_str in ('yes', 'true', '1', 'on')
        
        # خواندن BASE_URL
        base_url = os.getenv('TELEGRAM_LOCAL_API_BASE_URL', 'http://localhost')
        
        # خواندن PORT
        try:
            port = int(os.getenv('TELEGRAM_LOCAL_API_PORT', '8081'))
        except ValueError:
            logger.warning(
                "⚠️ TELEGRAM_LOCAL_API_PORT نامعتبر است. "
                "از پورت پیش‌فرض 8081 استفاده می‌شود."
            )
            port = 8081
        
        # Validation
        if enabled and not base_url:
            logger.error(
                "❌ TELEGRAM_LOCAL_API_ENABLED=yes ولی BASE_URL خالی است. "
                "Local API غیرفعال می‌شود."
            )
            enabled = False
        
        config = cls(
            enabled=enabled,
            base_url=base_url,
            port=port
        )
        
        # Logging configuration (فقط اگر فعال باشد)
        if config.enabled:
            logger.info(
                f"✅ Local Bot API فعال شد: {config.api_url}"
            )
        else:
            logger.info("ℹ️ Local Bot API غیرفعال است — از Standard API استفاده می‌شود")
        
        return config
    
    def __repr__(self) -> str:
        """نمایش امن تنظیمات (بدون اطلاعات حساس)"""
        return (
            f"LocalBotAPIConfig(enabled={self.enabled}, "
            f"api_url={self.api_url if self.enabled else 'N/A'})"
        )
