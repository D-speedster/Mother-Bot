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
        url = f"{self.BASE_URL}/bot{token}/getMe"
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    data = await response.json()
                    
                    # بررسی پاسخ بر اساس status code
                    if response.status == 401:
                        # توکن نامعتبر
                        error_desc = data.get('description', 'Unauthorized')
                        logger.warning(f"توکن نامعتبر: {error_desc}")
                        raise InvalidTokenError(f"توکن نامعتبر: {error_desc}")
                    
                    elif response.status == 429:
                        # محدودیت تعداد درخواست
                        retry_after = data.get('parameters', {}).get('retry_after')
                        logger.warning(f"محدودیت rate limit. retry_after: {retry_after}")
                        raise TelegramRateLimitError(retry_after=retry_after)
                    
                    elif response.status >= 500:
                        # خطای سمت سرور تلگرام
                        error_desc = data.get('description', 'Server Error')
                        logger.error(f"خطای سرور تلگرام [{response.status}]: {error_desc}")
                        raise TelegramAPIError(
                            f"خطای سرور تلگرام: {error_desc}",
                            status_code=response.status
                        )
                    
                    elif response.status != 200:
                        # سایر خطاها
                        error_desc = data.get('description', 'Unknown Error')
                        logger.error(f"خطای API تلگرام [{response.status}]: {error_desc}")
                        raise TelegramAPIError(
                            error_desc,
                            status_code=response.status,
                            error_code=data.get('error_code')
                        )
                    
                    # بررسی فیلد ok
                    if not data.get('ok'):
                        error_desc = data.get('description', 'Unknown Error')
                        logger.error(f"پاسخ نامعتبر از API: {error_desc}")
                        raise TelegramAPIError(error_desc)
                    
                    # موفق - برگرداندن result
                    result = data.get('result', {})
                    logger.info(f"getMe موفق: bot_id={result.get('id')}, username={result.get('username')}")
                    return result
        
        except aiohttp.ClientConnectionError as e:
            logger.error(f"خطای اتصال به سرور تلگرام: {e}")
            raise TelegramAPIError("خطا در اتصال به سرور تلگرام. لطفاً اتصال اینترنت خود را بررسی کنید.")
        
        except aiohttp.ServerTimeoutError as e:
            logger.error(f"زمان‌توقف در ارتباط با تلگرام: {e}")
            raise NetworkTimeoutError()
        
        except asyncio.TimeoutError as e:
            logger.error(f"زمان‌توقف در ارتباط با تلگرام: {e}")
            raise NetworkTimeoutError()
        
        except aiohttp.ClientError as e:
            logger.error(f"خطای کلاینت HTTP: {e}")
            raise TelegramAPIError(f"خطا در ارتباط با تلگرام: {str(e)}")
        
        except Exception as e:
            logger.error(f"خطای غیرمنتظره در TelegramClient: {e}", exc_info=True)
            raise TelegramAPIError(f"خطای غیرمنتظره: {str(e)}")
