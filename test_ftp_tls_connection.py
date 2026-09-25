"""
تست مستقل اتصال FTPS (FTP over TLS)

این اسکریپت با FTP_TLS تست می‌کند تا ببینیم آیا
مشکل از عدم استفاده از TLS است یا نه.
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
print("🧪 FTPS (FTP_TLS) Connection Test")
print("=" * 60)
print(f"Host: {FTP_HOST}")
print(f"Port: {FTP_PORT}")
print(f"User: {FTP_USER}")
print(f"Pass: {'*' * len(FTP_PASS)}")
print("=" * 60)

ftp = None

try:
    # مرحله ۱: ساخت FTP_TLS object
    print("\n[1/7] Creating FTP_TLS object...")
    ftp = ftplib.FTP_TLS()
    ftp.set_debuglevel(2)  # فعال کردن debug output
    print("✅ FTP_TLS object created")
    
    # مرحله ۲: اتصال
    print(f"\n[2/7] Connecting to {FTP_HOST}:{FTP_PORT}...")
    start = time.time()
    response = ftp.connect(host=FTP_HOST, port=FTP_PORT, timeout=30)
    elapsed = time.time() - start
    print(f"✅ Connected in {elapsed:.2f}s")
    print(f"Response: {response}")
    
    # مرحله ۳: Login
    print(f"\n[3/7] Logging in as {FTP_USER}...")
    start = time.time()
    response = ftp.login(user=FTP_USER, passwd=FTP_PASS)
    elapsed = time.time() - start
    print(f"✅ Logged in in {elapsed:.2f}s")
    print(f"Response: {response}")
    
    # مرحله ۴: Protect data connection (برای TLS)
    print("\n[4/7] Protecting data connection (PROT P)...")
    start = time.time()
    ftp.prot_p()
    elapsed = time.time() - start
    print(f"✅ Data protection enabled in {elapsed:.2f}s")
    
    # مرحله ۵: PWD (current directory)
    print("\n[5/7] Getting current directory (PWD)...")
    start = time.time()
    pwd = ftp.pwd()
    elapsed = time.time() - start
    print(f"✅ PWD in {elapsed:.2f}s")
    print(f"Current directory: {pwd}")
    
    # مرحله ۶: Passive Mode
    print("\n[6/7] Setting Passive Mode...")
    start = time.time()
    ftp.set_pasv(True)
    elapsed = time.time() - start
    print(f"✅ Passive mode set in {elapsed:.2f}s")
    
    # مرحله ۷: TYPE I (Binary mode)
    print("\n[7/7] Setting Binary Mode (TYPE I)...")
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
        try:
            ftp.cwd(base_path)
            elapsed = time.time() - start
            print(f"✅ CWD successful in {elapsed:.2f}s")
        except Exception as e:
            print(f"❌ CWD failed: {e}")
    
    # تست LIST
    print("\n[EXTRA] Testing LIST...")
    start = time.time()
    files = ftp.nlst()
    elapsed = time.time() - start
    print(f"✅ LIST successful in {elapsed:.2f}s")
    print(f"Found {len(files)} items")
    
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
