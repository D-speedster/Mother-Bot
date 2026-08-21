"""
Child Bot: AI Image Generator (UI Prototype)

⚠️ این یک Prototype UI است:
- هیچ تصویر واقعی تولید نمی‌شود
- هیچ API خارجی استفاده نمی‌شود
- هیچ GPU یا Stable Diffusion نیست
- فقط Mock Flow برای نمایش UI

این Bot از همان Runtime فعلی پروژه استفاده می‌کند
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.ai_image_keyboards import (
    get_main_menu_keyboard,
    get_cancel_keyboard,
    get_result_keyboard,
    get_gallery_keyboard,
    get_profile_keyboard,
    get_help_keyboard
)

logger = logging.getLogger(__name__)


# ========== FSM States ==========
class AIImageStates(StatesGroup):
    """State‌های FSM برای AI Image Bot"""
    waiting_for_prompt = State()


# ========== Router Factory Function ==========
def get_router() -> Router:
    """
    ساخت و برگرداندن Router جدید برای AI Image Bot
    
    ⚠️ CRITICAL: این تابع هر بار یک Router جدید می‌سازد
    - این از تداخل Router بین ربات‌های مختلف جلوگیری می‌کند
    - هر ربات فرزند Router اختصاصی خود را دارد
    
    Returns:
        Router جدید با تمام handler‌های ثبت‌شده
    """
    router = Router(name="ai_image_bot")
    
    # ثبت handler‌ها
    router.message.register(cmd_start, Command("start"))
    router.message.register(cmd_help, Command("help"))
    
    # Callback handlers با namespace ai:
    router.callback_query.register(callback_home, F.data == "ai:home")
    router.callback_query.register(callback_create, F.data == "ai:create")
    router.callback_query.register(callback_gallery, F.data == "ai:gallery")
    router.callback_query.register(callback_help, F.data == "ai:help")
    router.callback_query.register(callback_profile, F.data == "ai:profile")
    router.callback_query.register(callback_cancel, F.data == "ai:cancel")
    
    # FSM handler برای دریافت prompt
    router.message.register(handle_prompt_input, AIImageStates.waiting_for_prompt)
    
    return router


# ⚠️ DEPRECATED: این router global دیگر استفاده نمی‌شود
# فقط برای backward compatibility نگه داشته شده
ai_image_router = Router(name="ai_image_legacy")


# ========== Handler: /start ==========
async def cmd_start(message: Message, state: FSMContext):
    """
    Handler دستور /start
    نمایش صفحه اصلی
    """
    # Clear کردن state قبلی (اگر وجود داشته باشد)
    await state.clear()
    
    # دریافت نام ربات
    try:
        bot_info = await message.bot.me()
        bot_name = bot_info.first_name or "AI Image Bot"
    except Exception:
        bot_name = "AI Image Bot"
    
    welcome_text = (
        f"🖼️ **به {bot_name} خوش آمدید!**\n\n"
        f"✨ استودیو تولید تصویر با هوش مصنوعی\n\n"
        f"💡 **در این نسخه می‌توانید:**\n"
        f"• رابط کاربری تولید تصویر را مشاهده کنید\n"
        f"• Flow کامل را تجربه کنید\n\n"
        f"⚠️ **توجه:** این نسخه Prototype است و تصویر واقعی تولید نمی‌شود.\n\n"
        f"از منوی زیر یک گزینه را انتخاب کنید:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(f"کاربر {message.from_user.id} AI Image Bot را شروع کرد")


# ========== Handler: /help ==========
async def cmd_help(message: Message):
    """نمایش راهنمای استفاده از ربات"""
    help_text = (
        "📖 **راهنمای استفاده**\n\n"
        "**چگونه تصویر بسازم؟**\n"
        "1️⃣ روی دکمه «✨ ساخت تصویر» کلیک کنید\n"
        "2️⃣ توضیح تصویر موردنظر را به انگلیسی بنویسید\n"
        "3️⃣ منتظر نتیجه بمانید\n\n"
        "**مثال‌های Prompt:**\n"
        "• `a futuristic city at night`\n"
        "• `a cat wearing sunglasses`\n"
        "• `beautiful sunset over ocean`\n\n"
        "⚠️ **توجه:** این نسخه Prototype است.\n"
        "در نسخه آینده تصاویر واقعی تولید خواهند شد."
    )
    
    await message.answer(
        help_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(f"کاربر {message.from_user.id} راهنما را مشاهده کرد")


# ========== Callback: Home ==========
async def callback_home(callback: CallbackQuery, state: FSMContext):
    """بازگشت به صفحه اصلی"""
    await state.clear()
    
    text = (
        "🖼️ **استودیو AI Image**\n\n"
        "✨ به استودیو تولید تصویر هوش مصنوعی خوش آمدید.\n\n"
        "در این نسخه می‌توانید رابط کاربری تولید تصویر را مشاهده کنید.\n\n"
        "از منوی زیر یک گزینه را انتخاب کنید:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Create Image ==========
async def callback_create(callback: CallbackQuery, state: FSMContext):
    """شروع فرآیند ساخت تصویر"""
    await state.set_state(AIImageStates.waiting_for_prompt)
    
    text = (
        "✨ **ساخت تصویر جدید**\n\n"
        "📝 لطفاً توضیح تصویر موردنظر خود را به **انگلیسی** وارد کنید:\n\n"
        "**مثال:**\n"
        "• `a beautiful landscape with mountains`\n"
        "• `a futuristic robot`\n"
        "• `cute cat playing with ball`\n\n"
        "💡 هرچه Prompt دقیق‌تر باشد، نتیجه بهتر خواهد بود."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()
    logger.info(f"کاربر {callback.from_user.id} وارد حالت ساخت تصویر شد")


# ========== Callback: Gallery ==========
async def callback_gallery(callback: CallbackQuery):
    """نمایش گالری تصاویر"""
    user = callback.from_user
    
    text = (
        "🖼️ **گالری من**\n\n"
        f"👤 کاربر: {user.first_name}\n\n"
        "📊 آمار:\n"
        "• تصاویر تولیدشده: **0**\n"
        "• درخواست‌های انجام‌شده: **0**\n\n"
        "❌ هنوز تصویری تولید نکرده‌اید.\n\n"
        "💡 برای شروع، روی دکمه «✨ ساخت تصویر» کلیک کنید."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_gallery_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()
    logger.info(f"کاربر {callback.from_user.id} گالری را مشاهده کرد")


# ========== Callback: Help ==========
async def callback_help(callback: CallbackQuery):
    """نمایش راهنما"""
    text = (
        "📖 **راهنمای استفاده**\n\n"
        "**مراحل تولید تصویر:**\n\n"
        "1️⃣ روی «✨ ساخت تصویر» کلیک کنید\n\n"
        "2️⃣ توضیح تصویر موردنظر را به انگلیسی بنویسید\n\n"
        "3️⃣ در نسخه آینده تصویر تولید خواهد شد\n\n"
        "**نکات مهم:**\n"
        "• Prompt را به انگلیسی بنویسید\n"
        "• هرچه جزئیات بیشتر، نتیجه بهتر\n"
        "• از کلمات کلیدی استفاده کنید\n\n"
        "⚠️ **توجه:**\n"
        "این نسخه صرفاً Prototype است و تصویر واقعی تولید نمی‌شود."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_help_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Profile ==========
async def callback_profile(callback: CallbackQuery):
    """نمایش پروفایل کاربر"""
    user = callback.from_user
    
    text = (
        "👤 **حساب کاربری**\n\n"
        f"**نام:** {user.first_name}\n"
        f"**شناسه:** `{user.id}`\n"
        f"**یوزرنیم:** @{user.username if user.username else 'ندارد'}\n\n"
        "📊 **آمار استفاده:**\n"
        "🖼️ تصاویر تولیدشده: **0**\n"
        "✨ درخواست‌های انجام‌شده: **0**\n\n"
        "💡 این اطلاعات در نسخه Prototype Mock هستند."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_profile_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()
    logger.info(f"کاربر {callback.from_user.id} پروفایل را مشاهده کرد")


# ========== Callback: Cancel ==========
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    """لغو فرآیند و بازگشت به منوی اصلی"""
    await state.clear()
    
    text = (
        "❌ **لغو شد**\n\n"
        "فرآیند ساخت تصویر لغو شد.\n\n"
        "از منوی زیر یک گزینه را انتخاب کنید:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("لغو شد")
    logger.info(f"کاربر {callback.from_user.id} فرآیند ساخت تصویر را لغو کرد")


# ========== Handler: Prompt Input ==========
async def handle_prompt_input(message: Message, state: FSMContext):
    """پردازش ورودی Prompt"""
    prompt = message.text.strip()
    
    if not prompt:
        await message.answer(
            "⚠️ لطفاً یک توضیح معتبر وارد کنید.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # محدودیت طول Prompt
    if len(prompt) > 500:
        await message.answer(
            "⚠️ توضیح شما خیلی طولانی است.\n\n"
            "لطفاً حداکثر 500 کاراکتر وارد کنید.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Clear state
    await state.clear()
    
    # نمایش نتیجه Mock
    result_text = (
        "🎨 **درخواست شما دریافت شد**\n\n"
        f"📝 **Prompt:**\n`{prompt}`\n\n"
        "⏳ **وضعیت:** Prototype\n\n"
        "⚠️ تولید تصویر در این نسخه فعال نیست.\n\n"
        "💡 **در نسخه آینده:**\n"
        "• تصویر با کیفیت بالا تولید خواهد شد\n"
        "• امکان انتخاب استایل\n"
        "• تنظیمات پیشرفته\n"
        "• دانلود با کیفیت HD"
    )
    
    await message.answer(
        result_text,
        reply_markup=get_result_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(
        f"کاربر {message.from_user.id} Prompt ارسال کرد: "
        f"{prompt[:50]}{'...' if len(prompt) > 50 else ''}"
    )
