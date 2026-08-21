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
    "ai_image": "🎨 ربات هوش مصنوعی و ویرایش عکس",
    "movie_downloader": "🎬 ربات دانلود فیلم و سریال",
    "social_downloader": "📱 ربات دانلود از یوتیوب و اینستاگرام",
    "vpn_seller": "🔐 ربات فروش فیلترشکن"
}

# هزینه ساخت ربات (تومان)
BOT_CREATION_COST = int(os.getenv('BOT_CREATION_COST', '50000'))

# لیست آیدی ادمین‌های اصلی سیستم (ساخت ربات برای آنها رایگان است)
ADMIN_USER_IDS = [79049016]  # می‌توانید آیدی‌های بیشتری اضافه کنید

# اطلاعات کارت بانکی برای واریز (کارت به کارت)
BANK_CARD_NUMBER = os.getenv('BANK_CARD_NUMBER', '6037-9977-1234-5678')
BANK_CARD_HOLDER = os.getenv('BANK_CARD_HOLDER', 'علی احمدی')
BANK_NAME = os.getenv('BANK_NAME', 'بانک ملی ایران')
