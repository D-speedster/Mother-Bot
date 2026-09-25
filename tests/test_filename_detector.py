"""
Tests for Filename Detector Utility

تست‌های جامع برای تشخیص صحیح نام و پسوند فایل
"""
import pytest
from utils.filename_detector import FilenameDetector


class TestFilenameDetector:
    """تست‌های FilenameDetector"""
    
    def test_detect_from_url_with_extension(self):
        """تست: URL با extension مشخص"""
        url = "https://example.com/files/document.pdf"
        result = FilenameDetector.detect_filename(url)
        assert result == "document.pdf"
    
    def test_detect_from_url_without_extension(self):
        """تست: URL بدون extension"""
        url = "https://example.com/download?id=123"
        result = FilenameDetector.detect_filename(url)
        assert result == "download"
    
    def test_detect_from_content_disposition_simple(self):
        """تست: Content-Disposition با filename ساده"""
        url = "https://example.com/download"
        headers = {
            'content-disposition': 'attachment; filename="my-file.zip"'
        }
        result = FilenameDetector.detect_filename(url, headers)
        assert result == "my-file.zip"
    
    def test_detect_from_content_disposition_utf8(self):
        """تست: Content-Disposition با UTF-8 encoding"""
        url = "https://example.com/download"
        headers = {
            'content-disposition': "attachment; filename*=UTF-8''test%20file.pdf"
        }
        result = FilenameDetector.detect_filename(url, headers)
        assert result == "test file.pdf"
    
    def test_detect_from_content_disposition_persian(self):
        """تست: Content-Disposition با نام فارسی"""
        url = "https://example.com/download"
        headers = {
            'content-disposition': 'attachment; filename="فایل-تست.pdf"'
        }
        result = FilenameDetector.detect_filename(url, headers)
        assert result == "فایل-تست.pdf"
    
    def test_detect_from_final_url_after_redirect(self):
        """تست: Filename از URL نهایی بعد از redirect"""
        url = "https://example.com/download?id=123"
        final_url = "https://cdn.example.com/files/report.docx"
        result = FilenameDetector.detect_filename(url, final_url=final_url)
        assert result == "report.docx"
    
    def test_detect_from_content_type(self):
        """تست: تشخیص extension از Content-Type"""
        url = "https://example.com/download"
        headers = {
            'content-type': 'image/jpeg'
        }
        result = FilenameDetector.detect_filename(url, headers)
        assert result == "download.jpg"
    
    def test_detect_from_content_type_with_charset(self):
        """تست: Content-Type با charset"""
        url = "https://example.com/download"
        headers = {
            'content-type': 'application/pdf; charset=utf-8'
        }
        result = FilenameDetector.detect_filename(url, headers)
        assert result == "download.pdf"
    
    def test_priority_content_disposition_over_url(self):
        """تست: اولویت Content-Disposition نسبت به URL"""
        url = "https://example.com/download.txt"
        headers = {
            'content-disposition': 'attachment; filename="actual-file.zip"'
        }
        result = FilenameDetector.detect_filename(url, headers)
        assert result == "actual-file.zip"
    
    def test_priority_final_url_over_original(self):
        """تست: اولویت Final URL نسبت به Original URL"""
        url = "https://example.com/download"
        final_url = "https://cdn.example.com/files/video.mp4"
        result = FilenameDetector.detect_filename(url, final_url=final_url)
        assert result == "video.mp4"
    
    def test_sanitize_unsafe_characters(self):
        """تست: حذف کاراکترهای unsafe"""
        url = "https://example.com/files"
        headers = {
            'content-disposition': 'attachment; filename="file<name>:test.pdf"'
        }
        result = FilenameDetector.detect_filename(url, headers)
        # کاراکترهای <>: باید با _ جایگزین شوند
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
    
    def test_url_with_query_parameters(self):
        """تست: URL با query parameters"""
        url = "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user"
        result = FilenameDetector.detect_filename(url)
        assert result == "download"
    
    def test_url_with_encoded_filename(self):
        """تست: URL با نام encode شده"""
        url = "https://example.com/files/test%20file%20name.pdf"
        result = FilenameDetector.detect_filename(url)
        assert result == "test file name.pdf"
    
    def test_no_extension_no_content_type(self):
        """تست: بدون extension و بدون Content-Type"""
        url = "https://example.com/download"
        result = FilenameDetector.detect_filename(url)
        assert result == "download"
        # نباید extension جعلی اضافه شود
        assert "." not in result
    
    def test_generic_content_type(self):
        """تست: Content-Type عمومی (application/octet-stream)"""
        url = "https://example.com/download"
        headers = {
            'content-type': 'application/octet-stream'
        }
        result = FilenameDetector.detect_filename(url, headers)
        # نباید extension اضافه شود برای octet-stream
        assert result == "download"
    
    def test_empty_url_path(self):
        """تست: URL با path خالی"""
        url = "https://example.com/"
        result = FilenameDetector.detect_filename(url)
        assert result == "downloaded_file"
    
    def test_long_filename_truncation(self):
        """تست: نام خیلی بلند باید truncate شود"""
        very_long_name = "a" * 300 + ".pdf"
        url = "https://example.com/files"
        headers = {
            'content-disposition': f'attachment; filename="{very_long_name}"'
        }
        result = FilenameDetector.detect_filename(url, headers)
        # نام نهایی باید کوتاه‌تر از 255 کاراکتر باشد
        assert len(result) <= 255
        # اما extension باید حفظ شود
        assert result.endswith(".pdf")
    
    def test_filename_with_spaces(self):
        """تست: نام فایل با فاصله‌ها"""
        url = "https://example.com/files"
        headers = {
            'content-disposition': 'attachment; filename="my   file   name.zip"'
        }
        result = FilenameDetector.detect_filename(url, headers)
        # فاصله‌های اضافی باید normalize شوند
        assert result == "my file name.zip"
    
    def test_various_mime_types(self):
        """تست: انواع MIME types"""
        test_cases = [
            ('image/png', 'file.png'),
            ('video/mp4', 'file.mp4'),
            ('audio/mpeg', 'file.mp3'),
            ('application/zip', 'file.zip'),
            ('text/plain', 'file.txt'),
        ]
        
        for mime_type, expected in test_cases:
            url = "https://example.com/file"
            headers = {'content-type': mime_type}
            result = FilenameDetector.detect_filename(url, headers)
            assert result == expected, f"Failed for {mime_type}"
    
    def test_content_disposition_without_quotes(self):
        """تست: Content-Disposition بدون quotes"""
        url = "https://example.com/download"
        headers = {
            'content-disposition': 'attachment; filename=simple-file.pdf'
        }
        result = FilenameDetector.detect_filename(url, headers)
        assert result == "simple-file.pdf"
    
    def test_mixed_priority_scenario(self):
        """تست: سناریوی کامل با تمام اولویت‌ها"""
        url = "https://example.com/download?file=1"
        final_url = "https://cdn.example.com/files/redirected.txt"
        headers = {
            'content-disposition': 'attachment; filename="actual-document.pdf"',
            'content-type': 'application/pdf'
        }
        result = FilenameDetector.detect_filename(url, headers, final_url)
        # Content-Disposition باید بالاترین اولویت را داشته باشد
        assert result == "actual-document.pdf"


class TestExtractFromContentDisposition:
    """تست‌های متد extract_from_content_disposition"""
    
    def test_simple_quoted(self):
        result = FilenameDetector._extract_from_content_disposition(
            'attachment; filename="file.pdf"'
        )
        assert result == "file.pdf"
    
    def test_unquoted(self):
        result = FilenameDetector._extract_from_content_disposition(
            'attachment; filename=file.pdf'
        )
        assert result == "file.pdf"
    
    def test_utf8_encoded(self):
        result = FilenameDetector._extract_from_content_disposition(
            "attachment; filename*=UTF-8''my%20file.pdf"
        )
        assert result == "my file.pdf"
    
    def test_inline_disposition(self):
        result = FilenameDetector._extract_from_content_disposition(
            'inline; filename="document.docx"'
        )
        assert result == "document.docx"
    
    def test_no_filename(self):
        result = FilenameDetector._extract_from_content_disposition(
            'attachment'
        )
        assert result is None
    
    def test_invalid_format(self):
        result = FilenameDetector._extract_from_content_disposition(
            'some-invalid-header'
        )
        assert result is None


class TestSanitizeFilename:
    """تست‌های متد sanitize_filename"""
    
    def test_remove_unsafe_chars(self):
        unsafe = 'file<name>:test|?.pdf'
        result = FilenameDetector._sanitize_filename(unsafe)
        # کاراکترهای غیرمجاز باید با _ جایگزین شوند
        assert all(c not in result for c in '<>:|?')
    
    def test_preserve_safe_chars(self):
        safe = 'my-file_name.test.pdf'
        result = FilenameDetector._sanitize_filename(safe)
        assert result == safe
    
    def test_persian_characters(self):
        persian = 'فایل-تست.pdf'
        result = FilenameDetector._sanitize_filename(persian)
        assert result == persian
    
    def test_spaces(self):
        with_spaces = 'my  file   name.pdf'
        result = FilenameDetector._sanitize_filename(with_spaces)
        # فاصله‌های متعدد باید به یک فاصله تبدیل شوند
        assert result == 'my file name.pdf'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
