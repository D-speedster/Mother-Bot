"""
Admin Keyboards برای AI Image Bot

⚠️ این Keyboards فقط برای Admin Panel است
"""

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


# ========== Main Admin Navigation ==========

def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """
    منوی اصلی Admin Panel
    
    Reply Keyboard برای Navigation اصلی
    """
    keyboard = [
        [KeyboardButton(text="📊 مدیریت")],
        [KeyboardButton(text="📢 ارتباط")],
        [KeyboardButton(text="🧠 AI")],
        [KeyboardButton(text="📚 محتوا")],
        [KeyboardButton(text="⚙️ سیستم")],
        [KeyboardButton(text="⬅️ بازگشت")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="یک گزینه را انتخاب کنید..."
    )


def get_back_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد بازگشت"""
    keyboard = [
        [KeyboardButton(text="⬅️ بازگشت")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


# ========== Management Section ==========

def get_management_keyboard() -> InlineKeyboardMarkup:
    """منوی مدیریت"""
    keyboard = [
        [InlineKeyboardButton(
            text="👥 آمار کاربران",
            callback_data="admin:mgmt:users"
        )],
        [InlineKeyboardButton(
            text="🟢 کاربران فعال",
            callback_data="admin:mgmt:active_users"
        )],
        [InlineKeyboardButton(
            text="🖼 آمار Generation",
            callback_data="admin:mgmt:generations"
        )],
        [InlineKeyboardButton(
            text="💰 درآمد / مصرف",
            callback_data="admin:mgmt:revenue"
        )],
        [InlineKeyboardButton(
            text="🔄 تازه‌سازی",
            callback_data="admin:mgmt:refresh"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Communication Section ==========

def get_communication_keyboard() -> InlineKeyboardMarkup:
    """منوی ارتباطات"""
    keyboard = [
        [InlineKeyboardButton(
            text="📨 ارسال همگانی",
            callback_data="admin:comm:broadcast"
        )],
        [InlineKeyboardButton(
            text="💤 پیام‌های آفلاین",
            callback_data="admin:comm:offline"
        )],
        [InlineKeyboardButton(
            text="⭐ مدیریت Sponsor",
            callback_data="admin:comm:sponsor"
        )],
        [InlineKeyboardButton(
            text="📣 مدیریت تبلیغات",
            callback_data="admin:comm:ads"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_broadcast_target_keyboard() -> InlineKeyboardMarkup:
    """انتخاب Target برای Broadcast"""
    keyboard = [
        [InlineKeyboardButton(
            text="👥 همه کاربران",
            callback_data="admin:broadcast:target:all"
        )],
        [InlineKeyboardButton(
            text="🟢 کاربران فعال",
            callback_data="admin:broadcast:target:active"
        )],
        [InlineKeyboardButton(
            text="❌ لغو",
            callback_data="admin:broadcast:cancel"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_broadcast_confirm_keyboard(target_count: int) -> InlineKeyboardMarkup:
    """تأیید Broadcast"""
    keyboard = [
        [InlineKeyboardButton(
            text=f"✅ ارسال به {target_count} کاربر",
            callback_data="admin:broadcast:confirm"
        )],
        [InlineKeyboardButton(
            text="❌ لغو",
            callback_data="admin:broadcast:cancel"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_sponsor_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    """منوی مدیریت Sponsor"""
    toggle_text = "🔴 غیرفعال کردن" if enabled else "🟢 فعال کردن"
    keyboard = [
        [InlineKeyboardButton(
            text=toggle_text,
            callback_data="admin:sponsor:toggle"
        )],
        [InlineKeyboardButton(
            text="✏️ تغییر متن",
            callback_data="admin:sponsor:edit_text"
        )],
        [InlineKeyboardButton(
            text="🔗 تغییر لینک",
            callback_data="admin:sponsor:edit_url"
        )],
        [InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="admin:comm:main"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ads_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    """منوی مدیریت Ads"""
    toggle_text = "🔴 غیرفعال کردن" if enabled else "🟢 فعال کردن"
    keyboard = [
        [InlineKeyboardButton(
            text=toggle_text,
            callback_data="admin:ads:toggle"
        )],
        [InlineKeyboardButton(
            text="✏️ تغییر متن",
            callback_data="admin:ads:edit_text"
        )],
        [InlineKeyboardButton(
            text="🔗 تغییر لینک",
            callback_data="admin:ads:edit_url"
        )],
        [InlineKeyboardButton(
            text="📊 تنظیم فرکانس",
            callback_data="admin:ads:edit_frequency"
        )],
        [InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="admin:comm:main"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== AI Section ==========

def get_ai_settings_keyboard() -> InlineKeyboardMarkup:
    """منوی تنظیمات AI"""
    keyboard = [
        [InlineKeyboardButton(
            text="🔌 Provider / API",
            callback_data="admin:ai:provider"
        )],
        [InlineKeyboardButton(
            text="🤖 Model",
            callback_data="admin:ai:model"
        )],
        [InlineKeyboardButton(
            text="⚙️ Default Settings",
            callback_data="admin:ai:defaults"
        )],
        [InlineKeyboardButton(
            text="📝 Prompt Settings",
            callback_data="admin:ai:prompts"
        )],
        [InlineKeyboardButton(
            text="🎨 Style Settings",
            callback_data="admin:ai:styles"
        )],
        [InlineKeyboardButton(
            text="🚦 Generation Limits",
            callback_data="admin:ai:limits"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_styles_list_keyboard(styles) -> InlineKeyboardMarkup:
    """لیست Styles"""
    keyboard = []
    for style in styles:
        status_icon = "✅" if style.enabled else "❌"
        keyboard.append([InlineKeyboardButton(
            text=f"{status_icon} {style.name}",
            callback_data=f"admin:style:edit:{style.key}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        text="⬅️ بازگشت",
        callback_data="admin:ai:main"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_style_edit_keyboard(style_key: str, enabled: bool) -> InlineKeyboardMarkup:
    """ویرایش Style"""
    toggle_text = "🔴 غیرفعال کردن" if enabled else "🟢 فعال کردن"
    keyboard = [
        [InlineKeyboardButton(
            text=toggle_text,
            callback_data=f"admin:style:toggle:{style_key}"
        )],
        [InlineKeyboardButton(
            text="✏️ تغییر نام",
            callback_data=f"admin:style:edit_name:{style_key}"
        )],
        [InlineKeyboardButton(
            text="📝 تغییر توضیحات",
            callback_data=f"admin:style:edit_desc:{style_key}"
        )],
        [InlineKeyboardButton(
            text="🔧 تغییر Modifier",
            callback_data=f"admin:style:edit_modifier:{style_key}"
        )],
        [InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="admin:ai:styles"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== Content Section ==========

def get_content_keyboard() -> InlineKeyboardMarkup:
    """منوی محتوا"""
    keyboard = [
        [InlineKeyboardButton(
            text="📖 راهنمای ربات",
            callback_data="admin:content:guide"
        )],
        [InlineKeyboardButton(
            text="❓ FAQ",
            callback_data="admin:content:faq"
        )],
        [InlineKeyboardButton(
            text="💬 پیام‌های سیستم",
            callback_data="admin:content:messages"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_faq_list_keyboard(faqs) -> InlineKeyboardMarkup:
    """لیست FAQ"""
    keyboard = []
    for i, faq in enumerate(faqs[:10], 1):  # حداکثر 10 تا
        status_icon = "✅" if faq.enabled else "❌"
        keyboard.append([InlineKeyboardButton(
            text=f"{status_icon} {i}. {faq.question[:30]}...",
            callback_data=f"admin:faq:view:{faq.id}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        text="➕ افزودن FAQ جدید",
        callback_data="admin:faq:create"
    )])
    
    keyboard.append([InlineKeyboardButton(
        text="⬅️ بازگشت",
        callback_data="admin:content:main"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_faq_edit_keyboard(faq_id: str, enabled: bool) -> InlineKeyboardMarkup:
    """ویرایش FAQ"""
    toggle_text = "🔴 غیرفعال کردن" if enabled else "🟢 فعال کردن"
    keyboard = [
        [InlineKeyboardButton(
            text=toggle_text,
            callback_data=f"admin:faq:toggle:{faq_id}"
        )],
        [InlineKeyboardButton(
            text="✏️ ویرایش سوال",
            callback_data=f"admin:faq:edit_q:{faq_id}"
        )],
        [InlineKeyboardButton(
            text="📝 ویرایش جواب",
            callback_data=f"admin:faq:edit_a:{faq_id}"
        )],
        [InlineKeyboardButton(
            text="🗑️ حذف",
            callback_data=f"admin:faq:delete:{faq_id}"
        )],
        [InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="admin:content:faq"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_faq_delete_confirm_keyboard(faq_id: str) -> InlineKeyboardMarkup:
    """تأیید حذف FAQ"""
    keyboard = [
        [InlineKeyboardButton(
            text="✅ بله، حذف شود",
            callback_data=f"admin:faq:delete_confirm:{faq_id}"
        )],
        [InlineKeyboardButton(
            text="❌ خیر",
            callback_data=f"admin:faq:view:{faq_id}"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_system_messages_keyboard() -> InlineKeyboardMarkup:
    """لیست پیام‌های سیستم"""
    keyboard = [
        [InlineKeyboardButton(
            text="👋 خوش‌آمدگویی",
            callback_data="admin:msg:edit:welcome"
        )],
        [InlineKeyboardButton(
            text="🎨 شروع تولید",
            callback_data="admin:msg:edit:generation_started"
        )],
        [InlineKeyboardButton(
            text="✅ تولید موفق",
            callback_data="admin:msg:edit:generation_completed"
        )],
        [InlineKeyboardButton(
            text="❌ خطا",
            callback_data="admin:msg:edit:generation_failed"
        )],
        [InlineKeyboardButton(
            text="⚠️ محدودیت",
            callback_data="admin:msg:edit:limit_reached"
        )],
        [InlineKeyboardButton(
            text="🔧 Maintenance",
            callback_data="admin:msg:edit:maintenance"
        )],
        [InlineKeyboardButton(
            text="📖 راهنما",
            callback_data="admin:msg:edit:help"
        )],
        [InlineKeyboardButton(
            text="⬅️ بازگشت",
            callback_data="admin:content:main"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========== System Section ==========

def get_system_keyboard() -> InlineKeyboardMarkup:
    """منوی سیستم"""
    keyboard = [
        [InlineKeyboardButton(
            text="🖥 وضعیت Server",
            callback_data="admin:sys:status"
        )],
        [InlineKeyboardButton(
            text="📦 صف انتظار",
            callback_data="admin:sys:queue"
        )],
        [InlineKeyboardButton(
            text="❌ آمار خطا",
            callback_data="admin:sys:errors"
        )],
        [InlineKeyboardButton(
            text="🔧 Maintenance Mode",
            callback_data="admin:sys:maintenance"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_maintenance_keyboard(is_active: bool) -> InlineKeyboardMarkup:
    """منوی Maintenance Mode"""
    if is_active:
        keyboard = [
            [InlineKeyboardButton(
                text="🟢 خاموش کردن Maintenance",
                callback_data="admin:maintenance:off"
            )],
            [InlineKeyboardButton(
                text="✏️ تغییر پیام",
                callback_data="admin:maintenance:edit_message"
            )],
            [InlineKeyboardButton(
                text="⬅️ بازگشت",
                callback_data="admin:sys:main"
            )]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(
                text="🔴 روشن کردن Maintenance",
                callback_data="admin:maintenance:on"
            )],
            [InlineKeyboardButton(
                text="⬅️ بازگشت",
                callback_data="admin:sys:main"
            )]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_maintenance_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """تأیید تغییر Maintenance Mode"""
    action_text = "روشن" if action == "on" else "خاموش"
    keyboard = [
        [InlineKeyboardButton(
            text=f"✅ بله، {action_text} شود",
            callback_data=f"admin:maintenance:confirm:{action}"
        )],
        [InlineKeyboardButton(
            text="❌ خیر",
            callback_data="admin:sys:maintenance"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
