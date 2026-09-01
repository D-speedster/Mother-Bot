"""
Handler ربات فرزند انتقال فایل

این ربات دو قابلیت اصلی دارد:
۱. فایل → لینک مستقیم (آپلود به هاست)
۲. لینک مستقیم → فایل (دانلود و ارسال)

محدودیت‌ها:
- حداکثر حجم فایل: 2GB
- فقط لینک‌های مستقیم (نه YouTube/Instagram/...)
"""
import os
import logging
import tempfile
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.file_transfer_service import (
    FileTransferService,
    FileTransferError,
    HostNotConfiguredError,
    InvalidURLError,
    FileTooLargeError,
    DownloadError
)

logger = logging.getLogger(__name__)


# ========== FSM States ==========
class FileTransferStates(StatesGroup):
    """State‌های FSM برای ربات انتقال فایل"""
    waiting_for_file = State()  # منتظر دریافت فایل از کاربر
    waiting_for_url = State()   # منتظر دریافت لینک از کاربر


# ========== Router Factory Function ==========
def get_router() -> Router:
    """
    ساخت و برگرداندن Router جدید برای ربات انتقال فایل
    
    Returns:
        Router جدید با تمام handler‌های ثبت‌شده
    """
    router = Router(name="file_transfer")
    
    # سرویس انتقال فایل
    transfer_service = FileTransferService(timeout=600)  # 10 دقیقه timeout
    
    # ثبت handler‌ها
    router.message.register(cmd_start, Command("start"))
    router.message.register(handle_file_to_link, F.text == "📤 فایل به لینک")
    router.message.register(handle_link_to_file, F.text == "📥 لینک به فایل")
    router.message.register(handle_help, F.text == "📋 راهنما")
    router.message.register(handle_support, F.text == "💬 پشتیبانی")
    router.message.register(handle_cancel, F.text == "❌ لغو")
    router.message.register(handle_cancel, F.text == "❌ لغو")
    
    # Handler دریافت فایل (با dependency injection)
    async def handle_file_with_service(message: Message, state: FSMContext):
        await handle_file_input(message, state, transfer_service)
    
    router.message.register(
        handle_file_with_service,
        FileTransferStates.waiting_for_file,
        F.document | F.video | F.audio | F.photo
    )
    
    # Handler دریافت URL (با dependency injection)
    async def handle_url_with_service(message: Message, state: FSMContext):
        await handle_url_input(message, state, transfer_service)
    
    router.message.register(
        handle_url_with_service,
        FileTransferStates.waiting_for_url
    )
    
    return router


# ========== Keyboards ==========
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد اصلی"""
    keyboard = [
        [KeyboardButton(text="📤 فایل به لینک"), KeyboardButton(text="📥 لینک به فایل")],
        [KeyboardButton(text="📋 راهنما"), KeyboardButton(text="💬 پشتیبانی")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد لغو"""
    keyboard = [
        [KeyboardButton(text="❌ لغو")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# ========== Handlers ==========
async def cmd_start(message: Message, state: FSMContext):
    """
    Handler دستور /start
    """
    await state.clear()
    
    welcome_text = (
        "🤖 <b>ربات انتقال فایل</b>\n\n"
        "این ربات به شما کمک می‌کند:\n\n"
        "📤 <b>فایل به لینک</b>\n"
        "فایل خود را ارسال کنید و لینک مستقیم دریافت کنید\n"
        "⏳ <i>به زودی فعال می‌شود</i>\n\n"
        "📥 <b>لینک به فایل</b>\n"
        "لینک مستقیم بفرستید و فایل را دریافت کنید\n"
        "✅ <i>فعال است</i>\n\n"
        "💡 <b>محدودیت‌ها:</b>\n"
        "• حداکثر حجم: 2GB\n"
        "• فقط لینک‌های مستقیم (نه YouTube/Instagram)\n\n"
        "برای شروع از دکمه‌های زیر استفاده کنید 👇"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


async def handle_file_to_link(message: Message, state: FSMContext):
    """
    Handler دکمه «فایل به لینک»
    """
    await state.set_state(FileTransferStates.waiting_for_file)
    
    await message.answer(
        "📤 <b>فایل به لینک</b>\n\n"
        "لطفاً فایل خود را ارسال کنید:\n\n"
        "📝 <b>نکات مهم:</b>\n"
        "• حداکثر حجم: 2GB\n"
        "• تمام فرمت‌ها پشتیبانی می‌شوند\n"
        "• فایل شما به صورت ایمن ذخیره می‌شود\n\n"
        "⏳ <i>این قابلیت به زودی فعال می‌شود</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


async def handle_link_to_file(message: Message, state: FSMContext):
    """
    Handler دکمه «لینک به فایل»
    """
    await state.set_state(FileTransferStates.waiting_for_url)
    
    await message.answer(
        "📥 <b>لینک به فایل</b>\n\n"
        "لطفاً لینک مستقیم فایل را ارسال کنید:\n\n"
        "✅ <b>لینک‌های معتبر:</b>\n"
        "• http://example.com/file.zip\n"
        "• https://cdn.example.com/video.mp4\n\n"
        "❌ <b>لینک‌های نامعتبر:</b>\n"
        "• youtube.com/watch?v=...\n"
        "• instagram.com/p/...\n"
        "• aparat.com/v/...\n\n"
        "💡 فقط لینک‌های مستقیم به فایل مجاز هستند",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


async def handle_file_input(
    message: Message,
    state: FSMContext,
    service: FileTransferService
):
    """
    Handler دریافت فایل از کاربر
    
    ⚠️ این handler فعلاً فقط پیام می‌دهد که قابلیت به زودی فعال می‌شود
    چون آپلود به هاست هنوز پیاده نشده است
    """
    # تشخیص نوع فایل
    file_obj = None
    file_type = "فایل"
    
    if message.document:
        file_obj = message.document
        file_type = "سند"
    elif message.video:
        file_obj = message.video
        file_type = "ویدیو"
    elif message.audio:
        file_obj = message.audio
        file_type = "صوت"
    elif message.photo:
        file_obj = message.photo[-1]  # بزرگترین سایز
        file_type = "تصویر"
    
    if not file_obj:
        await message.answer(
            "❌ لطفاً یک فایل ارسال کنید",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # دریافت اطلاعات فایل
    file_name = getattr(file_obj, 'file_name', f'file_{file_obj.file_id}')
    file_size = getattr(file_obj, 'file_size', 0)
    
    # فرمت کردن حجم
    size_str = service._format_size(file_size) if file_size else "نامشخص"
    
    # نمایش اطلاعات فایل
    info_text = (
        f"📄 <b>اطلاعات {file_type}:</b>\n\n"
        f"📝 نام: <code>{file_name}</code>\n"
        f"📊 حجم: <b>{size_str}</b>\n"
        f"🆔 شناسه: <code>{file_obj.file_id[:20]}...</code>\n\n"
    )
    
    await message.answer(info_text, parse_mode="HTML")
    
    # پیام "در حال آپلود..."
    processing_msg = await message.answer(
        "⏳ در حال آپلود فایل به سرور...",
        parse_mode="HTML"
    )
    
    try:
        # تلاش برای آپلود (فعلاً فقط exception می‌دهد)
        # در آینده: دانلود فایل از تلگرام و آپلود به هاست
        link = await service.upload_to_host(file_obj.file_id, file_name)
        
        # اگر موفق بود (این بخش فعلاً اجرا نمی‌شود)
        await processing_msg.edit_text(
            f"✅ <b>آپلود موفق!</b>\n\n"
            f"🔗 لینک مستقیم:\n"
            f"<code>{link}</code>\n\n"
            f"💡 این لینک دائمی است و در هر زمانی قابل دانلود است",
            parse_mode="HTML"
        )
        
        await state.clear()
        await message.answer(
            "عملیات با موفقیت انجام شد ✅",
            reply_markup=get_main_keyboard()
        )
    
    except HostNotConfiguredError as e:
        # هاست هنوز تنظیم نشده
        await processing_msg.edit_text(
            "⏳ <b>این قابلیت به زودی فعال می‌شود</b>\n\n"
            "فعلاً می‌توانید از قابلیت «لینک به فایل» استفاده کنید.\n\n"
            "💡 برای تبدیل فایل به لینک، لطفاً منتظر بمانید تا این قابلیت فعال شود.",
            parse_mode="HTML"
        )
        
        await state.clear()
        await message.answer(
            "می‌توانید از منوی اصلی استفاده کنید:",
            reply_markup=get_main_keyboard()
        )
    
    except Exception as e:
        logger.error(
            f"❌ خطا در آپلود فایل: {type(e).__name__}",
            exc_info=True
        )
        
        await processing_msg.edit_text(
            f"❌ خطا در آپلود فایل:\n{str(e)}",
            parse_mode="HTML"
        )
        
        await state.clear()
        await message.answer(
            "لطفاً دوباره تلاش کنید",
            reply_markup=get_main_keyboard()
        )


async def handle_url_input(
    message: Message,
    state: FSMContext,
    service: FileTransferService
):
    """
    Handler دریافت URL از کاربر
    """
    url = message.text.strip()
    
    # اعتبارسنجی URL
    if not service.is_valid_direct_url(url):
        await message.answer(
            "❌ <b>لینک نامعتبر!</b>\n\n"
            "این لینک معتبر نیست یا از دامنه‌های مسدود شده است.\n\n"
            "✅ <b>لینک‌های معتبر:</b>\n"
            "• http://example.com/file.zip\n"
            "• https://cdn.example.com/video.mp4\n\n"
            "❌ <b>لینک‌های نامعتبر:</b>\n"
            "• youtube.com (برای YouTube از ربات دانلود شبکه‌های اجتماعی استفاده کنید)\n"
            "• instagram.com\n"
            "• aparat.com\n\n"
            "لطفاً یک لینک مستقیم ارسال کنید",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # پیام "در حال بررسی..."
    info_msg = await message.answer(
        "🔍 در حال بررسی لینک و شروع دانلود...",
        parse_mode="HTML"
    )
    
    temp_file = None
    
    try:
        # ⚠️ MVP: HEAD request در handler برای نمایش پیشرفت
        # TODO (بهبود): انتقال به service و برگرداندن progress
        import aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(url, allow_redirects=True, timeout=10) as response:
                    if response.status == 200:
                        content_length = response.headers.get('Content-Length')
                        if content_length:
                            file_size = int(content_length)
                            size_str = service._format_size(file_size)
                            
                            await info_msg.edit_text(
                                f"📊 <b>اطلاعات فایل:</b>\n\n"
                                f"📦 حجم: <b>{size_str}</b>\n"
                                f"🔗 منبع: <code>{url[:50]}...</code>\n\n"
                                f"⏬ شروع دانلود...",
                                parse_mode="HTML"
                            )
            except Exception as e:
                logger.warning(f"⚠️ HEAD request ناموفق: {type(e).__name__}")
        
        # پیام "در حال دانلود..."
        await info_msg.edit_text(
            "⏬ <b>در حال دانلود فایل...</b>\n\n"
            "⏳ این ممکن است چند دقیقه طول بکشد\n"
            "لطفاً صبر کنید...",
            parse_mode="HTML"
        )
        
        # دانلود فایل
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = await service.download_from_url(url, temp_dir)
            
            # دریافت اطلاعات فایل دانلود شده
            file_info = service.get_file_info(temp_file)
            
            await info_msg.edit_text(
                f"📤 <b>در حال ارسال فایل...</b>\n\n"
                f"📝 نام: <code>{file_info['name']}</code>\n"
                f"📊 حجم: <b>{file_info['size_str']}</b>",
                parse_mode="HTML"
            )
            
            # ارسال فایل به کاربر
            await message.answer_document(
                document=FSInputFile(temp_file, filename=file_info['name']),
                caption=(
                    f"✅ <b>دانلود موفق!</b>\n\n"
                    f"📝 نام: <code>{file_info['name']}</code>\n"
                    f"📊 حجم: <b>{file_info['size_str']}</b>\n"
                    f"📦 نوع: <code>{file_info['mime_type']}</code>"
                ),
                parse_mode="HTML"
            )
            
            # پاک کردن فایل موقت (اتفاقاً with TemporaryDirectory خودش این کار را می‌کند)
        
        await info_msg.delete()
        
        await state.clear()
        await message.answer(
            "✅ عملیات با موفقیت انجام شد!",
            reply_markup=get_main_keyboard()
        )
    
    except InvalidURLError as e:
        await info_msg.edit_text(
            "❌ <b>لینک نامعتبر!</b>\n\n"
            "این لینک معتبر نیست یا از دامنه‌های مسدود شده است.\n\n"
            "✅ لطفاً یک لینک مستقیم به فایل ارسال کنید",
            parse_mode="HTML"
        )
        
        await state.clear()
        await message.answer(
            "لطفاً یک لینک معتبر ارسال کنید",
            reply_markup=get_main_keyboard()
        )
    
    except FileTooLargeError as e:
        await info_msg.edit_text(
            "❌ <b>فایل بزرگ است!</b>\n\n"
            "حجم این فایل بیشتر از حداکثر مجاز است.\n\n"
            "💡 حداکثر حجم مجاز: 2GB\n\n"
            "لطفاً فایل کوچکتری ارسال کنید",
            parse_mode="HTML"
        )
        
        await state.clear()
        await message.answer(
            "لطفاً فایل کوچکتری ارسال کنید",
            reply_markup=get_main_keyboard()
        )
    
    except DownloadError as e:
        await info_msg.edit_text(
            "❌ <b>خطا در دانلود!</b>\n\n"
            "متأسفانه دانلود فایل ناموفق بود.\n\n"
            "دلایل احتمالی:\n"
            "• لینک منقضی شده است\n"
            "• سرور در دسترس نیست\n"
            "• اتصال اینترنت قطع شد\n\n"
            "💡 لطفاً دوباره تلاش کنید",
            parse_mode="HTML"
        )
        
        await state.clear()
        await message.answer(
            "لطفاً دوباره تلاش کنید",
            reply_markup=get_main_keyboard()
        )
    
    except Exception as e:
        logger.error(
            f"❌ خطای غیرمنتظره در دانلود: {type(e).__name__}",
            exc_info=True
        )
        
        await info_msg.edit_text(
            f"❌ <b>خطای غیرمنتظره!</b>\n\n"
            f"نوع خطا: <code>{type(e).__name__}</code>\n\n"
            f"لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید",
            parse_mode="HTML"
        )
        
        await state.clear()
        await message.answer(
            "لطفاً دوباره تلاش کنید",
            reply_markup=get_main_keyboard()
        )


async def handle_help(message: Message, state: FSMContext):
    """
    Handler دکمه راهنما
    """
    await state.clear()
    
    help_text = (
        "📖 <b>راهنمای استفاده</b>\n\n"
        "<b>📤 فایل به لینک:</b>\n"
        "۱. روی دکمه «فایل به لینک» کلیک کنید\n"
        "۲. فایل خود را ارسال کنید\n"
        "۳. لینک مستقیم دریافت کنید\n"
        "⏳ <i>به زودی فعال می‌شود</i>\n\n"
        "<b>📥 لینک به فایل:</b>\n"
        "۱. روی دکمه «لینک به فایل» کلیک کنید\n"
        "۲. لینک مستقیم فایل را ارسال کنید\n"
        "۳. فایل را از ربات دریافت کنید\n"
        "✅ <i>فعال است</i>\n\n"
        "<b>💡 نکات مهم:</b>\n"
        "• حداکثر حجم: 2GB\n"
        "• فقط لینک‌های مستقیم (نه YouTube/Instagram)\n"
        "• برای شبکه‌های اجتماعی از ربات دانلود اختصاصی استفاده کنید\n\n"
        "<b>❌ لینک‌های غیرمجاز:</b>\n"
        "• youtube.com, youtu.be\n"
        "• instagram.com\n"
        "• aparat.com\n"
        "• twitter.com, facebook.com\n"
        "• tiktok.com\n\n"
        "برای هر سوالی با پشتیبانی تماس بگیرید 💬"
    )
    
    await message.answer(
        help_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


async def handle_support(message: Message, state: FSMContext):
    """
    Handler دکمه پشتیبانی
    """
    await state.clear()
    
    support_text = (
        "💬 <b>پشتیبانی</b>\n\n"
        "برای ارتباط با پشتیبانی از راه‌های زیر استفاده کنید:\n\n"
        "📱 تلگرام: @YourSupportUsername\n"
        "📧 ایمیل: support@example.com\n"
        "☎️ تلفن: 021-12345678\n\n"
        "⏰ ساعات پاسخگویی: 9 صبح تا 9 شب\n\n"
        "💡 قبل از تماس با پشتیبانی، راهنما را مطالعه کنید"
    )
    
    await message.answer(
        support_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


async def handle_cancel(message: Message, state: FSMContext):
    """
    Handler دکمه لغو
    
    این handler عملیات جاری را لغو می‌کند و state را پاک می‌کند
    """
    await state.clear()
    
    await message.answer(
        "❌ عملیات لغو شد",
        reply_markup=get_main_keyboard()
    )
