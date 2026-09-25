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
    "file_transfer": "📁 ربات لینک به فایل و فایل به لینک"
}

# هزینه ساخت ربات (تومان)
BOT_CREATION_COST = int(os.getenv('BOT_CREATION_COST', '50000'))

# آیدی ادمین اصلی سیستم (ساخت ربات برای آنها رایگان است و غیرقابل حذف از لیست ادمین‌ها)
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))
if not ADMIN_USER_ID:
    raise ValueError(
        "🔴 خطا: متغیر محیطی ADMIN_USER_ID در فایل .env تنظیم نشده است!\n"
        "لطفاً آیدی تلگرام ادمین اصلی را در فایل .env قرار دهید.\n"
        "مثال: ADMIN_USER_ID=123456789"
    )

# لیست آیدی ادمین‌های اصلی سیستم (برای سازگاری با کدهای قبلی)
ADMIN_USER_IDS = [ADMIN_USER_ID]  # می‌توانید آیدی‌های بیشتری اضافه کنید

# اطلاعات کارت بانکی برای واریز (کارت به کارت)
BANK_CARD_NUMBER = os.getenv('BANK_CARD_NUMBER')
if not BANK_CARD_NUMBER:
    raise ValueError(
        "🔴 خطا: متغیر محیطی BANK_CARD_NUMBER در فایل .env تنظیم نشده است!\n"
        "لطفاً شماره کارت بانکی را در فایل .env قرار دهید.\n"
        "مثال: BANK_CARD_NUMBER=6037-9977-1234-5678"
    )

BANK_CARD_HOLDER = os.getenv('BANK_CARD_HOLDER')
if not BANK_CARD_HOLDER:
    raise ValueError(
        "🔴 خطا: متغیر محیطی BANK_CARD_HOLDER در فایل .env تنظیم نشده است!\n"
        "لطفاً نام و نام خانوادگی دارنده کارت را در فایل .env قرار دهید.\n"
        "مثال: BANK_CARD_HOLDER=علی احمدی"
    )

BANK_NAME = os.getenv('BANK_NAME')
if not BANK_NAME:
    raise ValueError(
        "🔴 خطا: متغیر محیطی BANK_NAME در فایل .env تنظیم نشده است!\n"
        "لطفاً نام بانک را در فایل .env قرار دهید.\n"
        "مثال: BANK_NAME=بانک ملی ایران"
    )
