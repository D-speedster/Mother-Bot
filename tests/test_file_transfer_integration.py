"""
Integration Tests for File Transfer Bot

تست‌های یکپارچه برای کل جریان File Transfer
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from services.file_transfer_service import FileTransferService


class TestFileTransferIntegration:
    """تست‌های Integration"""
    
    @pytest.mark.asyncio
    async def test_full_download_flow(self):
        """
        تست: کل جریان دانلود
        URL → Download → Filename Detection → Progress → File
        """
        # Setup
        service = FileTransferService(timeout=10)
        url = "https://code.visualstudio.com/sha/download?build=stable&os=win32"
        test_content = b"Mock VS Code installer content"
        
        # Mock HEAD response - بدون نام فایل در URL
        mock_head_response = MagicMock()
        mock_head_response.status = 200
        mock_head_response.headers = {
            'Content-Length': str(len(test_content)),
            # Final URL بعد از redirect با نام فایل
            'Content-Disposition': 'attachment; filename="VSCodeUserSetup-x64-1.85.0.exe"'
        }
        mock_head_response.url = "https://update.code.visualstudio.com/1.85.0/win32-x64-user/stable"
        mock_head_response.__aenter__ = AsyncMock(return_value=mock_head_response)
        mock_head_response.__aexit__ = AsyncMock(return_value=None)
        
        # Mock GET response
        progress_updates = []
        
        async def mock_iter_chunked(chunk_size):
            # شبیه‌سازی دانلود در چند chunk
            chunk_count = 5
            chunk_size_actual = len(test_content) // chunk_count
            for i in range(chunk_count):
                start = i * chunk_size_actual
                end = start + chunk_size_actual if i < chunk_count - 1 else len(test_content)
                yield test_content[start:end]
        
        mock_content = Mock()
        mock_content.iter_chunked = mock_iter_chunked
        
        mock_get_response = MagicMock()
        mock_get_response.status = 200
        mock_get_response.headers = {
            'Content-Length': str(len(test_content)),
            'Content-Disposition': 'attachment; filename="VSCodeUserSetup-x64-1.85.0.exe"'
        }
        mock_get_response.url = "https://update.code.visualstudio.com/1.85.0/win32-x64-user/stable"
        mock_get_response.content = mock_content
        mock_get_response.__aenter__ = AsyncMock(return_value=mock_get_response)
        mock_get_response.__aexit__ = AsyncMock(return_value=None)
        
        # Mock session
        mock_session = MagicMock()
        mock_session.head = MagicMock(return_value=mock_head_response)
        mock_session.get = MagicMock(return_value=mock_get_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Progress callback
        async def progress_callback(current, total):
            progress_updates.append({
                'current': current,
                'total': total,
                'percentage': int((current / total) * 100) if total else 0
            })
        
        # Execute
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('aiohttp.ClientSession', return_value=mock_session):
                result_path = await service.download_from_url(
                    url,
                    temp_dir,
                    progress_callback=progress_callback
                )
                
                # Verify
                # 1. نام فایل صحیح تشخیص داده شده
                assert os.path.basename(result_path) == "VSCodeUserSetup-x64-1.85.0.exe"
                
                # 2. فایل وجود دارد
                assert os.path.exists(result_path)
                
                # 3. محتوا صحیح است
                with open(result_path, 'rb') as f:
                    assert f.read() == test_content
                
                # 4. Progress updates فراخوانی شده
                assert len(progress_updates) > 0
                
                # 5. آخرین update کل حجم را نشان می‌دهد
                assert progress_updates[-1]['current'] == len(test_content)
                assert progress_updates[-1]['percentage'] == 100
    
    @pytest.mark.asyncio
    async def test_download_with_redirect_and_content_type(self):
        """
        تست: دانلود با redirect و تشخیص extension از Content-Type
        """
        service = FileTransferService(timeout=10)
        url = "https://example.com/download?id=12345"
        test_content = b"\x89PNG\r\n\x1a\n"  # PNG header
        
        # Mock HEAD response - بدون Content-Disposition
        mock_head_response = MagicMock()
        mock_head_response.status = 200
        mock_head_response.headers = {
            'Content-Length': str(len(test_content)),
            'Content-Type': 'image/png'  # فقط Content-Type
        }
        # Final URL بدون extension
        mock_head_response.url = "https://cdn.example.com/images/photo"
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
            'Content-Type': 'image/png'
        }
        mock_get_response.url = "https://cdn.example.com/images/photo"
        mock_get_response.content = mock_content
        mock_get_response.__aenter__ = AsyncMock(return_value=mock_get_response)
        mock_get_response.__aexit__ = AsyncMock(return_value=None)
        
        # Mock session
        mock_session = MagicMock()
        mock_session.head = MagicMock(return_value=mock_head_response)
        mock_session.get = MagicMock(return_value=mock_get_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Execute
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('aiohttp.ClientSession', return_value=mock_session):
                result_path = await service.download_from_url(url, temp_dir)
                
                # Verify
                # نام فایل باید extension .png داشته باشد
                filename = os.path.basename(result_path)
                assert filename.endswith('.png')
    
    @pytest.mark.asyncio
    async def test_small_and_large_file_scenarios(self):
        """
        تست: سناریوهای فایل کوچک و بزرگ
        """
        service = FileTransferService(timeout=10)
        
        # Test 1: فایل کوچک (چند KB)
        small_content = b"Small file" * 100  # ~1KB
        
        # Test 2: فایل متوسط (چند MB) - شبیه‌سازی
        medium_content = b"X" * (5 * 1024 * 1024)  # 5MB
        
        test_cases = [
            ("small.txt", small_content),
            ("medium.bin", medium_content)
        ]
        
        for filename, content in test_cases:
            url = f"https://example.com/{filename}"
            
            # Mock responses
            mock_head_response = MagicMock()
            mock_head_response.status = 200
            mock_head_response.headers = {'Content-Length': str(len(content))}
            mock_head_response.url = url
            mock_head_response.__aenter__ = AsyncMock(return_value=mock_head_response)
            mock_head_response.__aexit__ = AsyncMock(return_value=None)
            
            async def mock_iter_chunked(chunk_size):
                # دانلود در chunk‌های 8KB
                for i in range(0, len(content), 8192):
                    yield content[i:i+8192]
            
            mock_content = Mock()
            mock_content.iter_chunked = mock_iter_chunked
            
            mock_get_response = MagicMock()
            mock_get_response.status = 200
            mock_get_response.headers = {'Content-Length': str(len(content))}
            mock_get_response.url = url
            mock_get_response.content = mock_content
            mock_get_response.__aenter__ = AsyncMock(return_value=mock_get_response)
            mock_get_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = MagicMock()
            mock_session.head = MagicMock(return_value=mock_head_response)
            mock_session.get = MagicMock(return_value=mock_get_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Execute
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch('aiohttp.ClientSession', return_value=mock_session):
                    result_path = await service.download_from_url(url, temp_dir)
                    
                    # Verify
                    assert os.path.exists(result_path)
                    assert os.path.getsize(result_path) == len(content)
                    
                    # بررسی محتوا
                    with open(result_path, 'rb') as f:
                        assert f.read() == content
    
    @pytest.mark.asyncio
    async def test_get_file_info_after_download(self):
        """
        تست: دریافت اطلاعات فایل بعد از دانلود
        """
        service = FileTransferService(timeout=10)
        url = "https://example.com/document.pdf"
        test_content = b"PDF content" * 1000
        
        # Mock responses
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
        
        # Execute
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('aiohttp.ClientSession', return_value=mock_session):
                result_path = await service.download_from_url(url, temp_dir)
                
                # دریافت اطلاعات فایل
                file_info = service.get_file_info(result_path)
                
                # Verify
                assert file_info['name'] == 'document.pdf'
                assert file_info['size'] == len(test_content)
                assert file_info['extension'] == '.pdf'
                assert file_info['mime_type'] == 'application/pdf'
                assert 'KB' in file_info['size_str'] or 'MB' in file_info['size_str']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
