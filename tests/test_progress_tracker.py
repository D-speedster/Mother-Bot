"""
Tests for Progress Tracker Service

تست‌های Progress Tracker برای Download/Upload
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from services.progress_tracker import ProgressTracker


class TestProgressTracker:
    """تست‌های اصلی ProgressTracker"""
    
    @pytest.fixture
    def mock_message(self):
        """Mock برای Telegram Message"""
        message = Mock()
        message.edit_text = AsyncMock()
        return message
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_message):
        """تست: مقداردهی اولیه"""
        tracker = ProgressTracker(mock_message, operation="download")
        assert tracker.operation == "download"
        assert tracker.current_size == 0
        assert tracker.total_size is None
    
    @pytest.mark.asyncio
    async def test_set_total_size(self, mock_message):
        """تست: تنظیم حجم کل"""
        tracker = ProgressTracker(mock_message)
        tracker.set_total_size(1024 * 1024)  # 1MB
        assert tracker.total_size == 1024 * 1024
    
    @pytest.mark.asyncio
    async def test_update_without_throttling(self, mock_message):
        """تست: Update بدون throttling (force=True)"""
        tracker = ProgressTracker(mock_message)
        tracker.set_total_size(1000)
        
        await tracker.update(500, force=True)
        
        mock_message.edit_text.assert_called_once()
        call_args = mock_message.edit_text.call_args
        assert "50%" in call_args[0][0]  # 50% progress
    
    @pytest.mark.asyncio
    async def test_update_with_throttling(self, mock_message):
        """تست: Throttling - updateهای خیلی سریع ignore شوند"""
        tracker = ProgressTracker(mock_message, min_update_interval=1.0)
        tracker.set_total_size(1000)
        
        # اولین update
        await tracker.update(100)
        assert mock_message.edit_text.call_count == 1
        
        # Update خیلی سریع (باید ignore شود)
        await tracker.update(150)
        assert mock_message.edit_text.call_count == 1  # همان یکبار
        
        # منتظر می‌مانیم تا throttle interval بگذرد
        await asyncio.sleep(1.1)
        
        # حالا باید update شود
        await tracker.update(200)
        assert mock_message.edit_text.call_count == 2
    
    @pytest.mark.asyncio
    async def test_update_telegram_error_ignored(self, mock_message):
        """تست: خطای Telegram API نباید exception raise کند"""
        from aiogram.exceptions import TelegramAPIError
        
        # TelegramAPIError نیاز به method و message دارد
        mock_message.edit_text = AsyncMock(
            side_effect=TelegramAPIError(method="editMessageText", message="Rate limit")
        )
        
        tracker = ProgressTracker(mock_message)
        tracker.set_total_size(1000)
        
        # خطا باید catch شود و عملیات ادامه یابد
        await tracker.update(500, force=True)
        # اگر exception raise نشد، تست موفق است
    
    @pytest.mark.asyncio
    async def test_complete(self, mock_message):
        """تست: Complete باید 100% نمایش دهد"""
        tracker = ProgressTracker(mock_message)
        tracker.set_total_size(1000)
        tracker.current_size = 1000
        
        await tracker.complete()
        
        call_args = mock_message.edit_text.call_args
        assert "100%" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_progress_without_total_size(self, mock_message):
        """تست: Progress زمانی که total_size مشخص نیست"""
        tracker = ProgressTracker(mock_message)
        # total_size تنظیم نمی‌کنیم
        
        await tracker.update(1024 * 1024, force=True)  # 1MB
        
        call_args = mock_message.edit_text.call_args
        text = call_args[0][0]
        
        # نباید percentage نمایش داده شود
        assert "%" not in text or "100%" in text
        # اما حجم باید نمایش داده شود
        assert "1.00 MB" in text
    
    @pytest.mark.asyncio
    async def test_download_operation(self, mock_message):
        """تست: عملیات Download"""
        tracker = ProgressTracker(mock_message, operation="download")
        tracker.set_total_size(1000)
        
        await tracker.update(500, force=True)
        
        call_args = mock_message.edit_text.call_args
        text = call_args[0][0]
        
        assert "📥" in text  # Download emoji
        assert "Downloading" in text
    
    @pytest.mark.asyncio
    async def test_upload_operation(self, mock_message):
        """تست: عملیات Upload"""
        tracker = ProgressTracker(mock_message, operation="upload")
        tracker.set_total_size(1000)
        
        await tracker.update(500, force=True)
        
        call_args = mock_message.edit_text.call_args
        text = call_args[0][0]
        
        assert "📤" in text  # Upload emoji
        assert "Uploading" in text
    
    @pytest.mark.asyncio
    async def test_speed_calculation(self, mock_message):
        """تست: محاسبه سرعت"""
        tracker = ProgressTracker(mock_message)
        tracker.set_total_size(10 * 1024 * 1024)  # 10MB
        
        # شبیه‌سازی گذشت زمان
        tracker.start_time -= 1.0  # 1 ثانیه قبل
        
        await tracker.update(1 * 1024 * 1024, force=True)  # 1MB بعد از 1 ثانیه
        
        call_args = mock_message.edit_text.call_args
        text = call_args[0][0]
        
        # باید سرعت نمایش داده شود
        assert "⚡" in text
        assert "/s" in text
    
    @pytest.mark.asyncio
    async def test_percentage_change_threshold(self, mock_message):
        """تست: Update فقط اگر درصد حداقل 1% تغییر کرده باشد"""
        tracker = ProgressTracker(mock_message, min_update_interval=0.1)
        tracker.set_total_size(10000)
        
        # اولین update
        await tracker.update(1000)  # 10%
        assert mock_message.edit_text.call_count == 1
        
        await asyncio.sleep(0.2)  # منتظر می‌مانیم تا throttle بگذرد
        
        # تغییر کوچک (کمتر از 1%)
        await tracker.update(1005)  # هنوز 10%
        assert mock_message.edit_text.call_count == 1  # نباید update شود
        
        await asyncio.sleep(0.2)
        
        # تغییر بیشتر از 1%
        await tracker.update(1200)  # 12%
        assert mock_message.edit_text.call_count == 2  # باید update شود


class TestProgressBar:
    """تست‌های Progress Bar"""
    
    def test_progress_bar_0_percent(self):
        """تست: Progress bar در 0%"""
        bar = ProgressTracker._build_progress_bar(0, length=10)
        assert bar == "░░░░░░░░░░"
    
    def test_progress_bar_50_percent(self):
        """تست: Progress bar در 50%"""
        bar = ProgressTracker._build_progress_bar(50, length=10)
        assert bar == "█████░░░░░"
    
    def test_progress_bar_100_percent(self):
        """تست: Progress bar در 100%"""
        bar = ProgressTracker._build_progress_bar(100, length=10)
        assert bar == "██████████"
    
    def test_progress_bar_default_length(self):
        """تست: طول پیش‌فرض Progress bar"""
        bar = ProgressTracker._build_progress_bar(50)
        assert len(bar) == 20


class TestFormatters:
    """تست‌های توابع Format"""
    
    def test_format_size_bytes(self):
        """تست: فرمت bytes"""
        assert ProgressTracker._format_size(500) == "500.00 B"
    
    def test_format_size_kilobytes(self):
        """تست: فرمت kilobytes"""
        assert ProgressTracker._format_size(2048) == "2.00 KB"
    
    def test_format_size_megabytes(self):
        """تست: فرمت megabytes"""
        assert ProgressTracker._format_size(5 * 1024 * 1024) == "5.00 MB"
    
    def test_format_size_gigabytes(self):
        """تست: فرمت gigabytes"""
        assert ProgressTracker._format_size(3 * 1024 * 1024 * 1024) == "3.00 GB"
    
    def test_format_time_seconds(self):
        """تست: فرمت ثانیه"""
        assert ProgressTracker._format_time(45) == "00:45"
    
    def test_format_time_minutes(self):
        """تست: فرمت دقیقه"""
        assert ProgressTracker._format_time(125) == "02:05"
    
    def test_format_time_hours(self):
        """تست: فرمت ساعت"""
        assert ProgressTracker._format_time(3665) == "01:01:05"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
