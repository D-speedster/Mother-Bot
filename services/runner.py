"""
Bot Runner - مدیریت اجرای Child Bot‌ها با asyncio
"""
import logging
import asyncio
import importlib
from typing import Dict, Optional
from contextlib import suppress

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

from services.bot_service import BotService
from services.encryption import TokenEncryptionService

logger = logging.getLogger(__name__)


# ========== Router Registry ==========
def _get_router_for_bot_type(bot_type: str) -> Optional[Router]:
    """
    انتخاب router مناسب بر اساس bot_type
    
    ⚠️ CRITICAL FIX: Router Instance جدید برای هر ربات
    - هر بار این تابع صدا زده می‌شود، یک Router جدید ساخته می‌شود
    - این از تداخل Router بین ربات‌های مختلف جلوگیری می‌کند
    - Router‌های مشترک باعث RuntimeError می‌شوند
    
    Args:
        bot_type: نوع ربات (downloader, support, ...)
        
    Returns:
        Router جدید برای bot_type یا None اگر ناشناخته باشد
        
    Note:
    - برای اضافه کردن bot_type جدید، فقط BOT_TYPE_HANDLERS را آپدیت کن
    - هر handler module باید تابع get_router() داشته باشد که Router جدید برمی‌گرداند
    """
    BOT_TYPE_HANDLERS = {
        "ai_image": "handlers.child_bots.downloader",
        "movie_downloader": "handlers.child_bots.movie",
        "social_downloader": "handlers.child_bots.downloader",
        "vpn_seller": "handlers.child_bots.downloader",
        # Legacy support
        "downloader": "handlers.child_bots.downloader",
    }
    
    module_path = BOT_TYPE_HANDLERS.get(bot_type)
    
    if not module_path:
        return None
    
    # Lazy import با importlib
    try:
        module = importlib.import_module(module_path)
        
        # ⚠️ FIX: فراخوانی تابع get_router() برای ساخت Router جدید
        # به جای import مستقیم router global
        if hasattr(module, 'get_router'):
            return module.get_router()
        else:
            logger.error(
                f"❌ ماژول {module_path} تابع get_router() ندارد — "
                f"نمی‌توان Router جدید ساخت"
            )
            return None
    
    except Exception as e:
        logger.error(
            f"❌ خطا در لود کردن handler برای bot_type={bot_type}: "
            f"{type(e).__name__}",
            exc_info=True
        )
        return None


class BotRunner:
    """
    مدیریت اجرای همزمان Child Bot‌ها با asyncio
    
    مسئولیت‌ها:
    - نگهداری task‌های asyncio برای هر ربات
    - start/stop ربات‌های فرزند
    - مدیریت lifecycle و error handling
    - جلوگیری از duplicate task
    
    ⚠️ امنیت:
    - توکن‌های decrypt‌شده هیچ‌جا log نمی‌شوند
    - هر task ایزوله است و crash یکی روی دیگری تأثیر ندارد
    """
    
    def __init__(self, bot_service: BotService, encryption_service: TokenEncryptionService):
        """
        Args:
            bot_service: BotService instance برای دریافت اطلاعات ربات‌ها
            encryption_service: TokenEncryptionService instance برای دیکریپت کردن توکن‌ها
        """
        self._bot_service = bot_service
        self._encryption = encryption_service
        self._tasks: Dict[int, asyncio.Task] = {}
        # کلید: bot_id (DB id)، مقدار: asyncio.Task
    
    async def start_all_active_bots(self, owner_id: int) -> None:
        """
        همه ربات‌های active یک کاربر را از DB خوانده و start می‌کند
        
        Args:
            owner_id: ID کاربر تلگرام (صاحب ربات‌ها)
            
        Note:
        - فقط ربات‌هایی که task ندارند را start می‌کند (جلوگیری از duplicate)
        - ربات‌هایی با status='active' شروع می‌شوند
        
        ⚠️ TODO (فاز ۳):
        - این متد فقط یک کاربر را پوشش می‌دهد
        - برای restart ربات مادر، نیاز به start_all_bots_system_wide() داریم
        - آن متد باید مستقیم از repository همه active bot‌ها را بدون فیلتر owner بخواند
        """
        try:
            # دریافت لیست ربات‌های کاربر
            bots = await self._bot_service.get_user_bots(owner_id)
            
            # فیلتر ربات‌های active
            active_bots = [bot for bot in bots if bot['status'] == 'active']
            
            logger.info(
                f"شروع ربات‌های active برای کاربر {owner_id}: "
                f"{len(active_bots)} ربات یافت شد"
            )
            
            # شروع هر ربات (اگر قبلاً running نباشد)
            for bot in active_bots:
                bot_id = bot['bot_id']
                
                # جلوگیری از duplicate task
                if self.is_running(bot_id):
                    logger.info(
                        f"⏭️ ربات {bot_id} (@{bot['username']}) "
                        f"از قبل در حال اجراست"
                    )
                    continue
                
                # start ربات
                success = await self.start_bot(bot_id, owner_id)
                
                if success:
                    logger.info(
                        f"✅ ربات {bot_id} (@{bot['username']}) شروع شد"
                    )
                else:
                    logger.warning(
                        f"⚠️ شروع ربات {bot_id} (@{bot['username']}) ناموفق بود"
                    )
        
        except Exception as e:
            logger.error(
                f"❌ خطا در شروع ربات‌های active کاربر {owner_id}: "
                f"{type(e).__name__}",
                exc_info=True
            )
    
    async def start_bot(self, bot_id: int, owner_id: int) -> bool:
        """
        یک ربات خاص را start کن
        
        Args:
            bot_id: ID رکورد در دیتابیس
            owner_id: ID کاربر تلگرام (برای تأیید مالکیت)
            
        Returns:
            True اگر شروع موفق باشد، False اگر قبلاً running باشد یا خطایی رخ دهد
            
        Security:
        - توکن decrypt‌شده هیچ‌جا log نمی‌شود
        - بررسی ownership توسط bot_service انجام می‌شود
        
        ⚠️ TODO (فاز ۴):
        Performance optimization:
        - الان دو DB call برای start یک ربات (get_bot_info + get_bot_token)
        - بهتر است یک متد ترکیبی: get_bot_start_info(bot_id, owner_id)
        - که هم token و هم bot_type را با یک DB call برگرداند
        - برای MVP با تعداد کم ربات مشکلی ایجاد نمی‌کند
        """
        try:
            # اگر task برای این bot_id وجود دارد، False برگردان
            if self.is_running(bot_id):
                logger.warning(
                    f"⚠️ ربات {bot_id} از قبل در حال اجراست — duplicate start"
                )
                return False
            
            # دریافت اطلاعات ربات (برای گرفتن bot_type)
            bot_info = await self._bot_service.get_bot_info(bot_id, owner_id)
            bot_type = bot_info.get('bot_type', 'downloader')
            
            # دریافت توکن از bot_service (با بررسی ownership)
            token = await self._bot_service.get_bot_token(bot_id, owner_id)
            
            # ⚠️ SECURITY: توکن را log نمی‌کنیم
            logger.info(
                f"🚀 شروع ربات {bot_id} (type={bot_type}) برای کاربر {owner_id}"
            )
            
            # ساخت task و ذخیره در dict
            task = asyncio.create_task(
                self._run_bot_task(bot_id, token, bot_type),
                name=f"bot_{bot_id}"
            )
            
            self._tasks[bot_id] = task
            
            return True
        
        except ValueError as e:
            # ربات یافت نشد یا متعلق به این کاربر نیست
            logger.error(
                f"❌ شروع ربات {bot_id} ناموفق: {str(e)}"
            )
            return False
        
        except Exception as e:
            logger.error(
                f"❌ خطا در شروع ربات {bot_id}: {type(e).__name__}",
                exc_info=True
            )
            return False
    
    async def start_bot_system(
        self,
        bot_id: int,
        owner_id: int,
        token_encrypted: str,
        bot_type: str
    ) -> bool:
        """
        شروع یک ربات به صورت سیستمی (برای استارت‌آپ)
        
        این متد برای راه‌اندازی خودکار ربات‌های فعال در startup استفاده می‌شود.
        برخلاف start_bot()، این متد نیاز به چک ownership ندارد و مستقیماً با
        توکن رمزشده کار می‌کند.
        
        Args:
            bot_id: ID رکورد در دیتابیس
            owner_id: ID کاربر تلگرام (برای لاگ)
            token_encrypted: توکن رمزشده
            bot_type: نوع ربات
            
        Returns:
            True اگر شروع موفق باشد، False اگر قبلاً running باشد یا خطایی رخ دهد
            
        Security:
        - توکن decrypt‌شده هیچ‌جا log نمی‌شود
        - خطاها catch می‌شوند تا crash کل سیستم را جلوگیری کنند
        """
        try:
            # اگر task برای این bot_id وجود دارد، False برگردان
            if self.is_running(bot_id):
                logger.warning(
                    f"⚠️ ربات {bot_id} از قبل در حال اجراست — duplicate start در startup"
                )
                return False
            
            # دیکریپت کردن توکن با استفاده از encryption service تزریق‌شده
            token = self._encryption.decrypt(token_encrypted)
            
            # ⚠️ SECURITY: توکن را log نمی‌کنیم
            logger.info(
                f"🚀 شروع سیستمی ربات {bot_id} (type={bot_type}) برای کاربر {owner_id}"
            )
            
            # ساخت task و ذخیره در dict
            task = asyncio.create_task(
                self._run_bot_task(bot_id, token, bot_type),
                name=f"bot_{bot_id}_system"
            )
            
            self._tasks[bot_id] = task
            
            return True
        
        except Exception as e:
            # ⚠️ CRITICAL: خطا را log می‌کنیم اما raise نمی‌کنیم
            # تا خرابی یک ربات باعث crash کل startup نشود
            logger.error(
                f"❌ خطا در شروع سیستمی ربات {bot_id}: {type(e).__name__}",
                exc_info=True
            )
            return False
    
    async def stop_bot(self, bot_id: int) -> bool:
        """
        یک ربات خاص را stop کن
        
        Args:
            bot_id: ID رکورد در دیتابیس
            
        Returns:
            True اگر متوقف شد، False اگر task وجود نداشت
        """
        try:
            task = self._tasks.pop(bot_id, None)
            
            if not task:
                logger.warning(f"⚠️ ربات {bot_id} در حال اجرا نیست")
                return False
            
            if task.done():
                logger.info(f"ℹ️ ربات {bot_id} قبلاً متوقف شده بود")
                return True
            
            logger.info(f"🛑 در حال توقف ربات {bot_id}...")
            
            # مرحله ۱: cancel task
            task.cancel()
            
            # مرحله ۲: صبر کن تا task کاملاً تمام شود
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=5.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            
            logger.info(f"✅ ربات {bot_id} با موفقیت متوقف شد")
            return True
        
        except Exception as e:
            logger.error(
                f"❌ خطا در توقف ربات {bot_id}: {type(e).__name__}",
                exc_info=True
            )
            return False
    
    def is_running(self, bot_id: int) -> bool:
        """
        چک کن آیا task وجود دارد و done() نشده
        
        Args:
            bot_id: ID رکورد در دیتابیس
            
        Returns:
            True اگر ربات در حال اجرا باشد
        """
        task = self._tasks.get(bot_id)
        
        if not task:
            return False
        
        # اگر task وجود دارد ولی done شده، از dict حذف کن
        if task.done():
            self._tasks.pop(bot_id, None)
            return False
        
        return True
    
    async def _run_bot_task(self, bot_id: int, token: str, bot_type: str) -> None:
        """
        ⚠️ مهم‌ترین بخش — این تابع داخل asyncio.Task اجرا می‌شود
        
        الزامات:
        1. کل بدنه در try/except Exception بپیچ
        2. هر خطا فقط log شود — هیچ‌وقت raise نشود به بیرون
        3. در صورت crash، self._tasks[bot_id] را cleanup کن
        4. handler را بر اساس bot_type انتخاب کن
        5. بعد از اتمام (چه موفق چه خطا)، bot.session.close() حتماً صدا زده شود
        
        Args:
            bot_id: ID رکورد در دیتابیس
            token: توکن ربات (decrypt‌شده)
            bot_type: نوع ربات (downloader, support, ...)
            
        Security:
        - توکن هیچ‌جا log نمی‌شود
        - هیچ exception به event loop اصلی نمی‌رسد
        
        ⚠️ TODO (فاز ۴):
        Reconnect/Retry منطق:
        - اگر ربات crash کرد، exponential backoff retry (5s، 10s، 30s)
        - حداکثر 3 بار تلاش
        - بعد از 3 بار failure، status را در DB به 'error' تغییر بده
        - الان: ربات crash می‌کند و دیگر restart نمی‌شود (کاربر باید دستی restart کند)
        """
        bot = None
        dp = None
        
        try:
            # ⚠️ SECURITY: توکن را log نمی‌کنیم
            logger.info(f"🤖 ربات {bot_id} (type={bot_type}) در حال راه‌اندازی...")
            
            # ساخت Bot و Dispatcher
            bot = Bot(token=token)
            dp = Dispatcher(storage=MemoryStorage())
            
            # ⚠️ FIX: حذف webhook قبلی برای جلوگیری از TelegramConflictError
            try:
                await bot.delete_webhook(drop_pending_updates=True)
                logger.debug(f"✅ Webhook ربات {bot_id} پاک شد")
            except Exception as webhook_error:
                logger.warning(
                    f"⚠️ خطا در حذف webhook ربات {bot_id}: {type(webhook_error).__name__}"
                )
            
            # انتخاب router بر اساس bot_type
            router = _get_router_for_bot_type(bot_type)
            
            if router:
                dp.include_router(router)
                logger.info(
                    f"✅ Router برای bot_type={bot_type} لود شد (ربات {bot_id})"
                )
            else:
                logger.warning(
                    f"⚠️ Router برای bot_type={bot_type} یافت نشد — "
                    f"ربات {bot_id} بدون handler اجرا می‌شود"
                )
            
            logger.info(f"✅ ربات {bot_id} وارد حلقه polling شد")
            
            # ⚠️ FIX: شروع polling با مدیریت صحیح CancelledError
            # handle_signals=False برای جلوگیری از تداخل با signal handling ربات مادر
            try:
                await dp.start_polling(bot, handle_signals=False)
            except asyncio.CancelledError:
                # ⚠️ CRITICAL: این exception باید raise شود تا task کنسل شود
                logger.info(f"🛑 حلقه polling ربات {bot_id} کنسل شد")
                raise
            
            # این خط فقط در صورت توقف عادی اجرا می‌شود
            logger.info(f"ℹ️ ربات {bot_id} به‌طور عادی متوقف شد")
        
        except asyncio.CancelledError:
            # ⚠️ CRITICAL: این exception را دوباره raise می‌کنیم
            # تا task به‌درستی cancelled شود
            logger.info(f"🛑 تسک پولینگ ربات {bot_id} با موفقیت کنسل و متوقف شد")
            raise
        
        except Exception as e:
            # هر خطای دیگر
            logger.error(
                f"❌ ربات {bot_id} crash کرد: {type(e).__name__}",
                exc_info=True
            )
            # ⚠️ مهم: raise نمی‌کنیم — فقط log
        
        finally:
            # ⚠️ مهم: session را دستی نبند
            # aiogram خودش session را مدیریت می‌کند
            # بستن دستی session باعث SSL error می‌شود
            
            self._tasks.pop(bot_id, None)
            logger.info(f"🧹 Task ربات {bot_id} از dict حذف شد")
    
    async def start_all_bots_system_wide(self, repository) -> int:
        """
        همه ربات‌های active همه کاربران را از DB خوانده و start می‌کند
        
        این متد برای راه‌اندازی خودکار ربات‌ها در startup ربات مادر استفاده می‌شود.
        
        Args:
            repository: BotRepository instance برای دریافت لیست ربات‌ها
            
        Returns:
            تعداد ربات‌هایی که با موفقیت شروع شدند
            
        Security:
        - هر ربات در یک task جداگانه اجرا می‌شود
        - خطای یک ربات باعث crash سایرین نمی‌شود
        - توکن‌ها هیچ‌جا log نمی‌شوند
        
        Performance:
        - Task‌ها به صورت موازی (concurrent) شروع می‌شوند
        - برای تعداد زیاد ربات، می‌توان rate limiting اضافه کرد
        """
        try:
            # دریافت تمام ربات‌های فعال
            active_bots = await repository.get_all_active_bots()
            
            if not active_bots:
                logger.info("ℹ️ هیچ ربات فعالی برای شروع یافت نشد")
                return 0
            
            logger.info(
                f"📋 شروع راه‌اندازی {len(active_bots)} ربات فعال در استارت‌آپ..."
            )
            
            # شروع همه ربات‌ها
            success_count = 0
            for bot in active_bots:
                bot_id = bot['id']
                owner_id = bot['owner_id']
                token_encrypted = bot['token_encrypted']
                bot_type = bot['bot_type']
                username = bot.get('username', 'نامشخص')
                
                # شروع ربات (non-blocking)
                started = await self.start_bot_system(
                    bot_id=bot_id,
                    owner_id=owner_id,
                    token_encrypted=token_encrypted,
                    bot_type=bot_type
                )
                
                if started:
                    success_count += 1
                    logger.info(
                        f"✅ ربات {bot_id} (@{username}) شروع شد "
                        f"({success_count}/{len(active_bots)})"
                    )
                else:
                    logger.warning(
                        f"⚠️ ربات {bot_id} (@{username}) شروع نشد "
                        f"({success_count}/{len(active_bots)})"
                    )
            
            logger.info(
                f"🎉 استارت‌آپ کامل شد: {success_count}/{len(active_bots)} "
                f"ربات فرزند با موفقیت روشن شدند"
            )
            
            return success_count
        
        except Exception as e:
            logger.error(
                f"❌ خطا در راه‌اندازی سیستمی ربات‌ها: {type(e).__name__}",
                exc_info=True
            )
            return 0

