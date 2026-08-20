"""
Bot Service - اعتبارسنجی و مدیریت ربات‌ها
"""
import logging
from typing import Dict, Any

from .telegram_client import TelegramClient
from .exceptions import (
    BotValidationError,
    InvalidTokenError,
    TelegramRateLimitError,
    NetworkTimeoutError,
    TelegramAPIError
)

logger = logging.getLogger(__name__)


async def validate_bot_token(token: str) -> Dict[str, Any]:
    """
    اعتبارسنجی توکن ربات با استفاده از Telegram Bot API
    
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
        BotValidationError: اگر توکن نامعتبر باشد یا خطایی رخ دهد
        InvalidTokenError: توکن نامعتبر (401)
        TelegramRateLimitError: محدودیت تعداد درخواست (429)
        NetworkTimeoutError: زمان‌توقف شبکه
    """
    # اعتبارسنجی ساده فرمت توکن (قبل از درخواست API)
    _validate_token_format(token)
    
    # ساخت کلاینت تلگرام
    client = TelegramClient(timeout=15)
    
    try:
        # فراخوانی getMe از طریق کلاینت
        bot_info = await client.get_me(token)
        
        # بررسی اینکه واقعاً یک ربات است
        if not bot_info.get('is_bot', False):
            logger.warning(f"توکن متعلق به یک ربات نیست: {bot_info.get('id')}")
            raise BotValidationError("این توکن متعلق به یک حساب کاربری است، نه ربات!")
        
        # استخراج اطلاعات مورد نیاز
        result = {
            'id': bot_info.get('id'),
            'username': bot_info.get('username'),
            'first_name': bot_info.get('first_name'),
            'is_bot': bot_info.get('is_bot', False)
        }
        
        logger.info(f"توکن معتبر است. ربات: @{result['username']} (ID: {result['id']})")
        return result
    
    except (InvalidTokenError, TelegramRateLimitError, NetworkTimeoutError) as e:
        # این خطاها مستقیماً به handler ارسال می‌شوند
        raise
    
    except TelegramAPIError as e:
        # خطاهای عمومی API به BotValidationError تبدیل می‌شوند
        logger.error(f"خطای API در اعتبارسنجی: {e}")
        raise BotValidationError(str(e))
    
    except Exception as e:
        # خطاهای غیرمنتظره
        logger.error(f"خطای غیرمنتظره در اعتبارسنجی توکن: {e}", exc_info=True)
        raise BotValidationError(f"خطای غیرمنتظره: {str(e)}")


def _validate_token_format(token: str) -> None:
    """
    اعتبارسنجی ساده فرمت توکن (قبل از درخواست API)
    
    Args:
        token: توکن ربات
        
    Raises:
        BotValidationError: اگر فرمت توکن نامعتبر باشد
    """
    if not token or not isinstance(token, str):
        raise BotValidationError("توکن نمی‌تواند خالی باشد")
    
    if ':' not in token:
        raise BotValidationError("فرمت توکن نامعتبر است. توکن باید شامل ':' باشد")
    
    parts = token.split(':')
    if len(parts) != 2:
        raise BotValidationError("فرمت توکن نامعتبر است. توکن باید دقیقاً یک ':' داشته باشد")
    
    # بخش اول باید عدد باشد (Bot ID)
    if not parts[0].isdigit():
        raise BotValidationError("بخش اول توکن (Bot ID) باید عدد باشد")
    
    # بخش دوم باید حداقل 30 کاراکتر باشد
    if len(parts[1]) < 30:
        raise BotValidationError("بخش دوم توکن کوتاه است (حداقل 30 کاراکتر)")
    
    logger.debug("فرمت توکن معتبر است")
