"""
Handler برای دستور /start و منوی اصلی
"""
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """ساخت کیبورد اصلی"""
    keyboard = [
        [KeyboardButton(text="🤖 ساخت ربات")],  # دکمه تک‌سطری
        [KeyboardButton(text="💳 کیف پول من"), KeyboardButton(text="👤 حساب کاربری")],
        [KeyboardButton(text="💰 کسب درآمد"), KeyboardButton(text="🤖 مدیریت ربات‌ها")],
        [KeyboardButton(text="💬 پشتیبانی"), KeyboardButton(text="📋 قوانین")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: Message):
    """پیام خوش‌آمدگویی و نمایش منوی اصلی"""
    user = message.from_user
    welcome_message = f"""
سلام {user.first_name} عزیز! 👋

به ربات دستیار من خوش آمدید.
لطفاً از منوی زیر گزینه مورد نظر خود را انتخاب کنید:
    """
    await message.answer(welcome_message, reply_markup=get_main_keyboard())


@router.message(F.text == "👤 حساب کاربری")
async def handle_account(message: Message):
    """نمایش اطلاعات حساب کاربری"""
    user = message.from_user
    text = f"""
👤 حساب کاربری

نام کاربری: @{user.username if user.username else 'تنظیم نشده'}
نام: {user.first_name}
شناسه کاربری: {user.id}

وضعیت اشتراک: ⚠️ فعال نیست
تاریخ انقضا: ---
حجم مصرفی: 0 GB
موجودی کیف پول: 0 تومان

برای فعال‌سازی اشتراک، از منوی خرید اقدام کنید.
    """
    await message.answer(text, reply_markup=get_main_keyboard())


@router.message(F.text == "💰 کسب درآمد")
async def handle_earn_money(message: Message):
    """نمایش برنامه کسب درآمد"""
    user = message.from_user
    referral_link = f"https://t.me/YOUR_BOT_USERNAME?start={user.id}"
    
    text = f"""
💰 کسب درآمد

با معرفی دوستان خود، درآمد کسب کنید!

🎁 برای هر دوست که از طریق لینک شما ثبت‌نام کند:
• 10,000 تومان پاداش دریافت کنید

📊 آمار شما:
• تعداد دعوت‌شده‌ها: 0 نفر
• درآمد کل: 0 تومان
• قابل برداشت: 0 تومان

🔗 لینک دعوت شما:
{referral_link}

این لینک را با دوستان خود به اشتراک بگذارید!
    """
    await message.answer(text, reply_markup=get_main_keyboard())


@router.message(F.text == "🤖 مدیریت ربات‌ها")
async def handle_bot_management(message: Message):
    """نمایش منوی مدیریت ربات‌ها"""
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
    await message.answer(text, reply_markup=reply_markup)


@router.message(F.text == "💬 پشتیبانی")
async def handle_support(message: Message):
    """نمایش اطلاعات پشتیبانی"""
    text = """
💬 پشتیبانی

ما 24 ساعته در خدمت شما هستیم!

📞 راه‌های ارتباطی:
• تلگرام: @YourSupportUsername
• ایمیل: support@example.com
• تلفن: 021-12345678

⏰ پاسخگویی:
• چت آنلاین: فوری تا 30 دقیقه
• ایمیل: تا 2 ساعت
• تلفن: 9 صبح تا 9 شب

سوالات متداول:
1. چگونه اشتراک خریداری کنم؟
2. چگونه ربات بسازم؟
3. چگونه درآمد کسب کنم؟

برای سوالات خود پیام دهید.
    """
    await message.answer(text, reply_markup=get_main_keyboard())


@router.message(F.text == "📋 قوانین")
async def handle_rules(message: Message):
    """نمایش قوانین"""
    text = """
📋 قوانین و مقررات

1. استفاده از سرویس فقط برای مقاصد قانونی مجاز است
2. هر حساب کاربری فقط متعلق به یک نفر است
3. اشتراک‌گذاری حساب کاربری ممنوع است
4. در صورت تخلف، حساب کاربری مسدود خواهد شد
5. بازپرداخت وجه پس از فعال‌سازی امکان‌پذیر نیست
6. پشتیبانی 24 ساعته در خدمت شماست

با استفاده از خدمات ما، قوانین را می‌پذیرید.
    """
    await message.answer(text, reply_markup=get_main_keyboard())
