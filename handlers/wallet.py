"""
Handler برای مدیریت کیف پول کاربر
"""
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

from config import BANK_CARD_NUMBER, BANK_CARD_HOLDER, BANK_NAME, ADMIN_USER_IDS
from services import WalletService, DepositService

logger = logging.getLogger(__name__)

router = Router()


# تعریف State های FSM برای فرآیند ثبت فیش
class DepositStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_receipt = State()


@router.message(F.text == "💳 کیف پول من")
async def handle_my_wallet(message: Message, wallet_service: WalletService):
    """نمایش اطلاعات کیف پول کاربر"""
    user_id = message.from_user.id
    
    try:
        # دریافت موجودی
        balance = await wallet_service.get_balance(user_id)
        
        # دریافت آخرین تراکنش‌ها
        transactions = await wallet_service.get_user_transactions(user_id, limit=5)
        
        # ساخت متن تراکنش‌ها
        if transactions:
            transaction_text = "\n\n📊 آخرین تراکنش‌ها:\n"
            for tx in transactions:
                tx_type = tx['type']
                amount = tx['amount']
                description = tx['description']
                created_at = tx['created_at']
                
                # تعیین ایموجی و علامت
                if tx_type == 'deposit':
                    emoji = "➕"
                    sign = "+"
                    color = "🟢"
                else:  # withdraw
                    emoji = "➖"
                    sign = "-"
                    color = "🔴"
                
                transaction_text += f"{color} {emoji} {sign}{amount:,} تومان - {description}\n"
                transaction_text += f"   📅 {created_at[:19]}\n\n"
        else:
            transaction_text = "\n\n📊 هنوز تراکنشی ثبت نشده است."
        
        # ساخت کیبورد
        keyboard = [
            [InlineKeyboardButton(text="💰 شارژ کیف پول", callback_data="wallet_charge")],
            [InlineKeyboardButton(text="📜 تاریخچه کامل", callback_data="wallet_history")],
            [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        text = f"""
💳 کیف پول من

💰 موجودی فعلی: {balance:,} تومان
{transaction_text}

برای مدیریت کیف پول خود از دکمه‌های زیر استفاده کنید.
        """
        
        await message.answer(text, reply_markup=reply_markup)
    
    except Exception as e:
        logger.error(f"❌ خطا در نمایش کیف پول کاربر {user_id}: {e}", exc_info=True)
        await message.answer(
            "❌ خطا در بارگذاری اطلاعات کیف پول. لطفاً دوباره تلاش کنید."
        )


@router.callback_query(F.data == "my_wallet")
async def callback_my_wallet(callback: CallbackQuery, wallet_service: WalletService):
    """نمایش اطلاعات کیف پول کاربر (callback)"""
    user_id = callback.from_user.id
    
    try:
        # دریافت موجودی
        balance = await wallet_service.get_balance(user_id)
        
        # دریافت آخرین تراکنش‌ها
        transactions = await wallet_service.get_user_transactions(user_id, limit=5)
        
        # ساخت متن تراکنش‌ها
        if transactions:
            transaction_text = "\n\n📊 آخرین تراکنش‌ها:\n"
            for tx in transactions:
                tx_type = tx['type']
                amount = tx['amount']
                description = tx['description']
                created_at = tx['created_at']
                
                # تعیین ایموجی و علامت
                if tx_type == 'deposit':
                    emoji = "➕"
                    sign = "+"
                    color = "🟢"
                else:  # withdraw
                    emoji = "➖"
                    sign = "-"
                    color = "🔴"
                
                transaction_text += f"{color} {emoji} {sign}{amount:,} تومان - {description}\n"
                transaction_text += f"   📅 {created_at[:19]}\n\n"
        else:
            transaction_text = "\n\n📊 هنوز تراکنشی ثبت نشده است."
        
        # ساخت کیبورد
        keyboard = [
            [InlineKeyboardButton(text="💰 شارژ کیف پول", callback_data="wallet_charge")],
            [InlineKeyboardButton(text="📜 تاریخچه کامل", callback_data="wallet_history")],
            [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        text = f"""
💳 کیف پول من

💰 موجودی فعلی: {balance:,} تومان
{transaction_text}

برای مدیریت کیف پول خود از دکمه‌های زیر استفاده کنید.
        """
        
        await callback.message.edit_text(text, reply_markup=reply_markup)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"❌ خطا در نمایش کیف پول کاربر {user_id}: {e}", exc_info=True)
        await callback.answer("❌ خطا در بارگذاری اطلاعات کیف پول", show_alert=True)


@router.callback_query(F.data == "wallet_charge")
async def callback_wallet_charge(callback: CallbackQuery, state: FSMContext):
    """نمایش راهنمای شارژ کیف پول و شروع فرآیند ثبت فیش"""
    keyboard = [
        [InlineKeyboardButton(text="📤 ثبت فیش واریزی", callback_data="submit_receipt")],
        [InlineKeyboardButton(text="💳 کیف پول من", callback_data="my_wallet")],
        [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    text = f"""
💰 شارژ کیف پول

📋 اطلاعات واریز:

💳 شماره کارت: {BANK_CARD_NUMBER}
👤 به نام: {BANK_CARD_HOLDER}
🏦 {BANK_NAME}

⚠️ نکات مهم:
1️⃣ پس از واریز، روی دکمه "📤 ثبت فیش واریزی" کلیک کنید
2️⃣ مبلغ واریزی خود را وارد کنید
3️⃣ تصویر فیش واریزی یا شماره پیگیری را ارسال کنید
4️⃣ پس از بررسی ادمین، موجودی شما شارژ می‌شود

🆔 شناسه کاربری شما: {callback.from_user.id}
(این شناسه را در توضیحات واریز ذکر کنید)
    """
    
    await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(F.data == "wallet_history")
async def callback_wallet_history(callback: CallbackQuery, wallet_service: WalletService):
    """نمایش تاریخچه کامل تراکنش‌ها"""
    user_id = callback.from_user.id
    
    try:
        # دریافت موجودی
        balance = await wallet_service.get_balance(user_id)
        
        # دریافت تراکنش‌ها (20 تای آخر)
        transactions = await wallet_service.get_user_transactions(user_id, limit=20)
        
        # ساخت متن تراکنش‌ها
        if transactions:
            transaction_text = "\n\n📊 تاریخچه تراکنش‌ها:\n\n"
            for tx in transactions:
                tx_type = tx['type']
                amount = tx['amount']
                description = tx['description']
                created_at = tx['created_at']
                
                # تعیین ایموجی و علامت
                if tx_type == 'deposit':
                    emoji = "➕"
                    sign = "+"
                    color = "🟢"
                else:  # withdraw
                    emoji = "➖"
                    sign = "-"
                    color = "🔴"
                
                transaction_text += f"{color} {emoji} {sign}{amount:,} تومان - {description}\n"
                transaction_text += f"   📅 {created_at[:19]}\n\n"
        else:
            transaction_text = "\n\n📊 هنوز تراکنشی ثبت نشده است."
        
        # ساخت کیبورد
        keyboard = [
            [InlineKeyboardButton(text="💳 کیف پول من", callback_data="my_wallet")],
            [InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        text = f"""
📜 تاریخچه کامل تراکنش‌ها

💰 موجودی فعلی: {balance:,} تومان
{transaction_text}

نمایش {len(transactions)} تراکنش اخیر
        """
        
        # بررسی طول پیام (محدودیت تلگرام 4096 کاراکتر)
        if len(text) > 4000:
            text = text[:3950] + "\n\n... (تعداد تراکنش‌ها زیاد است)"
        
        await callback.message.edit_text(text, reply_markup=reply_markup)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"❌ خطا در نمایش تاریخچه تراکنش‌ها برای کاربر {user_id}: {e}", exc_info=True)
        await callback.answer("❌ خطا در بارگذاری تاریخچه تراکنش‌ها", show_alert=True)


# ========== جریان ثبت فیش واریزی ==========

@router.callback_query(F.data == "submit_receipt")
async def callback_submit_receipt(callback: CallbackQuery, state: FSMContext):
    """شروع فرآیند ثبت فیش واریزی"""
    keyboard = [
        [InlineKeyboardButton(text="❌ لغو", callback_data="wallet_charge")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    text = """
📤 ثبت فیش واریزی

لطفاً مبلغ واریزی خود را به تومان وارد کنید.

مثال: 100000

⚠️ فقط عدد وارد کنید (بدون کاما یا نقطه)
    """
    
    await state.set_state(DepositStates.waiting_for_amount)
    await callback.message.edit_text(text, reply_markup=reply_markup)
    await callback.answer()


@router.message(DepositStates.waiting_for_amount)
async def handle_deposit_amount(message: Message, state: FSMContext):
    """دریافت مبلغ واریزی"""
    try:
        # تبدیل به عدد
        amount = int(message.text.strip().replace(',', '').replace('.', ''))
        
        if amount <= 0:
            await message.answer(
                "❌ مبلغ باید بزرگتر از صفر باشد. لطفاً دوباره تلاش کنید."
            )
            return
        
        if amount < 10000:
            await message.answer(
                "❌ حداقل مبلغ شارژ 10,000 تومان است. لطفاً دوباره تلاش کنید."
            )
            return
        
        # ذخیره مبلغ در state
        await state.update_data(deposit_amount=amount)
        
        # انتقال به مرحله بعد
        await state.set_state(DepositStates.waiting_for_receipt)
        
        keyboard = [
            [InlineKeyboardButton(text="❌ لغو", callback_data="wallet_charge")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        text = f"""
📸 ارسال فیش واریزی

مبلغ واریزی: {amount:,} تومان

حالا لطفاً یکی از موارد زیر را ارسال کنید:
• تصویر فیش واریزی
• شماره پیگیری (به صورت متن)

پس از ارسال، درخواست شما برای ادمین ارسال می‌شود.
        """
        
        await message.answer(text, reply_markup=reply_markup)
    
    except ValueError:
        await message.answer(
            "❌ لطفاً فقط عدد وارد کنید. مثال: 100000"
        )
    except Exception as e:
        logger.error(f"❌ خطا در پردازش مبلغ: {e}", exc_info=True)
        await message.answer(
            "❌ خطا در پردازش مبلغ. لطفاً دوباره تلاش کنید."
        )


@router.message(DepositStates.waiting_for_receipt, F.photo)
async def handle_deposit_receipt_photo(
    message: Message,
    state: FSMContext,
    deposit_service: DepositService
):
    """دریافت تصویر فیش واریزی"""
    user_id = message.from_user.id
    
    try:
        # دریافت داده‌ها از state
        data = await state.get_data()
        amount = data.get('deposit_amount')
        
        if not amount:
            await message.answer("❌ خطا: مبلغ یافت نشد. لطفاً دوباره از ابتدا شروع کنید.")
            await state.clear()
            return
        
        # دریافت بزرگترین سایز عکس
        photo = message.photo[-1]
        receipt_photo_id = photo.file_id
        
        # ثبت درخواست در دیتابیس
        request_id = await deposit_service.create_deposit_request(
            user_id=user_id,
            amount=amount,
            receipt_photo_id=receipt_photo_id
        )
        
        # پاک کردن state
        await state.clear()
        
        # ارسال اعلان به ادمین
        await notify_admin_new_deposit(message.bot, request_id, user_id, amount, receipt_photo_id)
        
        # نمایش پیام موفقیت به کاربر
        keyboard = [
            [InlineKeyboardButton(text="💳 کیف پول من", callback_data="my_wallet")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        text = f"""
✅ فیش شما با موفقیت ثبت شد!

🆔 شماره درخواست: {request_id}
💰 مبلغ: {amount:,} تومان

📋 وضعیت: در انتظار بررسی ادمین

پس از تأیید ادمین، موجودی به کیف پول شما اضافه می‌شود و پیام اعلان دریافت خواهید کرد.

⏱️ زمان تقریبی بررسی: حداکثر 2 ساعت
        """
        
        await message.answer(text, reply_markup=reply_markup)
        
        logger.info(
            f"✅ فیش واریزی ثبت شد: request_id={request_id}, "
            f"کاربر={user_id}, مبلغ={amount:,}"
        )
    
    except Exception as e:
        logger.error(f"❌ خطا در ثبت فیش واریزی: {e}", exc_info=True)
        await message.answer(
            "❌ خطا در ثبت فیش. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
        )
        await state.clear()


@router.message(DepositStates.waiting_for_receipt, F.text)
async def handle_deposit_receipt_text(
    message: Message,
    state: FSMContext,
    deposit_service: DepositService
):
    """دریافت شماره پیگیری (متن)"""
    user_id = message.from_user.id
    
    try:
        # دریافت داده‌ها از state
        data = await state.get_data()
        amount = data.get('deposit_amount')
        
        if not amount:
            await message.answer("❌ خطا: مبلغ یافت نشد. لطفاً دوباره از ابتدا شروع کنید.")
            await state.clear()
            return
        
        tracking_code = message.text.strip()
        
        # ثبت درخواست در دیتابیس
        request_id = await deposit_service.create_deposit_request(
            user_id=user_id,
            amount=amount,
            tracking_code=tracking_code
        )
        
        # پاک کردن state
        await state.clear()
        
        # ارسال اعلان به ادمین
        await notify_admin_new_deposit(message.bot, request_id, user_id, amount, None, tracking_code)
        
        # نمایش پیام موفقیت به کاربر
        keyboard = [
            [InlineKeyboardButton(text="💳 کیف پول من", callback_data="my_wallet")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        text = f"""
✅ شماره پیگیری شما با موفقیت ثبت شد!

🆔 شماره درخواست: {request_id}
💰 مبلغ: {amount:,} تومان
🔢 شماره پیگیری: {tracking_code}

📋 وضعیت: در انتظار بررسی ادمین

پس از تأیید ادمین، موجودی به کیف پول شما اضافه می‌شود و پیام اعلان دریافت خواهید کرد.

⏱️ زمان تقریبی بررسی: حداکثر 2 ساعت
        """
        
        await message.answer(text, reply_markup=reply_markup)
        
        logger.info(
            f"✅ کد پیگیری ثبت شد: request_id={request_id}, "
            f"کاربر={user_id}, مبلغ={amount:,}"
        )
    
    except Exception as e:
        logger.error(f"❌ خطا در ثبت کد پیگیری: {e}", exc_info=True)
        await message.answer(
            "❌ خطا در ثبت کد پیگیری. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
        )
        await state.clear()


# ========== توابع کمکی ==========

async def notify_admin_new_deposit(
    bot,
    request_id: int,
    user_id: int,
    amount: int,
    receipt_photo_id: Optional[str] = None,
    tracking_code: Optional[str] = None
):
    """ارسال اعلان به ادمین برای درخواست شارژ جدید"""
    for admin_id in ADMIN_USER_IDS:
        try:
            # ساخت متن پیام
            text = f"""
🔔 درخواست شارژ جدید

🆔 شماره درخواست: {request_id}
👤 کاربر: {user_id}
💰 مبلغ: {amount:,} تومان
            """
            
            if tracking_code:
                text += f"🔢 شماره پیگیری: {tracking_code}\n"
            
            # ساخت دکمه‌های تأیید/رد
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="✅ تأیید و شارژ",
                        callback_data=f"approve_deposit_{request_id}"
                    ),
                    InlineKeyboardButton(
                        text="❌ رد فیش",
                        callback_data=f"reject_deposit_{request_id}"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            
            # ارسال پیام (با یا بدون عکس)
            if receipt_photo_id:
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=receipt_photo_id,
                    caption=text,
                    reply_markup=reply_markup
                )
            else:
                await bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    reply_markup=reply_markup
                )
            
            logger.info(f"✅ اعلان به ادمین {admin_id} ارسال شد")
        
        except Exception as e:
            logger.error(
                f"❌ خطا در ارسال اعلان به ادمین {admin_id}: {e}",
                exc_info=True
            )


# ========== Handler های ادمین ==========

@router.callback_query(F.data.startswith("approve_deposit_"))
async def callback_approve_deposit(
    callback: CallbackQuery,
    deposit_service: DepositService,
    wallet_service: WalletService
):
    """
    تأیید درخواست شارژ توسط ادمین
    
    ⚠️ CRITICAL: این handler از approve_request_atomic استفاده می‌کند
    برای جلوگیری از Double Approval (تایید همزمان توسط دو ادمین)
    """
    admin_id = callback.from_user.id
    
    # بررسی دسترسی ادمین
    if admin_id not in ADMIN_USER_IDS:
        await callback.answer("❌ شما دسترسی ادمین ندارید", show_alert=True)
        return
    
    try:
        # استخراج request_id
        request_id = int(callback.data.replace("approve_deposit_", ""))
        
        # ⚠️ CRITICAL: تأیید اتمیک درخواست
        # این متد فقط اگر status = 'pending' باشد، تأیید می‌کند
        result = await deposit_service.approve_request_atomic(
            request_id,
            admin_note=f"تأیید شده توسط ادمین {admin_id}"
        )
        
        if not result['success']:
            # درخواست قبلاً پردازش شده
            await callback.answer(
                f"⚠️ {result['message']}",
                show_alert=True
            )
            return
        
        user_id = result['user_id']
        amount = result['amount']
        
        # شارژ کیف پول کاربر
        try:
            await wallet_service.add_credit(
                user_id=user_id,
                amount=amount,
                description=f"شارژ کیف پول - درخواست #{request_id}"
            )
        except Exception as e:
            # ⚠️ CRITICAL: اگر شارژ کیف پول ناموفق بود، باید درخواست را به pending برگردانیم
            logger.error(
                f"❌ خطای حیاتی: شارژ کیف پول ناموفق برای درخواست {request_id}: {e}",
                exc_info=True
            )
            
            # تلاش برای برگرداندن وضعیت
            try:
                await deposit_service._conn.execute(
                    "UPDATE deposit_requests SET status = 'pending' WHERE id = ?",
                    (request_id,)
                )
                await deposit_service._conn.commit()
                logger.info(f"✅ وضعیت درخواست {request_id} به pending برگشت")
            except:
                logger.error(f"❌ خطای دوبل: نتوانستیم وضعیت را برگردانیم!")
            
            await callback.answer(
                "❌ خطا در شارژ کیف پول. لطفاً با پشتیبانی تماس بگیرید",
                show_alert=True
            )
            return
        
        # اعلان به کاربر
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=f"""
✅ کیف پول شما شارژ شد!

💰 مبلغ: {amount:,} تومان
🆔 شماره درخواست: {request_id}

موجودی جدید شما در بخش "💳 کیف پول من" قابل مشاهده است.

🙏 از صبر و شکیبایی شما سپاسگزاریم.
                """
            )
        except Exception as e:
            logger.error(f"❌ خطا در ارسال پیام به کاربر {user_id}: {e}")
        
        # آپدیت پیام ادمین
        new_text = callback.message.caption or callback.message.text
        new_text += f"\n\n✅ تأیید شده توسط ادمین {admin_id}"
        
        try:
            if callback.message.photo:
                await callback.message.edit_caption(caption=new_text)
            else:
                await callback.message.edit_text(new_text)
        except:
            pass
        
        await callback.answer("✅ درخواست تأیید شد و کیف پول کاربر شارژ شد", show_alert=True)
        
        logger.info(
            f"✅ درخواست {request_id} توسط ادمین {admin_id} تأیید شد - "
            f"کاربر {user_id} مبلغ {amount:,} تومان دریافت کرد"
        )
    
    except Exception as e:
        logger.error(f"❌ خطا در تأیید درخواست: {e}", exc_info=True)
        await callback.answer("❌ خطا در پردازش درخواست", show_alert=True)


@router.callback_query(F.data.startswith("reject_deposit_"))
async def callback_reject_deposit(
    callback: CallbackQuery,
    deposit_service: DepositService
):
    """
    رد درخواست شارژ توسط ادمین
    
    ⚠️ CRITICAL: این handler از reject_request_atomic استفاده می‌کند
    برای جلوگیری از Double Processing
    """
    admin_id = callback.from_user.id
    
    # بررسی دسترسی ادمین
    if admin_id not in ADMIN_USER_IDS:
        await callback.answer("❌ شما دسترسی ادمین ندارید", show_alert=True)
        return
    
    try:
        # استخراج request_id
        request_id = int(callback.data.replace("reject_deposit_", ""))
        
        # ⚠️ CRITICAL: رد اتمیک درخواست
        result = await deposit_service.reject_request_atomic(
            request_id,
            admin_note=f"رد شده توسط ادمین {admin_id}"
        )
        
        if not result['success']:
            # درخواست قبلاً پردازش شده
            await callback.answer(
                f"⚠️ {result['message']}",
                show_alert=True
            )
            return
        
        user_id = result['user_id']
        amount = result['amount']
        
        # اعلان به کاربر
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=f"""
❌ درخواست شارژ شما رد شد

💰 مبلغ: {amount:,} تومان
🆔 شماره درخواست: {request_id}

⚠️ دلایل احتمالی:
• عدم انطباق مبلغ واریزی
• عدم تطابق اطلاعات
• فیش نامعتبر

لطفاً با پشتیبانی تماس بگیرید یا دوباره با اطلاعات صحیح تلاش کنید.
                """
            )
        except Exception as e:
            logger.error(f"❌ خطا در ارسال پیام به کاربر {user_id}: {e}")
        
        # آپدیت پیام ادمین
        new_text = callback.message.caption or callback.message.text
        new_text += f"\n\n❌ رد شده توسط ادمین {admin_id}"
        
        try:
            if callback.message.photo:
                await callback.message.edit_caption(caption=new_text)
            else:
                await callback.message.edit_text(new_text)
        except:
            pass
        
        await callback.answer("✅ درخواست رد شد و به کاربر اطلاع داده شد", show_alert=True)
        
        logger.info(
            f"✅ درخواست {request_id} توسط ادمین {admin_id} رد شد - "
            f"کاربر {user_id}"
        )
    
    except Exception as e:
        logger.error(f"❌ خطا در رد درخواست: {e}", exc_info=True)
        await callback.answer("❌ خطا در پردازش درخواست", show_alert=True)
