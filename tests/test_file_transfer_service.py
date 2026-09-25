"""
Tests for File Transfer Service

تست‌های سرویس انتقال فایل
"""
import os
import pytest
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from services.file_transfer_service import (
    FileTransferService,
    InvalidURLError,
    FileTooLargeError,
    DownloadError,
    HostNotConfiguredError,
    MAX_FILE_SIZE
)


class TestFileTransferService:
    """تست‌های اصلی FileTransferService"""
    
    @pytest.fixture
    def service(self):
        """ساخت instance از service"""
        return FileTransferService(timeout=10)
    
    def test_initialization(self):
        """تست: مقداردهی اولیه"""
        service = FileTransferService(timeout=300)
        assert service.timeout.total == 300
    
    def test_is_valid_direct_url_valid_http(self, service):
        """تست: URL معتبر http"""
        assert service.is_valid_direct_url("http://example.com/file.zip") is True
    
    def test_is_valid_direct_url_valid_https(self, service):
        """تست: URL معتبر https"""
        assert service.is_valid_direct_url("https://example.com/file.pdf") is True
    
    def test_is_valid_direct_url_youtube(self, service):
        """تست: URL یوتیوب (نامعتبر)"""
        assert service.is_valid_direct_url("https://www.youtube.com/watch?v=123") is False
        assert service.is_valid_direct_url("https://youtu.be/123") is False
    
    def test_is_valid_direct_url_instagram(self, service):
        """تست: URL اینستاگرام (نامعتبر)"""
        assert service.is_valid_direct_url("https://www.instagram.com/p/123") is False
        assert service.is_valid_direct_url("https://instagr.am/p/123") is False
    
    def test_is_valid_direct_url_aparat(self, service):
        """تست: URL آپارات (نامعتبر)"""
        assert service.is_valid_direct_url("https://www.aparat.com/v/123") is False
    
    def test_is_valid_direct_url_no_protocol(self, service):
        """تست: URL بدون protocol (نامعتبر)"""
        assert service.is_valid_direct_url("example.com/file.zip") is False
    
    def test_is_valid_direct_url_ftp(self, service):
        """تست: URL با protocol ftp (نامعتبر)"""
        assert service.is_valid_direct_url("ftp://example.com/file.zip") is False
    
    def test_format_size(self, service):
        """تست: فرمت کردن حجم فایل"""
        assert service._format_size(500) == "500.00 B"
        assert service._format_size(2048) == "2.00 KB"
        assert service._format_size(5 * 1024 * 1024) == "5.00 MB"
        assert service._format_size(3 * 1024 * 1024 * 1024) == "3.00 GB"
    
    @pytest.mark.asyncio
    async def test_upload_to_host_not_implemented(self, service):
        """تست: آپلود به هاست - با storage disabled"""
        # Mock the storage service's is_enabled property
        with patch('services.storage.storage_service.StorageService.is_enabled', new_callable=lambda: property(lambda self: False)):
            with pytest.raises(HostNotConfiguredError):
                await service.upload_to_host("/path/to/file", "test.zip")
    
    @pytest.mark.asyncio
    async def test_download_invalid_url(self, service):
        """تست: دانلود با URL نامعتبر"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(InvalidURLError):
                await service.download_from_url(
                    "https://youtube.com/watch?v=123",
                    temp_dir
                )
    
    @pytest.mark.asyncio
    async def test_download_file_too_large(self, service):
        """تست: دانلود فایل بزرگ‌تر از حد مجاز"""
        url = "https://example.com/largefile.zip"
        
        # Mock response با حجم بیش از 2GB
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {
            'Content-Length': str(MAX_FILE_SIZE + 1000)
        }
        mock_response.url = url
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.head = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('aiohttp.ClientSession', return_value=mock_session):
                with pytest.raises(FileTooLargeError):
                    await service.download_from_url(url, temp_dir)
    
    @pytest.mark.asyncio
    async def test_download_success_with_filename_detection(self, service):
        """تست: دانلود موفق با تشخیص نام فایل"""
        url = "https://example.com/download?id=123"
        test_content = b"Test file content"
        
        # Mock HEAD response
        mock_head_response = MagicMock()
        mock_head_response.status = 200
        mock_head_response.headers = {
            'Content-Length': str(len(test_content)),
            'Content-Disposition': 'attachment; filename="test-file.pdf"'
        }
        mock_head_response.url = url
        mock_head_response.__aenter__ = AsyncMock(return_value=mock_head_response)
        mock_head_response.__aexit__ = AsyncMock(return_value=None)
        
        # Mock GET response
        async def mock_iter_chunked(chunk_size):
            yield test_content
        
        mock_content = Mock()
        mock_content.iter_chunked = mock_iter_chunked
        
        mock_get_response = MagicMock()
        mock_get_response.status = 200
        mock_get_response.headers = {
            'Content-Length': str(len(test_content)),
            'Content-Disposition': 'attachment; filename="test-file.pdf"'
        }
        mock_get_response.url = url
        mock_get_response.content = mock_content
        mock_get_response.__aenter__ = AsyncMock(return_value=mock_get_response)
        mock_get_response.__aexit__ = AsyncMock(return_value=None)
        
        # Mock session
        mock_session = MagicMock()
        mock_session.head = MagicMock(return_value=mock_head_response)
        mock_session.get = MagicMock(return_value=mock_get_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('aiohttp.ClientSession', return_value=mock_session):
                result = await service.download_from_url(url, temp_dir)
                
                # بررسی نام فایل
                assert os.path.basename(result) == "test-file.pdf"
                
                # بررسی محتوا
                assert os.path.exists(result)
                with open(result, 'rb') as f:
                    assert f.read() == test_content
    
    @pytest.mark.asyncio
    async def test_download_with_progress_callback(self, service):
        """تست: دانلود با Progress callback"""
        url = "https://example.com/file.zip"
        test_content = b"X" * 1000
        
        # Mock responses
        mock_head_response = AsyncMock()
        mock_head_response.status = 200
        mock_head_response.headers = {'Content-Length': str(len(test_content))}
        mock_head_response.url = url
        mock_head_response.__aenter__ = AsyncMock(return_value=mock_head_response)
        mock_head_response.__aexit__ = AsyncMock(return_value=None)
        
        async def mock_iter_chunked(chunk_size):
            # ارسال content در چند chunk
            for i in range(0, len(test_content), 100):
                yield test_content[i:i+100]
        
        mock_content = Mock()
        mock_content.iter_chunked = mock_iter_chunked
        
        mock_get_response = MagicMock()
        mock_get_response.status = 200
        mock_get_response.headers = {'Content-Length': str(len(test_content))}
        mock_get_response.url = url
        mock_get_response.content = mock_content
        mock_get_response.__aenter__ = AsyncMock(return_value=mock_get_response)
        mock_get_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.head = MagicMock(return_value=mock_head_response)
        mock_session.get = MagicMock(return_value=mock_get_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Callback برای ردیابی Progress
        progress_calls = []
        async def progress_callback(current, total):
            progress_calls.append((current, total))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('aiohttp.ClientSession', return_value=mock_session):
                result = await service.download_from_url(
                    url,
                    temp_dir,
                    progress_callback=progress_callback
                )
                
                # بررسی اینکه callback فراخوانی شده
                assert len(progress_calls) > 0
                
                # آخرین callback باید کل حجم را نشان دهد
                assert progress_calls[-1][0] == len(test_content)
    
    @pytest.mark.asyncio
    async def test_download_progress_callback_error_ignored(self, service):
        """تست: خطای Progress callback نباید دانلود را fail کند"""
        url = "https://example.com/file.zip"
        test_content = b"Test content"
        
        # Mock responses (مشابه تست قبل)
        mock_head_response = MagicMock()
        mock_head_response.status = 200
        mock_head_response.headers = {'Content-Length': str(len(test_content))}
        mock_head_response.url = url
        mock_head_response.__aenter__ = AsyncMock(return_value=mock_head_response)
        mock_head_response.__aexit__ = AsyncMock(return_value=None)
        
        async def mock_iter_chunked(chunk_size):
            yield test_content
        
        mock_content = Mock()
        mock_content.iter_chunked = mock_iter_chunked
        
        mock_get_response = MagicMock()
        mock_get_response.status = 200
        mock_get_response.headers = {'Content-Length': str(len(test_content))}
        mock_get_response.url = url
        mock_get_response.content = mock_content
        mock_get_response.__aenter__ = AsyncMock(return_value=mock_get_response)
        mock_get_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.head = MagicMock(return_value=mock_head_response)
        mock_session.get = MagicMock(return_value=mock_get_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Callback که exception raise می‌کند
        async def failing_callback(current, total):
            raise Exception("Progress callback failed")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('aiohttp.ClientSession', return_value=mock_session):
                # دانلود باید موفق باشد حتی با خطا در callback
                result = await service.download_from_url(
                    url,
                    temp_dir,
                    progress_callback=failing_callback
                )
                
                assert os.path.exists(result)
    
    def test_get_file_info(self, service):
        """تست: دریافت اطلاعات فایل"""
        with tempfile.NamedTemporaryFile(
            mode='wb',
            suffix='.pdf',
            delete=False
        ) as temp_file:
            temp_file.write(b"Test content")
            temp_path = temp_file.name
        
        try:
            info = service.get_file_info(temp_path)
            
            assert 'name' in info
            assert 'size' in info
            assert 'size_str' in info
            assert 'extension' in info
            assert 'mime_type' in info
            
            assert info['extension'] == '.pdf'
            assert info['size'] == 12  # "Test content" = 12 bytes
            assert info['mime_type'] == 'application/pdf'
        
        finally:
            os.unlink(temp_path)
    
    def test_get_file_info_not_found(self, service):
        """تست: فایل وجود ندارد"""
        with pytest.raises(FileNotFoundError):
            service.get_file_info("/nonexistent/file.txt")


class TestFileTooLargeError:
    """تست‌های خطای FileTooLargeError"""
    
    def test_error_message(self):
        """تست: پیام خطا"""
        error = FileTooLargeError(3 * 1024**3, 2 * 1024**3)
        assert "3.00 GB" in str(error)
        assert "2.00 GB" in str(error)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
