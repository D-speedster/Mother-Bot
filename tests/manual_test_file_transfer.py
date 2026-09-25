"""
Manual Test Script for File Transfer Bot

این فایل برای تست دستی عملکرد File Transfer Bot است.

⚠️ برای اجرا نیاز به BOT_TOKEN واقعی دارید
⚠️ این script صرفاً برای demonstration و manual testing است

Usage:
    python tests/manual_test_file_transfer.py
"""
import asyncio
from utils.filename_detector import FilenameDetector


def test_filename_detection():
    """تست تشخیص نام فایل"""
    print("\n" + "="*60)
    print("TEST: Filename Detection")
    print("="*60)
    
    test_cases = [
        {
            'url': 'https://code.visualstudio.com/sha/download?build=stable&os=win32',
            'headers': {
                'content-disposition': 'attachment; filename="VSCodeUserSetup-x64-1.85.0.exe"'
            },
            'expected': 'VSCodeUserSetup-x64-1.85.0.exe'
        },
        {
            'url': 'https://example.com/download?id=123',
            'headers': {
                'content-type': 'application/pdf'
            },
            'expected': 'download.pdf'
        },
        {
            'url': 'https://example.com/files/document.zip',
            'headers': {},
            'expected': 'document.zip'
        },
        {
            'url': 'https://example.com/download',
            'headers': {},
            'expected': 'download'
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        result = FilenameDetector.detect_filename(
            test['url'],
            test['headers']
        )
        
        if result == test['expected']:
            print(f"✅ Test {i}: PASS")
            print(f"   URL: {test['url'][:50]}...")
            print(f"   Result: {result}")
            passed += 1
        else:
            print(f"❌ Test {i}: FAIL")
            print(f"   URL: {test['url']}")
            print(f"   Expected: {test['expected']}")
            print(f"   Got: {result}")
            failed += 1
        
        print()
    
    print(f"Summary: {passed} passed, {failed} failed")
    return failed == 0


def test_progress_formatting():
    """تست فرمت Progress"""
    print("\n" + "="*60)
    print("TEST: Progress Formatting")
    print("="*60)
    
    from services.progress_tracker import ProgressTracker
    
    # تست Format Size
    sizes = [
        (500, "500.00 B"),
        (1024, "1.00 KB"),
        (1024 * 1024, "1.00 MB"),
        (1024 * 1024 * 1024, "1.00 GB"),
    ]
    
    print("\n📏 Size Formatting:")
    for size, expected in sizes:
        result = ProgressTracker._format_size(size)
        status = "✅" if result == expected else "❌"
        print(f"{status} {size:12} bytes → {result:12} (expected: {expected})")
    
    # تست Format Time
    times = [
        (45, "00:45"),
        (125, "02:05"),
        (3665, "01:01:05"),
    ]
    
    print("\n⏱ Time Formatting:")
    for seconds, expected in times:
        result = ProgressTracker._format_time(seconds)
        status = "✅" if result == expected else "❌"
        print(f"{status} {seconds:6} seconds → {result:10} (expected: {expected})")
    
    # تست Progress Bar
    print("\n📊 Progress Bar:")
    for percentage in [0, 25, 50, 75, 100]:
        bar = ProgressTracker._build_progress_bar(percentage, length=20)
        print(f"{percentage:3}% → {bar}")
    
    return True


def test_service_validation():
    """تست اعتبارسنجی URL"""
    print("\n" + "="*60)
    print("TEST: URL Validation")
    print("="*60)
    
    from services.file_transfer_service import FileTransferService
    
    service = FileTransferService(timeout=10)
    
    valid_urls = [
        "http://example.com/file.zip",
        "https://cdn.example.com/video.mp4",
    ]
    
    invalid_urls = [
        "https://youtube.com/watch?v=123",
        "https://instagram.com/p/123",
        "https://aparat.com/v/123",
        "ftp://example.com/file.zip",
        "example.com/file.zip",
    ]
    
    print("\n✅ Valid URLs:")
    all_valid = True
    for url in valid_urls:
        result = service.is_valid_direct_url(url)
        status = "✅" if result else "❌"
        print(f"{status} {url}")
        if not result:
            all_valid = False
    
    print("\n❌ Invalid URLs (should be blocked):")
    all_invalid = True
    for url in invalid_urls:
        result = service.is_valid_direct_url(url)
        status = "✅" if not result else "❌"
        print(f"{status} {url}")
        if result:
            all_invalid = False
    
    return all_valid and all_invalid


def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("🚀 FILE TRANSFER BOT - MANUAL TESTS")
    print("="*60)
    
    results = []
    
    # Test 1: Filename Detection
    try:
        results.append(("Filename Detection", test_filename_detection()))
    except Exception as e:
        print(f"❌ Error in Filename Detection: {e}")
        results.append(("Filename Detection", False))
    
    # Test 2: Progress Formatting
    try:
        results.append(("Progress Formatting", test_progress_formatting()))
    except Exception as e:
        print(f"❌ Error in Progress Formatting: {e}")
        results.append(("Progress Formatting", False))
    
    # Test 3: Service Validation
    try:
        results.append(("URL Validation", test_service_validation()))
    except Exception as e:
        print(f"❌ Error in URL Validation: {e}")
        results.append(("URL Validation", False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    print(f"Total: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
