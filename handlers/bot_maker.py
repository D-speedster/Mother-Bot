"""
Handler برای ساخت ربات جدید با FSM
"""
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import logging

from config import BOT_TYPES
from services import (
    validate_bot_token,
    BotValidationError,
    InvalidTokenError,
    TelegramRateLimitError,
    NetworkTimeoutError
)

logger = logging.getLogger(__name__)

router = Router()


# تعریف State های FSM
class BotCreation(StatesGroup):
    waiting_for_token = State()  # در حال انتظار برای دریافت توکن


def get_bot_types_keyboard() -> InlineKeyboardMarkup:
    """ساخت کیبورد انواع ربات"""
    keyboard = [
        [InlineKeyboardButton(text="🛒 ربات فروشگاهی", callback_data="bot_type_shop")],
        [InlineKeyboardButton(text="📥 ربات دانلودر", callback_data="bot_type_downloader")],
        [InlineKeyboardButton(text="🎫 ربات پشتیبانی و تیکت", callback_data="bot_type_support")],
        [InlineKeyboardButton(text="📢 ربات ارسال همگانی (Broadcast)", callback_data="bot_type_broadcast")],
        [InlineKeyboardButton(text="⚙️ ربات ابزار و خدمات", callback_data="bot_type_tools")],
        [InlineKeyboardButton(text="🔗 ربات همکاری در فروش (Affiliate)", callback_data="bot_type_affiliate")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_bot_management")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(F.text == "🤖 ساخت ربات")
async def handle_create_bot(message: Message):
    """هدایت مستقیم به منوی انتخاب نوع ربات"""
    text = """
➕ ساخت ربات جدید

لطفاً نوع رباتی که می‌خواهید بسازید را از لیست زیر انتخاب کنید:
    """
    await message.answer(text, reply_markup=get_bot_types_keyboard())


@router.callback_query(F.data == "create_new_bot")
async def callback_create_new_bot(callback: CallbackQuery):
    """نمایش لیست انواع ربات"""
    text = """
➕ ساخت ربات جدید

لطفاً نوع رباتی که می‌خواهید بسازید را از لیست زیر انتخاب کنید:
    """
    await callback.message.edit_text(text, reply_markup=get_bot_types_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("bot_type_"))
async def callback_bot_type_selected(callback: CallbackQuery, state: FSMContext):
    """مدیریت انتخاب نوع ربات"""
    bot_type = callback.data.replace("bot_type_", "")
    selected_bot = BOT_TYPES.get(bot_type, "ربات")
    
    # ذخیره نوع ربات در state
    await state.update_data(creating_bot_type=bot_type)
    
    # نمایش پیام تایید
    keyboard = [
        [InlineKeyboardButton(text="✅ ادامه ساخت ربات", callback_data=f"continue_create_{bot_type}")],
        [InlineKeyboardButton(text="🔙 بازگشت به انتخاب نوع", callback_data="create_new_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    text = f"""
✅ نوع ربات انتخاب شد

نوع ربات: {selected_bot}

در مراحل بعدی از شما توکن BotFather خواسته خواهد شد تا ربات شما راه‌اندازی شود.

آیا آماده ادامه هستید؟
    """
    
    await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(F.data.startswith("continue_create_"))
async def callback_continue_create(callback: CallbackQuery, state: FSMContext):
    """شروع فرآیند دریافت توکن"""
    bot_type = callback.data.replace("continue_create_", "")
    selected_bot = BOT_TYPES.get(bot_type, "ربات")
    
    # تنظیم state به حالت انتظار برای توکن
    await state.set_state(BotCreation.waiting_for_token)
    await state.update_data(creating_bot_type=bot_type)
    
    keyboard = [
        [InlineKeyboardButton(text="❌ لغو", callback_data="cancel_bot_creation")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    text = f"""
🔑 دریافت توکن ربات

نوع ربات: {selected_bot}

لطفاً مراحل زیر را انجام دهید:

1️⃣ به @BotFather در تلگرام مراجعه کنید
2️⃣ دستور /newbot را ارسال کنید
3️⃣ نام و نام کاربری (username) ربات را تعیین کنید
4️⃣ توکن دریافتی را کپی کنید
5️⃣ توکن را در همین چت برای من ارسال کنید

⚠️ توکن شما به صورت امن ذخیره خواهد شد.

⏳ منتظر دریافت توکن هستم...
    """
    
    await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(F.data == "cancel_bot_creation")
async def callback_cancel_creation(callback: CallbackQuery, state: FSMContext):
    """لغو فرآیند ساخت ربات"""
    await state.clear()
    
    keyboard = [
        [InlineKeyboardButton(text="➕ ساخت ربات جدید", callback_data="create_new_bot")],
        [InlineKeyboardButton(text="📋 ربات‌های من", callback_data="my_bots")],
        [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    text = """
🤖 مدیریت ربات‌ها

به پنل مدیریت ربات‌های خود خوش آمدید.
لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
    """
    
    await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer("❌ فرآیند ساخت ربات لغو شد")


@router.message(StateFilter(BotCreation.waiting_for_token))
async def handle_token_input(message: Message, state: FSMContext):
    """دریافت و اعتبارسنجی واقعی توکن با API تلگرام"""
    token = message.text.strip()
    
    # نمایش پیام در حال بررسی
    processing_msg = await message.answer("⏳ در حال بررسی توکن...")
    
    try:
        # اعتبارسنجی توکن با API تلگرام (فراخوانی getMe)
        bot_info = await validate_bot_token(token)
        
        # دریافت اطلاعات از state
        data = await state.get_data()
        bot_type = data.get('creating_bot_type', 'unknown')
        selected_bot = BOT_TYPES.get(bot_type, "ربات")
        
        # ذخیره توکن و اطلاعات ربات در state
        user_bots = data.get('user_bots', [])
        user_bots.append({
            'type': bot_type,
            'token': token,
            'bot_id': bot_info['id'],
            'bot_username': bot_info['username'],
            'bot_name': bot_info['first_name'],
            'created_at': 'اکنون'
        })
        
        await state.update_data(user_bots=user_bots)
        
        # پاک کردن state ساخت ربات
        await state.clear()
        # بازگرداندن لیست ربات‌ها به state
        await state.update_data(user_bots=user_bots)
        
        # حذف پیام "در حال بررسی"
        await processing_msg.delete()
        
        # ساخت دکمه‌های بازگشت
        keyboard = [
            [InlineKeyboardButton(text="🤖 مدیریت ربات‌ها", callback_data="back_to_bot_management")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        success_message = f"""
✅ توکن با موفقیت تایید شد!

نوع ربات: {selected_bot}
🤖 نام ربات: {bot_info['first_name']}
👤 یوزرنیم: @{bot_info['username']}
🆔 شناسه: {bot_info['id']}
وضعیت: ✅ فعال و آماده استفاده

🎉 تبریک! ربات شما با موفقیت ثبت و راه‌اندازی شد.

برای مدیریت ربات‌های خود، از منوی "🤖 مدیریت ربات‌ها" استفاده کنید.
        """
        
        await message.answer(success_message, reply_markup=reply_markup)
        logger.info(f"ربات جدید ثبت شد: @{bot_info['username']} توسط کاربر {message.from_user.id}")
    
    except InvalidTokenError as e:
        # توکن نامعتبر (401)
        await processing_msg.delete()
        
        error_message = f"""
❌ توکن نامعتبر است!

خطا: {str(e)}

لطفاً:
1️⃣ مطمئن شوید توکن را به درستی از @BotFather کپی کردید
2️⃣ توکن باید به این شکل باشد: 123456789:ABCdefGHI...
3️⃣ توکن نباید منقضی شده باشد

🔄 لطفاً دوباره توکن صحیح را ارسال کنید.
برای لغو، روی دکمه "❌ لغو" کلیک کنید.
        """
        
        await message.answer(error_message)
        logger.warning(f"توکن نامعتبر دریافت شد از کاربر {message.from_user.id}")
    
    except TelegramRateLimitError as e:
        # محدودیت تعداد درخواست (429)
        await processing_msg.delete()
        
        error_message = f"""
⏱️ محدودیت تعداد درخواست

{str(e)}

لطفاً کمی صبر کنید و سپس دوباره توکن را ارسال کنید.
        """
        
        await message.answer(error_message)
        logger.warning(f"Rate limit برای کاربر {message.from_user.id}")
    
    except NetworkTimeoutError as e:
        # زمان‌توقف شبکه
        await processing_msg.delete()
        
        error_message = f"""
⏰ زمان اتصال تمام شد

{str(e)}

لطفاً:
• اتصال اینترنت خود را بررسی کنید
• چند لحظه دیگر دوباره تلاش کنید

🔄 برای تلاش مجدد، توکن را دوباره ارسال کنید.
        """
        
        await message.answer(error_message)
        logger.warning(f"Timeout برای کاربر {message.from_user.id}")
    
    except BotValidationError as e:
        # سایر خطاهای اعتبارسنجی
        await processing_msg.delete()
        
        error_message = f"""
❌ خطا در اعتبارسنجی توکن

خطا: {str(e)}

🔄 لطفاً دوباره توکن صحیح را ارسال کنید.
برای لغو، روی دکمه "❌ لغو" کلیک کنید.
        """
        
        await message.answer(error_message)
        logger.warning(f"خطای اعتبارسنجی از کاربر {message.from_user.id}: {str(e)}")
    
    except Exception as e:
        # خطای غیرمنتظره
        await processing_msg.delete()
        
        error_message = """
❌ خطای غیرمنتظره رخ داد!

لطفاً چند لحظه دیگر دوباره تلاش کنید.
اگر مشکل ادامه داشت، با پشتیبانی تماس بگیرید.
        """
        
        await message.answer(error_message)
        logger.error(f"خطای غیرمنتظره در اعتبارسنجی توکن: {e}", exc_info=True)


@router.callback_query(F.data == "my_bots")
async def callback_my_bots(callback: CallbackQuery, state: FSMContext):
    """نمایش لیست ربات‌های کاربر با اطلاعات واقعی"""
    data = await state.get_data()
    user_bots = data.get('user_bots', [])
    
    if not user_bots:
        # هیچ رباتی ساخته نشده
        keyboard = [
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_bot_management")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        text = """
📋 ربات‌های من

شما هنوز هیچ رباتی نساخته‌اید.

برای ساخت اولین ربات خود، روی دکمه "➕ ساخت ربات جدید" کلیک کنید.
        """
    else:
        # نمایش لیست ربات‌ها با اطلاعات واقعی
        bots_list = "\n\n".join([
            f"🤖 {BOT_TYPES.get(bot['type'], 'ربات')}\n"
            f"📛 نام: {bot.get('bot_name', 'نامشخص')}\n"
            f"👤 یوزرنیم: @{bot.get('bot_username', 'نامشخص')}\n"
            f"🆔 شناسه: {bot.get('bot_id', 'نامشخص')}\n"
            f"⏰ زمان ساخت: {bot.get('created_at', 'نامشخص')}\n"
            f"✅ وضعیت: فعال"
            for bot in user_bots
        ])
        
        keyboard = [
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_bot_management")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        text = f"""
📋 ربات‌های من

تعداد ربات‌ها: {len(user_bots)} عدد

{bots_list}
        """
    
    await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(F.data == "back_to_bot_management")
async def callback_back_to_management(callback: CallbackQuery):
    """بازگشت به منوی مدیریت ربات‌ها"""
    keyboard = [
        [InlineKeyboardButton(text="➕ ساخت ربات جدید", callback_data="create_new_bot")],
        [InlineKeyboardButton(text="📋 ربات‌های من", callback_data="my_bots")],
        [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    text = """
🤖 مدیریت ربات‌ها

به پنل مدیریت ربات‌های خود خوش آمدید.
لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
    """
    
    await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery):
    """بازگشت به منوی اصلی"""
    from handlers.start import get_main_keyboard
    
    text = """
🏠 منوی اصلی

لطفاً از منوی زیر گزینه مورد نظر خود را انتخاب کنید:
    """
    
    await callback.message.edit_text(text)
    await callback.message.answer(
        "به منوی اصلی بازگشتید:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()
