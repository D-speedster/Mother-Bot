"""
Local Bot API Client

کلاینت HTTP برای ارتباط با Telegram Local Bot API Server
این کلاینت از همان interface TelegramClient استفاده می‌کند ولی به Local Server متصل می‌شود
"""
import asyncio
import aiohttp
import logging
from typing import Dict, Any

from services.exceptions import (
    TelegramAPIError,
    InvalidTokenError,
    TelegramRateLimitError,
    NetworkTimeoutError
)
from .local_api_config import LocalBotAPIConfig

logger = logging.getLogger(__name__)


class LocalBotAPIClient:
    """
    کلاینت HTTP برای ارتباط با Telegram Local Bot API Server
    
    این کلاینت interface مشابه TelegramClient دارد ولی به Local Server
    متصل می‌شود به جای https://api.telegram.org
    
    مسئولیت: فقط ارتباط HTTP با Local Bot API Server
    
    Security:
        - توکن‌ها هیچ‌جا لاگ نمی‌شوند
        - URL‌ها به صورت امن ساخته می‌شوند
        - خطاها به صورت safe sanitize می‌شوند
    
    Usage:
        config = LocalBotAPIConfig.from_env()
        if config.enabled:
            client = LocalBotAPIClient(config)
            bot_info = await client.get_me(token)
    """
    
    def __init__(self, config: LocalBotAPIConfig, timeout: int = 15):
        """
        Args:
            config: LocalBotAPIConfig instance
            timeout: زمان timeout به ثانیه (پیش‌فرض: 15 ثانیه)
            
        Raises:
            ValueError: اگر config غیرفعال باشد
        """
        if not config.enabled:
            raise ValueError(
                "نمی‌توان LocalBotAPIClient با config غیرفعال ساخت. "
                "لطفاً TELEGRAM_LOCAL_API_ENABLED را فعال کنید."
            )
        
        self.config = config
        self.timeout = aiohttp.ClientTimeout(
            total=timeout,
            connect=5,   # حداکثر 5 ثانیه برای برقراری اتصال
            sock_read=10  # حداکثر 10 ثانیه برای خواندن پاسخ
        )
    
    async def get_me(self, token: str) -> Dict[str, Any]:
        """
        فراخوانی متد getMe از Local Bot API
        
        این متد همان interface TelegramClient.get_me را دارد ولی
        به Local Server متصل می‌شود.
        
        Args:
            token: توکن ربات تلگرام
            
        Returns:
            Dict شامل اطلاعات ربات:
            {
                'id': int,
                'username': str,
                'first_name': str,
                'is_bot': bool
            }
            
        Raises:
            InvalidTokenError: توکن نامعتبر (401)
            TelegramRateLimitError: محدودیت تعداد درخواست (429)
            NetworkTimeoutError: زمان‌توقف شبکه
            TelegramAPIError: سایر خطاهای API
            
        Security:
            - توکن هیچ‌جا لاگ نمی‌شود
            - فقط masked token در لاگ ظاهر می‌شود
        """
        # Masking توکن برای لاگ‌ها
        masked_token = f"{token[:8]}...[MASKED]" if len(token) > 8 else "[MASKED]"
        
        # ساخت URL با استفاده از config
        url = f"{self.config.get_bot_api_url(token)}/getMe"
        
        # ⚠️ SECURITY: URL را لاگ نمی‌کنیم (شامل token است)
        logger.debug(f"فراخوانی getMe از Local API برای bot [{masked_token}]")
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    data = await response.json()
                    
                    # بررسی پاسخ بر اساس status code
                    if response.status == 401:
                        # توکن نامعتبر
                        error_desc = data.get('description', 'Unauthorized')
                        logger.warning(
                            f"توکن نامعتبر در Local API [{masked_token}]: {error_desc}"
                        )
                        raise InvalidTokenError(f"توکن نامعتبر: {error_desc}")
                    
                    elif response.status == 429:
                        # محدودیت تعداد درخواست
                        retry_after = data.get('parameters', {}).get('retry_after')
                        logger.warning(
                            f"محدودیت rate limit در Local API [{masked_token}]. "
                            f"retry_after: {retry_after}"
                        )
                        raise TelegramRateLimitError(retry_after=retry_after)
                    
                    elif response.status >= 500:
                        # خطای سمت سرور
                        error_desc = data.get('description', 'Server Error')
                        logger.error(
                            f"خطای سرور Local API [{masked_token}] "
                            f"[{response.status}]: {error_desc}"
                        )
                        raise TelegramAPIError(
                            f"خطای سرور Local API: {error_desc}",
                            status_code=response.status
                        )
                    
                    elif response.status != 200:
                        # سایر خطاها
                        error_desc = data.get('description', 'Unknown Error')
                        logger.error(
                            f"خطای Local API [{masked_token}] "
                            f"[{response.status}]: {error_desc}"
                        )
                        raise TelegramAPIError(
                            error_desc,
                            status_code=response.status,
                            error_code=data.get('error_code')
                        )
                    
                    # بررسی فیلد ok
                    if not data.get('ok'):
                        error_desc = data.get('description', 'Unknown Error')
                        logger.error(
                            f"پاسخ نامعتبر از Local API [{masked_token}]: {error_desc}"
                        )
                        raise TelegramAPIError(error_desc)
                    
                    # موفق - برگرداندن result
                    result = data.get('result', {})
                    logger.info(
                        f"✅ getMe موفق از Local API: "
                        f"bot_id={result.get('id')}, username={result.get('username')}"
                    )
                    return result
        
        except aiohttp.ClientConnectionError as e:
            # خطای اتصال به Local Server
            # ⚠️ این معمولاً یعنی Local Server اجرا نمی‌شود
            logger.error(
                f"❌ خطای اتصال به Local API Server [{masked_token}]: "
                f"{type(e).__name__}\n"
                f"آیا Local Bot API Server در {self.config.api_url} اجرا می‌شود؟"
            )
            raise TelegramAPIError(
                f"خطا در اتصال به Local API Server ({self.config.api_url}). "
                f"لطفاً مطمئن شوید که سرور در حال اجراست."
            )
        
        except aiohttp.ServerTimeoutError:
            logger.error(
                f"⏱️ زمان‌توقف در ارتباط با Local API [{masked_token}]"
            )
            raise NetworkTimeoutError(
                f"زمان اتصال به Local API Server ({self.config.api_url}) "
                f"به پایان رسید."
            )
        
        except asyncio.TimeoutError:
            logger.error(
                f"⏱️ زمان‌توقف در ارتباط با Local API [{masked_token}]"
            )
            raise NetworkTimeoutError(
                f"زمان اتصال به Local API Server ({self.config.api_url}) "
                f"به پایان رسید."
            )
        
        except aiohttp.ClientError as e:
            # خطای کلاینت HTTP
            logger.error(
                f"❌ خطای HTTP Client در Local API [{masked_token}]: "
                f"{type(e).__name__}"
            )
            raise TelegramAPIError("خطا در ارتباط با Local API Server.")
        
        except (InvalidTokenError, TelegramRateLimitError, NetworkTimeoutError, TelegramAPIError):
            # این خطاها را مستقیماً raise می‌کنیم (قبلاً log شده‌اند)
            raise
        
        except Exception as e:
            # خطای غیرمنتظره
            # ⚠️ SECURITY: exc_info=True ولی str(e) در پیام نیست
            logger.error(
                f"❌ خطای غیرمنتظره در LocalBotAPIClient [{masked_token}]: "
                f"{type(e).__name__}",
                exc_info=True
            )
            raise TelegramAPIError("خطای غیرمنتظره در ارتباط با Local API Server.")
    
    async def get_file(self, token: str, file_id: str) -> Dict[str, Any]:
        """
        فراخوانی متد getFile از Local Bot API
        
        ⚠️ این متد برای File Transfer Bot در فاز بعدی استفاده می‌شود.
        در حالت Local API، file_path می‌تواند یک مسیر محلی باشد.
        
        Args:
            token: توکن ربات
            file_id: شناسه فایل در تلگرام
            
        Returns:
            Dict شامل اطلاعات فایل:
            {
                'file_id': str,
                'file_unique_id': str,
                'file_size': int,
                'file_path': str  # در Local API یک مسیر محلی است
            }
            
        Raises:
            TelegramAPIError: در صورت بروز خطا
            
        Note:
            این متد برای PoC آماده شده ولی هنوز استفاده نمی‌شود.
            File Transfer Bot در فاز بعدی از این متد استفاده خواهد کرد.
        """
        masked_token = f"{token[:8]}...[MASKED]" if len(token) > 8 else "[MASKED]"
        url = f"{self.config.get_bot_api_url(token)}/getFile"
        
        logger.debug(
            f"فراخوانی getFile از Local API برای bot [{masked_token}], "
            f"file_id={file_id}"
        )
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json={'file_id': file_id}) as response:
                    data = await response.json()
                    
                    if response.status != 200 or not data.get('ok'):
                        error_desc = data.get('description', 'Unknown Error')
                        logger.error(
                            f"خطای getFile در Local API [{masked_token}]: {error_desc}"
                        )
                        raise TelegramAPIError(
                            f"خطا در getFile: {error_desc}",
                            status_code=response.status
                        )
                    
                    result = data.get('result', {})
                    logger.info(
                        f"✅ getFile موفق از Local API: "
                        f"file_size={result.get('file_size')}, "
                        f"file_path={'[LOCAL_PATH]' if result.get('file_path') else 'N/A'}"
                    )
                    return result
        
        except Exception as e:
            logger.error(
                f"❌ خطا در getFile از Local API [{masked_token}]: "
                f"{type(e).__name__}",
                exc_info=True
            )
            raise TelegramAPIError(f"خطا در دریافت اطلاعات فایل از Local API")
