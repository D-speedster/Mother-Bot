"""
Middleware برای کش کردن وضعیت ادمین بودن کاربر
"""
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

logger = logging.getLogger(__name__)


class AdminCheckMiddleware(BaseMiddleware):
    """
    Middleware برای بررسی ادمین بودن کاربر
    
    این middleware یک بار در ابتدای هر handler وضعیت ادمین بودن را چک می‌کند
    و نتیجه را در data['is_admin'] قرار می‌دهد تا handler‌ها دیگر نیازی به
    query مجدد نداشته باشند.
    
    Features:
    - کاهش تعداد DB queries از N به 1 در هر پیام
    - بهبود performance
    - کد تمیزتر در handler‌ها
    
    Usage:
        dp.message.middleware(AdminCheckMiddleware(admin_service))
        dp.callback_query.middleware(AdminCheckMiddleware(admin_service))
    """
    
    def __init__(self, admin_service):
        """
        Args:
            admin_service: نمونه AdminService برای چک کردن ادمین
        """
        super().__init__()
        self.admin_service = admin_service
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        فراخوانی middleware
        
        Args:
            handler: Handler بعدی در زنجیره
            event: Event تلگرام (Message یا CallbackQuery)
            data: داده‌های middleware
            
        Returns:
            نتیجه handler
        """
        # دریافت user از event
        user: User = data.get('event_from_user')
        
        if user:
            # چک کردن ادمین بودن (فقط یک بار)
            is_admin = await self.admin_service.is_admin(user.id)
            
            # ذخیره در data برای استفاده در handler‌ها
            data['is_admin'] = is_admin
            
            logger.debug(
                f"AdminCheckMiddleware: user_id={user.id}, is_admin={is_admin}"
            )
        else:
            # اگر user وجود نداشت (نباید اتفاق بیفتد)
            data['is_admin'] = False
            logger.warning("AdminCheckMiddleware: user not found in event")
        
        # فراخوانی handler بعدی
        return await handler(event, data)
