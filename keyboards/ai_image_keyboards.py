"""
Inline Keyboards برای AI Image Bot

⚠️ Namespace: تمام callback_data ها با ai: شروع می‌شوند
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ========== Main Menu Keyboard ==========
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """کیبورد منوی اصلی AI Image Bot"""
    keyboard = [
        [InlineKeyboardButton(text="✨ ساخت تصویر", callback_data="ai:create")],
        [InlineKeyboardButton(text="🖼️ گالری من", callback_data="ai:gallery")],
        [
            InlineKeyboardButton(text="📖 راهنما", callback_data="ai:help"),
            InlineKeyboardButton(text="👤 حساب کاربری", callback_data="ai:profile")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Cancel Keyboard (FSM) ==========
def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """کیبورد لغو برای FSM"""
    keyboard = [
        [InlineKeyboardButton(text="❌ لغو", callback_data="ai:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Result Keyboard ==========
def get_result_keyboard() -> InlineKeyboardMarkup:
    """کیبورد بعد از نمایش نتیجه Mock"""
    keyboard = [
        [InlineKeyboardButton(text="🔄 درخواست جدید", callback_data="ai:create")],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="ai:home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Gallery Keyboard ==========
def get_gallery_keyboard() -> InlineKeyboardMarkup:
    """کیبورد گالری"""
    keyboard = [
        [InlineKeyboardButton(text="✨ ساخت تصویر", callback_data="ai:create")],
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="ai:home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Profile Keyboard ==========
def get_profile_keyboard() -> InlineKeyboardMarkup:
    """کیبورد پروفایل"""
    keyboard = [
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="ai:home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Help Keyboard ==========
def get_help_keyboard() -> InlineKeyboardMarkup:
    """کیبورد راهنما"""
    keyboard = [
        [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="ai:home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
