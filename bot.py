"""
نقطه شروع ربات - راه‌اندازی Dispatcher و Polling
"""
import asyncio
import logging
import re
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, DATABASE_PATH
from handlers import start_router, bot_maker_router
from database import Database
from database.repository import BotRepository
from services import TokenEncryptionService, BotService


class TokenMaskingFilter(logging.Filter):
    """
    Log Filter برای Masking توکن‌های تلگرام در لاگ‌ها
    
    با استفاده از Regex، توکن‌های تلگرام را شناسایی و با [MASKED_TOKEN] جایگزین می‌کند
    """
    
    # الگوی Regex برای شناسایی توکن‌های تلگرام
    # فرمت: 8-10 رقم + : + 35 کاراکتر alphanumeric و -_
    TOKEN_PATTERN = re.compile(r'\d{8,10}:[A-Za-z0-9_-]{35}')
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        فیلتر کردن و Masking توکن‌ها در پیام‌های لاگ
        
        Args:
            record: رکورد لاگ
            
        Returns:
            True (همیشه لاگ را نگه می‌دارد، فقط محتوا را تغییر می‌دهد)
        """
        # Masking توکن در پیام اصلی
        if record.msg and isinstance(record.msg, str):
            record.msg = self.TOKEN_PATTERN.sub('[MASKED_TOKEN]', record.msg)
        
        # Masking توکن در args (اگر وجود داشته باشد)
        if record.args:
            # اگر args رشته باشد (نه tuple)
            if isinstance(record.args, str):
                record.args = self.TOKEN_PATTERN.sub('[MASKED_TOKEN]', record.args)
            # اگر tuple باشد
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self.TOKEN_PATTERN.sub('[MASKED_TOKEN]', arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        
        return True


def setup_logging():
    """تنظیم سیستم logging با Token Masking Filter"""
    # ساخت handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    
    # ساخت formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # ساخت Token Masking Filter
    token_filter = TokenMaskingFilter()
    
    # اضافه کردن فیلتر به handler
    handler.addFilter(token_filter)
    
    # تنظیم root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    
    # اعمال فیلتر روی root logger برای پوشش همه logger‌ها
    root_logger.addFilter(token_filter)
    
    return root_logger


# تنظیم logging با Token Masking
logger = setup_logging()


async def main():
    """تابع اصلی برای راه‌اندازی ربات"""
    # راه‌اندازی پایگاه داده
    database = Database(DATABASE_PATH)
    await database.connect()
    
    # راه‌اندازی سرویس‌ها
    encryption_service = TokenEncryptionService()
    repository = BotRepository(database.connection)
    bot_service = BotService(repository, encryption_service)
    
    # ساخت Bot و Dispatcher
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # اضافه کردن سرویس‌ها به middleware data (برای دسترسی در handlers)
    dp.workflow_data.update({
        'bot_service': bot_service,
        'repository': repository,
        'encryption': encryption_service
    })
    
    # ثبت routerها
    dp.include_router(start_router)
    dp.include_router(bot_maker_router)
    
    logger.info("🤖 ربات در حال اجرا است...")
    logger.info(f"📊 پایگاه داده: {DATABASE_PATH}")
    
    try:
        # حذف webhook و شروع polling
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await database.disconnect()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("❌ ربات متوقف شد")
