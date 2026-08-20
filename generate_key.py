"""
اسکریپت کمکی برای تولید کلید رمزنگاری Fernet

استفاده:
    python generate_key.py
    
خروجی:
    کلید رمزنگاری جدید که باید در فایل .env با نام FERNET_KEY قرار گیرد
"""
from cryptography.fernet import Fernet


def generate_fernet_key():
    """تولید کلید رمزنگاری جدید"""
    key = Fernet.generate_key()
    key_str = key.decode()
    
    print("=" * 60)
    print("🔑 کلید رمزنگاری Fernet جدید:")
    print("=" * 60)
    print(key_str)
    print("=" * 60)
    print("\n📝 دستورالعمل:")
    print("1. کلید بالا را کپی کنید")
    print("2. فایل .env را باز کنید")
    print("3. خط زیر را اضافه یا ویرایش کنید:")
    print(f"   FERNET_KEY={key_str}")
    print("\n⚠️ هشدار امنیتی:")
    print("- این کلید را به Git commit نکنید")
    print("- این کلید را در جای امنی نگهداری کنید")
    print("- اگر کلید را گم کنید، توکن‌های رمزشده قابل بازیابی نیستند")
    print("=" * 60)


if __name__ == '__main__':
    generate_fernet_key()
