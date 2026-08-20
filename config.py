"""
تنظیمات پروژه
"""
import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# توکن ربات
BOT_TOKEN = os.getenv('BOT_TOKEN', '117685606:AAHn3oSD92Y71PkTIWwi86hcisLpvRpY_Hc')

# انواع ربات‌های قابل ساخت
BOT_TYPES = {
    "shop": "🛒 ربات فروشگاهی",
    "downloader": "📥 ربات دانلودر",
    "support": "🎫 ربات پشتیبانی و تیکت",
    "broadcast": "📢 ربات ارسال همگانی",
    "tools": "⚙️ ربات ابزار و خدمات",
    "affiliate": "🔗 ربات همکاری در فروش"
}
