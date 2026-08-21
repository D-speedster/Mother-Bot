"""
Handler برای پنل مدیریت ادمین
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)

# Router برای handlers مدیریتی
admin_router = Router()


class AdminStates(StatesGroup):
    """حالت‌های FSM برای پنل ادمین"""
    waiting_for_new_admin_id = State()
    waiting_for_remove_admin_id = State()


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد اصلی پنل ادمین"""
    keyboard = [
        [KeyboardButton(text="📊 آمار کلی")],
        [KeyboardButton(text="👥 مدیریت ادمین‌ها"), KeyboardButton(text="📋 فیش‌های در انتظار")],
        [KeyboardButton(text="🔙 بازگشت به منوی اصلی")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_admin_management_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد مدیریت ادمین‌ها"""
    keyboard = [
        [KeyboardButton(text="➕ افزودن ادمین"), KeyboardButton(text="➖ حذف ادمین")],
        [KeyboardButton(text="📋 لیست ادمین‌ها")],
        [KeyboardButton(text="🔙 بازگشت به پنل ادمین")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد اصلی (کپی از handlers.start)"""
    keyboard = [
        [KeyboardButton(text="🤖 ساخت ربات")],
        [KeyboardButton(text="💳 کیف پول من"), KeyboardButton(text="👤 حساب کاربری")],
        [KeyboardButton(text="💰 کسب درآمد"), KeyboardButton(text="🤖 مدیریت ربات‌ها")],
        [KeyboardButton(text="💬 پشتیبانی"), KeyboardButton(text="📋 قوانین")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, admin_service):
    """
    دستور /admin - ورود به پنل مدیریت
    """
    # چک کردن ادمین بودن
    is_admin = await admin_service.is_admin(message.from_user.id)
    if not is_admin:
        return  # بدون پیام، فقط ignore
    
    await message.answer(
        "🔐 به پنل مدیریت خوش آمدید",
        reply_markup=get_admin_keyboard()
    )


@admin_router.message(F.text == "⚙️ پنل ادمین")
async def handle_admin_panel(message: Message, admin_service):
    """
    دکمه پنل ادمین از منوی اصلی
    """
    # چک کردن ادمین بودن
    is_admin = await admin_service.is_admin(message.from_user.id)
    if not is_admin:
        return  # بدون پیام، فقط ignore
    
    await message.answer(
        "🔐 به پنل مدیریت خوش آمدید",
        reply_markup=get_admin_keyboard()
    )


@admin_router.message(F.text == "📊 آمار کلی")
async def handle_stats(message: Message, admin_service):
    """
    نمایش آمار کلی سیستم
    """
    # چک کردن ادمین بودن
    is_admin = await admin_service.is_admin(message.from_user.id)
    if not is_admin:
        return
    
    # دریافت آمار
    stats = await admin_service.get_stats()
    
    # نمایش آمار
    text = f"""
📊 آمار سیستم

👥 کاربران: {stats['total_users']:,}
🤖 کل ربات‌ها: {stats['total_bots']:,}
✅ ربات‌های فعال: {stats['active_bots']:,}
💰 درآمد کل: {stats['total_revenue']:,} تومان
⏳ فیش‌های در انتظار: {stats['pending_receipts']:,}
"""
    
    await message.answer(text, reply_markup=get_admin_keyboard())


@admin_router.message(F.text == "👥 مدیریت ادمین‌ها")
async def handle_admin_management(message: Message, admin_service):
    """
    ورود به بخش مدیریت ادمین‌ها
    """
    # چک کردن ادمین بودن
    is_admin = await admin_service.is_admin(message.from_user.id)
    if not is_admin:
        return
    
    await message.answer(
        "👥 مدیریت ادمین‌ها\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_admin_management_keyboard()
    )


@admin_router.message(F.text == "📋 لیست ادمین‌ها")
async def handle_list_admins(message: Message, admin_service):
    """
    نمایش لیست تمام ادمین‌ها
    """
    # چک کردن ادمین بودن
    is_admin = await admin_service.is_admin(message.from_user.id)
    if not is_admin:
        return
    
    # دریافت لیست ادمین‌ها
    admins = await admin_service.get_all_admins()
    
    if not admins:
        await message.answer(
            "⚠️ هیچ ادمینی در سیستم ثبت نشده است",
            reply_markup=get_admin_management_keyboard()
        )
        return
    
    # ساخت متن لیست
    text = "📋 لیست ادمین‌ها:\n\n"
    for idx, admin in enumerate(admins, 1):
        text += f"{idx}. 🔹 User ID: `{admin['user_id']}`\n"
        text += f"   📅 تاریخ: {admin['created_at']}\n\n"
    
    await message.answer(
        text,
        reply_markup=get_admin_management_keyboard(),
        parse_mode="Markdown"
    )


@admin_router.message(F.text == "➕ افزودن ادمین")
async def handle_add_admin_request(message: Message, state: FSMContext, admin_service):
    """
    درخواست افزودن ادمین جدید
    """
    # چک کردن ادمین بودن
    is_admin = await admin_service.is_admin(message.from_user.id)
    if not is_admin:
        return
    
    # تنظیم حالت FSM
    await state.set_state(AdminStates.waiting_for_new_admin_id)
    
    await message.answer(
        "➕ افزودن ادمین جدید\n\n"
        "لطفاً User ID کاربر جدید را ارسال کنید:\n"
        "(یک عدد مثل: 123456789)\n\n"
        "برای لغو، /cancel را ارسال کنید.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 بازگشت به پنل ادمین")]],
            resize_keyboard=True
        )
    )


@admin_router.message(AdminStates.waiting_for_new_admin_id)
async def handle_add_admin_process(message: Message, state: FSMContext, admin_service):
    """
    پردازش افزودن ادمین جدید
    """
    # چک لغو
    if message.text == "🔙 بازگشت به پنل ادمین":
        await state.clear()
        await message.answer(
            "❌ عملیات لغو شد",
            reply_markup=get_admin_keyboard()
        )
        return
    
    # چک اینکه عدد باشد
    if not message.text or not message.text.isdigit():
        await message.answer(
            "⚠️ لطفاً فقط عدد (User ID) ارسال کنید\n"
            "مثال: 123456789"
        )
        return
    
    new_admin_id = int(message.text)
    requester_id = message.from_user.id
    
    # افزودن ادمین
    success = await admin_service.add_admin(new_admin_id, requester_id)
    
    # پاک کردن state
    await state.clear()
    
    if success:
        await message.answer(
            f"✅ ادمین جدید با موفقیت اضافه شد\n\n"
            f"User ID: `{new_admin_id}`",
            reply_markup=get_admin_management_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "⚠️ این کاربر قبلاً ادمین است یا خطایی رخ داده است",
            reply_markup=get_admin_management_keyboard()
        )


@admin_router.message(F.text == "➖ حذف ادمین")
async def handle_remove_admin_request(message: Message, state: FSMContext, admin_service):
    """
    درخواست حذف ادمین
    """
    # چک کردن ادمین بودن
    is_admin = await admin_service.is_admin(message.from_user.id)
    if not is_admin:
        return
    
    # تنظیم حالت FSM
    await state.set_state(AdminStates.waiting_for_remove_admin_id)
    
    await message.answer(
        "➖ حذف ادمین\n\n"
        "لطفاً User ID ادمینی که می‌خواهید حذف کنید را ارسال کنید:\n"
        "(یک عدد مثل: 123456789)\n\n"
        "⚠️ توجه: ادمین اصلی سیستم قابل حذف نیست\n\n"
        "برای لغو، /cancel را ارسال کنید.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 بازگشت به پنل ادمین")]],
            resize_keyboard=True
        )
    )


@admin_router.message(AdminStates.waiting_for_remove_admin_id)
async def handle_remove_admin_process(message: Message, state: FSMContext, admin_service):
    """
    پردازش حذف ادمین
    """
    # چک لغو
    if message.text == "🔙 بازگشت به پنل ادمین":
        await state.clear()
        await message.answer(
            "❌ عملیات لغو شد",
            reply_markup=get_admin_keyboard()
        )
        return
    
    # چک اینکه عدد باشد
    if not message.text or not message.text.isdigit():
        await message.answer(
            "⚠️ لطفاً فقط عدد (User ID) ارسال کنید\n"
            "مثال: 123456789"
        )
        return
    
    remove_admin_id = int(message.text)
    requester_id = message.from_user.id
    
    # حذف ادمین (با تمام محافظت‌های Business-Level)
    success = await admin_service.remove_admin(remove_admin_id, requester_id)
    
    # پاک کردن state
    await state.clear()
    
    if success:
        await message.answer(
            f"✅ ادمین با موفقیت حذف شد\n\n"
            f"User ID: `{remove_admin_id}`",
            reply_markup=get_admin_management_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "⚠️ امکان حذف این ادمین وجود ندارد:\n\n"
            "• ادمین اصلی سیستم را نمی‌توان حذف کرد\n"
            "• نمی‌توانید خودتان را حذف کنید\n"
            "• این کاربر ادمین نیست",
            reply_markup=get_admin_management_keyboard()
        )


@admin_router.message(F.text == "📋 فیش‌های در انتظار")
async def handle_pending_receipts(message: Message, admin_service):
    """
    هدایت به پنل فیش‌های در انتظار
    (این handler فقط redirect می‌کند - پیاده‌سازی واقعی در wallet.py است)
    """
    # چک کردن ادمین بودن
    is_admin = await admin_service.is_admin(message.from_user.id)
    if not is_admin:
        return
    
    await message.answer(
        "📋 بررسی فیش‌های در انتظار\n\n"
        "لطفاً از دستور /review_deposits استفاده کنید",
        reply_markup=get_admin_keyboard()
    )


@admin_router.message(F.text == "🔙 بازگشت به پنل ادمین")
async def handle_back_to_admin_panel(message: Message, state: FSMContext, admin_service):
    """
    بازگشت به پنل اصلی ادمین
    """
    # چک کردن ادمین بودن
    is_admin = await admin_service.is_admin(message.from_user.id)
    if not is_admin:
        return
    
    # پاک کردن هر state ممکن
    await state.clear()
    
    await message.answer(
        "🔙 بازگشت به پنل مدیریت",
        reply_markup=get_admin_keyboard()
    )


@admin_router.message(F.text == "🔙 بازگشت به منوی اصلی")
async def handle_back_to_main_menu(message: Message, state: FSMContext, admin_service):
    """
    بازگشت به منوی اصلی
    """
    # چک کردن ادمین بودن
    is_admin = await admin_service.is_admin(message.from_user.id)
    if not is_admin:
        return
    
    # پاک کردن هر state ممکن
    await state.clear()
    
    await message.answer(
        "🔙 بازگشت به منوی اصلی",
        reply_markup=get_main_keyboard()
    )
