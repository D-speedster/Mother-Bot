"""
Telegram HTTP Client - لایه ارتباط با Telegram Bot API
"""
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional

from .exceptions import (
    TelegramAPIError,
    InvalidTokenError,
    TelegramRateLimitError,
    NetworkTimeoutError
)

logger = logging.getLogger(__name__)


class TelegramClient:
    """
    کلاینت HTTP برای ارتباط با Telegram Bot API
    
    مسئولیت: فقط ارتباط HTTP با تلگرام
    """
    
    BASE_URL = "https://api.telegram.org"
    
    def __init__(self, timeout: int = 15):
        """
        Args:
            timeout: زمان timeout به ثانیه (پیش‌فرض: 15 ثانیه)
        """
        self.timeout = aiohttp.ClientTimeout(
            total=timeout,
            connect=5,   # حداکثر 5 ثانیه برای برقراری اتصال
            sock_read=10  # حداکثر 10 ثانیه برای خواندن پاسخ
        )
    
    async def get_me(self, token: str) -> Dict[str, Any]:
        """
        فراخوانی متد getMe از Telegram Bot API
        
        Args:
            token: توکن ربات تلگرام
            
        Returns:
            Dict شامل اطلاعات ربات
            
        Raises:
            InvalidTokenError: توکن نامعتبر (401)
            TelegramRateLimitError: محدودیت تعداد درخواست (429)
            NetworkTimeoutError: زمان‌توقف شبکه
            TelegramAPIError: سایر خطاهای API
        """
        # Masking توکن برای لاگ‌ها (جلوگیری از نشت در exception messages)
        masked_token = f"{token[:8]}...[MASKED]" if len(token) > 8 else "[MASKED]"
        url = f"{self.BASE_URL}/bot{token}/getMe"
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    data = await response.json()
                    
                    # بررسی پاسخ بر اساس status code
                    if response.status == 401:
                        # توکن نامعتبر
                        error_desc = data.get('description', 'Unauthorized')
                        logger.warning(f"توکن نامعتبر [{masked_token}]: {error_desc}")
                        raise InvalidTokenError(f"توکن نامعتبر: {error_desc}")
                    
                    elif response.status == 429:
                        # محدودیت تعداد درخواست
                        retry_after = data.get('parameters', {}).get('retry_after')
                        logger.warning(f"محدودیت rate limit [{masked_token}]. retry_after: {retry_after}")
                        raise TelegramRateLimitError(retry_after=retry_after)
                    
                    elif response.status >= 500:
                        # خطای سمت سرور تلگرام
                        error_desc = data.get('description', 'Server Error')
                        logger.error(f"خطای سرور تلگرام [{masked_token}] [{response.status}]: {error_desc}")
                        raise TelegramAPIError(
                            f"خطای سرور تلگرام: {error_desc}",
                            status_code=response.status
                        )
                    
                    elif response.status != 200:
                        # سایر خطاها
                        error_desc = data.get('description', 'Unknown Error')
                        logger.error(f"خطای API تلگرام [{masked_token}] [{response.status}]: {error_desc}")
                        raise TelegramAPIError(
                            error_desc,
                            status_code=response.status,
                            error_code=data.get('error_code')
                        )
                    
                    # بررسی فیلد ok
                    if not data.get('ok'):
                        error_desc = data.get('description', 'Unknown Error')
                        logger.error(f"پاسخ نامعتبر از API [{masked_token}]: {error_desc}")
                        raise TelegramAPIError(error_desc)
                    
                    # موفق - برگرداندن result
                    result = data.get('result', {})
                    logger.info(f"getMe موفق: bot_id={result.get('id')}, username={result.get('username')}")
                    return result
        
        except aiohttp.ClientConnectionError as e:
            # ⚠️ SECURITY: str(e) ممکن است URL (و توکن) را لو دهد
            # فقط نوع خطا را log می‌کنیم
            logger.error(f"خطای اتصال [{masked_token}]: {type(e).__name__}")
            raise TelegramAPIError("خطا در اتصال به سرور تلگرام. لطفاً اتصال اینترنت خود را بررسی کنید.")
        
        except aiohttp.ServerTimeoutError:
            # ⚠️ SECURITY: پیام خطا را log نمی‌کنیم
            logger.error(f"زمان‌توقف در ارتباط با تلگرام [{masked_token}]: ServerTimeoutError")
            raise NetworkTimeoutError()
        
        except asyncio.TimeoutError:
            # ⚠️ SECURITY: پیام خطا را log نمی‌کنیم
            logger.error(f"زمان‌توقف در ارتباط با تلگرام [{masked_token}]: TimeoutError")
            raise NetworkTimeoutError()
        
        except aiohttp.ClientError as e:
            # ⚠️ SECURITY: فقط نوع خطا را log می‌کنیم
            logger.error(f"خطای کلاینت HTTP [{masked_token}]: {type(e).__name__}")
            raise TelegramAPIError("خطا در ارتباط با تلگرام.")
        
        except (InvalidTokenError, TelegramRateLimitError, NetworkTimeoutError, TelegramAPIError):
            # این خطاها را مستقیماً raise می‌کنیم (قبلاً log شده‌اند)
            raise
        
        except Exception as e:
            # ⚠️ SECURITY: exc_info=True را نگه می‌داریم ولی str(e) را در پیام نمی‌گذاریم
            logger.error(
                f"خطای غیرمنتظره در TelegramClient [{masked_token}]: {type(e).__name__}",
                exc_info=True
            )
            raise TelegramAPIError("خطای غیرمنتظره در ارتباط با تلگرام.")
