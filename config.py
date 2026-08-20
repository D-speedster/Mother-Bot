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

# کلید رمزنگاری Fernet - اجباری از .env
FERNET_KEY = os.getenv('FERNET_KEY')
if not FERNET_KEY:
    raise ValueError(
        "🔴 خطا: متغیر محیطی FERNET_KEY در فایل .env تنظیم نشده است!\n"
        "لطفاً فایل .env را ویرایش کرده و کلید رمزنگاری را در آن قرار دهید.\n"
        "برای تولید کلید جدید از Python استفاده کنید:\n"
        "  from cryptography.fernet import Fernet\n"
        "  print(Fernet.generate_key().decode())\n"
        "سپس در .env اضافه کنید: FERNET_KEY=<کلید_تولیدشده>"
    )

# مسیر پایگاه داده
DATABASE_PATH = os.getenv('DATABASE_PATH', 'mother_bot.db')

# انواع ربات‌های قابل ساخت
BOT_TYPES = {
    "shop": "🛒 ربات فروشگاهی",
    "downloader": "📥 ربات دانلودر",
    "support": "🎫 ربات پشتیبانی و تیکت",
    "broadcast": "📢 ربات ارسال همگانی",
    "tools": "⚙️ ربات ابزار و خدمات",
    "affiliate": "🔗 ربات همکاری در فروش"
}
