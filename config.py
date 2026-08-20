"""
تنظیمات پروژه
"""
import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# توکن ربات - اجباری از .env
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError(
        "🔴 خطا: متغیر محیطی BOT_TOKEN در فایل .env تنظیم نشده است!\n"
        "لطفاً فایل .env را ایجاد کرده و توکن ربات خود را در آن قرار دهید.\n"
        "مثال: BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    )

# انواع ربات‌های قابل ساخت
BOT_TYPES = {
    "shop": "🛒 ربات فروشگاهی",
    "downloader": "📥 ربات دانلودر",
    "support": "🎫 ربات پشتیبانی و تیکت",
    "broadcast": "📢 ربات ارسال همگانی",
    "tools": "⚙️ ربات ابزار و خدمات",
    "affiliate": "🔗 ربات همکاری در فروش"
}
