"""
FTP Connection Debug Script

تست مرحله به مرحله اتصال FTP
"""
import os
import socket
import ftplib
from dotenv import load_dotenv

load_dotenv()

host = os.getenv('FILE_STORAGE_FTP_HOST')
port = int(os.getenv('FILE_STORAGE_FTP_PORT', '21'))
username = os.getenv('FILE_STORAGE_FTP_USERNAME')
password = os.getenv('FILE_STORAGE_FTP_PASSWORD')

print("="*60)
print("🧪 FTP Connection Debug")
print("="*60)
print(f"\nHost: {host}")
print(f"Port: {port}")
print(f"User: {username}")
print(f"Pass: {'*' * len(password)}")

# Test 1: DNS Resolution
print("\n" + "="*60)
print("1️⃣ DNS Resolution Test")
print("="*60)

try:
    ip = socket.gethostbyname(host)
    print(f"✅ DNS OK: {host} → {ip}")
except socket.gaierror as e:
    print(f"❌ DNS Failed: {e}")
    print("\n💡 Suggestions:")
    print("   - Check if domain is correct")
    print("   - Try with 'ftp.radif-ecu.ir' instead")
    print("   - Try with IP address directly")
    print("   - Check your internet connection")
    exit(1)

# Test 2: Socket Connection
print("\n" + "="*60)
print("2️⃣ Socket Connection Test")
print("="*60)

try:
    sock = socket.create_connection((host, port), timeout=10)
    print(f"✅ Socket connected to {host}:{port}")
    sock.close()
except (socket.timeout, ConnectionRefusedError, OSError) as e:
    print(f"❌ Socket connection failed: {e}")
    print("\n💡 Suggestions:")
    print("   - Check if FTP port 21 is open")
    print("   - Check firewall settings")
    print("   - Try different port (some hosts use 2121 or other)")
    exit(1)

# Test 3: FTP Connection
print("\n" + "="*60)
print("3️⃣ FTP Protocol Test")
print("="*60)

try:
    ftp = ftplib.FTP()
    print(f"Connecting to {host}:{port}...")
    response = ftp.connect(host, port, timeout=30)
    print(f"✅ FTP connected: {response}")
    
    # Test 4: Login
    print("\n" + "="*60)
    print("4️⃣ FTP Login Test")
    print("="*60)
    
    print(f"Logging in as {username}...")
    ftp.login(username, password)
    print("✅ Login successful!")
    
    # Test 5: PWD
    print("\n" + "="*60)
    print("5️⃣ Current Directory")
    print("="*60)
    
    pwd = ftp.pwd()
    print(f"Current directory: {pwd}")
    
    # Test 6: List files
    print("\n" + "="*60)
    print("6️⃣ Directory Listing")
    print("="*60)
    
    print("\nFiles and directories:")
    files = []
    ftp.retrlines('LIST', files.append)
    
    for i, line in enumerate(files[:20], 1):  # Show first 20
        print(f"   {line}")
    
    if len(files) > 20:
        print(f"   ... and {len(files) - 20} more")
    
    print(f"\n✅ Total items: {len(files)}")
    
    # Test 7: Check configured path
    print("\n" + "="*60)
    print("7️⃣ Test Configured Path")
    print("="*60)
    
    configured_path = os.getenv('FILE_STORAGE_FTP_BASE_PATH', '')
    if configured_path:
        print(f"\nConfigured path: {configured_path}")
        try:
            ftp.cwd(configured_path)
            config_pwd = ftp.pwd()
            print(f"✅ Path accessible: {config_pwd}")
            
            config_files = []
            ftp.retrlines('LIST', config_files.append)
            print(f"   Items in directory: {len(config_files)}")
            
            ftp.cwd('/')
        except ftplib.error_perm as e:
            print(f"❌ Cannot access configured path: {e}")
    else:
        print("No path configured in FILE_STORAGE_FTP_BASE_PATH")
    
    # Test 8: Suggested paths
    print("\n" + "="*60)
    print("8️⃣ Directory Structure Analysis")
    print("="*60)
    
    # Parse directory listing
    dirs = []
    for line in files:
        if line.startswith('d'):
            parts = line.split()
            if len(parts) >= 9:
                dirname = ' '.join(parts[8:])
                if not dirname.startswith('.'):
                    dirs.append(dirname)
    
    print(f"\nRoot directories: {', '.join(dirs) if dirs else 'none'}")
    
    if 'public_html' in dirs:
        print("\n✅ Found public_html directory")
        
        # Check inside public_html
        try:
            ftp.cwd('public_html')
            public_pwd = ftp.pwd()
            print(f"   Absolute path: {public_pwd}")
            
            public_files = []
            ftp.retrlines('LIST', public_files.append)
            
            public_dirs = []
            for line in public_files:
                if line.startswith('d'):
                    parts = line.split()
                    if len(parts) >= 9:
                        dirname = ' '.join(parts[8:])
                        if not dirname.startswith('.'):
                            public_dirs.append(dirname)
            
            print(f"   Contents: {', '.join(public_dirs) if public_dirs else 'empty'}")
            
            if 'files' in public_dirs:
                print("\n✅ Found public_html/files directory")
                
                ftp.cwd('files')
                files_pwd = ftp.pwd()
                print(f"   Absolute path: {files_pwd}")
                ftp.cwd('/')
                
                print("\n📋 Recommended .env settings:")
                print(f"FILE_STORAGE_FTP_BASE_PATH={files_pwd}")
                print(f"FILE_STORAGE_PUBLIC_BASE_URL=https://radif-ecu.ir/files")
            else:
                print("\n⚠️  files directory not found in public_html")
                print("   You can create it or use public_html directly")
                print("\n📋 Option 1 (create files/ subdirectory):")
                print(f"FILE_STORAGE_FTP_BASE_PATH={public_pwd}/files")
                print(f"FILE_STORAGE_PUBLIC_BASE_URL=https://radif-ecu.ir/files")
                print("\n📋 Option 2 (use public_html/ directly):")
                print(f"FILE_STORAGE_FTP_BASE_PATH={public_pwd}")
                print(f"FILE_STORAGE_PUBLIC_BASE_URL=https://radif-ecu.ir")
            
            ftp.cwd('/')
            
        except ftplib.error_perm as e:
            print(f"   ❌ Cannot access public_html: {e}")
    
    elif 'htdocs' in dirs:
        print("\n✅ Found htdocs directory (alternative to public_html)")
        try:
            ftp.cwd('htdocs')
            htdocs_pwd = ftp.pwd()
            ftp.cwd('/')
            
            print("\n📋 Recommended .env settings:")
            print(f"FILE_STORAGE_FTP_BASE_PATH={htdocs_pwd}/files")
            print(f"FILE_STORAGE_PUBLIC_BASE_URL=https://radif-ecu.ir/files")
        except:
            print(f"FILE_STORAGE_FTP_BASE_PATH=/htdocs/files")
            print(f"FILE_STORAGE_PUBLIC_BASE_URL=https://radif-ecu.ir/files")
    
    else:
        print("\n⚠️  Standard web directories not found")
        print(f"   Current path: {pwd}")
        print("\n📋 Use current directory:")
        print(f"FILE_STORAGE_FTP_BASE_PATH={pwd}")
        print(f"FILE_STORAGE_PUBLIC_BASE_URL=https://radif-ecu.ir")
    
    print("\n✅ All tests passed!")
    print("\n" + "="*60)
    
    ftp.quit()
    
except ftplib.error_perm as e:
    print(f"❌ FTP Permission Error: {e}")
    print("\n💡 Suggestions:")
    print("   - Check username and password")
    print("   - Check if account is active")
    print("   - Check if FTP access is enabled")

except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
