"""
AI Image Bot - Admin Panel Handler

⚠️ CRITICAL RULES:
1. این Handler فقط برای AI Image Bot است
2. Mother Bot را تغییر نمی‌دهد
3. Owner-Based Authorization را بررسی می‌کند (Bot Instance Ownership)
4. Error Handling امن دارد (هیچ Stack Trace به Admin نمی‌فرستد)
5. از Reply Keyboard برای Navigation اصلی استفاده می‌کند
6. از Inline Keyboard فقط برای Actions استفاده می‌کند

AUTHORIZATION:
- هر کاربری که Bot می‌سازد، Owner آن Bot است
- فقط Owner می‌تواند Admin Panel را ببیند
- دسترسی غیرمجاز کاملاً Silent است (هیچ پاسخی ارسال نمی‌شود)
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.ai_image_admin_keyboards import (
    get_admin_main_keyboard,
    get_back_keyboard,
    get_management_keyboard,
    get_communication_keyboard,
    get_broadcast_target_keyboard,
    get_broadcast_confirm_keyboard,
    get_sponsor_keyboard,
    get_ads_keyboard,
    get_ai_settings_keyboard,
    get_styles_list_keyboard,
    get_style_edit_keyboard,
    get_content_keyboard,
    get_faq_list_keyboard,
    get_faq_edit_keyboard,
    get_faq_delete_confirm_keyboard,
    get_system_messages_keyboard,
    get_system_keyboard,
    get_maintenance_keyboard,
    get_maintenance_confirm_keyboard
)

from services.ai_image import (
    AdminService,
    ConfigService,
    ContentService,
    BroadcastService,
    MaintenanceMode
)

logger = logging.getLogger(__name__)


# ========== Owner-Based Authorization ==========

def get_bot_context(message_or_callback) -> dict:
    """
    دریافت Bot Context از Bot Instance
    
    Args:
        message_or_callback: Message یا CallbackQuery object
        
    Returns:
        dict شامل bot_id, owner_id, bot_type
        اگر context موجود نباشد، dict خالی برمی‌گرداند
    """
    try:
        bot = message_or_callback.bot
        return getattr(bot, 'bot_context', {})
    except Exception as e:
        logger.error(f"خطا در دریافت bot_context: {e}")
        return {}


def is_owner(user_id: int, bot_context: dict) -> bool:
    """
    بررسی Owner بودن کاربر
    
    این تابع چک می‌کند که آیا user_id با owner_id ذخیره‌شده
    در bot_context مطابقت دارد یا خیر.
    
    Args:
        user_id: شناسه کاربر Telegram
        bot_context: dict شامل bot_id و owner_id
        
    Returns:
        True اگر کاربر Owner این Bot باشد
        
    Security:
    - هر Bot Instance context مستقل خودش را دارد
    - Owner یک Bot نمی‌تواند به Admin Panel Bot دیگری دسترسی داشته باشد
    """
    owner_id = bot_context.get('owner_id')
    if owner_id is None:
        logger.warning("owner_id در bot_context موجود نیست")
        return False
    
    return user_id == owner_id


# ========== FSM States ==========

class AdminStates(StatesGroup):
    """State‌های FSM برای Admin Panel"""
    # Broadcast
    waiting_for_broadcast_message = State()
    waiting_for_broadcast_confirmation = State()
    
    # Sponsor
    editing_sponsor_text = State()
    editing_sponsor_url = State()
    
    # Ads
    editing_ad_text = State()
    editing_ad_url = State()
    editing_ad_frequency = State()
    
    # AI Settings
    editing_prompt_setting = State()
    editing_generation_limit = State()
    editing_style_name = State()
    editing_style_desc = State()
    editing_style_modifier = State()
    
    # Content
    editing_guide = State()
    creating_faq_question = State()
    creating_faq_answer = State()
    editing_faq_question = State()
    editing_faq_answer = State()
    editing_system_message = State()
    
    # Maintenance
    editing_maintenance_message = State()


# ========== Service Instances ==========
# این Instances برای هر Bot جداگانه ساخته می‌شوند
admin_service = AdminService()
config_service = ConfigService()
content_service = ContentService()
broadcast_service = BroadcastService()


# ========== Router Factory ==========

def get_admin_router() -> Router:
    """
    ساخت و برگرداندن Admin Router
    
    Returns:
        Router جدید با تمام handler‌های Admin
    """
    router = Router(name="ai_image_admin")
    
    # ========== Commands ==========
    router.message.register(cmd_admin, Command("admin"))
    
    # ========== Reply Keyboard Navigation ==========
    router.message.register(handle_management_button, F.text == "📊 مدیریت")
    router.message.register(handle_communication_button, F.text == "📢 ارتباط")
    router.message.register(handle_ai_button, F.text == "🧠 AI")
    router.message.register(handle_content_button, F.text == "📚 محتوا")
    router.message.register(handle_system_button, F.text == "⚙️ سیستم")
    router.message.register(handle_back_button, F.text == "⬅️ بازگشت")
    
    # ========== Callback Handlers: Management ==========
    router.callback_query.register(
        callback_management_main,
        F.data == "admin:mgmt:main"
    )
    router.callback_query.register(
        callback_user_stats,
        F.data == "admin:mgmt:users"
    )
    router.callback_query.register(
        callback_active_users,
        F.data == "admin:mgmt:active_users"
    )
    router.callback_query.register(
        callback_generation_stats,
        F.data == "admin:mgmt:generations"
    )
    router.callback_query.register(
        callback_revenue_stats,
        F.data == "admin:mgmt:revenue"
    )
    router.callback_query.register(
        callback_refresh_stats,
        F.data == "admin:mgmt:refresh"
    )
    
    # ========== Callback Handlers: Communication ==========
    router.callback_query.register(
        callback_communication_main,
        F.data == "admin:comm:main"
    )
    router.callback_query.register(
        callback_broadcast_start,
        F.data == "admin:comm:broadcast"
    )
    router.callback_query.register(
        callback_broadcast_target,
        F.data.startswith("admin:broadcast:target:")
    )
    router.callback_query.register(
        callback_broadcast_confirm,
        F.data == "admin:broadcast:confirm"
    )
    router.callback_query.register(
        callback_broadcast_cancel,
        F.data == "admin:broadcast:cancel"
    )
    router.callback_query.register(
        callback_offline_messages,
        F.data == "admin:comm:offline"
    )
    router.callback_query.register(
        callback_sponsor_settings,
        F.data == "admin:comm:sponsor"
    )
    router.callback_query.register(
        callback_sponsor_toggle,
        F.data == "admin:sponsor:toggle"
    )
    router.callback_query.register(
        callback_sponsor_edit_text,
        F.data == "admin:sponsor:edit_text"
    )
    router.callback_query.register(
        callback_sponsor_edit_url,
        F.data == "admin:sponsor:edit_url"
    )
    router.callback_query.register(
        callback_ads_settings,
        F.data == "admin:comm:ads"
    )
    router.callback_query.register(
        callback_ads_toggle,
        F.data == "admin:ads:toggle"
    )
    router.callback_query.register(
        callback_ads_edit_text,
        F.data == "admin:ads:edit_text"
    )
    router.callback_query.register(
        callback_ads_edit_url,
        F.data == "admin:ads:edit_url"
    )
    router.callback_query.register(
        callback_ads_edit_frequency,
        F.data == "admin:ads:edit_frequency"
    )
    
    # ========== Callback Handlers: AI ==========
    router.callback_query.register(
        callback_ai_main,
        F.data == "admin:ai:main"
    )
    router.callback_query.register(
        callback_ai_provider,
        F.data == "admin:ai:provider"
    )
    router.callback_query.register(
        callback_ai_model,
        F.data == "admin:ai:model"
    )
    router.callback_query.register(
        callback_ai_defaults,
        F.data == "admin:ai:defaults"
    )
    router.callback_query.register(
        callback_ai_prompts,
        F.data == "admin:ai:prompts"
    )
    router.callback_query.register(
        callback_ai_styles,
        F.data == "admin:ai:styles"
    )
    router.callback_query.register(
        callback_ai_limits,
        F.data == "admin:ai:limits"
    )
    router.callback_query.register(
        callback_style_edit,
        F.data.startswith("admin:style:edit:")
    )
    router.callback_query.register(
        callback_style_toggle,
        F.data.startswith("admin:style:toggle:")
    )
    
    # ========== Callback Handlers: Content ==========
    router.callback_query.register(
        callback_content_main,
        F.data == "admin:content:main"
    )
    router.callback_query.register(
        callback_content_guide,
        F.data == "admin:content:guide"
    )
    router.callback_query.register(
        callback_content_faq,
        F.data == "admin:content:faq"
    )
    router.callback_query.register(
        callback_faq_view,
        F.data.startswith("admin:faq:view:")
    )
    router.callback_query.register(
        callback_faq_create,
        F.data == "admin:faq:create"
    )
    router.callback_query.register(
        callback_faq_toggle,
        F.data.startswith("admin:faq:toggle:")
    )
    router.callback_query.register(
        callback_faq_delete,
        F.data.startswith("admin:faq:delete:")
    )
    router.callback_query.register(
        callback_faq_delete_confirm,
        F.data.startswith("admin:faq:delete_confirm:")
    )
    router.callback_query.register(
        callback_content_messages,
        F.data == "admin:content:messages"
    )
    router.callback_query.register(
        callback_message_edit,
        F.data.startswith("admin:msg:edit:")
    )
    
    # ========== Callback Handlers: System ==========
    router.callback_query.register(
        callback_system_main,
        F.data == "admin:sys:main"
    )
    router.callback_query.register(
        callback_system_status,
        F.data == "admin:sys:status"
    )
    router.callback_query.register(
        callback_system_queue,
        F.data == "admin:sys:queue"
    )
    router.callback_query.register(
        callback_system_errors,
        F.data == "admin:sys:errors"
    )
    router.callback_query.register(
        callback_maintenance_settings,
        F.data == "admin:sys:maintenance"
    )
    router.callback_query.register(
        callback_maintenance_toggle,
        F.data.startswith("admin:maintenance:")
    )
    
    # ========== FSM Handlers ==========
    router.message.register(
        handle_broadcast_message_input,
        AdminStates.waiting_for_broadcast_message
    )
    router.message.register(
        handle_sponsor_text_input,
        AdminStates.editing_sponsor_text
    )
    router.message.register(
        handle_sponsor_url_input,
        AdminStates.editing_sponsor_url
    )
    router.message.register(
        handle_ad_text_input,
        AdminStates.editing_ad_text
    )
    router.message.register(
        handle_ad_url_input,
        AdminStates.editing_ad_url
    )
    router.message.register(
        handle_ad_frequency_input,
        AdminStates.editing_ad_frequency
    )
    router.message.register(
        handle_guide_input,
        AdminStates.editing_guide
    )
    router.message.register(
        handle_faq_question_create_input,
        AdminStates.creating_faq_question
    )
    router.message.register(
        handle_faq_answer_create_input,
        AdminStates.creating_faq_answer
    )
    router.message.register(
        handle_system_message_input,
        AdminStates.editing_system_message
    )
    router.message.register(
        handle_maintenance_message_input,
        AdminStates.editing_maintenance_message
    )
    
    return router


# ========== Authorization Helper ==========

async def check_owner_access(message_or_callback) -> bool:
    """
    بررسی دسترسی Owner
    
    ⚠️ SECURITY/UX:
    - برای Message: Silent return (هیچ پاسخی ارسال نمی‌شود)
    - برای CallbackQuery: Silent answer (فقط dismiss می‌شود)
    - هدف: کاربر غیرمجاز نباید از وجود Admin Panel اطلاع پیدا کند
    
    Args:
        message_or_callback: Message یا CallbackQuery
        
    Returns:
        True اگر Owner باشد، False اگر نباشد
        
    Security:
    - هیچ اطلاعاتی به کاربر غیرمجاز نمایش داده نمی‌شود
    - فقط log داخلی برای audit
    """
    user_id = message_or_callback.from_user.id
    
    # دریافت bot context
    bot_context = get_bot_context(message_or_callback)
    
    # بررسی ownership
    if not is_owner(user_id, bot_context):
        # Unauthorized Access
        bot_id = bot_context.get('bot_id', 'unknown')
        owner_id = bot_context.get('owner_id', 'unknown')
        logger.warning(
            f"⚠️ Unauthorized admin access attempt: user {user_id} "
            f"tried to access bot {bot_id} owned by {owner_id}"
        )
        
        # ⚠️ SECURITY FIX: Silent mode
        # کاربر غیرمجاز نباید اطلاع پیدا کند که Admin Panel وجود دارد
        if isinstance(message_or_callback, Message):
            # برای Message: هیچ پاسخی ارسال نمی‌شود (Silent)
            pass
        else:  # CallbackQuery
            # برای CallbackQuery: فقط dismiss می‌شود (بدون متن)
            try:
                await message_or_callback.answer()
            except Exception:
                pass
        
        return False
    
    return True


# ========== Command: /admin ==========

async def cmd_admin(message: Message, state: FSMContext):
    """Handler دستور /admin - نمایش Admin Panel"""
    if not await check_owner_access(message):
        return
    
    await state.clear()
    
    text = (
        "━━━━━━━━━━━━━━━━\n"
        "🛠 **پنل مدیریت AI Image**\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "از منوی زیر یک بخش را انتخاب کنید:\n\n"
        "📊 **مدیریت**: آمار و گزارشات\n"
        "📢 **ارتباط**: ارسال همگانی و تبلیغات\n"
        "🧠 **AI**: تنظیمات هوش مصنوعی\n"
        "📚 **محتوا**: راهنما و FAQ\n"
        "⚙️ **سیستم**: وضعیت و Maintenance"
    )
    
    await message.answer(
        text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(f"Admin {message.from_user.id} opened admin panel")


# ========== Reply Keyboard Handlers ==========

async def handle_management_button(message: Message, state: FSMContext):
    """Handler دکمه «📊 مدیریت»"""
    if not await check_owner_access(message):
        return
    
    await state.clear()
    
    text = (
        "📊 **مدیریت**\n\n"
        "آمار و گزارشات ربات:"
    )
    
    await message.answer(
        text,
        reply_markup=get_management_keyboard(),
        parse_mode="Markdown"
    )


async def handle_communication_button(message: Message, state: FSMContext):
    """Handler دکمه «📢 ارتباط»"""
    if not await check_owner_access(message):
        return
    
    await state.clear()
    
    text = (
        "📢 **ارتباط**\n\n"
        "ارسال همگانی و مدیریت تبلیغات:"
    )
    
    await message.answer(
        text,
        reply_markup=get_communication_keyboard(),
        parse_mode="Markdown"
    )


async def handle_ai_button(message: Message, state: FSMContext):
    """Handler دکمه «🧠 AI»"""
    if not await check_owner_access(message):
        return
    
    await state.clear()
    
    text = (
        "🧠 **تنظیمات AI**\n\n"
        "مدیریت Provider، Model و تنظیمات تولید:"
    )
    
    await message.answer(
        text,
        reply_markup=get_ai_settings_keyboard(),
        parse_mode="Markdown"
    )


async def handle_content_button(message: Message, state: FSMContext):
    """Handler دکمه «📚 محتوا»"""
    if not await check_owner_access(message):
        return
    
    await state.clear()
    
    text = (
        "📚 **مدیریت محتوا**\n\n"
        "راهنما، FAQ و پیام‌های سیستم:"
    )
    
    await message.answer(
        text,
        reply_markup=get_content_keyboard(),
        parse_mode="Markdown"
    )


async def handle_system_button(message: Message, state: FSMContext):
    """Handler دکمه «⚙️ سیستم»"""
    if not await check_owner_access(message):
        return
    
    await state.clear()
    
    text = (
        "⚙️ **سیستم**\n\n"
        "وضعیت Server و Maintenance Mode:"
    )
    
    await message.answer(
        text,
        reply_markup=get_system_keyboard(),
        parse_mode="Markdown"
    )


async def handle_back_button(message: Message, state: FSMContext):
    """Handler دکمه «⬅️ بازگشت»"""
    if not await check_owner_access(message):
        return
    
    await state.clear()
    
    # بازگشت به Admin Panel اصلی
    await cmd_admin(message, state)


# ادامه در بخش بعد...


# ========== Callback Handlers: Management ==========

async def callback_management_main(callback: CallbackQuery, state: FSMContext):
    """بازگشت به منوی مدیریت"""
    if not await check_owner_access(callback):
        return
    
    await state.clear()
    
    text = (
        "📊 **مدیریت**\n\n"
        "آمار و گزارشات ربات:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_management_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


async def callback_user_stats(callback: CallbackQuery, state: FSMContext):
    """نمایش آمار کاربران"""
    if not await check_owner_access(callback):
        return
    
    try:
        stats = await admin_service.get_user_statistics()
        
        text = (
            "👥 **آمار کاربران**\n\n"
            f"📊 **کل کاربران:** {stats['total_users']}\n"
            f"🟢 **فعال امروز:** {stats['active_users_today']}\n"
            f"📅 **فعال این هفته:** {stats['active_users_week']}\n\n"
            f"➕ **کاربر جدید امروز:** {stats['new_users_today']}\n"
            f"➕ **کاربر جدید این هفته:** {stats['new_users_week']}\n"
            f"➕ **کاربر جدید این ماه:** {stats['new_users_month']}\n\n"
            "💡 آمار فعلی بر اساس داده‌های Session است."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_management_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting user stats: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت آمار", show_alert=True)


async def callback_active_users(callback: CallbackQuery, state: FSMContext):
    """نمایش کاربران فعال"""
    if not await check_owner_access(callback):
        return
    
    try:
        active_users = await admin_service.get_active_users(days=7)
        
        text = (
            "🟢 **کاربران فعال (7 روز اخیر)**\n\n"
            f"📊 تعداد: {len(active_users)}\n\n"
        )
        
        if not active_users:
            text += "❌ کاربر فعالی یافت نشد."
        else:
            text += "💡 لیست کاربران فعال در آینده نمایش داده می‌شود."
        
        await callback.message.edit_text(
            text,
            reply_markup=get_management_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting active users: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت کاربران فعال", show_alert=True)


async def callback_generation_stats(callback: CallbackQuery, state: FSMContext):
    """نمایش آمار Generation"""
    if not await check_owner_access(callback):
        return
    
    try:
        stats = await admin_service.get_generation_statistics()
        
        text = (
            "🖼 **آمار Generation**\n\n"
            f"📊 **کل:** {stats['total_generations']}\n"
            f"✅ **موفق:** {stats['successful_generations']}\n"
            f"❌ **ناموفق:** {stats['failed_generations']}\n\n"
            f"📅 **امروز:** {stats['generations_today']}\n"
            f"📅 **این هفته:** {stats['generations_week']}\n"
            f"📅 **این ماه:** {stats['generations_month']}\n\n"
            f"⏱ **میانگین زمان:** {stats['average_generation_time']:.2f}s\n\n"
            "💡 آمار فعلی بر اساس داده‌های Session است."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_management_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting generation stats: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت آمار", show_alert=True)


async def callback_revenue_stats(callback: CallbackQuery, state: FSMContext):
    """نمایش آمار درآمد"""
    if not await check_owner_access(callback):
        return
    
    try:
        stats = await admin_service.get_revenue_statistics()
        
        text = (
            "💰 **آمار درآمد و مصرف**\n\n"
            f"💳 **کل اعتبار مصرف‌شده:** {stats['total_credits_used']:,} تومان\n"
            f"📊 **میانگین هزینه:** {stats['average_cost_per_generation']:,} تومان\n\n"
            f"📅 **درآمد امروز:** {stats['revenue_today']:,} تومان\n"
            f"📅 **درآمد این هفته:** {stats['revenue_week']:,} تومان\n"
            f"📅 **درآمد این ماه:** {stats['revenue_month']:,} تومان\n\n"
            "💡 اتصال به Mother Bot Wallet در آینده پیاده‌سازی می‌شود."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_management_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting revenue stats: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت آمار", show_alert=True)


async def callback_refresh_stats(callback: CallbackQuery, state: FSMContext):
    """تازه‌سازی آمار"""
    if not await check_owner_access(callback):
        return
    
    try:
        await admin_service.refresh_statistics_cache()
        await callback.answer("✅ آمار به‌روزرسانی شد", show_alert=False)
    except Exception as e:
        logger.error(f"Error refreshing stats: {e}", exc_info=True)
        await callback.answer("❌ خطا در به‌روزرسانی", show_alert=True)


# ========== Callback Handlers: Communication ==========

async def callback_communication_main(callback: CallbackQuery, state: FSMContext):
    """بازگشت به منوی ارتباط"""
    if not await check_owner_access(callback):
        return
    
    await state.clear()
    
    text = (
        "📢 **ارتباط**\n\n"
        "ارسال همگانی و مدیریت تبلیغات:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_communication_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


async def callback_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """شروع Broadcast"""
    if not await check_owner_access(callback):
        return
    
    text = (
        "📨 **ارسال همگانی**\n\n"
        "پیام خود را بنویسید:\n\n"
        "⚠️ این پیام به تمام کاربران ارسال خواهد شد.\n"
        "لطفاً با دقت بنویسید."
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown"
    )
    
    await state.set_state(AdminStates.waiting_for_broadcast_message)
    await callback.answer()


async def handle_broadcast_message_input(message: Message, state: FSMContext):
    """دریافت پیام Broadcast"""
    if not await check_owner_access(message):
        return
    
    broadcast_text = message.text.strip()
    
    if len(broadcast_text) < 10:
        await message.answer(
            "⚠️ پیام باید حداقل 10 کاراکتر باشد.",
            reply_markup=get_back_keyboard()
        )
        return
    
    # ذخیره پیام در State
    await state.update_data(broadcast_text=broadcast_text)
    
    # نمایش انتخاب Target
    text = (
        "📨 **انتخاب مخاطبان**\n\n"
        "به چه کسانی ارسال شود؟"
    )
    
    await message.answer(
        text,
        reply_markup=get_broadcast_target_keyboard(),
        parse_mode="Markdown"
    )


async def callback_broadcast_target(callback: CallbackQuery, state: FSMContext):
    """انتخاب Target برای Broadcast"""
    if not await check_owner_access(callback):
        return
    
    target_type = callback.data.split(":")[-1]
    
    # دریافت لیست کاربران
    if target_type == "all":
        target_users = await broadcast_service.get_all_user_ids()
        target_name = "همه کاربران"
    elif target_type == "active":
        target_users = await broadcast_service.get_active_user_ids(days=7)
        target_name = "کاربران فعال (7 روز اخیر)"
    else:
        await callback.answer("❌ نوع نامعتبر", show_alert=True)
        return
    
    # ذخیره در State
    await state.update_data(
        target_users=target_users,
        target_name=target_name
    )
    
    # دریافت پیام از State
    data = await state.get_data()
    broadcast_text = data.get('broadcast_text', '')
    
    # نمایش Preview و تأیید
    text = (
        "📨 **تأیید ارسال همگانی**\n\n"
        f"**مخاطبان:** {target_name}\n"
        f"**تعداد:** {len(target_users)} کاربر\n\n"
        f"**پیام:**\n{broadcast_text}\n\n"
        "⚠️ **توجه:** این عملیات قابل بازگشت نیست!"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_broadcast_confirm_keyboard(len(target_users)),
        parse_mode="Markdown"
    )
    await callback.answer()


async def callback_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    """تأیید و اجرای Broadcast"""
    if not await check_owner_access(callback):
        return
    
    data = await state.get_data()
    broadcast_text = data.get('broadcast_text', '')
    target_users = data.get('target_users', [])
    
    if not broadcast_text or not target_users:
        await callback.answer("❌ داده‌ها ناقص است", show_alert=True)
        await state.clear()
        return
    
    # ایجاد Broadcast
    try:
        broadcast = await broadcast_service.create_broadcast(
            admin_user_id=callback.from_user.id,
            text=broadcast_text,
            target_users=target_users
        )
        
        # نمایش پیام Processing
        processing_text = (
            "⏳ **در حال ارسال...**\n\n"
            f"مخاطبان: {len(target_users)} کاربر\n\n"
            "لطفاً صبر کنید..."
        )
        
        await callback.message.edit_text(
            processing_text,
            parse_mode="Markdown"
        )
        
        # اجرای Broadcast
        # ⚠️ این باید در background task اجرا شود
        # فعلاً به صورت sync اجرا می‌کنیم
        result = await broadcast_service.execute_broadcast(
            broadcast.id,
            callback.bot
        )
        
        # نمایش نتیجه
        result_text = (
            "✅ **ارسال همگانی انجام شد!**\n\n"
            f"✅ **ارسال موفق:** {result['sent_count']}\n"
            f"❌ **ارسال ناموفق:** {result['failed_count']}\n"
        )
        
        await callback.message.edit_text(
            result_text,
            parse_mode="Markdown"
        )
        
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ **خطا در ارسال همگانی**\n\n"
            "لطفاً دوباره تلاش کنید.",
            parse_mode="Markdown"
        )
        await state.clear()
        await callback.answer()


async def callback_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """لغو Broadcast"""
    if not await check_owner_access(callback):
        return
    
    await state.clear()
    
    await callback.message.edit_text(
        "❌ ارسال همگانی لغو شد.",
        parse_mode="Markdown"
    )
    await callback.answer()


async def callback_offline_messages(callback: CallbackQuery, state: FSMContext):
    """نمایش پیام‌های آفلاین"""
    if not await check_owner_access(callback):
        return
    
    try:
        offline_messages = content_service.get_offline_messages(only_unhandled=False)
        
        text = (
            "💤 **پیام‌های آفلاین**\n\n"
            f"📊 **تعداد کل:** {len(offline_messages)}\n"
        )
        
        unhandled_count = sum(1 for m in offline_messages if not m['handled'])
        text += f"⚠️ **بررسی نشده:** {unhandled_count}\n\n"
        
        if not offline_messages:
            text += "✅ پیام آفلاینی وجود ندارد."
        else:
            text += "💡 مدیریت پیام‌های آفلاین در نسخه آینده اضافه می‌شود."
        
        await callback.message.edit_text(
            text,
            reply_markup=get_communication_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting offline messages: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت پیام‌ها", show_alert=True)


async def callback_sponsor_settings(callback: CallbackQuery, state: FSMContext):
    """نمایش تنظیمات Sponsor"""
    if not await check_owner_access(callback):
        return
    
    try:
        sponsor_config = broadcast_service.get_sponsor_config()
        
        status = "🟢 فعال" if sponsor_config.enabled else "🔴 غیرفعال"
        
        text = (
            "⭐ **مدیریت Sponsor**\n\n"
            f"**وضعیت:** {status}\n"
            f"**متن:** {sponsor_config.text or 'تنظیم نشده'}\n"
            f"**لینک:** {sponsor_config.url or 'تنظیم نشده'}\n"
            f"**متن دکمه:** {sponsor_config.button_text}\n"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_sponsor_keyboard(sponsor_config.enabled),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting sponsor settings: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت تنظیمات", show_alert=True)


async def callback_sponsor_toggle(callback: CallbackQuery, state: FSMContext):
    """فعال/غیرفعال کردن Sponsor"""
    if not await check_owner_access(callback):
        return
    
    try:
        sponsor_config = broadcast_service.get_sponsor_config()
        new_status = not sponsor_config.enabled
        
        success = await broadcast_service.update_sponsor_config(enabled=new_status)
        
        if success:
            status_text = "فعال" if new_status else "غیرفعال"
            await callback.answer(f"✅ Sponsor {status_text} شد", show_alert=False)
            # به‌روزرسانی منو
            await callback_sponsor_settings(callback, state)
        else:
            await callback.answer("❌ خطا در تغییر وضعیت", show_alert=True)
    except Exception as e:
        logger.error(f"Error toggling sponsor: {e}", exc_info=True)
        await callback.answer("❌ خطا رخ داد", show_alert=True)


async def callback_sponsor_edit_text(callback: CallbackQuery, state: FSMContext):
    """ویرایش متن Sponsor"""
    if not await check_owner_access(callback):
        return
    
    text = (
        "✏️ **تغییر متن Sponsor**\n\n"
        "متن جدید را وارد کنید:"
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(AdminStates.editing_sponsor_text)
    await callback.answer()


async def handle_sponsor_text_input(message: Message, state: FSMContext):
    """دریافت متن جدید Sponsor"""
    if not await check_owner_access(message):
        return
    
    new_text = message.text.strip()
    
    try:
        success = await broadcast_service.update_sponsor_config(text=new_text)
        
        if success:
            await message.answer(
                "✅ متن Sponsor به‌روزرسانی شد.",
                reply_markup=get_admin_main_keyboard()
            )
        else:
            await message.answer(
                "❌ خطا در به‌روزرسانی.",
                reply_markup=get_admin_main_keyboard()
            )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating sponsor text: {e}", exc_info=True)
        await message.answer(
            "❌ خطا رخ داد.",
            reply_markup=get_admin_main_keyboard()
        )
        await state.clear()


async def callback_sponsor_edit_url(callback: CallbackQuery, state: FSMContext):
    """ویرایش لینک Sponsor"""
    if not await check_owner_access(callback):
        return
    
    text = (
        "🔗 **تغییر لینک Sponsor**\n\n"
        "لینک جدید را وارد کنید:"
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(AdminStates.editing_sponsor_url)
    await callback.answer()


async def handle_sponsor_url_input(message: Message, state: FSMContext):
    """دریافت لینک جدید Sponsor"""
    if not await check_owner_access(message):
        return
    
    new_url = message.text.strip()
    
    try:
        success = await broadcast_service.update_sponsor_config(url=new_url)
        
        if success:
            await message.answer(
                "✅ لینک Sponsor به‌روزرسانی شد.",
                reply_markup=get_admin_main_keyboard()
            )
        else:
            await message.answer(
                "❌ خطا در به‌روزرسانی.",
                reply_markup=get_admin_main_keyboard()
            )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating sponsor url: {e}", exc_info=True)
        await message.answer(
            "❌ خطا رخ داد.",
            reply_markup=get_admin_main_keyboard()
        )
        await state.clear()


async def callback_ads_settings(callback: CallbackQuery, state: FSMContext):
    """نمایش تنظیمات Ads"""
    if not await check_owner_access(callback):
        return
    
    try:
        ad_config = broadcast_service.get_ad_config()
        
        status = "🟢 فعال" if ad_config.enabled else "🔴 غیرفعال"
        
        text = (
            "📣 **مدیریت تبلیغات**\n\n"
            f"**وضعیت:** {status}\n"
            f"**متن:** {ad_config.text or 'تنظیم نشده'}\n"
            f"**لینک:** {ad_config.url or 'تنظیم نشده'}\n"
            f"**فرکانس نمایش:** هر {ad_config.show_frequency} درخواست\n"
            f"**تعداد نمایش:** {ad_config.show_count}\n"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_ads_keyboard(ad_config.enabled),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting ads settings: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت تنظیمات", show_alert=True)


async def callback_ads_toggle(callback: CallbackQuery, state: FSMContext):
    """فعال/غیرفعال کردن Ads"""
    if not await check_owner_access(callback):
        return
    
    try:
        ad_config = broadcast_service.get_ad_config()
        new_status = not ad_config.enabled
        
        success = await broadcast_service.update_ad_config(enabled=new_status)
        
        if success:
            status_text = "فعال" if new_status else "غیرفعال"
            await callback.answer(f"✅ تبلیغات {status_text} شد", show_alert=False)
            # به‌روزرسانی منو
            await callback_ads_settings(callback, state)
        else:
            await callback.answer("❌ خطا در تغییر وضعیت", show_alert=True)
    except Exception as e:
        logger.error(f"Error toggling ads: {e}", exc_info=True)
        await callback.answer("❌ خطا رخ داد", show_alert=True)


async def callback_ads_edit_text(callback: CallbackQuery, state: FSMContext):
    """ویرایش متن تبلیغ"""
    if not await check_owner_access(callback):
        return
    
    text = (
        "✏️ **تغییر متن تبلیغ**\n\n"
        "متن جدید را وارد کنید:"
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(AdminStates.editing_ad_text)
    await callback.answer()


async def handle_ad_text_input(message: Message, state: FSMContext):
    """دریافت متن جدید تبلیغ"""
    if not await check_owner_access(message):
        return
    
    new_text = message.text.strip()
    
    try:
        success = await broadcast_service.update_ad_config(text=new_text)
        
        if success:
            await message.answer(
                "✅ متن تبلیغ به‌روزرسانی شد.",
                reply_markup=get_admin_main_keyboard()
            )
        else:
            await message.answer(
                "❌ خطا در به‌روزرسانی.",
                reply_markup=get_admin_main_keyboard()
            )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating ad text: {e}", exc_info=True)
        await message.answer(
            "❌ خطا رخ داد.",
            reply_markup=get_admin_main_keyboard()
        )
        await state.clear()


async def callback_ads_edit_url(callback: CallbackQuery, state: FSMContext):
    """ویرایش لینک تبلیغ"""
    if not await check_owner_access(callback):
        return
    
    text = (
        "🔗 **تغییر لینک تبلیغ**\n\n"
        "لینک جدید را وارد کنید:"
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(AdminStates.editing_ad_url)
    await callback.answer()


async def handle_ad_url_input(message: Message, state: FSMContext):
    """دریافت لینک جدید تبلیغ"""
    if not await check_owner_access(message):
        return
    
    new_url = message.text.strip()
    
    try:
        success = await broadcast_service.update_ad_config(url=new_url)
        
        if success:
            await message.answer(
                "✅ لینک تبلیغ به‌روزرسانی شد.",
                reply_markup=get_admin_main_keyboard()
            )
        else:
            await message.answer(
                "❌ خطا در به‌روزرسانی.",
                reply_markup=get_admin_main_keyboard()
            )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating ad url: {e}", exc_info=True)
        await message.answer(
            "❌ خطا رخ داد.",
            reply_markup=get_admin_main_keyboard()
        )
        await state.clear()


async def callback_ads_edit_frequency(callback: CallbackQuery, state: FSMContext):
    """ویرایش فرکانس نمایش تبلیغ"""
    if not await check_owner_access(callback):
        return
    
    text = (
        "📊 **تنظیم فرکانس نمایش**\n\n"
        "هر چند درخواست یک‌بار تبلیغ نمایش داده شود؟\n\n"
        "عدد را وارد کنید (مثلاً 5):"
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(AdminStates.editing_ad_frequency)
    await callback.answer()


async def handle_ad_frequency_input(message: Message, state: FSMContext):
    """دریافت فرکانس جدید"""
    if not await check_owner_access(message):
        return
    
    try:
        frequency = int(message.text.strip())
        
        if frequency < 1:
            await message.answer(
                "⚠️ فرکانس باید حداقل 1 باشد.",
                reply_markup=get_admin_main_keyboard()
            )
            return
        
        success = await broadcast_service.update_ad_config(show_frequency=frequency)
        
        if success:
            await message.answer(
                f"✅ فرکانس نمایش به {frequency} تغییر یافت.",
                reply_markup=get_admin_main_keyboard()
            )
        else:
            await message.answer(
                "❌ خطا در به‌روزرسانی.",
                reply_markup=get_admin_main_keyboard()
            )
        
        await state.clear()
    except ValueError:
        await message.answer(
            "⚠️ لطفاً یک عدد معتبر وارد کنید.",
            reply_markup=get_admin_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Error updating ad frequency: {e}", exc_info=True)
        await message.answer(
            "❌ خطا رخ داد.",
            reply_markup=get_admin_main_keyboard()
        )
        await state.clear()


# ========== Callback Handlers: AI Settings ==========

async def callback_ai_main(callback: CallbackQuery, state: FSMContext):
    """بازگشت به منوی AI"""
    if not await check_owner_access(callback):
        return
    
    await state.clear()
    
    text = (
        "🧠 **تنظیمات AI**\n\n"
        "مدیریت Provider، Model و تنظیمات تولید:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_ai_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


async def callback_ai_provider(callback: CallbackQuery, state: FSMContext):
    """نمایش اطلاعات Provider"""
    if not await check_owner_access(callback):
        return
    
    try:
        provider_status = config_service.get_provider_status()
        
        status_icon = "✅" if provider_status['api_configured'] else "❌"
        
        text = (
            "🔌 **Provider / API**\n\n"
            f"**Provider:** {provider_status['provider']}\n"
            f"**Model:** {provider_status['model']}\n"
            f"**وضعیت:** {status_icon} {provider_status['status']}\n\n"
            "⚠️ **توجه:** API Key هرگز در Telegram نمایش داده نمی‌شود.\n\n"
            "💡 تغییر Provider در نسخه آینده امکان‌پذیر خواهد بود."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_ai_settings_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting provider status: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت اطلاعات", show_alert=True)


async def callback_ai_model(callback: CallbackQuery, state: FSMContext):
    """نمایش اطلاعات Model"""
    if not await check_owner_access(callback):
        return
    
    try:
        ai_config = config_service.get_ai_config()
        
        text = (
            "🤖 **Model**\n\n"
            f"**Model فعلی:** {ai_config.model}\n\n"
            "💡 تغییر Model در نسخه آینده امکان‌پذیر خواهد بود."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_ai_settings_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting model info: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت اطلاعات", show_alert=True)


async def callback_ai_defaults(callback: CallbackQuery, state: FSMContext):
    """نمایش Default Settings"""
    if not await check_owner_access(callback):
        return
    
    try:
        ai_config = config_service.get_ai_config()
        
        text = (
            "⚙️ **Default Settings**\n\n"
            f"**سبک پیش‌فرض:** {ai_config.default_style.get_display_name()}\n"
            f"**نسبت پیش‌فرض:** {ai_config.default_ratio.get_display_name()}\n"
            f"**کیفیت پیش‌فرض:** {ai_config.default_quality.get_display_name()}\n"
            f"**تعداد پیش‌فرض:** {ai_config.default_count}\n\n"
            "💡 تغییر تنظیمات پیش‌فرض در نسخه آینده امکان‌پذیر خواهد بود."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_ai_settings_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting defaults: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت اطلاعات", show_alert=True)


async def callback_ai_prompts(callback: CallbackQuery, state: FSMContext):
    """نمایش Prompt Settings"""
    if not await check_owner_access(callback):
        return
    
    try:
        ai_config = config_service.get_ai_config()
        
        text = (
            "📝 **Prompt Settings**\n\n"
            f"**حداقل طول:** {ai_config.min_prompt_length}\n"
            f"**حداکثر طول:** {ai_config.max_prompt_length}\n\n"
            f"**System Prompt:** {ai_config.system_prompt or 'تنظیم نشده'}\n"
            f"**Prefix:** {ai_config.prompt_prefix or 'ندارد'}\n"
            f"**Suffix:** {ai_config.prompt_suffix or 'ندارد'}\n"
            f"**Negative Prompt:** {ai_config.negative_prompt or 'ندارد'}\n\n"
            "💡 تغییر تنظیمات Prompt در نسخه آینده امکان‌پذیر خواهد بود."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_ai_settings_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting prompt settings: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت اطلاعات", show_alert=True)


async def callback_ai_styles(callback: CallbackQuery, state: FSMContext):
    """نمایش لیست Styles"""
    if not await check_owner_access(callback):
        return
    
    try:
        styles = config_service.get_all_styles()
        
        text = (
            "🎨 **Style Settings**\n\n"
            "لیست Styleها:"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_styles_list_keyboard(styles),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting styles: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت لیست", show_alert=True)


async def callback_style_edit(callback: CallbackQuery, state: FSMContext):
    """نمایش تنظیمات یک Style"""
    if not await check_owner_access(callback):
        return
    
    style_key = callback.data.split(":")[-1]
    
    try:
        style = config_service.get_style(style_key)
        
        if not style:
            await callback.answer("❌ Style یافت نشد", show_alert=True)
            return
        
        status = "🟢 فعال" if style.enabled else "🔴 غیرفعال"
        
        text = (
            f"🎨 **{style.name}**\n\n"
            f"**وضعیت:** {status}\n"
            f"**توضیحات:** {style.description}\n"
            f"**Prompt Modifier:** `{style.prompt_modifier}`\n"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_style_edit_keyboard(style_key, style.enabled),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting style {style_key}: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت اطلاعات", show_alert=True)


async def callback_style_toggle(callback: CallbackQuery, state: FSMContext):
    """فعال/غیرفعال کردن Style"""
    if not await check_owner_access(callback):
        return
    
    style_key = callback.data.split(":")[-1]
    
    try:
        style = config_service.get_style(style_key)
        if not style:
            await callback.answer("❌ Style یافت نشد", show_alert=True)
            return
        
        new_status = not style.enabled
        success = await config_service.update_style(style_key, enabled=new_status)
        
        if success:
            status_text = "فعال" if new_status else "غیرفعال"
            await callback.answer(f"✅ Style {status_text} شد", show_alert=False)
            # به‌روزرسانی منو
            await callback_style_edit(callback, state)
        else:
            await callback.answer("❌ خطا در تغییر وضعیت", show_alert=True)
    except Exception as e:
        logger.error(f"Error toggling style {style_key}: {e}", exc_info=True)
        await callback.answer("❌ خطا رخ داد", show_alert=True)


async def callback_ai_limits(callback: CallbackQuery, state: FSMContext):
    """نمایش Generation Limits"""
    if not await check_owner_access(callback):
        return
    
    try:
        limits = config_service.get_generation_limits()
        
        text = (
            "🚦 **Generation Limits**\n\n"
            f"**محدودیت روزانه هر کاربر:** {limits['daily_limit_per_user']}\n"
            f"**حداکثر تصاویر هر درخواست:** {limits['max_images_per_request']}\n"
            f"**Rate Limit:** {limits['rate_limit_seconds']} ثانیه\n"
            f"**Cooldown کاربر:** {limits['user_cooldown_seconds']} ثانیه\n\n"
            "💡 تغییر محدودیت‌ها در نسخه آینده امکان‌پذیر خواهد بود."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_ai_settings_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting limits: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت اطلاعات", show_alert=True)


# ========== Callback Handlers: Content ==========

async def callback_content_main(callback: CallbackQuery, state: FSMContext):
    """بازگشت به منوی محتوا"""
    if not await check_owner_access(callback):
        return
    
    await state.clear()
    
    text = (
        "📚 **مدیریت محتوا**\n\n"
        "راهنما، FAQ و پیام‌های سیستم:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_content_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


async def callback_content_guide(callback: CallbackQuery, state: FSMContext):
    """نمایش راهنما"""
    if not await check_owner_access(callback):
        return
    
    try:
        guide = content_service.get_guide()
        
        # نمایش 500 کاراکتر اول
        preview = guide[:500] + "..." if len(guide) > 500 else guide
        
        text = (
            "📖 **راهنمای ربات**\n\n"
            f"{preview}\n\n"
            "💡 ویرایش راهنما در نسخه آینده امکان‌پذیر خواهد بود."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_content_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting guide: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت راهنما", show_alert=True)


async def callback_content_faq(callback: CallbackQuery, state: FSMContext):
    """نمایش لیست FAQ"""
    if not await check_owner_access(callback):
        return
    
    try:
        faqs = content_service.get_all_faqs()
        
        text = (
            "❓ **FAQ**\n\n"
            f"تعداد: {len(faqs)}\n\n"
        )
        
        if not faqs:
            text += "هنوز FAQ ای اضافه نشده است."
        
        await callback.message.edit_text(
            text,
            reply_markup=get_faq_list_keyboard(faqs),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting FAQs: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت لیست", show_alert=True)


async def callback_faq_view(callback: CallbackQuery, state: FSMContext):
    """نمایش جزئیات FAQ"""
    if not await check_owner_access(callback):
        return
    
    faq_id = callback.data.split(":")[-1]
    
    try:
        faq = content_service.get_faq(faq_id)
        
        if not faq:
            await callback.answer("❌ FAQ یافت نشد", show_alert=True)
            return
        
        status = "🟢 فعال" if faq.enabled else "🔴 غیرفعال"
        
        text = (
            f"❓ **FAQ**\n\n"
            f"**وضعیت:** {status}\n\n"
            f"**سوال:**\n{faq.question}\n\n"
            f"**جواب:**\n{faq.answer}\n"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_faq_edit_keyboard(faq_id, faq.enabled),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error viewing FAQ {faq_id}: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت اطلاعات", show_alert=True)


async def callback_faq_create(callback: CallbackQuery, state: FSMContext):
    """شروع ایجاد FAQ جدید"""
    if not await check_owner_access(callback):
        return
    
    text = (
        "➕ **افزودن FAQ جدید**\n\n"
        "سوال را وارد کنید:"
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(AdminStates.creating_faq_question)
    await callback.answer()


async def handle_faq_question_create_input(message: Message, state: FSMContext):
    """دریافت سوال FAQ جدید"""
    if not await check_owner_access(message):
        return
    
    question = message.text.strip()
    
    if len(question) < 5:
        await message.answer(
            "⚠️ سوال باید حداقل 5 کاراکتر باشد.",
            reply_markup=get_back_keyboard()
        )
        return
    
    # ذخیره سوال در State
    await state.update_data(faq_question=question)
    
    text = (
        "➕ **افزودن FAQ جدید**\n\n"
        f"**سوال:** {question}\n\n"
        "حالا جواب را وارد کنید:"
    )
    
    await message.answer(text, parse_mode="Markdown", reply_markup=get_back_keyboard())
    await state.set_state(AdminStates.creating_faq_answer)


async def handle_faq_answer_create_input(message: Message, state: FSMContext):
    """دریافت جواب FAQ جدید"""
    if not await check_owner_access(message):
        return
    
    answer = message.text.strip()
    
    if len(answer) < 10:
        await message.answer(
            "⚠️ جواب باید حداقل 10 کاراکتر باشد.",
            reply_markup=get_back_keyboard()
        )
        return
    
    # دریافت سوال از State
    data = await state.get_data()
    question = data.get('faq_question', '')
    
    try:
        # ایجاد FAQ
        faq = await content_service.create_faq(
            question=question,
            answer=answer,
            enabled=True
        )
        
        await message.answer(
            "✅ FAQ جدید با موفقیت اضافه شد.",
            reply_markup=get_admin_main_keyboard()
        )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error creating FAQ: {e}", exc_info=True)
        await message.answer(
            "❌ خطا در ایجاد FAQ.",
            reply_markup=get_admin_main_keyboard()
        )
        await state.clear()


async def callback_faq_toggle(callback: CallbackQuery, state: FSMContext):
    """فعال/غیرفعال کردن FAQ"""
    if not await check_owner_access(callback):
        return
    
    faq_id = callback.data.split(":")[-1]
    
    try:
        faq = content_service.get_faq(faq_id)
        if not faq:
            await callback.answer("❌ FAQ یافت نشد", show_alert=True)
            return
        
        new_status = not faq.enabled
        success = await content_service.update_faq(faq_id, enabled=new_status)
        
        if success:
            status_text = "فعال" if new_status else "غیرفعال"
            await callback.answer(f"✅ FAQ {status_text} شد", show_alert=False)
            # به‌روزرسانی منو
            await callback_faq_view(callback, state)
        else:
            await callback.answer("❌ خطا در تغییر وضعیت", show_alert=True)
    except Exception as e:
        logger.error(f"Error toggling FAQ {faq_id}: {e}", exc_info=True)
        await callback.answer("❌ خطا رخ داد", show_alert=True)


async def callback_faq_delete(callback: CallbackQuery, state: FSMContext):
    """تأیید حذف FAQ"""
    if not await check_owner_access(callback):
        return
    
    faq_id = callback.data.split(":")[-1]
    
    text = (
        "🗑️ **حذف FAQ**\n\n"
        "⚠️ آیا مطمئن هستید؟\n"
        "این عملیات قابل بازگشت نیست."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_faq_delete_confirm_keyboard(faq_id),
        parse_mode="Markdown"
    )
    await callback.answer()


async def callback_faq_delete_confirm(callback: CallbackQuery, state: FSMContext):
    """حذف قطعی FAQ"""
    if not await check_owner_access(callback):
        return
    
    faq_id = callback.data.split(":")[-1]
    
    try:
        success = await content_service.delete_faq(faq_id)
        
        if success:
            await callback.answer("✅ FAQ حذف شد", show_alert=False)
            # بازگشت به لیست FAQ
            await callback_content_faq(callback, state)
        else:
            await callback.answer("❌ خطا در حذف", show_alert=True)
    except Exception as e:
        logger.error(f"Error deleting FAQ {faq_id}: {e}", exc_info=True)
        await callback.answer("❌ خطا رخ داد", show_alert=True)


async def callback_content_messages(callback: CallbackQuery, state: FSMContext):
    """نمایش لیست پیام‌های سیستم"""
    if not await check_owner_access(callback):
        return
    
    text = (
        "💬 **پیام‌های سیستم**\n\n"
        "لیست پیام‌های قابل تنظیم:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_system_messages_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


async def callback_message_edit(callback: CallbackQuery, state: FSMContext):
    """ویرایش پیام سیستم"""
    if not await check_owner_access(callback):
        return
    
    message_key = callback.data.split(":")[-1]
    
    try:
        current_message = content_service.get_system_message(message_key)
        
        text = (
            "✏️ **ویرایش پیام سیستم**\n\n"
            f"**پیام فعلی:**\n{current_message}\n\n"
            "پیام جدید را وارد کنید:"
        )
        
        await callback.message.edit_text(text, parse_mode="Markdown")
        await state.update_data(editing_message_key=message_key)
        await state.set_state(AdminStates.editing_system_message)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting message {message_key}: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت پیام", show_alert=True)


async def handle_system_message_input(message: Message, state: FSMContext):
    """دریافت پیام جدید سیستم"""
    if not await check_owner_access(message):
        return
    
    new_message = message.text.strip()
    
    # دریافت key از State
    data = await state.get_data()
    message_key = data.get('editing_message_key', '')
    
    try:
        success = await content_service.update_system_message(message_key, new_message)
        
        if success:
            await message.answer(
                "✅ پیام سیستم به‌روزرسانی شد.",
                reply_markup=get_admin_main_keyboard()
            )
        else:
            await message.answer(
                "❌ خطا در به‌روزرسانی.",
                reply_markup=get_admin_main_keyboard()
            )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating message {message_key}: {e}", exc_info=True)
        await message.answer(
            "❌ خطا رخ داد.",
            reply_markup=get_admin_main_keyboard()
        )
        await state.clear()


async def handle_guide_input(message: Message, state: FSMContext):
    """دریافت راهنمای جدید"""
    if not await check_owner_access(message):
        return
    
    new_guide = message.text.strip()
    
    try:
        success = await content_service.update_guide(new_guide)
        
        if success:
            await message.answer(
                "✅ راهنما به‌روزرسانی شد.",
                reply_markup=get_admin_main_keyboard()
            )
        else:
            await message.answer(
                "❌ خطا در به‌روزرسانی.",
                reply_markup=get_admin_main_keyboard()
            )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating guide: {e}", exc_info=True)
        await message.answer(
            "❌ خطا رخ داد.",
            reply_markup=get_admin_main_keyboard()
        )
        await state.clear()


# ========== Callback Handlers: System ==========

async def callback_system_main(callback: CallbackQuery, state: FSMContext):
    """بازگشت به منوی سیستم"""
    if not await check_owner_access(callback):
        return
    
    await state.clear()
    
    text = (
        "⚙️ **سیستم**\n\n"
        "وضعیت Server و Maintenance Mode:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_system_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


async def callback_system_status(callback: CallbackQuery, state: FSMContext):
    """نمایش وضعیت Server"""
    if not await check_owner_access(callback):
        return
    
    try:
        stats = await admin_service.get_system_statistics()
        
        # فرمت Uptime
        uptime_hours = stats.get('uptime_seconds', 0) // 3600
        uptime_minutes = (stats.get('uptime_seconds', 0) % 3600) // 60
        
        text = (
            "🖥 **وضعیت Server**\n\n"
            f"**Status:** {stats.get('status', 'unknown')}\n"
            f"**Uptime:** {uptime_hours}h {uptime_minutes}m\n\n"
            f"**CPU:** {stats.get('cpu_percent', 0):.1f}%\n"
            f"**RAM:** {stats.get('memory_percent', 0):.1f}% "
            f"({stats.get('memory_used_mb', 0):.0f}MB / "
            f"{stats.get('memory_total_mb', 0):.0f}MB)\n\n"
            f"**Python:** {stats.get('python_version', 'N/A')}\n"
            f"**Platform:** {stats.get('platform', 'N/A')}\n"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_system_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت وضعیت", show_alert=True)


async def callback_system_queue(callback: CallbackQuery, state: FSMContext):
    """نمایش صف انتظار"""
    if not await check_owner_access(callback):
        return
    
    # TODO: پیاده‌سازی Queue Management
    text = (
        "📦 **صف انتظار**\n\n"
        "**Pending:** 0\n"
        "**Processing:** 0\n"
        "**Completed:** 0\n"
        "**Failed:** 0\n\n"
        "💡 مدیریت صف در نسخه آینده پیاده‌سازی می‌شود."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_system_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


async def callback_system_errors(callback: CallbackQuery, state: FSMContext):
    """نمایش آمار خطا"""
    if not await check_owner_access(callback):
        return
    
    try:
        error_stats = await admin_service.get_error_statistics()
        
        text = (
            "❌ **آمار خطا**\n\n"
            f"**کل خطاها:** {error_stats.get('total_errors', 0)}\n"
            f"**خطاهای امروز:** {error_stats.get('errors_today', 0)}\n"
            f"**خطاهای Generation:** {error_stats.get('generation_errors', 0)}\n"
            f"**خطاهای Provider:** {error_stats.get('provider_errors', 0)}\n\n"
            "💡 جزئیات خطاها در Log ذخیره می‌شوند."
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_system_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting error stats: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت آمار", show_alert=True)


async def callback_maintenance_settings(callback: CallbackQuery, state: FSMContext):
    """نمایش تنظیمات Maintenance Mode"""
    if not await check_owner_access(callback):
        return
    
    try:
        maintenance_config = config_service.get_maintenance_config()
        is_active = config_service.is_maintenance_active()
        
        status = "🔴 فعال" if is_active else "🟢 غیرفعال"
        
        text = (
            "🔧 **Maintenance Mode**\n\n"
            f"**وضعیت:** {status}\n\n"
            f"**پیام:**\n{maintenance_config.message}\n\n"
        )
        
        if is_active:
            text += "⚠️ **توجه:** ربات در حالت Maintenance است.\nکاربران نمی‌توانند تصویر تولید کنند."
        
        await callback.message.edit_text(
            text,
            reply_markup=get_maintenance_keyboard(is_active),
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error getting maintenance settings: {e}", exc_info=True)
        await callback.answer("❌ خطا در دریافت تنظیمات", show_alert=True)


async def callback_maintenance_toggle(callback: CallbackQuery, state: FSMContext):
    """مدیریت Maintenance Mode"""
    if not await check_owner_access(callback):
        return
    
    parts = callback.data.split(":")
    
    if len(parts) < 3:
        await callback.answer("❌ داده نامعتبر", show_alert=True)
        return
    
    action = parts[2]
    
    if action == "on":
        # تأیید روشن کردن
        text = (
            "🔴 **روشن کردن Maintenance Mode**\n\n"
            "⚠️ **توجه:** با فعال کردن Maintenance Mode:\n"
            "• کاربران نمی‌توانند تصویر تولید کنند\n"
            "• پیام Maintenance به کاربران نمایش داده می‌شود\n\n"
            "آیا مطمئن هستید؟"
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_maintenance_confirm_keyboard("on"),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    elif action == "off":
        # تأیید خاموش کردن
        text = (
            "🟢 **خاموش کردن Maintenance Mode**\n\n"
            "✅ با خاموش کردن Maintenance Mode:\n"
            "• کاربران می‌توانند تصویر تولید کنند\n"
            "• ربات به حالت عادی برمی‌گردد\n\n"
            "آیا مطمئن هستید؟"
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_maintenance_confirm_keyboard("off"),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    elif action == "confirm":
        # اجرای تغییر
        if len(parts) < 4:
            await callback.answer("❌ داده ناقص", show_alert=True)
            return
        
        confirm_action = parts[3]
        
        try:
            if confirm_action == "on":
                success = await config_service.set_maintenance_mode(
                    MaintenanceMode.ON
                )
                status_text = "فعال"
            elif confirm_action == "off":
                success = await config_service.set_maintenance_mode(
                    MaintenanceMode.OFF
                )
                status_text = "غیرفعال"
            else:
                await callback.answer("❌ عملیات نامعتبر", show_alert=True)
                return
            
            if success:
                await callback.answer(
                    f"✅ Maintenance Mode {status_text} شد",
                    show_alert=True
                )
                # بازگشت به منوی Maintenance
                await callback_maintenance_settings(callback, state)
            else:
                await callback.answer("❌ خطا در تغییر وضعیت", show_alert=True)
        
        except Exception as e:
            logger.error(f"Error toggling maintenance: {e}", exc_info=True)
            await callback.answer("❌ خطا رخ داد", show_alert=True)
    
    elif action == "edit_message":
        # ویرایش پیام Maintenance
        text = (
            "✏️ **تغییر پیام Maintenance**\n\n"
            "پیام جدید را وارد کنید:"
        )
        await callback.message.edit_text(text, parse_mode="Markdown")
        await state.set_state(AdminStates.editing_maintenance_message)
        await callback.answer()
    
    else:
        await callback.answer("❌ عملیات نامعتبر", show_alert=True)


async def handle_maintenance_message_input(message: Message, state: FSMContext):
    """دریافت پیام جدید Maintenance"""
    if not await check_owner_access(message):
        return
    
    new_message = message.text.strip()
    
    if len(new_message) < 10:
        await message.answer(
            "⚠️ پیام باید حداقل 10 کاراکتر باشد.",
            reply_markup=get_back_keyboard()
        )
        return
    
    try:
        # دریافت تنظیمات فعلی
        maintenance_config = config_service.get_maintenance_config()
        
        # به‌روزرسانی پیام
        success = await config_service.set_maintenance_mode(
            maintenance_config.mode,
            message=new_message
        )
        
        if success:
            await message.answer(
                "✅ پیام Maintenance به‌روزرسانی شد.",
                reply_markup=get_admin_main_keyboard()
            )
        else:
            await message.answer(
                "❌ خطا در به‌روزرسانی.",
                reply_markup=get_admin_main_keyboard()
            )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating maintenance message: {e}", exc_info=True)
        await message.answer(
            "❌ خطا رخ داد.",
            reply_markup=get_admin_main_keyboard()
        )
        await state.clear()


# ========== Export ==========

# ⚠️ این تابع توسط Runner برای اضافه کردن Admin Router استفاده می‌شود
__all__ = ['get_admin_router', 'is_admin']
