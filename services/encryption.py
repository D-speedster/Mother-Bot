"""
سرویس رمزنگاری - مدیریت امن توکن‌ها
"""
import os
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class TokenEncryptionService:
    """
    سرویس رمزنگاری و رمزگشایی توکن‌های ربات با استفاده از Fernet (AES-128)
    
    Features:
    - رمزنگاری متقارن با Fernet
    - استفاده از کلید محیطی (FERNET_KEY)
    - عدم ذخیره کلید در کد یا دیتابیس
    
    Security Notes:
    - کلید FERNET_KEY باید در .env باشد و به Git commit نشود
    - برای تولید کلید جدید: Fernet.generate_key().decode()
    
    ⚠️ IMPORTANT - Key Rotation:
    اگر کلید FERNET_KEY تغییر کند، تمام توکن‌های قدیمی در دیتابیس
    غیرقابل رمزگشایی می‌شوند.
    
    راه‌حل‌های آینده:
    1. افزودن فیلد key_version به جدول bots
    2. نگهداری چند کلید همزمان (active + retired keys)
    3. Migration تدریجی توکن‌ها به کلید جدید
    
    این موارد در roadmap آینده قرار دارند.
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Args:
            encryption_key: کلید رمزنگاری (base64). اگر None باشد از متغیر محیطی خوانده می‌شود
            
        Raises:
            ValueError: اگر کلید رمزنگاری موجود نباشد یا نامعتبر باشد
        """
        # خواندن کلید از متغیر محیطی یا پارامتر
        key = encryption_key or os.getenv('FERNET_KEY')
        
        if not key:
            raise ValueError(
                "🔴 خطا: کلید رمزنگاری (FERNET_KEY) یافت نشد!\n"
                "لطفاً در فایل .env متغیر FERNET_KEY را تنظیم کنید.\n"
                "برای تولید کلید جدید از Python استفاده کنید:\n"
                "  from cryptography.fernet import Fernet\n"
                "  print(Fernet.generate_key().decode())"
            )
        
        try:
            # تبدیل رشته به bytes و ساخت Fernet instance
            key_bytes = key.encode() if isinstance(key, str) else key
            self._fernet = Fernet(key_bytes)
            logger.info("✅ سرویس رمزنگاری با موفقیت راه‌اندازی شد")
            
        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی سرویس رمزنگاری: {e}")
            raise ValueError(f"کلید رمزنگاری نامعتبر است: {e}")
    
    def encrypt(self, plaintext: str) -> str:
        """
        رمزنگاری متن (توکن)
        
        Args:
            plaintext: متن خام (توکن)
            
        Returns:
            متن رمزشده (base64)
            
        Raises:
            ValueError: اگر ورودی خالی یا نامعتبر باشد
            
        Security:
        - متن خام هرگز در لاگ ثبت نمی‌شود
        - فقط وضعیت موفق/ناموفق log می‌شود
        """
        if not plaintext:
            raise ValueError("متن برای رمزنگاری نمی‌تواند خالی باشد")
        
        try:
            # تبدیل به bytes، رمزنگاری، و بازگشت به string
            plaintext_bytes = plaintext.encode('utf-8')
            encrypted_bytes = self._fernet.encrypt(plaintext_bytes)
            encrypted_str = encrypted_bytes.decode('utf-8')
            
            # ⚠️ SECURITY: هرگز plaintext را log نمی‌کنیم
            logger.debug("✅ رمزنگاری موفق")
            return encrypted_str
            
        except Exception as e:
            # ⚠️ SECURITY: از str(e) استفاده نمی‌کنیم، فقط نوع خطا
            logger.error(f"❌ خطا در رمزنگاری: {type(e).__name__}", exc_info=True)
            raise ValueError(f"خطا در رمزنگاری")
    
    def decrypt(self, encrypted: str) -> str:
        """
        رمزگشایی متن (توکن)
        
        Args:
            encrypted: متن رمزشده (base64)
            
        Returns:
            متن خام (توکن)
            
        Raises:
            ValueError: اگر رمزگشایی ناموفق باشد (کلید اشتباه یا داده خراب)
            
        Security:
        - متن رمزگشایی‌شده هرگز در لاگ ثبت نمی‌شود
        - InvalidToken به طور جداگانه catch می‌شود
        
        ⚠️ Timing Attack:
        Fernet خود در برابر timing attack مقاوم است، اما اگر
        چندین کلید را check کنیم (key rotation)، باید مراقب باشیم
        که زمان پاسخ یکسان باشد.
        """
        if not encrypted:
            raise ValueError("متن رمزشده نمی‌تواند خالی باشد")
        
        try:
            # تبدیل به bytes، رمزگشایی، و بازگشت به string
            encrypted_bytes = encrypted.encode('utf-8')
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            decrypted_str = decrypted_bytes.decode('utf-8')
            
            # ⚠️ SECURITY: هرگز decrypted text را log نمی‌کنیم
            logger.debug("✅ رمزگشایی موفق")
            return decrypted_str
            
        except InvalidToken:
            # کلید اشتباه یا داده خراب
            logger.error("❌ رمزگشایی ناموفق: InvalidToken")
            raise ValueError(
                "رمزگشایی ناموفق. ممکن است کلید رمزنگاری تغییر کرده یا داده خراب شده باشد"
            )
        except Exception as e:
            # سایر خطاها
            # ⚠️ SECURITY: از str(e) استفاده نمی‌کنیم
            logger.error(f"❌ خطا در رمزگشایی: {type(e).__name__}", exc_info=True)
            raise ValueError(f"خطا در رمزگشایی")
    
    @staticmethod
    def generate_key() -> str:
        """
        تولید کلید رمزنگاری جدید
        
        Returns:
            کلید base64 برای استفاده در FERNET_KEY
            
        Usage:
            key = TokenEncryptionService.generate_key()
            print(f"FERNET_KEY={key}")
        """
        return Fernet.generate_key().decode()
