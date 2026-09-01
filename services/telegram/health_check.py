"""
Health Check Service for Local Bot API Server

سرویس بررسی سلامت Local Bot API Server
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .local_api_client import LocalBotAPIClient
from .local_api_config import LocalBotAPIConfig
from services.exceptions import TelegramAPIError, InvalidTokenError, NetworkTimeoutError

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """
    نتیجه health check
    
    Attributes:
        success: آیا health check موفق بود
        message: پیام توضیحی
        server_reachable: آیا سرور قابل دسترسی است
        api_response_valid: آیا پاسخ API معتبر است
        get_me_works: آیا getMe با توکن تست کار می‌کند
        error_type: نوع خطا (اگر وجود داشته باشد)
        api_url: URL سرور بررسی شده
    """
    
    success: bool
    message: str
    server_reachable: bool
    api_response_valid: bool
    get_me_works: bool
    error_type: Optional[str]
    api_url: str
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary برای logging یا API response"""
        return {
            'success': self.success,
            'message': self.message,
            'server_reachable': self.server_reachable,
            'api_response_valid': self.api_response_valid,
            'get_me_works': self.get_me_works,
            'error_type': self.error_type,
            'api_url': self.api_url
        }


class HealthCheckService:
    """
    سرویس بررسی سلامت Local Bot API Server
    
    این سرویس برای تست و تأیید عملکرد Local API Server استفاده می‌شود.
    
    مراحل Health Check:
        1. بررسی دسترسی به سرور (server reachable)
        2. بررسی معتبر بودن پاسخ HTTP (API response valid)
        3. تست getMe با یک توکن تست (getMe works)
        4. بررسی parse شدن پاسخ Telegram API (response parseable)
    
    Security:
        - توکن تست هیچ‌جا لاگ نمی‌شود
        - فقط نتیجه موفق/ناموفق لاگ می‌شود
        - خطاها به صورت امن sanitize می‌شوند
    
    Usage:
        config = LocalBotAPIConfig.from_env()
        service = HealthCheckService(config)
        result = await service.check_health(test_token)
        
        if result.success:
            print("✅ Local API Server سالم است")
        else:
            print(f"❌ خطا: {result.message}")
    """
    
    def __init__(self, config: LocalBotAPIConfig):
        """
        Args:
            config: LocalBotAPIConfig instance
        """
        self.config = config
    
    async def check_health(self, test_token: str) -> HealthCheckResult:
        """
        بررسی سلامت Local Bot API Server با یک توکن تست
        
        این متد تمام مراحل health check را انجام می‌دهد:
        1. Server reachable
        2. HTTP response valid
        3. getMe works
        4. Telegram API response parseable
        
        Args:
            test_token: یک توکن ربات معتبر برای تست
                       ⚠️ این توکن باید از environment variable خوانده شود
                       ⚠️ هیچ‌جا لاگ نمی‌شود
        
        Returns:
            HealthCheckResult شامل نتایج تمام بررسی‌ها
            
        Security:
            - test_token هیچ‌جا لاگ نمی‌شود
            - فقط نتیجه موفق/ناموفق لاگ می‌شود
        
        Note:
            اگر Local API غیرفعال باشد، بلافاصله با خطا برمی‌گردد
        """
        # بررسی اینکه Local API فعال است
        if not self.config.enabled:
            return HealthCheckResult(
                success=False,
                message="Local Bot API غیرفعال است",
                server_reachable=False,
                api_response_valid=False,
                get_me_works=False,
                error_type="disabled",
                api_url="N/A"
            )
        
        api_url = self.config.api_url
        
        # بررسی اینکه test_token خالی نیست
        if not test_token or not isinstance(test_token, str):
            logger.error("❌ Health Check: توکن تست خالی یا نامعتبر است")
            return HealthCheckResult(
                success=False,
                message="توکن تست خالی یا نامعتبر است",
                server_reachable=False,
                api_response_valid=False,
                get_me_works=False,
                error_type="invalid_test_token",
                api_url=api_url
            )
        
        logger.info(f"🔍 شروع Health Check برای Local API: {api_url}")
        
        try:
            # ساخت کلاینت
            client = LocalBotAPIClient(self.config, timeout=10)
            
            # تست getMe
            bot_info = await client.get_me(test_token)
            
            # بررسی اینکه پاسخ شامل فیلدهای ضروری است
            if not bot_info.get('id'):
                logger.error("❌ Health Check: پاسخ getMe فاقد id است")
                return HealthCheckResult(
                    success=False,
                    message="پاسخ API معتبر نیست (فاقد bot id)",
                    server_reachable=True,
                    api_response_valid=False,
                    get_me_works=False,
                    error_type="invalid_response",
                    api_url=api_url
                )
            
            # بررسی اینکه واقعاً یک ربات است
            if not bot_info.get('is_bot', False):
                logger.warning("⚠️ Health Check: توکن متعلق به یک user است، نه bot")
                return HealthCheckResult(
                    success=False,
                    message="توکن تست متعلق به یک حساب کاربری است، نه ربات",
                    server_reachable=True,
                    api_response_valid=True,
                    get_me_works=False,
                    error_type="not_a_bot",
                    api_url=api_url
                )
            
            # همه چیز موفق
            bot_username = bot_info.get('username', 'نامشخص')
            logger.info(
                f"✅ Health Check موفق: Local API سالم است "
                f"(test bot: @{bot_username})"
            )
            
            return HealthCheckResult(
                success=True,
                message=f"Local API Server سالم است (test bot: @{bot_username})",
                server_reachable=True,
                api_response_valid=True,
                get_me_works=True,
                error_type=None,
                api_url=api_url
            )
        
        except InvalidTokenError as e:
            # توکن تست نامعتبر است
            logger.warning(f"⚠️ Health Check: توکن تست نامعتبر است")
            return HealthCheckResult(
                success=False,
                message="توکن تست نامعتبر است",
                server_reachable=True,
                api_response_valid=True,
                get_me_works=False,
                error_type="invalid_token",
                api_url=api_url
            )
        
        except NetworkTimeoutError as e:
            # Timeout — سرور خیلی کند پاسخ می‌دهد یا در دسترس نیست
            logger.error(f"❌ Health Check: Timeout در اتصال به Local API")
            return HealthCheckResult(
                success=False,
                message=f"Timeout در اتصال به Local API ({api_url})",
                server_reachable=False,
                api_response_valid=False,
                get_me_works=False,
                error_type="timeout",
                api_url=api_url
            )
        
        except TelegramAPIError as e:
            # خطای عمومی API
            # این معمولاً یعنی سرور در حال اجراست ولی مشکلی وجود دارد
            logger.error(f"❌ Health Check: خطای API — {type(e).__name__}")
            
            # اگر پیام خطا شامل "connection" باشد، یعنی سرور در دسترس نیست
            if "connection" in str(e).lower() or "connect" in str(e).lower():
                server_reachable = False
            else:
                server_reachable = True
            
            return HealthCheckResult(
                success=False,
                message=f"خطای API: {e.message}",
                server_reachable=server_reachable,
                api_response_valid=False,
                get_me_works=False,
                error_type="api_error",
                api_url=api_url
            )
        
        except ValueError as e:
            # خطای config (مثلاً config غیرفعال)
            logger.error(f"❌ Health Check: خطای تنظیمات — {str(e)}")
            return HealthCheckResult(
                success=False,
                message=str(e),
                server_reachable=False,
                api_response_valid=False,
                get_me_works=False,
                error_type="config_error",
                api_url=api_url
            )
        
        except Exception as e:
            # خطای غیرمنتظره
            logger.error(
                f"❌ Health Check: خطای غیرمنتظره — {type(e).__name__}",
                exc_info=True
            )
            return HealthCheckResult(
                success=False,
                message=f"خطای غیرمنتظره: {type(e).__name__}",
                server_reachable=False,
                api_response_valid=False,
                get_me_works=False,
                error_type="unexpected_error",
                api_url=api_url
            )
    
    async def quick_check(self, test_token: str) -> bool:
        """
        بررسی سریع سلامت (فقط True/False)
        
        این متد برای استفاده در startup یا monitoring ساده است.
        
        Args:
            test_token: توکن ربات برای تست
            
        Returns:
            True اگر Local API سالم باشد، False در غیر این صورت
        """
        result = await self.check_health(test_token)
        return result.success
