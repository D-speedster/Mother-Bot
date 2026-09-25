"""
تست مستقل اتصال FTP

این اسکریپت مراحل اتصال FTP را جداگانه تست می‌کند
تا root cause مشکل timeout در TYPE I پیدا شود.
"""
import ftplib
import time
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# اطلاعات اتصال
FTP_HOST = os.getenv('FILE_STORAGE_FTP_HOST', 'radif-ecu.ir')
FTP_PORT = int(os.getenv('FILE_STORAGE_FTP_PORT', '21'))
FTP_USER = os.getenv('FILE_STORAGE_FTP_USERNAME', 'speedster@radif-ecu.ir')
FTP_PASS = os.getenv('FILE_STORAGE_FTP_PASSWORD', '')

print("=" * 60)
print("🧪 FTP Connection Test")
print("=" * 60)
print(f"Host: {FTP_HOST}")
print(f"Port: {FTP_PORT}")
print(f"User: {FTP_USER}")
print(f"Pass: {'*' * len(FTP_PASS)}")
print("=" * 60)

ftp = None

try:
    # مرحله ۱: ساخت object
    print("\n[1/6] Creating FTP object...")
    ftp = ftplib.FTP()
    ftp.set_debuglevel(2)  # فعال کردن debug output
    print("✅ FTP object created")
    
    # مرحله ۲: اتصال
    print(f"\n[2/6] Connecting to {FTP_HOST}:{FTP_PORT}...")
    start = time.time()
    response = ftp.connect(host=FTP_HOST, port=FTP_PORT, timeout=30)
    elapsed = time.time() - start
    print(f"✅ Connected in {elapsed:.2f}s")
    print(f"Response: {response}")
    
    # مرحله ۳: Login
    print(f"\n[3/6] Logging in as {FTP_USER}...")
    start = time.time()
    response = ftp.login(user=FTP_USER, passwd=FTP_PASS)
    elapsed = time.time() - start
    print(f"✅ Logged in in {elapsed:.2f}s")
    print(f"Response: {response}")
    
    # مرحله ۴: PWD (current directory)
    print("\n[4/6] Getting current directory (PWD)...")
    start = time.time()
    pwd = ftp.pwd()
    elapsed = time.time() - start
    print(f"✅ PWD in {elapsed:.2f}s")
    print(f"Current directory: {pwd}")
    
    # مرحله ۵: Passive Mode
    print("\n[5/6] Setting Passive Mode...")
    start = time.time()
    ftp.set_pasv(True)
    elapsed = time.time() - start
    print(f"✅ Passive mode set in {elapsed:.2f}s")
    
    # مرحله ۶: TYPE I (Binary mode)
    print("\n[6/6] Setting Binary Mode (TYPE I)...")
    start = time.time()
    response = ftp.voidcmd('TYPE I')
    elapsed = time.time() - start
    print(f"✅ Binary mode set in {elapsed:.2f}s")
    print(f"Response: {response}")
    
    # مرحله اضافی: تست CWD
    base_path = os.getenv('FILE_STORAGE_FTP_BASE_PATH', '')
    if base_path:
        print(f"\n[EXTRA] Testing CWD to {base_path}...")
        start = time.time()
        ftp.cwd(base_path)
        elapsed = time.time() - start
        print(f"✅ CWD successful in {elapsed:.2f}s")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)

except ftplib.error_perm as e:
    print(f"\n❌ FTP Permission Error: {e}")
    print("→ احتمالاً username/password اشتباه است")

except TimeoutError as e:
    print(f"\n❌ Timeout Error: {e}")
    print("→ احتمالاً firewall یا passive mode مشکل دارد")

except OSError as e:
    print(f"\n❌ OS Error: {e}")
    print("→ احتمالاً مشکل شبکه یا DNS است")

except ftplib.Error as e:
    print(f"\n❌ FTP Error: {type(e).__name__}: {e}")

except Exception as e:
    print(f"\n❌ Unexpected Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

finally:
    if ftp:
        try:
            print("\nClosing connection...")
            ftp.quit()
            print("✅ Connection closed")
        except Exception as e:
            print(f"⚠️ Error closing: {e}")

print("\n" + "=" * 60)
print("🏁 Test Complete")
print("=" * 60)
