"""
Config Service برای AI Image Bot

مدیریت تنظیمات و پیکربندی AI Image Bot
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from .models import ImageStyle, AspectRatio, Quality

logger = logging.getLogger(__name__)


@dataclass
class AIConfig:
    """تنظیمات AI"""
    provider: str = "mock"  # mock, openai, stability, etc.
    model: str = "default"
    api_configured: bool = False
    
    # Default Settings
    default_style: ImageStyle = ImageStyle.NONE
    default_ratio: AspectRatio = AspectRatio.SQUARE
    default_quality: Quality = Quality.STANDARD
    default_count: int = 1
    
    # Prompt Settings
    system_prompt: str = ""
    prompt_prefix: str = ""
    prompt_suffix: str = ""
    negative_prompt: str = ""
    max_prompt_length: int = 500
    min_prompt_length: int = 3
    
    # Generation Limits
    daily_limit_per_user: int = 10
    max_images_per_request: int = 4
    rate_limit_seconds: int = 30
    user_cooldown_seconds: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        data = asdict(self)
        # تبدیل Enums به string
        data['default_style'] = self.default_style.value
        data['default_ratio'] = self.default_ratio.value
        data['default_quality'] = self.default_quality.value
        return data


@dataclass
class StyleConfig:
    """تنظیمات یک Style"""
    key: str
    name: str
    description: str
    prompt_modifier: str = ""
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return asdict(self)


class MaintenanceMode(str, Enum):
    """وضعیت Maintenance"""
    OFF = "off"
    ON = "on"
    SCHEDULED = "scheduled"


@dataclass
class MaintenanceConfig:
    """تنظیمات Maintenance Mode"""
    mode: MaintenanceMode = MaintenanceMode.OFF
    message: str = "سیستم در حال تعمیر و نگهداری است. لطفاً بعداً مراجعه کنید."
    scheduled_start: Optional[str] = None  # ISO format
    scheduled_end: Optional[str] = None  # ISO format
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return {
            'mode': self.mode.value,
            'message': self.message,
            'scheduled_start': self.scheduled_start,
            'scheduled_end': self.scheduled_end
        }


class ConfigService:
    """
    سرویس مدیریت تنظیمات AI Image Bot
    
    ⚠️ فعلاً تنظیمات در حافظه نگهداری می‌شوند
    در آینده به Database متصل خواهد شد
    """
    
    def __init__(self):
        """مقداردهی اولیه"""
        self._ai_config = AIConfig()
        self._maintenance_config = MaintenanceConfig()
        self._styles_config: Dict[str, StyleConfig] = self._init_default_styles()
    
    def _init_default_styles(self) -> Dict[str, StyleConfig]:
        """مقداردهی Styles پیش‌فرض"""
        return {
            'realistic': StyleConfig(
                key='realistic',
                name='واقع‌گرایانه',
                description='تصویر واقع‌گرایانه و دقیق',
                prompt_modifier='realistic, photorealistic, highly detailed',
                enabled=True
            ),
            'cinematic': StyleConfig(
                key='cinematic',
                name='سینمایی',
                description='حس و حال سینمایی',
                prompt_modifier='cinematic, dramatic lighting, movie style',
                enabled=True
            ),
            'anime': StyleConfig(
                key='anime',
                name='انیمه',
                description='سبک انیمه و مانگا',
                prompt_modifier='anime style, manga, vibrant colors',
                enabled=True
            ),
            'digital_art': StyleConfig(
                key='digital_art',
                name='هنر دیجیتال',
                description='هنر دیجیتال مدرن',
                prompt_modifier='digital art, concept art, artstation',
                enabled=True
            ),
            'photography': StyleConfig(
                key='photography',
                name='عکاسی',
                description='سبک عکاسی حرفه‌ای',
                prompt_modifier='photography, professional photo, high quality',
                enabled=True
            )
        }
    
    # ========== AI Config ==========
    
    def get_ai_config(self) -> AIConfig:
        """دریافت تنظیمات AI"""
        return self._ai_config
    
    async def update_ai_config(self, **kwargs) -> bool:
        """
        به‌روزرسانی تنظیمات AI
        
        Args:
            **kwargs: تنظیمات جدید
            
        Returns:
            True اگر موفق بود
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self._ai_config, key):
                    # تبدیل string به Enum در صورت نیاز
                    if key == 'default_style' and isinstance(value, str):
                        value = ImageStyle(value)
                    elif key == 'default_ratio' and isinstance(value, str):
                        value = AspectRatio(value)
                    elif key == 'default_quality' and isinstance(value, str):
                        value = Quality(value)
                    
                    setattr(self._ai_config, key, value)
            
            logger.info(f"AI config updated: {kwargs}")
            # TODO: ذخیره در Database
            return True
        except Exception as e:
            logger.error(f"Error updating AI config: {e}")
            return False
    
    def get_provider_status(self) -> Dict[str, Any]:
        """
        دریافت وضعیت Provider
        
        Returns:
            اطلاعات Provider
        """
        return {
            'provider': self._ai_config.provider,
            'model': self._ai_config.model,
            'api_configured': self._ai_config.api_configured,
            'status': 'active' if self._ai_config.api_configured else 'not_configured'
        }
    
    # ========== Styles Config ==========
    
    def get_all_styles(self) -> List[StyleConfig]:
        """دریافت تمام Styles"""
        return list(self._styles_config.values())
    
    def get_enabled_styles(self) -> List[StyleConfig]:
        """دریافت Styles فعال"""
        return [s for s in self._styles_config.values() if s.enabled]
    
    def get_style(self, key: str) -> Optional[StyleConfig]:
        """دریافت یک Style"""
        return self._styles_config.get(key)
    
    async def update_style(
        self,
        key: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prompt_modifier: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> bool:
        """
        به‌روزرسانی یک Style
        
        Args:
            key: کلید Style
            name: نام جدید
            description: توضیحات جدید
            prompt_modifier: Modifier جدید
            enabled: فعال/غیرفعال
            
        Returns:
            True اگر موفق بود
        """
        style = self._styles_config.get(key)
        if not style:
            logger.warning(f"Style not found: {key}")
            return False
        
        try:
            if name is not None:
                style.name = name
            if description is not None:
                style.description = description
            if prompt_modifier is not None:
                style.prompt_modifier = prompt_modifier
            if enabled is not None:
                style.enabled = enabled
            
            logger.info(f"Style updated: {key}")
            # TODO: ذخیره در Database
            return True
        except Exception as e:
            logger.error(f"Error updating style {key}: {e}")
            return False
    
    # ========== Maintenance Config ==========
    
    def get_maintenance_config(self) -> MaintenanceConfig:
        """دریافت تنظیمات Maintenance"""
        return self._maintenance_config
    
    def is_maintenance_active(self) -> bool:
        """بررسی اینکه Maintenance فعال است"""
        return self._maintenance_config.mode == MaintenanceMode.ON
    
    async def set_maintenance_mode(
        self,
        mode: MaintenanceMode,
        message: Optional[str] = None
    ) -> bool:
        """
        تنظیم Maintenance Mode
        
        Args:
            mode: وضعیت جدید
            message: پیام سفارشی
            
        Returns:
            True اگر موفق بود
        """
        try:
            self._maintenance_config.mode = mode
            if message:
                self._maintenance_config.message = message
            
            logger.info(f"Maintenance mode set to: {mode.value}")
            # TODO: ذخیره در Database
            return True
        except Exception as e:
            logger.error(f"Error setting maintenance mode: {e}")
            return False
    
    # ========== Generation Limits ==========
    
    def get_generation_limits(self) -> Dict[str, int]:
        """دریافت محدودیت‌های Generation"""
        return {
            'daily_limit_per_user': self._ai_config.daily_limit_per_user,
            'max_images_per_request': self._ai_config.max_images_per_request,
            'rate_limit_seconds': self._ai_config.rate_limit_seconds,
            'user_cooldown_seconds': self._ai_config.user_cooldown_seconds
        }
    
    async def update_generation_limits(self, **kwargs) -> bool:
        """
        به‌روزرسانی محدودیت‌های Generation
        
        Args:
            **kwargs: محدودیت‌های جدید
            
        Returns:
            True اگر موفق بود
        """
        try:
            valid_keys = [
                'daily_limit_per_user',
                'max_images_per_request',
                'rate_limit_seconds',
                'user_cooldown_seconds'
            ]
            
            for key, value in kwargs.items():
                if key in valid_keys and isinstance(value, int) and value > 0:
                    setattr(self._ai_config, key, value)
            
            logger.info(f"Generation limits updated: {kwargs}")
            # TODO: ذخیره در Database
            return True
        except Exception as e:
            logger.error(f"Error updating generation limits: {e}")
            return False
