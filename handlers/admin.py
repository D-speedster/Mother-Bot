"""
Handler برای پنل مدیریت ادمین
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Import مشترک از start.py
from handlers.start import get_main_keyboard

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
async def handle_pending_receipts(message: Message, admin_service, deposit_service):
    """
    نمایش فیش‌های در انتظار تأیید
    """
    # چک کردن ادمین بودن
    is_admin = await admin_service.is_admin(message.from_user.id)
    if not is_admin:
        return
    
    try:
        # دریافت فیش‌های pending
        pending_requests = await deposit_service.get_pending_requests(limit=20)
        
        if not pending_requests:
            await message.answer(
                "✅ هیچ فیش در انتظاری وجود ندارد\n\n"
                "تمام درخواست‌ها پردازش شده‌اند.",
                reply_markup=get_admin_keyboard()
            )
            return
        
        # نمایش لیست فیش‌ها
        text = f"📋 فیش‌های در انتظار تأیید\n\n"
        text += f"تعداد: {len(pending_requests)} فیش\n\n"
        
        for req in pending_requests[:5]:  # نمایش 5 فیش اول
            req_id = req['id']
            user_id = req['user_id']
            amount = req['amount']
            created_at = req['created_at']
            
            text += f"🆔 درخواست #{req_id}\n"
            text += f"👤 کاربر: {user_id}\n"
            text += f"💰 مبلغ: {amount:,} تومان\n"
            text += f"📅 تاریخ: {created_at[:19]}\n"
            
            # لینک به فیش برای بررسی
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        text=f"✅ تأیید #{req_id}",
                        callback_data=f"approve_deposit_{req_id}"
                    ),
                    InlineKeyboardButton(
                        text=f"❌ رد #{req_id}",
                        callback_data=f"reject_deposit_{req_id}"
                    )
                ]
            ]
            
            # اگر عکس فیش وجود دارد، ارسال با عکس
            if req.get('receipt_photo_id'):
                await message.bot.send_photo(
                    chat_id=message.from_user.id,
                    photo=req['receipt_photo_id'],
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                )
            else:
                # اگر فقط کد پیگیری است
                tracking = req.get('tracking_code', 'ندارد')
                text += f"🔢 کد پیگیری: {tracking}\n\n"
                
                await message.answer(
                    text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                )
            
            text = ""  # Reset برای فیش بعدی
        
        # پیام نهایی
        if len(pending_requests) > 5:
            await message.answer(
                f"⚠️ {len(pending_requests) - 5} فیش دیگر در انتظار است.\n"
                "برای مشاهده بیشتر، دوباره کلیک کنید.",
                reply_markup=get_admin_keyboard()
            )
        else:
            await message.answer(
                "✅ تمام فیش‌های در انتظار نمایش داده شد.",
                reply_markup=get_admin_keyboard()
            )
        
    except Exception as e:
        logger.error(f"❌ خطا در نمایش فیش‌های pending: {e}", exc_info=True)
        await message.answer(
            "❌ خطا در بارگذاری فیش‌ها",
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
    
    # استفاده از تابع مشترک
    keyboard = await get_main_keyboard(admin_service, message.from_user.id)
    await message.answer(
        "🔙 بازگشت به منوی اصلی",
        reply_markup=keyboard
    )
