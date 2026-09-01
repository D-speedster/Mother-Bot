"""
Handler برای ساخت ربات جدید با FSM
"""
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import logging

from config import BOT_TYPES, BOT_CREATION_COST, ADMIN_USER_IDS
from services import (
    BotService,
    WalletService,
    validate_bot_token,
    BotValidationError,
    InvalidTokenError,
    TelegramRateLimitError,
    NetworkTimeoutError,
    TokenAlreadyRegisteredError
)

logger = logging.getLogger(__name__)

router = Router()


# تعریف State های FSM
class BotCreation(StatesGroup):
    waiting_for_token = State()  # در حال انتظار برای دریافت توکن


def get_bot_types_keyboard() -> InlineKeyboardMarkup:
    """
    ساخت کیبورد انواع ربات به صورت dynamic از BOT_TYPES
    
    این keyboard به صورت خودکار از config.BOT_TYPES ساخته می‌شود
    تا همیشه با لیست ربات‌های موجود همگام باشد
    """
    keyboard = []
    
    # ساخت دکمه برای هر نوع ربات
    for bot_type, bot_description in BOT_TYPES.items():
        keyboard.append([
            InlineKeyboardButton(
                text=bot_description,
                callback_data=f"bot_type_{bot_type}"
            )
        ])
    
    # دکمه بازگشت
    keyboard.append([
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_bot_management")
    ])
    
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
async def handle_token_input(
    message: Message,
    state: FSMContext,
    bot_service: BotService,
    wallet_service: WalletService,
    bot_runner  # BotRunner برای روشن کردن ربات بعد از ساخت
):
    """دریافت و اعتبارسنجی واقعی توکن با API تلگرام و ذخیره در دیتابیس"""
    token = message.text.strip()
    user_id = message.from_user.id
    
    # بررسی اینکه آیا کاربر ادمین است
    is_admin = user_id in ADMIN_USER_IDS
    
    # نمایش پیام در حال بررسی
    if is_admin:
        processing_msg = await message.answer("⏳ در حال بررسی و ثبت توکن... (ادمین - رایگان)")
    else:
        processing_msg = await message.answer("⏳ در حال بررسی موجودی و ثبت توکن...")
    
    try:
        # ۱. دریافت اطلاعات از state
        data = await state.get_data()
        bot_type = data.get('creating_bot_type', 'unknown')
        selected_bot = BOT_TYPES.get(bot_type, "ربات")
        
        # ۲. ثبت ربات (اعتبارسنجی + رمزنگاری + ذخیره در دیتابیس)
        result = await bot_service.register_bot(
            owner_id=user_id,
            token=token,
            bot_type=bot_type
        )
        
        bot_id = result['bot_id']
        
        # ۳. کسر هزینه از کیف پول (فقط برای غیرادمین‌ها)
        # ⚠️ CRITICAL: deduct_credit به صورت اتمیک موجودی را چک و کسر می‌کند
        # جلوگیری از Double Spending در درخواست‌های همزمان
        if not is_admin:
            try:
                await wallet_service.deduct_credit(
                    user_id=user_id,
                    amount=BOT_CREATION_COST,
                    description=f"ساخت ربات {selected_bot} (@{result['username']})"
                )
            except ValueError as e:
                # موجودی کافی نبود (احتمالاً توسط درخواست همزمان دیگر کسر شده)
                # باید ربات را از دیتابیس حذف کنیم
                logger.warning(
                    f"⚠️ موجودی ناکافی بعد از ثبت ربات {bot_id} - حذف ربات"
                )
                
                try:
                    await bot_service.delete_bot(bot_id, user_id)
                    logger.info(f"✅ ربات {bot_id} با موفقیت حذف شد")
                except:
                    logger.error(f"❌ خطا در حذف ربات {bot_id} بعد از کسر ناموفق")
                
                # نمایش پیام خطا به کاربر
                await processing_msg.delete()
                
                keyboard = [
                    [InlineKeyboardButton(
                        text="💳 شارژ کیف پول",
                        callback_data="wallet_charge"
                    )],
                    [InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data="back_to_bot_management"
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
                
                await message.answer(
                    f"⚠️ {str(e)}\n\nلطفاً ابتدا کیف پول خود را شارژ کنید.",
                    reply_markup=reply_markup
                )
                await state.clear()
                return
            
            # دریافت موجودی جدید
            new_balance = await wallet_service.get_balance(user_id)
            balance_text = f"\n\n💰 هزینه ساخت: {BOT_CREATION_COST:,} تومان\n💳 موجودی باقیمانده: {new_balance:,} تومان"
        else:
            balance_text = "\n\n👑 ساخت ربات برای ادمین: رایگان"
        
        # ۴. روشن کردن ربات بلافاصله
        bot_started = await bot_runner.start_bot(bot_id, user_id)
        
        if bot_started:
            bot_status_text = "🟢 ربات شما الان آنلاین است و در حال اجراست!"
            logger.info(f"✅ ربات {bot_id} بلافاصله پس از ساخت روشن شد")
        else:
            bot_status_text = "⚠️ ربات ثبت شد اما خطایی در روشن کردن آن رخ داد. لطفاً دستی آن را فعال کنید."
            logger.warning(f"⚠️ ربات {bot_id} ثبت شد اما روشن نشد")
        
        # پاک کردن state
        await state.clear()
        
        # حذف پیام "در حال بررسی"
        await processing_msg.delete()
        
        # ساخت دکمه‌های بازگشت
        keyboard = [
            [InlineKeyboardButton(text="🤖 مدیریت ربات‌ها", callback_data="back_to_bot_management")],
            [InlineKeyboardButton(text="💳 کیف پول من", callback_data="my_wallet")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        success_message = f"""
✅ توکن با موفقیت تایید و ثبت شد!

نوع ربات: {selected_bot}
🤖 نام ربات: {result['first_name']}
👤 یوزرنیم: @{result['username']}
🆔 شناسه: {result['telegram_id']}
🔐 وضعیت: ✅ فعال و آماده استفاده{balance_text}

{bot_status_text}

🎉 تبریک! ربات شما با موفقیت ثبت و راه‌اندازی شد.

🔒 توکن شما به صورت رمزنگاری‌شده در دیتابیس ذخیره شده است.

برای مدیریت ربات‌های خود، از منوی "🤖 مدیریت ربات‌ها" استفاده کنید.
        """
        
        await message.answer(success_message, reply_markup=reply_markup)
        
        if is_admin:
            logger.info(
                f"✅ ربات جدید ثبت شد (ادمین - رایگان): @{result['username']} "
                f"(ID={bot_id}) توسط ادمین {user_id}"
            )
        else:
            logger.info(
                f"✅ ربات جدید ثبت شد: @{result['username']} "
                f"(ID={bot_id}) توسط کاربر {user_id}, "
                f"هزینه={BOT_CREATION_COST:,}, موجودی جدید={new_balance:,}"
            )
    
    except TokenAlreadyRegisteredError as e:
        # ⚠️ SECURITY: از str(e) استفاده نمی‌کنیم - Information Leakage
        # کاربر نباید بداند این ربات متعلق به چه کسی است
        await processing_msg.delete()
        
        error_message = """
⚠️ این ربات قبلاً در سیستم ثبت شده است.

این ربات قبلاً توسط کاربری دیگر ثبت شده و نمی‌توان مجدداً آن را ثبت کرد.

💡 اگر صاحب این ربات هستید، می‌توانید از قسمت "📋 ربات‌های من" آن را مدیریت کنید.
        """
        
        keyboard = [
            [InlineKeyboardButton(text="📋 ربات‌های من", callback_data="my_bots")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_bot_management")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        await message.answer(error_message, reply_markup=reply_markup)
        await state.clear()
        # ⚠️ SECURITY: لاگ داخلی می‌تواند جزئیات داشته باشد، اما به کاربر نشان نمی‌دهیم
        logger.warning(
            f"⚠️ تلاش برای ثبت مجدد ربات توسط کاربر {user_id}: {type(e).__name__}"
        )
    
    except InvalidTokenError as e:
        # توکن نامعتبر (401)
        # ⚠️ SECURITY: str(e) را به کاربر نشان نمی‌دهیم
        await processing_msg.delete()
        
        error_message = """
❌ توکن نامعتبر است!

لطفاً:
1️⃣ مطمئن شوید توکن را به درستی از @BotFather کپی کردید
2️⃣ توکن باید به این شکل باشد: 123456789:ABCdefGHI...
3️⃣ توکن نباید منقضی شده باشد

🔄 لطفاً دوباره توکن صحیح را ارسال کنید.
برای لغو، روی دکمه "❌ لغو" کلیک کنید.
        """
        
        await message.answer(error_message)
        # ⚠️ جزئیات خطا فقط در log
        logger.warning(
            f"توکن نامعتبر دریافت شد از کاربر {user_id}: {type(e).__name__}"
        )
    
    except TelegramRateLimitError as e:
        # محدودیت تعداد درخواست (429)
        await processing_msg.delete()
        
        # ⚠️ می‌توانیم retry_after را نمایش دهیم (خطری ندارد)
        retry_text = ""
        if hasattr(e, 'retry_after') and e.retry_after:
            retry_text = f"\n\n⏱️ لطفاً {e.retry_after} ثانیه صبر کنید."
        
        error_message = f"""
⏱️ محدودیت تعداد درخواست

تعداد درخواست‌های شما بیش از حد مجاز است.{retry_text}

لطفاً کمی صبر کنید و سپس دوباره توکن را ارسال کنید.
        """
        
        await message.answer(error_message)
        logger.warning(f"Rate limit برای کاربر {user_id}")
    
    except NetworkTimeoutError:
        # زمان‌توقف شبکه
        await processing_msg.delete()
        
        error_message = """
⏰ زمان اتصال تمام شد

لطفاً:
• اتصال اینترنت خود را بررسی کنید
• چند لحظه دیگر دوباره تلاش کنید

🔄 برای تلاش مجدد، توکن را دوباره ارسال کنید.
        """
        
        await message.answer(error_message)
        logger.warning(f"Timeout برای کاربر {user_id}")
    
    except BotValidationError as e:
        # سایر خطاهای اعتبارسنجی
        await processing_msg.delete()
        
        # ⚠️ SECURITY: پیام خطا را محدود می‌کنیم
        error_message = """
❌ خطا در اعتبارسنجی توکن

توکن وارد شده معتبر نیست.

🔄 لطفاً دوباره توکن صحیح را ارسال کنید.
برای لغو، روی دکمه "❌ لغو" کلیک کنید.
        """
        
        await message.answer(error_message)
        logger.warning(f"خطای اعتبارسنجی از کاربر {user_id}: {type(e).__name__}")
    
    except ValueError as e:
        # خطای کسر موجودی (نباید اتفاق بیفتد چون قبلاً چک کردیم)
        await processing_msg.delete()
        
        error_message = f"""
❌ خطا در پردازش تراکنش

{str(e)}

لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.
        """
        
        await message.answer(error_message)
        logger.error(f"خطای ValueError در ثبت ربات: {e}", exc_info=True)
    
    except Exception as e:
        # خطای غیرمنتظره
        await processing_msg.delete()
        
        error_message = """
❌ خطای غیرمنتظره رخ داد!

لطفاً چند لحظه دیگر دوباره تلاش کنید.
اگر مشکل ادامه داشت، با پشتیبانی تماس بگیرید.
        """
        
        await message.answer(error_message)
        logger.error(f"خطای غیرمنتظره در ثبت ربات: {e}", exc_info=True)


@router.callback_query(F.data == "my_bots")
async def callback_my_bots(callback: CallbackQuery, bot_service: BotService):
    """نمایش لیست ربات‌های کاربر با دکمه‌های مدیریت"""
    user_id = callback.from_user.id
    
    try:
        # دریافت لیست ربات‌ها از دیتابیس
        user_bots = await bot_service.get_user_bots(user_id)
        
        if not user_bots:
            # هیچ رباتی ساخته نشده
            keyboard = [
                [InlineKeyboardButton(text="➕ ساخت ربات جدید", callback_data="create_new_bot")],
                [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_bot_management")]
            ]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            
            text = """
📋 ربات‌های من

شما هنوز هیچ رباتی نساخته‌اید.

برای ساخت اولین ربات خود، روی دکمه "➕ ساخت ربات جدید" کلیک کنید.
            """
        else:
            # ساخت دکمه‌های مدیریت برای هر ربات
            keyboard = []
            for bot in user_bots:
                bot_name = bot.get('first_name', 'ربات')
                bot_username = bot.get('username', 'نامشخص')
                # نمایش نام و username — بدون token_encrypted
                button_text = f"🤖 {bot_name} (@{bot_username})"
                keyboard.append([
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"manage_bot_{bot['bot_id']}"
                    )
                ])
            
            # دکمه بازگشت
            keyboard.append([
                InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_bot_management")
            ])
            
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            
            text = f"""
📋 ربات‌های من

تعداد ربات‌ها: {len(user_bots)} عدد

برای مدیریت هر ربات، روی آن کلیک کنید:
            """
        
        await callback.message.edit_text(text, reply_markup=reply_markup)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"❌ خطا در نمایش لیست ربات‌ها: {e}", exc_info=True)
        await callback.answer("❌ خطا در بارگذاری لیست ربات‌ها", show_alert=True)


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
    
    # ⚠️ UX: فقط یک پیام ارسال می‌کنیم، نه دو تا
    text = """
🏠 منوی اصلی

به منوی اصلی بازگشتید.
لطفاً از دکمه‌های زیر گزینه مورد نظر خود را انتخاب کنید:
    """
    
    # پیام inline را حذف می‌کنیم و فقط keyboard اصلی را نمایش می‌دهیم
    await callback.message.delete()
    await callback.message.answer(
        text,
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("manage_bot_"))
async def callback_manage_single_bot(callback: CallbackQuery, bot_service: BotService):
    """نمایش پنل مدیریت یک ربات خاص"""
    try:
        # Parse کردن bot_id از callback.data
        bot_id = int(callback.data.replace("manage_bot_", ""))
        owner_id = callback.from_user.id
        
        # تأیید مالکیت و دریافت اطلاعات از طریق bot_service
        bot_info = await bot_service.get_bot_info(bot_id, owner_id)
        
        # نمایش اطلاعات ربات
        bot_name = bot_info.get('first_name', 'نامشخص')
        bot_username = bot_info.get('username', 'نامشخص')
        bot_type_key = bot_info.get('bot_type', 'unknown')
        bot_type_name = BOT_TYPES.get(bot_type_key, 'ربات')
        bot_status = bot_info.get('status', 'نامشخص')
        created_at = bot_info.get('created_at', 'نامشخص')
        
        # تعیین ایموجی وضعیت
        status_emoji = "✅" if bot_status == 'active' else "⏸"
        status_text = "فعال" if bot_status == 'active' else "غیرفعال"
        
        # تعیین دکمه toggle
        if bot_status == 'active':
            toggle_button_text = "⏸ توقف ربات"
        else:
            toggle_button_text = "▶️ فعال‌سازی ربات"
        
        # ساخت کیبورد مدیریت
        keyboard = [
            [InlineKeyboardButton(
                text=toggle_button_text,
                callback_data=f"toggle_bot_{bot_id}"
            )],
            [InlineKeyboardButton(
                text="🗑 حذف ربات",
                callback_data=f"confirm_delete_{bot_id}"
            )],
            [InlineKeyboardButton(
                text="🔙 بازگشت به لیست",
                callback_data="my_bots"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        text = f"""
🤖 مدیریت ربات

📛 نام: {bot_name}
👤 یوزرنیم: @{bot_username}
🔖 نوع: {bot_type_name}
📅 تاریخ ساخت: {created_at}
{status_emoji} وضعیت: {status_text}

برای مدیریت ربات، از دکمه‌های زیر استفاده کنید:
        """
        
        await callback.message.edit_text(text, reply_markup=reply_markup)
        await callback.answer()
    
    except ValueError as e:
        # ربات یافت نشد یا متعلق به کاربر نیست
        logger.warning(f"⚠️ تلاش برای دسترسی به ربات غیرمجاز: {e}")
        await callback.answer("❌ ربات یافت نشد یا شما مجاز به مدیریت آن نیستید", show_alert=True)
    
    except Exception as e:
        # خطای غیرمنتظره
        logger.error(f"❌ خطا در نمایش پنل مدیریت ربات: {e}", exc_info=True)
        await callback.answer("❌ خطا در بارگذاری اطلاعات ربات", show_alert=True)


@router.callback_query(F.data.startswith("confirm_delete_"))
async def callback_confirm_delete_bot(callback: CallbackQuery):
    """نمایش پیام تأیید حذف ربات"""
    try:
        # Parse کردن bot_id
        bot_id = int(callback.data.replace("confirm_delete_", ""))
        
        # ساخت کیبورد تأیید
        keyboard = [
            [InlineKeyboardButton(
                text="✅ بله، حذف شود",
                callback_data=f"delete_bot_{bot_id}"
            )],
            [InlineKeyboardButton(
                text="❌ انصراف",
                callback_data=f"manage_bot_{bot_id}"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        text = """
⚠️ تأیید حذف ربات

آیا مطمئن هستید که می‌خواهید این ربات را حذف کنید؟

🚨 این عمل غیرقابل بازگشت است!

تمام اطلاعات مربوط به این ربات از سیستم حذف خواهد شد.
        """
        
        await callback.message.edit_text(text, reply_markup=reply_markup)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"❌ خطا در نمایش پیام تأیید حذف: {e}", exc_info=True)
        await callback.answer("❌ خطا در پردازش درخواست", show_alert=True)


@router.callback_query(F.data.startswith("delete_bot_"))
async def callback_delete_bot(callback: CallbackQuery, bot_service: BotService, bot_runner):
    """حذف ربات بعد از تأیید"""
    try:
        # Parse کردن bot_id
        bot_id = int(callback.data.replace("delete_bot_", ""))
        owner_id = callback.from_user.id
        
        # ۱. توقف ربات در حال اجرا (اگر فعال باشد)
        stopped = await bot_runner.stop_bot(bot_id)
        if stopped:
            logger.info(f"🛑 ربات {bot_id} متوقف شد قبل از حذف")
        
        # ۲. حذف ربات از دیتابیس
        await bot_service.delete_bot(bot_id, owner_id)
        
        # نمایش پیام موفقیت
        keyboard = [
            [InlineKeyboardButton(
                text="📋 ربات‌های من",
                callback_data="my_bots"
            )],
            [InlineKeyboardButton(
                text="🏠 منوی اصلی",
                callback_data="back_to_main"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        text = """
✅ ربات با موفقیت حذف شد

ربات شما از سیستم حذف شد و پولینگ آن متوقف شد.

برای مشاهده ربات‌های باقیمانده، از دکمه "📋 ربات‌های من" استفاده کنید.
        """
        
        await callback.message.edit_text(text, reply_markup=reply_markup)
        await callback.answer("✅ ربات حذف شد")
        
        logger.info(f"✅ ربات {bot_id} توسط کاربر {owner_id} حذف شد")
    
    except ValueError as e:
        # ربات یافت نشد یا متعلق به کاربر نیست
        logger.warning(f"⚠️ تلاش برای حذف ربات غیرمجاز: {e}")
        await callback.answer("❌ ربات یافت نشد یا شما مجاز به حذف آن نیستید", show_alert=True)
    
    except Exception as e:
        # خطای غیرمنتظره
        logger.error(f"❌ خطا در حذف ربات: {e}", exc_info=True)
        await callback.answer("❌ خطا در حذف ربات", show_alert=True)


@router.callback_query(F.data.startswith("toggle_bot_"))
async def callback_toggle_bot_status(callback: CallbackQuery, bot_service: BotService, bot_runner):
    """تغییر وضعیت ربات (فعال/غیرفعال)"""
    try:
        # Parse کردن bot_id
        bot_id = int(callback.data.replace("toggle_bot_", ""))
        owner_id = callback.from_user.id
        
        # دریافت وضعیت فعلی
        bot_info = await bot_service.get_bot_info(bot_id, owner_id)
        current_status = bot_info.get('status', 'inactive')
        
        # Toggle وضعیت
        new_status = 'inactive' if current_status == 'active' else 'active'
        
        # به‌روزرسانی وضعیت در دیتابیس
        await bot_service.update_bot_status(bot_id, owner_id, new_status)
        
        # مدیریت ربات در BotRunner
        if new_status == 'active':
            # فعال‌سازی: شروع ربات
            started = await bot_runner.start_bot(bot_id, owner_id)
            if started:
                logger.info(f"✅ ربات {bot_id} روشن شد")
                runtime_status = "🟢 ربات الان آنلاین است"
            else:
                logger.warning(f"⚠️ ربات {bot_id} در دیتابیس فعال شد اما شروع نشد")
                runtime_status = "⚠️ ربات فعال شد اما خطایی در روشن کردن رخ داد"
        else:
            # غیرفعال‌سازی: توقف ربات
            stopped = await bot_runner.stop_bot(bot_id)
            if stopped:
                logger.info(f"🛑 ربات {bot_id} متوقف شد")
                runtime_status = "⏸ ربات متوقف شد"
            else:
                logger.info(f"ℹ️ ربات {bot_id} در حال اجرا نبود")
                runtime_status = "ℹ️ ربات غیرفعال شد"
        
        logger.info(
            f"✅ وضعیت ربات {bot_id} توسط کاربر {owner_id} "
            f"از {current_status} به {new_status} تغییر یافت"
        )
        
        # دریافت اطلاعات به‌روز شده
        bot_info_updated = await bot_service.get_bot_info(bot_id, owner_id)
        
        # نمایش UI به‌روز شده
        bot_name = bot_info_updated.get('first_name', 'نامشخص')
        bot_username = bot_info_updated.get('username', 'نامشخص')
        bot_type_key = bot_info_updated.get('bot_type', 'unknown')
        bot_type_name = BOT_TYPES.get(bot_type_key, 'ربات')
        bot_status = bot_info_updated.get('status', 'نامشخص')
        created_at = bot_info_updated.get('created_at', 'نامشخص')
        
        # تعیین ایموجی وضعیت
        status_emoji = "✅" if bot_status == 'active' else "⏸"
        status_text = "فعال" if bot_status == 'active' else "غیرفعال"
        
        # تعیین دکمه toggle
        if bot_status == 'active':
            toggle_button_text = "⏸ توقف ربات"
        else:
            toggle_button_text = "▶️ فعال‌سازی ربات"
        
        # ساخت کیبورد مدیریت
        keyboard = [
            [InlineKeyboardButton(
                text=toggle_button_text,
                callback_data=f"toggle_bot_{bot_id}"
            )],
            [InlineKeyboardButton(
                text="🗑 حذف ربات",
                callback_data=f"confirm_delete_{bot_id}"
            )],
            [InlineKeyboardButton(
                text="🔙 بازگشت به لیست",
                callback_data="my_bots"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        text = f"""
🤖 مدیریت ربات

📛 نام: {bot_name}
👤 یوزرنیم: @{bot_username}
🔖 نوع: {bot_type_name}
📅 تاریخ ساخت: {created_at}
{status_emoji} وضعیت: {status_text}

{runtime_status}

برای مدیریت ربات، از دکمه‌های زیر استفاده کنید:
        """
        
        await callback.message.edit_text(text, reply_markup=reply_markup)
        await callback.answer(f"✅ وضعیت ربات به '{status_text}' تغییر یافت")
    
    except ValueError as e:
        # ربات یافت نشد یا متعلق به کاربر نیست
        logger.warning(f"⚠️ تلاش برای تغییر وضعیت ربات غیرمجاز: {e}")
        await callback.answer("❌ ربات یافت نشد یا شما مجاز به تغییر وضعیت آن نیستید", show_alert=True)
    
    except Exception as e:
        # خطای غیرمنتظره
        logger.error(f"❌ خطا در تغییر وضعیت ربات: {e}", exc_info=True)
        await callback.answer("❌ خطا در تغییر وضعیت ربات", show_alert=True)
