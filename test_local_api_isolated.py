"""
تست ایزوله LocalBotAPIConfig

این تست بررسی می‌کند که LocalBotAPIConfig بدون وابستگی به import order کار می‌کند
"""
import sys
from pathlib import Path

# اضافه کردن project root
sys.path.insert(0, str(Path(__file__).parent))

print("="*70)
print("🧪 تست ایزوله LocalBotAPIConfig")
print("="*70)

# تست: import کردن مستقیم بدون هیچ import دیگری
print("\n1️⃣ Import کردن LocalBotAPIConfig (بدون config.py):")
print("-" * 70)

from services.telegram import LocalBotAPIConfig

print("✅ Import موفق بود")

# تست: Load کردن configuration
print("\n2️⃣ Load کردن Configuration:")
print("-" * 70)

config = LocalBotAPIConfig.from_env()

print(f"enabled: {config.enabled}")
print(f"base_url: {config.base_url}")
print(f"port: {config.port}")
print(f"api_url: {config.api_url}")

# تست: بررسی port
print("\n3️⃣ بررسی Port:")
print("-" * 70)

if config.port == 5000:
    print("✅ Port صحیح است: 5000")
    print("✅ FIX کار کرده است!")
elif config.port == 8081:
    print("❌ Port هنوز 8081 است")
    print("❌ FIX کار نکرده است!")
else:
    print(f"⚠️  Port غیرمنتظره: {config.port}")

# تست: بررسی enabled
print("\n4️⃣ بررسی Enabled:")
print("-" * 70)

if config.enabled:
    print("✅ Local API فعال است")
else:
    print("❌ Local API غیرفعال است")

print("\n" + "="*70)
print("✅ تست کامل شد!")
print("="*70)
