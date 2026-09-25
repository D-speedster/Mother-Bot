"""
Tests for Storage Filename Utilities

تست‌های ساخت نام‌های امن برای فایل‌ها
"""
import pytest
from services.storage.filename_utils import FilenameGenerator


class TestFilenameGenerator:
    """تست‌های FilenameGenerator"""
    
    def test_generate_safe_filename_simple(self):
        """تست: ساخت نام فایل ساده"""
        filename = FilenameGenerator.generate_safe_filename("video.mp4")
        
        # باید شامل extension باشد
        assert filename.endswith(".mp4")
        
        # باید unique ID داشته باشد
        assert "_" in filename
    
    def test_generate_safe_filename_with_spaces(self):
        """تست: نام فایل با فاصله"""
        filename = FilenameGenerator.generate_safe_filename("my video file.mp4")
        
        # فاصله‌ها باید به underscore تبدیل شوند
        assert " " not in filename
        assert "my_video_file" in filename or "_my_video_file" in filename.split("_", 1)[1]
    
    def test_generate_safe_filename_unsafe_chars(self):
        """تست: کاراکترهای غیرمجاز"""
        filename = FilenameGenerator.generate_safe_filename("test<file>:name?.pdf")
        
        # کاراکترهای غیرمجاز نباید موجود باشند
        assert "<" not in filename
        assert ">" not in filename
        assert ":" not in filename
        assert "?" not in filename
    
    def test_generate_safe_filename_path_traversal(self):
        """تست: جلوگیری از path traversal"""
        filename = FilenameGenerator.generate_safe_filename("../../../etc/passwd")
        
        # نباید .. داشته باشد
        assert ".." not in filename
    
    def test_generate_safe_filename_uniqueness(self):
        """تست: تضمین uniqueness"""
        filename1 = FilenameGenerator.generate_safe_filename("test.pdf")
        filename2 = FilenameGenerator.generate_safe_filename("test.pdf")
        
        # دو فایل با نام یکسان باید unique ID متفاوت داشته باشند
        assert filename1 != filename2
    
    def test_generate_safe_filename_no_extension(self):
        """تست: فایل بدون extension"""
        filename = FilenameGenerator.generate_safe_filename("readme")
        
        # باید unique ID داشته باشد
        assert len(filename) > 8
    
    def test_validate_filename_safe(self):
        """تست: اعتبارسنجی نام امن"""
        assert FilenameGenerator.validate_filename("test_file.pdf") is True
        assert FilenameGenerator.validate_filename("abc123_video.mp4") is True
    
    def test_validate_filename_path_traversal(self):
        """تست: رد کردن path traversal"""
        assert FilenameGenerator.validate_filename("../file.pdf") is False
        assert FilenameGenerator.validate_filename("../../etc/passwd") is False
    
    def test_validate_filename_absolute_path(self):
        """تست: رد کردن absolute path"""
        assert FilenameGenerator.validate_filename("/etc/passwd") is False
        assert FilenameGenerator.validate_filename("\\Windows\\System32") is False
    
    def test_validate_filename_empty(self):
        """تست: رد کردن نام خالی"""
        assert FilenameGenerator.validate_filename("") is False
        assert FilenameGenerator.validate_filename("   ") is False
    
    def test_sanitize_filename(self):
        """تست: تمیز کردن نام فایل"""
        result = FilenameGenerator._sanitize_filename("my  file  name")
        assert result == "my_file_name"
    
    def test_truncate_long_filename(self):
        """تست: truncate کردن نام طولانی"""
        long_name = "a" * 300 + ".pdf"
        filename = FilenameGenerator.generate_safe_filename(long_name)
        
        # نام نهایی باید کوتاه‌تر از حد مجاز باشد
        assert len(filename) <= FilenameGenerator.MAX_FILENAME_LENGTH
        
        # extension باید حفظ شود
        assert filename.endswith(".pdf")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
