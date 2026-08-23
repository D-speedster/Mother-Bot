"""
Keyboards برای AI Image Bot

⚠️ استراتژی:
- Main Navigation: Reply Keyboard
- Selection/Actions: Inline Keyboard
- Namespace: تمام callback_data ها با ai: شروع می‌شوند
"""

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

from services.ai_image.models import ImageStyle, AspectRatio, Quality


# ========== Reply Keyboards ==========

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد اصلی Reply - Navigation اصلی"""
    keyboard = [
        [KeyboardButton(text="🖼️ ساخت تصویر")],
        [
            KeyboardButton(text="🖼️ تصاویر من"),
            KeyboardButton(text="👤 حساب کاربری")
        ],
        [
            KeyboardButton(text="⚙️ تنظیمات"),
            KeyboardButton(text="📖 راهنما")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="یک گزینه را انتخاب کنید..."
    )


def get_cancel_reply_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد لغو برای FSM"""
    keyboard = [
        [KeyboardButton(text="❌ لغو")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="پیام خود را بنویسید یا لغو کنید"
    )


# ========== Inline Keyboards ==========

def get_style_keyboard() -> InlineKeyboardMarkup:
    """کیبورد انتخاب Style"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🎨 واقع‌گرایانه",
                callback_data="ai:style:realistic"
            ),
            InlineKeyboardButton(
                text="🎬 سینمایی",
                callback_data="ai:style:cinematic"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎨 انیمه",
                callback_data="ai:style:anime"
            ),
            InlineKeyboardButton(
                text="🖌️ هنر دیجیتال",
                callback_data="ai:style:digital_art"
            )
        ],
        [
            InlineKeyboardButton(
                text="📷 عکاسی",
                callback_data="ai:style:photography"
            ),
            InlineKeyboardButton(
                text="✨ بدون سبک",
                callback_data="ai:style:none"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ratio_keyboard() -> InlineKeyboardMarkup:
    """کیبورد انتخاب Aspect Ratio"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="1:1 (مربع)",
                callback_data="ai:ratio:1x1"
            ),
            InlineKeyboardButton(
                text="16:9 (افقی)",
                callback_data="ai:ratio:16x9"
            )
        ],
        [
            InlineKeyboardButton(
                text="9:16 (عمودی)",
                callback_data="ai:ratio:9x16"
            ),
            InlineKeyboardButton(
                text="4:3 (استاندارد)",
                callback_data="ai:ratio:4x3"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_quality_keyboard() -> InlineKeyboardMarkup:
    """کیبورد انتخاب Quality"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="⚡ استاندارد",
                callback_data="ai:quality:standard"
            ),
            InlineKeyboardButton(
                text="✨ بالا",
                callback_data="ai:quality:high"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_count_keyboard() -> InlineKeyboardMarkup:
    """کیبورد انتخاب تعداد تصاویر"""
    keyboard = [
        [
            InlineKeyboardButton(text="1", callback_data="ai:count:1"),
            InlineKeyboardButton(text="2", callback_data="ai:count:2"),
            InlineKeyboardButton(text="4", callback_data="ai:count:4")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_preview_keyboard() -> InlineKeyboardMarkup:
    """کیبورد Preview قبل از Generate"""
    keyboard = [
        [InlineKeyboardButton(
            text="✅ تولید تصویر",
            callback_data="ai:generate"
        )],
        [
            InlineKeyboardButton(
                text="✏️ تغییر Prompt",
                callback_data="ai:edit:prompt"
            ),
            InlineKeyboardButton(
                text="🎨 تغییر سبک",
                callback_data="ai:edit:style"
            )
        ],
        [
            InlineKeyboardButton(
                text="📐 تغییر نسبت",
                callback_data="ai:edit:ratio"
            ),
            InlineKeyboardButton(
                text="⚙️ تغییر تنظیمات",
                callback_data="ai:edit:settings"
            )
        ],
        [InlineKeyboardButton(
            text="❌ لغو",
            callback_data="ai:cancel"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_result_keyboard() -> InlineKeyboardMarkup:
    """کیبورد بعد از نمایش نتیجه"""
    keyboard = [
        [InlineKeyboardButton(
            text="🔄 تولید مجدد",
            callback_data="ai:regenerate"
        )],
        [InlineKeyboardButton(
            text="✏️ تغییر Prompt",
            callback_data="ai:edit:prompt"
        )],
        [InlineKeyboardButton(
            text="🏠 منوی اصلی",
            callback_data="ai:home"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """کیبورد تنظیمات"""
    keyboard = [
        [InlineKeyboardButton(
            text="🎨 سبک پیش‌فرض",
            callback_data="ai:settings:style"
        )],
        [InlineKeyboardButton(
            text="📐 نسبت پیش‌فرض",
            callback_data="ai:settings:ratio"
        )],
        [InlineKeyboardButton(
            text="⚡ کیفیت پیش‌فرض",
            callback_data="ai:settings:quality"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_gallery_navigation_keyboard(
    has_prev: bool,
    has_next: bool,
    page: int
) -> InlineKeyboardMarkup:
    """کیبورد Navigation گالری"""
    keyboard = []
    
    # دکمه‌های prev/next
    nav_row = []
    if has_prev:
        nav_row.append(InlineKeyboardButton(
            text="⬅️ قبلی",
            callback_data=f"ai:gallery:page:{page-1}"
        ))
    if has_next:
        nav_row.append(InlineKeyboardButton(
            text="➡️ بعدی",
            callback_data=f"ai:gallery:page:{page+1}"
        ))
    
    if nav_row:
        keyboard.append(nav_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_image_detail_keyboard(generation_id: str) -> InlineKeyboardMarkup:
    """کیبورد جزئیات تصویر"""
    keyboard = [
        [InlineKeyboardButton(
            text="🔄 تولید مجدد",
            callback_data=f"ai:regenerate:{generation_id}"
        )],
        [InlineKeyboardButton(
            text="🗑️ حذف",
            callback_data=f"ai:delete:{generation_id}"
        )],
        [InlineKeyboardButton(
            text="⬅️ بازگشت به گالری",
            callback_data="ai:gallery"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
