"""
Progress Tracker Service

مسئولیت: نمایش Progress برای عملیات طولانی (Download/Upload)

Rules:
- Progress update حداکثر هر 3 ثانیه یکبار
- خطای Progress نباید عملیات اصلی را fail کند
- Update نهایی در 100% حتماً انجام شود
"""
import time
import logging
import asyncio
from typing import Optional, Callable
from aiogram.types import Message
from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Tracker برای نمایش Progress عملیات دانلود/آپلود
    
    Features:
    - Throttling: حداکثر یک update در هر 3 ثانیه
    - Safe: خطای Telegram API عملیات را fail نمی‌کند
    - Complete: Update نهایی در 100% حتماً انجام می‌شود
    """
    
    def __init__(
        self,
        message: Message,
        operation: str = "download",
        min_update_interval: float = 3.0
    ):
        """
        Args:
            message: پیام Telegram برای update
            operation: نوع عملیات ("download" یا "upload")
            min_update_interval: حداقل فاصله بین updateها (ثانیه)
        """
        self.message = message
        self.operation = operation
        self.min_update_interval = min_update_interval
        
        self.total_size: Optional[int] = None
        self.current_size: int = 0
        self.start_time: float = time.time()
        self.last_update_time: float = 0
        self.last_percentage: int = -1
        
        # Emoji‌ها
        self.emoji = {
            "download": "📥",
            "upload": "📤"
        }
        
        self.verb = {
            "download": "Downloading",
            "upload": "Uploading"
        }
    
    def set_total_size(self, size: int):
        """تنظیم حجم کل فایل"""
        self.total_size = size
    
    async def update(self, current_size: int, force: bool = False):
        """
        Update Progress
        
        Args:
            current_size: مقدار دانلود/آپلود شده (bytes)
            force: اجبار به update بدون توجه به throttling
        """
        self.current_size = current_size
        current_time = time.time()
        
        # محاسبه درصد
        percentage = 0
        if self.total_size and self.total_size > 0:
            percentage = int((current_size / self.total_size) * 100)
        
        # Throttling: update فقط اگر:
        # 1. Force باشد (برای 100%)
        # 2. یا 3 ثانیه از آخرین update گذشته باشد
        # 3. و درصد تغییر کرده باشد (حداقل 1%)
        time_passed = current_time - self.last_update_time
        percentage_changed = abs(percentage - self.last_percentage) >= 1
        
        if not force and (time_passed < self.min_update_interval or not percentage_changed):
            return
        
        try:
            # ساخت متن Progress
            text = self._build_progress_text(percentage)
            
            # Update پیام Telegram
            await self.message.edit_text(text, parse_mode="HTML")
            
            self.last_update_time = current_time
            self.last_percentage = percentage
        
        except TelegramAPIError as e:
            # خطای Telegram (مثل rate limit) نباید عملیات را fail کند
            logger.warning(
                f"⚠️ خطا در update Progress (ignored): {type(e).__name__}"
            )
        
        except Exception as e:
            logger.error(
                f"❌ خطای غیرمنتظره در Progress Tracker: {type(e).__name__}",
                exc_info=True
            )
    
    async def complete(self):
        """
        نمایش Progress نهایی (100%)
        """
        await self.update(self.total_size or self.current_size, force=True)
    
    def _build_progress_text(self, percentage: int) -> str:
        """
        ساخت متن Progress
        
        Returns:
            متن HTML برای نمایش Progress
        """
        emoji = self.emoji.get(self.operation, "⏳")
        verb = self.verb.get(self.operation, "Processing")
        
        # Progress bar
        if self.total_size:
            bar = self._build_progress_bar(percentage)
            size_text = (
                f"📦 {self._format_size(self.current_size)} / "
                f"{self._format_size(self.total_size)}"
            )
        else:
            bar = "░░░░░░░░░░░░░░░░░░░░"
            size_text = f"📦 {self._format_size(self.current_size)}"
        
        # محاسبه سرعت
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            speed = self.current_size / elapsed
            speed_text = f"⚡ {self._format_size(int(speed))}/s"
        else:
            speed_text = "⚡ -- MB/s"
        
        # محاسبه زمان باقیمانده
        if self.total_size and speed > 0:
            remaining_bytes = self.total_size - self.current_size
            remaining_seconds = remaining_bytes / speed
            eta_text = f"⏳ {self._format_time(int(remaining_seconds))} remaining"
        else:
            eta_text = ""
        
        # زمان سپری شده
        elapsed_text = f"⏱ {self._format_time(int(elapsed))}"
        
        # ساخت متن نهایی
        lines = [
            f"{emoji} <b>{verb}...</b>",
            "",
            bar
        ]
        
        if self.total_size:
            lines.append(f"{percentage}%")
            lines.append("")
        
        lines.append(size_text)
        lines.append(speed_text)
        
        if eta_text:
            lines.append(eta_text)
        
        if percentage == 100:
            lines.append("")
            lines.append(elapsed_text)
        
        return "\n".join(lines)
    
    @staticmethod
    def _build_progress_bar(percentage: int, length: int = 20) -> str:
        """
        ساخت Progress bar نموداری
        
        Args:
            percentage: درصد (0-100)
            length: طول bar
            
        Returns:
            رشته Progress bar مثل: ████████████░░░░░░░░
        """
        filled = int((percentage / 100) * length)
        empty = length - filled
        return "█" * filled + "░" * empty
    
    @staticmethod
    def _format_size(size: int) -> str:
        """
        تبدیل bytes به واحد خوانا
        
        Args:
            size: حجم به bytes
            
        Returns:
            رشته قابل خواندن مثل "25.3 MB"
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    @staticmethod
    def _format_time(seconds: int) -> str:
        """
        تبدیل ثانیه به فرمت خوانا
        
        Args:
            seconds: زمان به ثانیه
            
        Returns:
            رشته قابل خواندن مثل "02:35" یا "01:23:45"
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
