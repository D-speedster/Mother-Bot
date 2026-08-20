"""
Bot Service - اعتبارسنجی و مدیریت ربات‌ها
"""
import logging
from typing import Dict, Any

from .telegram_client import TelegramClient
from .encryption import TokenEncryptionService
from .exceptions import (
    BotValidationError,
    InvalidTokenError,
    TelegramRateLimitError,
    NetworkTimeoutError,
    TelegramAPIError,
    TokenAlreadyRegisteredError
)

logger = logging.getLogger(__name__)


class BotService:
    """
    سرویس مدیریت ربات‌ها
    
    معماری لایه‌بندی: Handler -> BotService -> Repository -> Database
    
    مسئولیت‌ها:
    - اعتبارسنجی توکن از طریق Telegram API
    - رمزنگاری توکن قبل از ذخیره
    - مدیریت منطق کسب‌وکار ربات‌ها
    """
    
    def __init__(self, repository, encryption_service: TokenEncryptionService):
        """
        Args:
            repository: BotRepository instance
            encryption_service: TokenEncryptionService instance
        """
        self.repository = repository
        self.encryption = encryption_service
    
    async def register_bot(
        self,
        owner_id: int,
        token: str,
        bot_type: str
    ) -> Dict[str, Any]:
        """
        ثبت ربات جدید
        
        فرآیند:
        1. اعتبارسنجی توکن از طریق Telegram API
        2. بررسی عدم وجود قبلی در دیتابیس
        3. رمزنگاری توکن
        4. ذخیره در دیتابیس
        
        Args:
            owner_id: ID کاربر تلگرام (صاحب ربات)
            token: توکن ربات (خام)
            bot_type: نوع ربات
            
        Returns:
            Dict شامل:
            {
                'bot_id': int (ID در دیتابیس),
                'telegram_id': int,
                'username': str,
                'first_name': str,
                'bot_type': str
            }
            
        Raises:
            BotValidationError: اگر توکن نامعتبر باشد
            TokenAlreadyRegisteredError: اگر ربات قبلاً ثبت شده باشد
        """
        # گام 1: اعتبارسنجی توکن از طریق getMe
        bot_info = await validate_bot_token(token)
        
        # گام 2: بررسی عدم وجود قبلی
        existing_bot = await self.repository.get_bot_by_telegram_id(bot_info['id'])
        if existing_bot:
            logger.warning(
                f"⚠️ تلاش برای ثبت مجدد ربات موجود: @{bot_info['username']} "
                f"توسط کاربر {owner_id}"
            )
            raise TokenAlreadyRegisteredError(
                bot_id=bot_info['id'],
                username=bot_info['username']
            )
        
        # گام 3: رمزنگاری توکن
        token_encrypted = self.encryption.encrypt(token)
        
        # گام 4: ذخیره در دیتابیس
        try:
            bot_id = await self.repository.create_bot(
                owner_id=owner_id,
                bot_telegram_id=bot_info['id'],
                username=bot_info.get('username'),
                first_name=bot_info.get('first_name'),
                bot_type=bot_type,
                token_encrypted=token_encrypted,
                status='active'
            )
            
            logger.info(
                f"✅ ربات با موفقیت ثبت شد: @{bot_info['username']} "
                f"(DB_ID={bot_id}, TG_ID={bot_info['id']}) توسط کاربر {owner_id}"
            )
            
            return {
                'bot_id': bot_id,
                'telegram_id': bot_info['id'],
                'username': bot_info.get('username'),
                'first_name': bot_info.get('first_name'),
                'bot_type': bot_type
            }
        
        except TokenAlreadyRegisteredError:
            # Race Condition: ربات در همین لحظه توسط فرآیند دیگری ثبت شده
            logger.warning(
                f"⚠️ Race Condition: ربات @{bot_info['username']} "
                f"در حین ثبت توسط فرآیند دیگری ایجاد شد"
            )
            raise
    
    async def get_user_bots(self, owner_id: int) -> list:
        """
        دریافت لیست ربات‌های یک کاربر
        
        Args:
            owner_id: ID کاربر تلگرام
            
        Returns:
            لیست ربات‌ها (بدون token_encrypted برای امنیت)
            
        Security:
        - token_encrypted از repository برنگردانده می‌شود
        - Repository قبلاً آن را حذف کرده است
        """
        bots = await self.repository.get_bots_by_owner(owner_id)
        
        # Repository قبلاً token_encrypted را حذف کرده، فقط format می‌کنیم
        return [
            {
                'bot_id': bot['id'],
                'telegram_id': bot['bot_telegram_id'],
                'username': bot['username'],
                'first_name': bot['first_name'],
                'bot_type': bot['bot_type'],
                'status': bot['status'],
                'created_at': bot['created_at']
            }
            for bot in bots
        ]
    
    async def get_bot_token(
        self,
        bot_id: int,
        owner_id: int
    ) -> str:
        """
        دریافت توکن رمزگشایی‌شده یک ربات (با بررسی ownership)
        
        Args:
            bot_id: ID رکورد در دیتابیس
            owner_id: ID کاربر تلگرام (برای تأیید مالکیت)
            
        Returns:
            توکن خام (رمزگشایی‌شده)
            
        Raises:
            ValueError: اگر ربات یافت نشود یا متعلق به کاربر نباشد
            
        Security:
        - بررسی owner_id برای جلوگیری از دسترسی غیرمجاز
        - فقط صاحب ربات می‌تواند توکن را دریافت کند
        """
        # دریافت توکن رمزشده با بررسی ownership
        token_encrypted = await self.repository.get_bot_token_encrypted(
            bot_id, owner_id
        )
        
        if not token_encrypted:
            raise ValueError(
                f"ربات با ID {bot_id} یافت نشد یا متعلق به این کاربر نیست"
            )
        
        # رمزگشایی توکن
        token = self.encryption.decrypt(token_encrypted)
        return token
    
    async def delete_bot(
        self,
        bot_id: int,
        owner_id: int
    ) -> bool:
        """
        حذف ربات (با بررسی ownership)
        
        Args:
            bot_id: ID رکورد در دیتابیس
            owner_id: ID کاربر تلگرام (برای تأیید مالکیت)
            
        Returns:
            True اگر حذف موفق باشد
            
        Raises:
            ValueError: اگر ربات یافت نشود یا متعلق به کاربر نباشد
            
        Security:
        - بررسی owner_id برای جلوگیری از حذف غیرمجاز
        """
        success = await self.repository.delete_bot(bot_id, owner_id)
        
        if not success:
            raise ValueError(
                f"ربات با ID {bot_id} یافت نشد یا متعلق به این کاربر نیست"
            )
        
        return True


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
