"""
Exception های سفارشی برای مدیریت خطاهای تلگرام
"""


class TelegramAPIError(Exception):
    """خطای عمومی API تلگرام"""
    
    def __init__(self, message: str, status_code: int = None, error_code: int = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)
    
    def __str__(self):
        if self.error_code:
            return f"Telegram API Error [{self.error_code}]: {self.message}"
        return f"Telegram API Error: {self.message}"


class InvalidTokenError(TelegramAPIError):
    """خطای توکن نامعتبر (401 Unauthorized)"""
    
    def __init__(self, message: str = "توکن ربات نامعتبر است"):
        super().__init__(message, status_code=401, error_code=401)


class TelegramRateLimitError(TelegramAPIError):
    """خطای محدودیت تعداد درخواست (429 Too Many Requests)"""
    
    def __init__(self, message: str = "تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً کمی صبر کنید.", retry_after: int = None):
        super().__init__(message, status_code=429, error_code=429)
        self.retry_after = retry_after
    
    def __str__(self):
        if self.retry_after:
            return f"{self.message} (تلاش مجدد بعد از {self.retry_after} ثانیه)"
        return self.message


class NetworkTimeoutError(TelegramAPIError):
    """خطای زمان‌توقف شبکه (Timeout)"""
    
    def __init__(self, message: str = "زمان اتصال به سرور تلگرام به پایان رسید. لطفاً دوباره تلاش کنید."):
        super().__init__(message, status_code=None, error_code=None)


class BotValidationError(TelegramAPIError):
    """خطای اعتبارسنجی ربات (خطای عمومی برای validation)"""
    
    def __init__(self, message: str):
        super().__init__(message)


class TokenAlreadyRegisteredError(BotValidationError):
    """
    خطای توکن تکراری - زمانی که ربات قبلاً ثبت شده است
    
    این خطا برای مدیریت Race Condition و جلوگیری از ثبت مجدد یک ربات استفاده می‌شود
    """
    
    def __init__(self, bot_id: int, username: str = None):
        self.bot_id = bot_id
        self.username = username
        
        if username:
            message = f"این ربات (@{username}) قبلاً ثبت شده است"
        else:
            message = f"این ربات (ID: {bot_id}) قبلاً ثبت شده است"
        
        super().__init__(message)
