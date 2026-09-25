"""
تست تشخیص مشکل Local Bot API Configuration

این اسکریپت بررسی می‌کند که چرا child bot به Local API متصل نمی‌شود
"""
import os
import sys
from pathlib import Path

# اضافه کردن project root به Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

print("="*70)
print("🔍 تشخیص مشکل Local Bot API Configuration")
print("="*70)

# تست 1: بررسی .env file
print("\n1️⃣ بررسی فایل .env:")
print("-" * 70)

env_path = Path(__file__).parent / '.env'
if env_path.exists():
    print(f"✅ فایل .env وجود دارد: {env_path}")
    
    # خواندن محتوای .env
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # جستجوی خطوط مربوط به Local API
    for line in content.split('\n'):
        if 'TELEGRAM_LOCAL_API' in line and not line.strip().startswith('#'):
            print(f"   {line}")
else:
    print(f"❌ فایل .env یافت نشد: {env_path}")

# تست 2: بررسی Environment Variables قبل از load_dotenv
print("\n2️⃣ Environment Variables قبل از load_dotenv():")
print("-" * 70)

env_before = {
    'TELEGRAM_LOCAL_API_ENABLED': os.getenv('TELEGRAM_LOCAL_API_ENABLED'),
    'TELEGRAM_LOCAL_API_BASE_URL': os.getenv('TELEGRAM_LOCAL_API_BASE_URL'),
    'TELEGRAM_LOCAL_API_PORT': os.getenv('TELEGRAM_LOCAL_API_PORT')
}

for key, value in env_before.items():
    if value:
        print(f"✅ {key} = {value}")
    else:
        print(f"❌ {key} = None (خالی)")

# تست 3: فراخوانی load_dotenv
print("\n3️⃣ فراخوانی load_dotenv():")
print("-" * 70)

result = load_dotenv()
if result:
    print("✅ load_dotenv() موفق بود")
else:
    print("⚠️  load_dotenv() False برگرداند (ممکن است .env نباشد یا قبلاً load شده)")

# تست 4: بررسی Environment Variables بعد از load_dotenv
print("\n4️⃣ Environment Variables بعد از load_dotenv():")
print("-" * 70)

env_after = {
    'TELEGRAM_LOCAL_API_ENABLED': os.getenv('TELEGRAM_LOCAL_API_ENABLED'),
    'TELEGRAM_LOCAL_API_BASE_URL': os.getenv('TELEGRAM_LOCAL_API_BASE_URL'),
    'TELEGRAM_LOCAL_API_PORT': os.getenv('TELEGRAM_LOCAL_API_PORT')
}

for key, value in env_after.items():
    if value:
        print(f"✅ {key} = {value}")
    else:
        print(f"❌ {key} = None (خالی)")

# تست 5: مقایسه قبل و بعد
print("\n5️⃣ مقایسه قبل و بعد از load_dotenv():")
print("-" * 70)

for key in env_before.keys():
    before = env_before[key]
    after = env_after[key]
    
    if before != after:
        print(f"🔄 {key}: {before} → {after}")
    else:
        if after:
            print(f"➡️  {key}: {after} (بدون تغییر)")
        else:
            print(f"❌ {key}: هنوز خالی است")

# تست 6: Load کردن LocalBotAPIConfig
print("\n6️⃣ Load کردن LocalBotAPIConfig:")
print("-" * 70)

try:
    from services.telegram import LocalBotAPIConfig
    
    config = LocalBotAPIConfig.from_env()
    
    print(f"✅ Config لود شد:")
    print(f"   enabled: {config.enabled}")
    print(f"   base_url: {config.base_url}")
    print(f"   port: {config.port}")
    print(f"   api_url: {config.api_url}")
    
    # بررسی مطابقت
    print("\n7️⃣ بررسی مطابقت:")
    print("-" * 70)
    
    expected_port = os.getenv('TELEGRAM_LOCAL_API_PORT')
    actual_port = str(config.port)
    
    if expected_port == actual_port:
        print(f"✅ Port مطابقت دارد: {actual_port}")
    else:
        print(f"❌ Port مطابقت ندارد:")
        print(f"   انتظار: {expected_port}")
        print(f"   واقعی: {actual_port}")
        print(f"   دلیل: احتمالاً default port در کد اشتباه است")

except Exception as e:
    print(f"❌ خطا در لود LocalBotAPIConfig: {e}")
    import traceback
    traceback.print_exc()

# تست 8: بررسی Local API Server
print("\n8️⃣ بررسی دسترسی Local API Server:")
print("-" * 70)

import socket

def check_port(host, port):
    """بررسی اینکه port باز است یا نه"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

# بررسی port از .env
env_port_str = os.getenv('TELEGRAM_LOCAL_API_PORT', '5000')
try:
    env_port = int(env_port_str)
    if check_port('localhost', env_port):
        print(f"✅ Local API در دسترس است: localhost:{env_port}")
    else:
        print(f"❌ Local API در دسترس نیست: localhost:{env_port}")
        print(f"   آیا Local Bot API Server اجرا می‌شود؟")
except ValueError:
    print(f"❌ Port نامعتبر: {env_port_str}")

# بررسی port 8081 (default کد)
if check_port('localhost', 8081):
    print(f"⚠️  پورت 8081 باز است (default کد)")
    print(f"   اما Local API روی port {env_port_str} است!")
else:
    print(f"ℹ️  پورت 8081 باز نیست (default کد)")

# خلاصه نهایی
print("\n" + "="*70)
print("📊 خلاصه تشخیص:")
print("="*70)

issues = []

# چک 1: آیا .env وجود دارد؟
if not env_path.exists():
    issues.append("❌ فایل .env وجود ندارد")

# چک 2: آیا environment variable لود شده؟
if not env_after['TELEGRAM_LOCAL_API_PORT']:
    issues.append("❌ TELEGRAM_LOCAL_API_PORT لود نشده")

# چک 3: آیا config مطابقت دارد؟
try:
    if expected_port and expected_port != actual_port:
        issues.append(f"❌ Port mismatch: env={expected_port}, config={actual_port}")
except:
    pass

# چک 4: آیا Local API در دسترس است؟
try:
    if not check_port('localhost', int(env_port_str)):
        issues.append(f"❌ Local API Server روی port {env_port_str} پاسخ نمی‌دهد")
except:
    pass

if issues:
    print("\n🔴 مشکلات یافت شده:")
    for issue in issues:
        print(f"   {issue}")
    
    print("\n💡 توصیه:")
    if not env_path.exists():
        print("   1. فایل .env را ایجاد کنید")
    if not env_after['TELEGRAM_LOCAL_API_PORT']:
        print("   2. TELEGRAM_LOCAL_API_PORT را در .env تنظیم کنید")
    if any("Port mismatch" in i for i in issues):
        print("   3. Default port در services/telegram/local_api_config.py را تغییر دهید")
    if any("پاسخ نمی‌دهد" in i for i in issues):
        print("   4. Local Bot API Server را روی port مناسب اجرا کنید")
else:
    print("\n✅ هیچ مشکلی یافت نشد!")
    print("   Configuration صحیح به نظر می‌رسد")
    print("   اگر هنوز مشکل دارید، log های ربات را بررسی کنید")

print("\n" + "="*70)
