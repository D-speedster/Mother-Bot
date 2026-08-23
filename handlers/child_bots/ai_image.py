"""
Child Bot: AI Image Generator (Product-ready Template)

⚠️ این نسخه Product-ready است:
- UI/UX کامل با Reply + Inline Keyboards
- State Machine کامل
- GenerationService برای Business Logic
- MockProvider برای شبیه‌سازی
- آماده برای اتصال به Real AI Provider

این Bot از همان Runtime فعلی پروژه استفاده می‌کند
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.ai_image_keyboards import (
    get_main_reply_keyboard,
    get_cancel_reply_keyboard,
    get_style_keyboard,
    get_ratio_keyboard,
    get_quality_keyboard,
    get_count_keyboard,
    get_preview_keyboard,
    get_result_keyboard,
    get_settings_keyboard,
    get_image_detail_keyboard
)

from services.ai_image import (
    GenerationService,
    GenerationRequest,
    ImageStyle,
    AspectRatio,
    Quality
)

logger = logging.getLogger(__name__)


# ========== FSM States ==========
class AIImageStates(StatesGroup):
    """State‌های FSM برای AI Image Bot"""
    # Wizard States
    waiting_for_prompt = State()
    selecting_style = State()
    selecting_ratio = State()
    selecting_quality = State()
    selecting_count = State()
    preview = State()
    processing = State()
    
    # Edit States
    editing_prompt = State()


# ========== Service Instance ==========
# این instance برای هر Bot جداگانه ساخته می‌شود
# چون هر Bot در Runtime جداگانه اجرا می‌شود
generation_service = GenerationService()


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
    
    # ========== Command Handlers ==========
    router.message.register(cmd_start, Command("start"))
    router.message.register(cmd_help, Command("help"))
    
    # ========== Reply Keyboard Handlers ==========
    router.message.register(handle_create_button, F.text == "🖼️ ساخت تصویر")
    router.message.register(handle_gallery_button, F.text == "🖼️ تصاویر من")
    router.message.register(handle_profile_button, F.text == "👤 حساب کاربری")
    router.message.register(handle_settings_button, F.text == "⚙️ تنظیمات")
    router.message.register(handle_help_button, F.text == "📖 راهنما")
    router.message.register(handle_cancel_button, F.text == "❌ لغو")
    
    # ========== Callback Handlers ==========
    # Home
    router.callback_query.register(callback_home, F.data == "ai:home")
    router.callback_query.register(callback_cancel, F.data == "ai:cancel")
    
    # Gallery
    router.callback_query.register(callback_gallery, F.data == "ai:gallery")
    
    # Style Selection
    router.callback_query.register(
        callback_style_selected,
        F.data.startswith("ai:style:")
    )
    
    # Ratio Selection
    router.callback_query.register(
        callback_ratio_selected,
        F.data.startswith("ai:ratio:")
    )
    
    # Quality Selection
    router.callback_query.register(
        callback_quality_selected,
        F.data.startswith("ai:quality:")
    )
    
    # Count Selection
    router.callback_query.register(
        callback_count_selected,
        F.data.startswith("ai:count:")
    )
    
    # Generate
    router.callback_query.register(callback_generate, F.data == "ai:generate")
    router.callback_query.register(callback_regenerate, F.data == "ai:regenerate")
    
    # Edit
    router.callback_query.register(
        callback_edit,
        F.data.startswith("ai:edit:")
    )
    
    # Settings
    router.callback_query.register(
        callback_settings,
        F.data.startswith("ai:settings:")
    )
    
    # ========== FSM Handlers ==========
    router.message.register(
        handle_prompt_input,
        AIImageStates.waiting_for_prompt
    )
    router.message.register(
        handle_edit_prompt_input,
        AIImageStates.editing_prompt
    )
    
    return router


# ⚠️ DEPRECATED: این router global دیگر استفاده نمی‌شود
ai_image_router = Router(name="ai_image_legacy")


# ========== Helper Functions ==========

def format_generation_preview(data: dict) -> str:
    """فرمت کردن Preview تولید تصویر"""
    prompt = data.get('prompt', 'N/A')
    style = data.get('style', ImageStyle.NONE)
    ratio = data.get('aspect_ratio', AspectRatio.SQUARE)
    quality = data.get('quality', Quality.STANDARD)
    count = data.get('count', 1)
    
    return (
        "🎨 **آماده تولید تصویر**\n\n"
        f"📝 **Prompt:**\n`{prompt}`\n\n"
        f"🎨 **سبک:** {style.get_display_name()}\n"
        f"📐 **نسبت:** {ratio.get_display_name()}\n"
        f"⚡ **کیفیت:** {quality.get_display_name()}\n"
        f"🖼️ **تعداد:** {count}\n\n"
        "برای تولید تصویر روی دکمه «✅ تولید تصویر» کلیک کنید."
    )


# ========== Command: /start ==========
async def cmd_start(message: Message, state: FSMContext):
    """Handler دستور /start - نمایش صفحه اصلی با Reply Keyboard"""
    await state.clear()
    
    try:
        bot_info = await message.bot.me()
        bot_name = bot_info.first_name or "AI Image Bot"
    except Exception:
        bot_name = "AI Image Bot"
    
    welcome_text = (
        f"🖼️ **به {bot_name} خوش آمدید!**\n\n"
        f"✨ استودیو تولید تصویر با هوش مصنوعی\n\n"
        f"در این نسخه رابط کامل تولید تصویر آماده است.\n"
        f"اتصال به موتور تولید تصویر واقعی در مرحله بعد انجام خواهد شد.\n\n"
        f"از منوی زیر یک گزینه را انتخاب کنید:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_reply_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(f"کاربر {message.from_user.id} AI Image Bot را شروع کرد")


# ========== Command: /help ==========
async def cmd_help(message: Message):
    """نمایش راهنمای کامل"""
    help_text = (
        "📖 **راهنمای AI Image**\n\n"
        "**مراحل تولید تصویر:**\n\n"
        "1️⃣ روی «🖼️ ساخت تصویر» کلیک کنید\n"
        "2️⃣ Prompt خود را بنویسید\n"
        "3️⃣ سبک تصویر را انتخاب کنید\n"
        "4️⃣ نسبت و کیفیت را مشخص کنید\n"
        "5️⃣ تعداد تصاویر را انتخاب کنید\n"
        "6️⃣ درخواست را تأیید کنید\n\n"
        "💡 **نکات:**\n"
        "• Prompt را به انگلیسی بنویسید\n"
        "• هرچه جزئیات بیشتر، کنترل بیشتر\n"
        "• از کلمات کلیدی دقیق استفاده کنید\n\n"
        "📝 **مثال Prompt خوب:**\n"
        "`a futuristic city at night, neon lights, cyberpunk style, highly detailed`"
    )
    
    await message.answer(
        help_text,
        reply_markup=get_main_reply_keyboard(),
        parse_mode="Markdown"
    )


# ========== Reply Keyboard: ساخت تصویر ==========
async def handle_create_button(message: Message, state: FSMContext):
    """شروع Wizard ساخت تصویر - Step 1: Prompt"""
    await state.set_state(AIImageStates.waiting_for_prompt)
    
    text = (
        "� **توضیح تصویر موردنظر خود را وارد کنید:**\n\n"
        "**مثال:**\n"
        "• یک شهر آینده‌نگر در شب، نورهای نئونی، فضای سینمایی\n"
        "• a futuristic city at night, neon lights, cinematic\n\n"
        "💡 Prompt را به **انگلیسی** بنویسید تا نتیجه بهتری دریافت کنید."
    )
    
    await message.answer(
        text,
        reply_markup=get_cancel_reply_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(f"کاربر {message.from_user.id} وارد Wizard ساخت تصویر شد")


# ========== FSM: Prompt Input ==========
async def handle_prompt_input(message: Message, state: FSMContext):
    """دریافت Prompt از کاربر - Step 2: Style"""
    prompt = message.text.strip()
    
    # Validation
    if len(prompt) < 3:
        await message.answer(
            "⚠️ Prompt باید حداقل 3 کاراکتر باشد.",
            reply_markup=get_cancel_reply_keyboard()
        )
        return
    
    if len(prompt) > 500:
        await message.answer(
            "⚠️ Prompt نباید بیش از 500 کاراکتر باشد.\n\n"
            "لطفاً توضیح کوتاه‌تری بنویسید.",
            reply_markup=get_cancel_reply_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # ذخیره در State
    await state.update_data(prompt=prompt)
    await state.set_state(AIImageStates.selecting_style)
    
    # نمایش انتخاب Style
    text = (
        "🎨 **سبک تصویر را انتخاب کنید:**\n\n"
        "سبک مشخص می‌کند تصویر شما چه حس و حالی داشته باشد."
    )
    
    await message.answer(
        text,
        reply_markup=get_style_keyboard(),
        parse_mode="Markdown"
    )


# ========== Callback: Style Selected ==========
async def callback_style_selected(callback: CallbackQuery, state: FSMContext):
    """انتخاب Style - Step 3: Ratio"""
    style_key = callback.data.split(":")[-1]
    
    # تبدیل به Enum
    style_map = {
        "realistic": ImageStyle.REALISTIC,
        "cinematic": ImageStyle.CINEMATIC,
        "anime": ImageStyle.ANIME,
        "digital_art": ImageStyle.DIGITAL_ART,
        "photography": ImageStyle.PHOTOGRAPHY,
        "none": ImageStyle.NONE
    }
    
    style = style_map.get(style_key, ImageStyle.NONE)
    
    # ذخیره در State
    await state.update_data(style=style)
    await state.set_state(AIImageStates.selecting_ratio)
    
    # نمایش انتخاب Ratio
    text = (
        "📐 **نسبت تصویر را انتخاب کنید:**\n\n"
        "• 1:1 برای پست‌های اینستاگرام\n"
        "• 16:9 برای والپیپر یا ویدیو\n"
        "• 9:16 برای استوری\n"
        "• 4:3 برای عکس کلاسیک"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_ratio_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Ratio Selected ==========
async def callback_ratio_selected(callback: CallbackQuery, state: FSMContext):
    """انتخاب Ratio - Step 4: Quality"""
    ratio_key = callback.data.split(":")[-1]
    
    # تبدیل به Enum
    ratio_map = {
        "1x1": AspectRatio.SQUARE,
        "16x9": AspectRatio.LANDSCAPE,
        "9x16": AspectRatio.PORTRAIT,
        "4x3": AspectRatio.STANDARD
    }
    
    ratio = ratio_map.get(ratio_key, AspectRatio.SQUARE)
    
    # ذخیره در State
    await state.update_data(aspect_ratio=ratio)
    await state.set_state(AIImageStates.selecting_quality)
    
    # نمایش انتخاب Quality
    text = (
        "⚡ **کیفیت تصویر را انتخاب کنید:**\n\n"
        "• **استاندارد:** سریع‌تر، مناسب برای تست\n"
        "• **بالا:** کیفیت بهتر، زمان بیشتر"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_quality_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Quality Selected ==========
async def callback_quality_selected(callback: CallbackQuery, state: FSMContext):
    """انتخاب Quality - Step 5: Count"""
    quality_key = callback.data.split(":")[-1]
    
    # تبدیل به Enum
    quality_map = {
        "standard": Quality.STANDARD,
        "high": Quality.HIGH
    }
    
    quality = quality_map.get(quality_key, Quality.STANDARD)
    
    # ذخیره در State
    await state.update_data(quality=quality)
    await state.set_state(AIImageStates.selecting_count)
    
    # نمایش انتخاب Count
    text = (
        "🖼️ **چند تصویر تولید شود؟**\n\n"
        "می‌توانید چند نسخه با Prompt یکسان تولید کنید."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_count_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Count Selected ==========
async def callback_count_selected(callback: CallbackQuery, state: FSMContext):
    """انتخاب Count - Step 6: Preview"""
    count = int(callback.data.split(":")[-1])
    
    # ذخیره در State
    await state.update_data(count=count)
    await state.set_state(AIImageStates.preview)
    
    # دریافت تمام Data
    data = await state.get_data()
    
    # نمایش Preview
    preview_text = format_generation_preview(data)
    
    await callback.message.edit_text(
        preview_text,
        reply_markup=get_preview_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Callback: Generate ==========
async def callback_generate(callback: CallbackQuery, state: FSMContext):
    """تولید تصویر - Step 7: Processing"""
    await state.set_state(AIImageStates.processing)
    
    # دریافت Data
    data = await state.get_data()
    user_id = callback.from_user.id
    
    # نمایش پیام Processing
    processing_text = (
        "🎨 **در حال آماده‌سازی تصویر...**\n\n"
        "⏳ وضعیت: Processing\n\n"
        "لطفاً چند لحظه صبر کنید..."
    )
    
    await callback.message.edit_text(
        processing_text,
        parse_mode="Markdown"
    )
    await callback.answer()
    
    try:
        # ساخت Request
        request = await generation_service.create_generation(
            user_id=user_id,
            prompt=data['prompt'],
            style=data.get('style', ImageStyle.NONE),
            aspect_ratio=data.get('aspect_ratio', AspectRatio.SQUARE),
            quality=data.get('quality', Quality.STANDARD),
            count=data.get('count', 1)
        )
        
        # اجرای Generation
        result = await generation_service.execute_generation(request)
        
        # نمایش نتیجه
        result_text = (
            "� **تولید تصویر انجام شد!**\n\n"
            f"{result.mock_result}\n\n"
            "💡 در نسخه واقعی اینجا تصویر نمایش داده می‌شود."
        )
        
        # ذخیره generation_id در State برای Regenerate
        await state.update_data(last_generation_id=result.generation_id)
        
        await callback.message.edit_text(
            result_text,
            reply_markup=get_result_keyboard(),
            parse_mode="Markdown"
        )
        
        # پاک کردن State
        await state.clear()
        
        logger.info(
            f"Generation completed for user {user_id}: "
            f"id={result.generation_id}"
        )
    
    except ValueError as e:
        # Validation Error
        await callback.message.edit_text(
            f"❌ **خطا:**\n{str(e)}\n\nلطفاً دوباره تلاش کنید.",
            parse_mode="Markdown"
        )
        await state.clear()
    
    except Exception as e:
        # خطای غیرمنتظره
        logger.error(
            f"Generation failed for user {user_id}: {type(e).__name__}",
            exc_info=True
        )
        
        await callback.message.edit_text(
            "❌ **خطایی رخ داد!**\n\n"
            "لطفاً دوباره تلاش کنید.",
            parse_mode="Markdown"
        )
        await state.clear()


# ادامه در بخش بعد...


# ========== Callback: Regenerate ==========
async def callback_regenerate(callback: CallbackQuery, state: FSMContext):
    """تولید مجدد با همان تنظیمات"""
    # دریافت last generation از state یا service
    data = await state.get_data()
    last_gen_id = data.get('last_generation_id')
    
    if not last_gen_id:
        await callback.answer(
            "❌ اطلاعات قبلی یافت نشد",
            show_alert=True
        )
        return
    
    user_id = callback.from_user.id
    
    # دریافت Generation قبلی
    last_result = generation_service.get_generation_by_id(last_gen_id, user_id)
    
    if not last_result:
        await callback.answer(
            "❌ درخواست قبلی یافت نشد",
            show_alert=True
        )
        return
    
    # نمایش Processing
    processing_text = (
        "🎨 **در حال تولید مجدد...**\n\n"
        "⏳ وضعیت: Processing\n\n"
        "لطفاً چند لحظه صبر کنید..."
    )
    
    await callback.message.edit_text(
        processing_text,
        parse_mode="Markdown"
    )
    await callback.answer()
    
    try:
        # ساخت Request جدید با همان تنظیمات
        request = await generation_service.create_generation(
            user_id=user_id,
            prompt=last_result.prompt,
            style=last_result.style,
            aspect_ratio=last_result.aspect_ratio,
            quality=last_result.quality,
            count=last_result.count
        )
        
        # اجرا
        result = await generation_service.execute_generation(request)
        
        # نمایش نتیجه
        result_text = (
            "🎉 **تولید مجدد انجام شد!**\n\n"
            f"{result.mock_result}\n\n"
            "💡 در نسخه واقعی اینجا تصویر نمایش داده می‌شود."
        )
        
        await state.update_data(last_generation_id=result.generation_id)
        
        await callback.message.edit_text(
            result_text,
            reply_markup=get_result_keyboard(),
            parse_mode="Markdown"
        )
        
        logger.info(f"Regeneration completed for user {user_id}")
    
    except Exception as e:
        logger.error(
            f"Regeneration failed for user {user_id}: {type(e).__name__}",
            exc_info=True
        )
        
        await callback.message.edit_text(
            "❌ **خطایی رخ داد!**\n\nلطفاً دوباره تلاش کنید.",
            parse_mode="Markdown"
        )


# ========== Callback: Edit ==========
async def callback_edit(callback: CallbackQuery, state: FSMContext):
    """ویرایش تنظیمات در Preview"""
    edit_type = callback.data.split(":")[-1]
    
    if edit_type == "prompt":
        # بازگشت به Prompt Input
        await state.set_state(AIImageStates.editing_prompt)
        
        text = (
            "✏️ **Prompt جدید را وارد کنید:**\n\n"
            "یا روی «❌ لغو» کلیک کنید تا به Preview بازگردید."
        )
        
        await callback.message.edit_text(
            text,
            parse_mode="Markdown"
        )
        await callback.answer()
    
    elif edit_type == "style":
        # بازگشت به Style Selection
        await state.set_state(AIImageStates.selecting_style)
        
        text = "🎨 **سبک جدید را انتخاب کنید:**"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_style_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    elif edit_type == "ratio":
        # بازگشت به Ratio Selection
        await state.set_state(AIImageStates.selecting_ratio)
        
        text = "📐 **نسبت جدید را انتخاب کنید:**"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_ratio_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    elif edit_type == "settings":
        # تغییر Quality و Count
        await state.set_state(AIImageStates.selecting_quality)
        
        text = "⚡ **کیفیت جدید را انتخاب کنید:**"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_quality_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()


# ========== FSM: Edit Prompt Input ==========
async def handle_edit_prompt_input(message: Message, state: FSMContext):
    """دریافت Prompt جدید در حالت Edit"""
    prompt = message.text.strip()
    
    # Validation
    if len(prompt) < 3:
        await message.answer(
            "⚠️ Prompt باید حداقل 3 کاراکتر باشد.",
            reply_markup=get_cancel_reply_keyboard()
        )
        return
    
    if len(prompt) > 500:
        await message.answer(
            "⚠️ Prompt نباید بیش از 500 کاراکتر باشد.",
            reply_markup=get_cancel_reply_keyboard()
        )
        return
    
    # به‌روزرسانی Prompt
    await state.update_data(prompt=prompt)
    await state.set_state(AIImageStates.preview)
    
    # بازگشت به Preview
    data = await state.get_data()
    preview_text = format_generation_preview(data)
    
    await message.answer(
        preview_text,
        reply_markup=get_preview_keyboard(),
        parse_mode="Markdown"
    )


# ========== Reply Keyboard: تصاویر من ==========
async def handle_gallery_button(message: Message, state: FSMContext):
    """نمایش گالری تصاویر"""
    await state.clear()
    user_id = message.from_user.id
    
    # دریافت History
    history = generation_service.get_user_history(user_id, limit=10)
    
    if not history:
        text = (
            "🖼️ **تصاویر من**\n\n"
            "❌ هنوز تصویری تولید نکرده‌اید.\n\n"
            "💡 برای شروع، روی «🖼️ ساخت تصویر» کلیک کنید."
        )
        
        await message.answer(
            text,
            reply_markup=get_main_reply_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # نمایش لیست History
    text = f"🖼️ **تصاویر من**\n\n📊 تعداد: {len(history)} تصویر\n\n"
    
    for i, result in enumerate(history[:5], 1):
        text += (
            f"{i}. `{result.prompt[:30]}...`\n"
            f"   🎨 {result.style.get_display_name()} • "
            f"📐 {result.aspect_ratio.value}\n\n"
        )
    
    text += "💡 برای مشاهده جزئیات، از منوی Inline استفاده کنید."
    
    await message.answer(
        text,
        reply_markup=get_main_reply_keyboard(),
        parse_mode="Markdown"
    )


# ========== Callback: Gallery ==========
async def callback_gallery(callback: CallbackQuery, state: FSMContext):
    """نمایش گالری (از Inline)"""
    user_id = callback.from_user.id
    
    history = generation_service.get_user_history(user_id, limit=10)
    
    if not history:
        text = (
            "🖼️ **گالری من**\n\n"
            "❌ هنوز تصویری تولید نکرده‌اید."
        )
        
        await callback.message.edit_text(
            text,
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    # نمایش لیست
    text = f"🖼️ **گالری من**\n\n📊 {len(history)} تصویر\n\n"
    
    for i, result in enumerate(history[:5], 1):
        text += (
            f"{i}. `{result.prompt[:30]}...`\n"
            f"   {result.style.get_display_name()}\n\n"
        )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown"
    )
    await callback.answer()


# ========== Reply Keyboard: حساب کاربری ==========
async def handle_profile_button(message: Message, state: FSMContext):
    """نمایش پروفایل کاربر"""
    await state.clear()
    user_id = message.from_user.id
    user = message.from_user
    
    # دریافت آمار
    stats = generation_service.get_user_stats(user_id)
    
    text = (
        "👤 **حساب کاربری**\n\n"
        f"**نام:** {user.first_name}\n"
        f"**شناسه:** `{user.id}`\n"
        f"**یوزرنیم:** @{user.username if user.username else 'ندارد'}\n\n"
        "📊 **آمار استفاده:**\n"
        f"🖼️ تصاویر تولیدشده: **{stats['total_images']}**\n"
        f"✨ درخواست‌ها: **{stats['total_requests']}**\n"
        f"✅ موفق: **{stats['completed_requests']}**"
    )
    
    await message.answer(
        text,
        reply_markup=get_main_reply_keyboard(),
        parse_mode="Markdown"
    )


# ========== Reply Keyboard: تنظیمات ==========
async def handle_settings_button(message: Message, state: FSMContext):
    """نمایش تنظیمات"""
    await state.clear()
    
    # دریافت تنظیمات فعلی (از State/Memory)
    # در نسخه واقعی از Database خوانده می‌شود
    
    text = (
        "⚙️ **تنظیمات**\n\n"
        "🎨 **سبک پیش‌فرض:** سینمایی\n"
        "📐 **نسبت پیش‌فرض:** 1:1\n"
        "⚡ **کیفیت پیش‌فرض:** استاندارد\n\n"
        "💡 تنظیمات پیش‌فرض در Wizard استفاده می‌شوند.\n\n"
        "⚠️ تغییر تنظیمات در نسخه فعلی Session-based است."
    )
    
    await message.answer(
        text,
        reply_markup=get_main_reply_keyboard(),
        parse_mode="Markdown"
    )


# ========== Callback: Settings ==========
async def callback_settings(callback: CallbackQuery, state: FSMContext):
    """مدیریت تنظیمات (Placeholder)"""
    setting_type = callback.data.split(":")[-1]
    
    text = (
        f"⚙️ **تنظیم {setting_type}**\n\n"
        "این قابلیت در نسخه فعلی فعال نیست.\n\n"
        "در نسخه آینده می‌توانید تنظیمات پیش‌فرض را تغییر دهید."
    )
    
    await callback.answer(
        "این قابلیت در نسخه فعلی فعال نیست",
        show_alert=True
    )


# ========== Reply Keyboard: راهنما ==========
async def handle_help_button(message: Message, state: FSMContext):
    """نمایش راهنما"""
    await state.clear()
    
    help_text = (
        "📖 **راهنمای استفاده از AI Image**\n\n"
        "**مراحل تولید تصویر:**\n\n"
        "1️⃣ روی «🖼️ ساخت تصویر» کلیک کنید\n"
        "2️⃣ Prompt خود را بنویسید\n"
        "3️⃣ سبک تصویر را انتخاب کنید\n"
        "4️⃣ نسبت و کیفیت را مشخص کنید\n"
        "5️⃣ تعداد تصاویر را انتخاب کنید\n"
        "6️⃣ Preview را بررسی و تأیید کنید\n\n"
        "💡 **نکات مهم:**\n"
        "• Prompt را به انگلیسی بنویسید\n"
        "• هرچه جزئیات بیشتر، نتیجه بهتر\n"
        "• از کلمات کلیدی دقیق استفاده کنید\n\n"
        "📝 **مثال Prompt خوب:**\n"
        "`a futuristic city at night, neon lights, cyberpunk style`"
    )
    
    await message.answer(
        help_text,
        reply_markup=get_main_reply_keyboard(),
        parse_mode="Markdown"
    )


# ========== Reply Keyboard: لغو ==========
async def handle_cancel_button(message: Message, state: FSMContext):
    """لغو فرآیند و بازگشت به Home"""
    current_state = await state.get_state()
    
    if current_state is None:
        # هیچ State فعالی وجود ندارد
        await message.answer(
            "شما در منوی اصلی هستید.",
            reply_markup=get_main_reply_keyboard()
        )
        return
    
    # پاک کردن State
    await state.clear()
    
    text = (
        "❌ **لغو شد**\n\n"
        "فرآیند لغو شد. از منوی زیر یک گزینه را انتخاب کنید."
    )
    
    await message.answer(
        text,
        reply_markup=get_main_reply_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(f"کاربر {message.from_user.id} فرآیند را لغو کرد")


# ========== Callback: Cancel ==========
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    """لغو از Inline Callback"""
    await state.clear()
    
    text = (
        "❌ **لغو شد**\n\n"
        "فرآیند لغو شد. از منوی زیر یک گزینه را انتخاب کنید."
    )
    
    # نمایش پیام جدید با Reply Keyboard
    await callback.message.answer(
        text,
        reply_markup=get_main_reply_keyboard(),
        parse_mode="Markdown"
    )
    
    # حذف پیام Inline
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.answer("لغو شد")


# ========== Callback: Home ==========
async def callback_home(callback: CallbackQuery, state: FSMContext):
    """بازگشت به Home"""
    await state.clear()
    
    text = (
        "🏠 **منوی اصلی**\n\n"
        "از منوی زیر یک گزینه را انتخاب کنید:"
    )
    
    # نمایش پیام جدید با Reply Keyboard
    await callback.message.answer(
        text,
        reply_markup=get_main_reply_keyboard(),
        parse_mode="Markdown"
    )
    
    # حذف پیام Inline
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.answer()
