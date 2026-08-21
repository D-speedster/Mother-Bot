"""
Handler ربات فرزند دانلود فیلم و سریال

⚠️ فاز فعلی: فقط UI و معماری — بدون دانلود واقعی
این فایل proof of concept است برای نشان دادن ساختار handler‌های dynamic
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)


# ========== FSM States ==========
class DownloaderStates(StatesGroup):
    """
    State‌های FSM برای ربات دانلود
    """
    waiting_for_movie_name = State()
    waiting_for_series_name = State()


# ========== Router Factory Function ==========
def get_router() -> Router:
    """
    ساخت و برگرداندن Router جدید برای ربات دانلودر
    
    ⚠️ CRITICAL: این تابع هر بار یک Router جدید می‌سازد
    - این از تداخل Router بین ربات‌های مختلف جلوگیری می‌کند
    - هر ربات فرزند Router اختصاصی خود را دارد
    
    Returns:
        Router جدید با تمام handler‌های ثبت‌شده
    """
    router = Router(name="downloader")
    
    # ثبت handler‌ها روی router جدید
    # ⚠️ توجه: نام توابع باید با handler‌های تعریف شده در پایین فایل مطابقت داشته باشند
    router.message.register(cmd_start, Command("start"))
    router.message.register(cmd_help, Command("help"))
    router.message.register(handle_download_movie, F.text == "🎬 دانلود فیلم")
    router.message.register(handle_download_series, F.text == "📺 دانلود سریال")
    router.message.register(handle_my_downloads, F.text == "📥 دانلودهای من")
    router.message.register(handle_support, F.text == "💬 پشتیبانی")
    router.message.register(handle_movie_name_input, DownloaderStates.waiting_for_movie_name)
    router.message.register(handle_series_name_input, DownloaderStates.waiting_for_series_name)
    
    return router


# ⚠️ DEPRECATED: این router global دیگر استفاده نمی‌شود
# فقط برای backward compatibility نگه داشته شده
downloader_router = Router(name="downloader_legacy")


# ========== Keyboards ==========
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    کیبورد اصلی ربات دانلود
    """
    keyboard = [
        [
            KeyboardButton(text="🎬 دانلود فیلم"),
            KeyboardButton(text="📺 دانلود سریال")
        ],
        [
            KeyboardButton(text="📥 دانلودهای من"),
            KeyboardButton(text="💬 پشتیبانی")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="یک گزینه را انتخاب کنید..."
    )


# ========== Handler: /start ==========
async def cmd_start(message: Message, state: FSMContext):
    """
    Handler دستور /start
    
    - خوش‌آمدگویی
    - نمایش کیبورد اصلی
    - clear کردن state (در صورت وجود)
    """
    # Clear کردن state قبلی (اگر وجود داشته باشد)
    await state.clear()
    
    # دریافت نام ربات
    try:
        bot_info = await message.bot.me()
        bot_name = bot_info.first_name or "ربات دانلود"
    except Exception:
        bot_name = "ربات دانلود"
    
    welcome_text = (
        f"👋 به {bot_name} خوش آمدید!\n\n"
        f"🎬 ربات دانلود فیلم و سریال\n\n"
        f"از منوی زیر یک گزینه را انتخاب کنید:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )
    
    logger.info(f"کاربر {message.from_user.id} دستور /start را زد")


# ========== Handler: /help ==========
async def cmd_help(message: Message):
    """نمایش راهنمای استفاده از ربات"""
    help_text = (
        "📋 راهنمای استفاده از ربات دانلود\n\n"
        "🎬 دانلود فیلم:\n"
        "• روی دکمه «دانلود فیلم» کلیک کنید\n"
        "• نام فیلم را بنویسید\n"
        "• منتظر نتایج بمانید\n\n"
        "📺 دانلود سریال:\n"
        "• روی دکمه «دانلود سریال» کلیک کنید\n"
        "• نام سریال را بنویسید\n"
        "• منتظر نتایج بمانید\n\n"
        "💡 نکته: این ربات در حال توسعه است"
    )
    await message.answer(help_text)
    logger.info(f"کاربر {message.from_user.id} راهنما را مشاهده کرد")


# ========== Handler: دانلود فیلم ==========
async def handle_download_movie(message: Message, state: FSMContext):
    """شروع فرآیند دانلود فیلم"""
    await state.set_state(DownloaderStates.waiting_for_movie_name)
    await message.answer(
        "🎬 نام فیلم مورد نظر را بنویسید:\n\nمثال: Inception"
    )
    logger.info(f"کاربر {message.from_user.id} وارد حالت دانلود فیلم شد")


async def handle_movie_name_input(message: Message, state: FSMContext):
    """پردازش نام فیلم دریافتی"""
    movie_name = message.text.strip()
    await state.clear()
    
    response_text = (
        f"⏳ در حال جستجو برای: {movie_name}\n\n"
        f"🎬 نتایج به زودی نمایش داده می‌شود...\n\n"
        f"[این قابلیت در حال توسعه است]"
    )
    
    await message.answer(response_text, reply_markup=get_main_keyboard())
    logger.info(f"کاربر {message.from_user.id} درخواست دانلود فیلم داد")


# ========== Handler: دانلود سریال ==========
async def handle_download_series(message: Message, state: FSMContext):
    """شروع فرآیند دانلود سریال"""
    await state.set_state(DownloaderStates.waiting_for_series_name)
    await message.answer(
        "📺 نام سریال مورد نظر را بنویسید:\n\nمثال: Breaking Bad"
    )
    logger.info(f"کاربر {message.from_user.id} وارد حالت دانلود سریال شد")


async def handle_series_name_input(message: Message, state: FSMContext):
    """پردازش نام سریال دریافتی"""
    series_name = message.text.strip()
    await state.clear()
    
    response_text = (
        f"⏳ در حال جستجو برای: {series_name}\n\n"
        f"📺 نتایج به زودی نمایش داده می‌شوند...\n\n"
        f"[این قابلیت در حال توسعه است]"
    )
    
    await message.answer(response_text, reply_markup=get_main_keyboard())
    logger.info(f"کاربر {message.from_user.id} درخواست دانلود سریال داد")


# ========== Handler: دانلودهای من ==========
async def handle_my_downloads(message: Message):
    """نمایش لیست دانلودهای کاربر"""
    text = (
        "📥 دانلودهای من\n\n"
        "شما هنوز هیچ فایلی دانلود نکرده‌اید.\n\n"
        "[این قابلیت در حال توسعه است]"
    )
    await message.answer(text)
    logger.info(f"کاربر {message.from_user.id} لیست دانلودها را مشاهده کرد")


# ========== Handler: پشتیبانی ==========
async def handle_support(message: Message):
    """نمایش اطلاعات پشتیبانی"""
    text = (
        "💬 پشتیبانی\n\n"
        "برای دریافت پشتیبانی:\n\n"
        "📧 ایمیل: support@example.com\n"
        "💬 تلگرام: @support\n\n"
        "⏰ ساعات پاسخگویی: ۹ صبح تا ۹ شب"
    )
    await message.answer(text)
    logger.info(f"کاربر {message.from_user.id} پشتیبانی را مشاهده کرد")
