"""
Utility Script: Local Bot API Health Check

اسکریپت کمکی برای بررسی سلامت Local Bot API Server

Usage:
    python utils/check_local_api.py
    
Environment Variables Required:
    - TELEGRAM_LOCAL_API_ENABLED=yes
    - TELEGRAM_LOCAL_API_TEST_TOKEN=<token>
"""
import asyncio
import os
import sys
from pathlib import Path

# اضافه کردن root directory به Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from services.telegram import LocalBotAPIConfig, HealthCheckService


async def main():
    """اجرای health check"""
    print("=" * 60)
    print("Local Bot API Health Check")
    print("=" * 60)
    print()
    
    # بارگذاری .env
    load_dotenv()
    
    # خواندن configuration
    config = LocalBotAPIConfig.from_env()
    
    print(f"Configuration:")
    print(f"  Enabled: {config.enabled}")
    if config.enabled:
        print(f"  API URL: {config.api_url}")
    print()
    
    # بررسی اینکه Local API فعال است
    if not config.enabled:
        print("❌ Local Bot API غیرفعال است")
        print()
        print("برای فعال‌سازی:")
        print("  1. فایل .env را ویرایش کنید")
        print("  2. TELEGRAM_LOCAL_API_ENABLED=yes")
        print("  3. TELEGRAM_LOCAL_API_TEST_TOKEN=<token> (اختیاری)")
        return 1
    
    # خواندن test token
    test_token = os.getenv('TELEGRAM_LOCAL_API_TEST_TOKEN')
    
    if not test_token:
        print("⚠️  توکن تست در .env تعریف نشده است")
        print()
        print("برای تست کامل:")
        print("  1. یک Bot تست در @BotFather ایجاد کنید")
        print("  2. توکن را به .env اضافه کنید:")
        print("     TELEGRAM_LOCAL_API_TEST_TOKEN=123456789:ABCdefGHI...")
        print()
        print("بدون توکن تست، فقط endpoint بررسی می‌شود.")
        return 1
    
    print("🔍 در حال بررسی سلامت Local API Server...")
    print()
    
    # اجرای health check
    service = HealthCheckService(config)
    result = await service.check_health(test_token)
    
    # نمایش نتایج
    print("نتایج:")
    print(f"  ✓ Server Reachable: {'✅' if result.server_reachable else '❌'}")
    print(f"  ✓ API Response Valid: {'✅' if result.api_response_valid else '❌'}")
    print(f"  ✓ getMe Works: {'✅' if result.get_me_works else '❌'}")
    print()
    
    if result.success:
        print("✅ Health Check موفق")
        print(f"   {result.message}")
        return 0
    else:
        print("❌ Health Check ناموفق")
        print(f"   {result.message}")
        if result.error_type:
            print(f"   Error Type: {result.error_type}")
        print()
        
        # پیشنهادات troubleshooting
        if result.error_type == 'timeout' or not result.server_reachable:
            print("💡 Troubleshooting:")
            print("   1. مطمئن شوید که Local Bot API Server اجرا می‌شود")
            print("   2. پورت 8081 باز باشد")
            print("   3. Firewall آن را block نکرده باشد")
            print()
            print("   برای راه‌اندازی Server:")
            print("   telegram-bot-api.exe --api-id=... --api-hash=... --local")
        
        elif result.error_type == 'invalid_token':
            print("💡 Troubleshooting:")
            print("   1. توکن تست را بررسی کنید")
            print("   2. مطمئن شوید که توکن معتبر است")
            print("   3. از @BotFather توکن جدید بگیرید")
        
        return 1


if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ لغو شد توسط کاربر")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ خطای غیرمنتظره: {type(e).__name__}")
        print(f"   {str(e)}")
        sys.exit(1)
