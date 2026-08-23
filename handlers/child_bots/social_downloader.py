"""
Handler ربات فرزند دانلود از شبکه‌های اجتماعی

این ربات از پلتفرم‌های مختلف (YouTube، Aparat، Instagram و...) ویدیو دانلود می‌کند.

پلتفرم‌های پشتیبانی شده:
- YouTube (youtube.com, youtu.be)
- Aparat (aparat.com)
- Instagram (instagram.com)
- Universal (سایر پلتفرم‌ها)

محدودیت‌ها:
- حداکثر حجم فایل: 50MB (محدودیت Telegram)
"""
import os
import logging
import hashlib
import tempfile
import shutil
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.download_service import DownloadService, DownloadError, UnsupportedURLError, FileTooLargeError

logger = logging.getLogger(__name__)


# ========== FSM States ==========
class SocialDownloaderStates(StatesGroup):
    """State‌های FSM برای ربات دانلودر شبکه‌های اجتماعی"""
    waiting_for_url = State()


# ========== URL Cache ==========
# ⚠️ MVP Solution: ذخیره URL در حافظه با hash
# برای production باید از Redis یا database استفاده شود
_url_cache: dict[str, str] = {}
# کلید: url_hash (8 کاراکتر)، مقدار: URL کامل

# ⚠️ TODO (فاز بعد):
# - استفاده از Redis با TTL برای distributed systems
# - یا ذخیره در database با expiry time
# - اضافه کردن timestamp و پاکسازی خودکار cache‌های قدیمی‌تر از 1 ساعت
# - فعلاً برای MVP همین کافی است (single-instance bot)


def cleanup_old_cache_entries():
    """
    پاکسازی دستی cache (اگر لازم باشد)
    
    ⚠️ MVP: این تابع فعلاً صدا زده نمی‌شود
    برای production می‌توان یک background task اضافه کرد که هر 1 ساعت
    این تابع را صدا بزند
    """
    # برای MVP: cache را کاملاً پاک نمی‌کنیم
    # در صورت نیاز می‌توان این تابع را از یک scheduler صدا زد
    pass


# ========== Router Factory Function ==========
def get_router() -> Router:
    """
    ساخت و برگرداندن Router جدید برای ربات دانلودر شبکه‌های اجتماعی
    
    Returns:
        Router جدید با تمام handler‌های ثبت‌شده
    """
    router = Router(name="social_downloader")
    
    # سرویس دانلود (بدون وابستگی به Telegram)
    download_service = DownloadService()
    
    # ثبت handler‌ها
    router.message.register(cmd_start, Command("start"))
    router.message.register(handle_download_video, F.text == "📥 دانلود ویدیو")
    router.message.register(handle_help, F.text == "📋 راهنما")
    router.message.register(handle_support, F.text == "💬 پشتیبانی")
    
    # Handler دریافت URL (با dependency injection سرویس)
    async def handle_url_with_service(message: Message, state: FSMContext):
        await handle_url_input(message, state, download_service)
    
    router.message.register(handle_url_with_service, SocialDownloaderStates.waiting_for_url)
    
    # Callback handler برای انتخاب کیفیت (با dependency injection)
    async def handle_quality_with_service(callback: CallbackQuery, state: FSMContext):
        await handle_quality_selection(callback, state, download_service)
    
    router.callback_query.register(handle_quality_with_service, F.data.startswith("sdl_"))
    
    return router


# ========== Keyboards ==========
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد اصلی ربات"""
    keyboard = [
        [KeyboardButton(text="📥 دانلود ویدیو")],
        [
            KeyboardButton(text="📋 راهنما"),
            KeyboardButton(text="💬 پشتیبانی")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="یک گزینه را انتخاب کنید..."
    )


def get_quality_keyboard(url: str, qualities: dict) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انتخاب کیفیت
    
    Args:
        url: آدرس ویدیو (برای hash کردن)
        qualities: dict کیفیت‌های موجود
        
    Returns:
        InlineKeyboardMarkup با دکمه‌های کیفیت
    """
    # ساخت hash کوتاه از URL (برای callback_data)
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    
    # ⚠️ FIX: ذخیره URL در cache با hash
    _url_cache[url_hash] = url
    
    buttons = []
    
    # ترتیب کیفیت‌ها از پایین به بالا
    quality_order = ['360', '480', '720', '1080', 'best']
    
    for quality in quality_order:
        if quality in qualities:
            quality_info = qualities[quality]
            filesize = quality_info.get('filesize', 0)
            
            # متن دکمه
            if filesize > 0:
                size_mb = filesize / (1024 * 1024)
                button_text = f"{quality}p ({size_mb:.1f}MB)"
            else:
                button_text = f"{quality}p"
            
            # callback_data: sdl_{quality}_{url_hash}
            callback_data = f"sdl_{quality}_{url_hash}"
            
            buttons.append([
                InlineKeyboardButton(text=button_text, callback_data=callback_data)
            ])
    
    # اگر هیچ کیفیتی نبود، دکمه best را اضافه کن
    if not buttons:
        buttons.append([
            InlineKeyboardButton(text="بهترین کیفیت", callback_data=f"sdl_best_{url_hash}")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ========== Handler: /start ==========
async def cmd_start(message: Message, state: FSMContext):
    """
    Handler دستور /start
    """
    # Clear کردن state قبلی
    await state.clear()
    
    # دریافت نام ربات
    try:
        bot_info = await message.bot.me()
        bot_name = bot_info.first_name or "ربات دانلود"
    except Exception:
        bot_name = "ربات دانلود"
    
    welcome_text = (
        f"👋 به {bot_name} خوش آمدید!\n\n"
        f"📥 دانلود ویدیو از:\n"
        f"• YouTube\n"
        f"• Aparat\n"
        f"• Instagram\n"
        f"• و بسیاری پلتفرم‌های دیگر\n\n"
        f"از منوی زیر یک گزینه را انتخاب کنید:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )
    
    logger.info(f"کاربر {message.from_user.id} دستور /start را زد")


# ========== Handler: دانلود ویدیو ==========
async def handle_download_video(message: Message, state: FSMContext):
    """شروع فرآیند دانلود ویدیو"""
    await state.set_state(SocialDownloaderStates.waiting_for_url)
    
    help_text = (
        "📥 لینک ویدیو را ارسال کنید:\n\n"
        "پلتفرم‌های پشتیبانی شده:\n"
        "• YouTube (youtube.com, youtu.be)\n"
        "• Aparat (aparat.com)\n"
        "• Instagram (instagram.com)\n"
        "• و بسیاری پلتفرم‌های دیگر\n\n"
        "مثال:\n"
        "https://www.youtube.com/watch?v=..."
    )
    
    await message.answer(help_text)
    logger.info(f"کاربر {message.from_user.id} وارد حالت دانلود ویدیو شد")


# ========== Handler: دریافت URL ==========
async def handle_url_input(message: Message, state: FSMContext, download_service: DownloadService):
    """
    پردازش URL دریافتی از کاربر
    
    Args:
        message: پیام کاربر
        state: FSM context
        download_service: سرویس دانلود
    """
    url = message.text.strip()
    
    # اعتبارسنجی ساده URL
    if not (url.startswith('http://') or url.startswith('https://')):
        await message.answer(
            "❌ لینک نامعتبر است.\n\n"
            "لطفاً یک لینک معتبر ارسال کنید که با http:// یا https:// شروع شود."
        )
        return
    
    # پیام در حال پردازش
    processing_msg = await message.answer("⏳ در حال دریافت اطلاعات...")
    
    try:
        # استخراج اطلاعات ویدیو
        info = await download_service.extract_info(url)
        
        # ⚠️ FIX: حذف state.update_data — دیگر URL را در state ذخیره نمی‌کنیم
        # URL در _url_cache ذخیره می‌شود (در get_quality_keyboard)
        
        # ساخت متن اطلاعات
        title = info['title']
        duration = info['duration']
        uploader = info['uploader']
        platform = info['platform']
        
        # فرمت کردن مدت زمان
        if duration > 0:
            minutes = duration // 60
            seconds = duration % 60
            duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "نامشخص"
        
        info_text = (
            f"📹 <b>{title}</b>\n\n"
            f"👤 {uploader}\n"
            f"⏱ مدت زمان: {duration_str}\n"
            f"📱 پلتفرم: {platform.upper()}\n\n"
            f"کیفیت مورد نظر را انتخاب کنید:"
        )
        
        # ساخت کیبورد کیفیت
        keyboard = get_quality_keyboard(url, info['qualities'])
        
        # حذف پیام "در حال پردازش"
        try:
            await processing_msg.delete()
        except:
            pass
        
        # ارسال اطلاعات با کیبورد
        await message.answer(
            info_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        logger.info(
            f"کاربر {message.from_user.id} اطلاعات ویدیو را دریافت کرد: {title}"
        )
    
    except UnsupportedURLError as e:
        # حذف پیام "در حال پردازش"
        try:
            await processing_msg.delete()
        except:
            pass
        
        await message.answer(
            f"❌ این لینک پشتیبانی نمی‌شود.\n\n"
            f"لطفاً لینک از یکی از پلتفرم‌های پشتیبانی شده ارسال کنید."
        )
        
        # پاک کردن state
        await state.clear()
        
        logger.warning(f"کاربر {message.from_user.id} لینک نامعتبر ارسال کرد: {url}")
    
    except DownloadError as e:
        # حذف پیام "در حال پردازش"
        try:
            await processing_msg.delete()
        except:
            pass
        
        await message.answer(
            f"❌ خطا در دریافت اطلاعات.\n\n"
            f"لطفاً دوباره تلاش کنید یا لینک دیگری ارسال کنید."
        )
        
        # پاک کردن state
        await state.clear()
        
        logger.error(f"خطا در استخراج اطلاعات: {type(e).__name__}: {str(e)}")
    
    except Exception as e:
        # حذف پیام "در حال پردازش"
        try:
            await processing_msg.delete()
        except:
            pass
        
        await message.answer(
            f"❌ خطای غیرمنتظره رخ داد.\n\n"
            f"لطفاً بعداً دوباره تلاش کنید."
        )
        
        # پاک کردن state
        await state.clear()
        
        logger.error(f"خطای غیرمنتظره در handle_url_input: {type(e).__name__}", exc_info=True)


# ========== Handler: انتخاب کیفیت ==========
async def handle_quality_selection(callback: CallbackQuery, state: FSMContext, download_service: DownloadService):
    """
    پردازش انتخاب کیفیت و دانلود ویدیو
    
    Args:
        callback: callback query
        state: FSM context
        download_service: سرویس دانلود
    """
    # تأیید callback
    await callback.answer()
    
    # پارس کردن callback_data
    # فرمت: sdl_{quality}_{url_hash}
    parts = callback.data.split('_')
    
    if len(parts) < 3:
        await callback.message.answer("❌ خطا در پردازش درخواست.")
        return
    
    quality = parts[1]
    url_hash = parts[2]
    
    # ⚠️ FIX: دریافت URL از cache به جای state
    url = _url_cache.get(url_hash)
    
    if not url:
        await callback.message.answer(
            "❌ لینک منقضی شده است.\n\n"
            "لطفاً دوباره لینک را ارسال کنید.\n\n"
            "💡 برای جلوگیری از این مشکل، سریع‌تر روی دکمه کیفیت کلیک کنید.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        logger.warning(f"URL با hash {url_hash} در cache یافت نشد")
        return
    
    # پاک کردن state
    await state.clear()
    
    # پیام در حال دانلود
    download_msg = await callback.message.answer("⬇️ در حال دانلود...")
    
    file_path: Optional[str] = None
    temp_dir: Optional[str] = None
    
    try:
        # ⚠️ FIX: ساخت پوشه موقت منحصربه‌فرد برای این دانلود
        # این از collision بین دانلودهای همزمان جلوگیری می‌کند
        temp_dir = tempfile.mkdtemp(prefix=f"dl_{callback.from_user.id}_")
        logger.debug(f"پوشه موقت ایجاد شد: {temp_dir}")
        
        # دانلود ویدیو
        file_path = await download_service.download(url, quality, temp_dir)
        
        # آپدیت پیام
        try:
            await download_msg.edit_text("📤 در حال ارسال...")
        except:
            pass
        
        # ارسال فایل
        with open(file_path, 'rb') as video_file:
            await callback.message.answer_video(
                video=video_file,
                caption=f"✅ دانلود شد (کیفیت: {quality}p)",
                reply_markup=get_main_keyboard()
            )
        
        # حذف پیام "در حال ارسال"
        try:
            await download_msg.delete()
        except:
            pass
        
        # ⚠️ FIX: حذف URL از cache بعد از دانلود موفق
        _url_cache.pop(url_hash, None)
        
        logger.info(
            f"کاربر {callback.from_user.id} ویدیو را دانلود کرد "
            f"(کیفیت: {quality})"
        )
    
    except FileTooLargeError as e:
        # حذف پیام "در حال دانلود"
        try:
            await download_msg.delete()
        except:
            pass
        
        await callback.message.answer(
            f"❌ فایل بیشتر از 50MB است.\n\n"
            f"لطفاً کیفیت پایین‌تری انتخاب کنید.",
            reply_markup=get_main_keyboard()
        )
        
        # URL را در cache نگه می‌داریم (کاربر می‌تواند کیفیت دیگری انتخاب کند)
        
        logger.warning(f"فایل بیشتر از 50MB: {str(e)}")
    
    except DownloadError as e:
        # حذف پیام "در حال دانلود"
        try:
            await download_msg.delete()
        except:
            pass
        
        await callback.message.answer(
            f"❌ خطا در دانلود ویدیو.\n\n"
            f"لطفاً دوباره تلاش کنید.",
            reply_markup=get_main_keyboard()
        )
        
        # حذف URL از cache در صورت خطا
        _url_cache.pop(url_hash, None)
        
        logger.error(f"خطا در دانلود: {type(e).__name__}: {str(e)}")
    
    except Exception as e:
        # حذف پیام "در حال دانلود"
        try:
            await download_msg.delete()
        except:
            pass
        
        await callback.message.answer(
            f"❌ خطای غیرمنتظره رخ داد.\n\n"
            f"لطفاً بعداً دوباره تلاش کنید.",
            reply_markup=get_main_keyboard()
        )
        
        # حذف URL از cache در صورت خطا
        _url_cache.pop(url_hash, None)
        
        logger.error(f"خطای غیرمنتظره در handle_quality_selection: {type(e).__name__}", exc_info=True)
    
    finally:
        # ⚠️ FIX: حذف کامل پوشه موقت (همیشه اجرا می‌شود)
        # این شامل همه فایل‌های داخل پوشه است
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.debug(f"پوشه موقت حذف شد: {temp_dir}")
            except Exception as e:
                logger.warning(f"خطا در حذف پوشه موقت: {type(e).__name__}")


# ========== Handler: راهنما ==========
async def handle_help(message: Message):
    """نمایش راهنمای استفاده"""
    help_text = (
        "📋 <b>راهنمای استفاده</b>\n\n"
        "<b>پلتفرم‌های پشتیبانی شده:</b>\n"
        "• YouTube (youtube.com, youtu.be)\n"
        "• Aparat (aparat.com)\n"
        "• Instagram (instagram.com)\n"
        "• Twitter/X (twitter.com, x.com)\n"
        "• و بسیاری پلتفرم‌های دیگر\n\n"
        "<b>نحوه استفاده:</b>\n"
        "1️⃣ روی دکمه «📥 دانلود ویدیو» کلیک کنید\n"
        "2️⃣ لینک ویدیو را ارسال کنید\n"
        "3️⃣ کیفیت مورد نظر را انتخاب کنید\n"
        "4️⃣ منتظر دانلود بمانید\n\n"
        "<b>محدودیت‌ها:</b>\n"
        "• حداکثر حجم فایل: 50MB\n"
        "• فرمت خروجی: MP4\n\n"
        "💡 <b>نکته:</b> برای ویدیوهای بزرگ، کیفیت پایین‌تر را انتخاب کنید."
    )
    
    await message.answer(help_text, parse_mode="HTML")
    logger.info(f"کاربر {message.from_user.id} راهنما را مشاهده کرد")


# ========== Handler: پشتیبانی ==========
async def handle_support(message: Message):
    """نمایش اطلاعات پشتیبانی"""
    support_text = (
        "💬 <b>پشتیبانی</b>\n\n"
        "برای دریافت پشتیبانی یا گزارش مشکل:\n\n"
        "📧 ایمیل: support@example.com\n"
        "💬 تلگرام: @support\n\n"
        "⏰ ساعات پاسخگویی:\n"
        "شنبه تا پنجشنبه: ۹ صبح تا ۹ شب\n\n"
        "⚡️ پاسخگویی سریع در کمتر از ۲۴ ساعت"
    )
    
    await message.answer(support_text, parse_mode="HTML")
    logger.info(f"کاربر {message.from_user.id} پشتیبانی را مشاهده کرد")
