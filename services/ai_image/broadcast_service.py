"""
Broadcast Service برای AI Image Bot

مدیریت ارسال همگانی پیام و Sponsor/Ads
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class BroadcastStatus(str, Enum):
    """وضعیت Broadcast"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BroadcastMessage:
    """پیام Broadcast"""
    id: str
    text: str
    created_by: int  # admin user_id
    target_users: List[int]  # لیست user_id ها
    status: BroadcastStatus = BroadcastStatus.PENDING
    sent_count: int = 0
    failed_count: int = 0
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        return data


@dataclass
class SponsorConfig:
    """تنظیمات Sponsor"""
    enabled: bool = False
    text: str = ""
    url: Optional[str] = None
    button_text: str = "Sponsor"
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return asdict(self)


@dataclass
class AdConfig:
    """تنظیمات تبلیغات"""
    enabled: bool = False
    text: str = ""
    url: Optional[str] = None
    button_text: str = "مشاهده"
    show_frequency: int = 5  # هر چند درخواست یک‌بار نمایش داده شود
    show_count: int = 0  # تعداد نمایش‌های انجام‌شده
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return asdict(self)


class BroadcastService:
    """
    سرویس Broadcast برای AI Image Bot
    
    ⚠️ فعلاً داده‌ها در حافظه نگهداری می‌شوند
    در آینده به Database متصل خواهد شد
    """
    
    def __init__(self):
        """مقداردهی اولیه"""
        self._broadcasts: Dict[str, BroadcastMessage] = {}
        self._sponsor_config = SponsorConfig()
        self._ad_config = AdConfig()
    
    # ========== Broadcast ==========
    
    async def create_broadcast(
        self,
        admin_user_id: int,
        text: str,
        target_users: List[int]
    ) -> BroadcastMessage:
        """
        ایجاد Broadcast جدید
        
        Args:
            admin_user_id: شناسه Admin
            text: متن پیام
            target_users: لیست user_id های هدف
            
        Returns:
            BroadcastMessage ساخته‌شده
        """
        import uuid
        broadcast_id = str(uuid.uuid4())
        
        broadcast = BroadcastMessage(
            id=broadcast_id,
            text=text,
            created_by=admin_user_id,
            target_users=target_users,
            status=BroadcastStatus.PENDING
        )
        
        self._broadcasts[broadcast_id] = broadcast
        logger.info(
            f"Broadcast created: {broadcast_id}, "
            f"targets: {len(target_users)}"
        )
        
        # TODO: ذخیره در Database
        return broadcast
    
    async def execute_broadcast(
        self,
        broadcast_id: str,
        bot
    ) -> Dict[str, Any]:
        """
        اجرای Broadcast
        
        ⚠️ این تابع باید در background/task اجرا شود
        
        Args:
            broadcast_id: شناسه Broadcast
            bot: Bot instance
            
        Returns:
            نتیجه ارسال
        """
        broadcast = self._broadcasts.get(broadcast_id)
        if not broadcast:
            logger.warning(f"Broadcast not found: {broadcast_id}")
            return {'success': False, 'error': 'Broadcast not found'}
        
        # تغییر وضعیت
        broadcast.status = BroadcastStatus.IN_PROGRESS
        broadcast.started_at = datetime.utcnow().isoformat()
        
        sent_count = 0
        failed_count = 0
        
        # ارسال به کاربران
        for user_id in broadcast.target_users:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=broadcast.text,
                    parse_mode="Markdown"
                )
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send to {user_id}: {e}")
                failed_count += 1
        
        # به‌روزرسانی آمار
        broadcast.sent_count = sent_count
        broadcast.failed_count = failed_count
        broadcast.status = BroadcastStatus.COMPLETED
        broadcast.completed_at = datetime.utcnow().isoformat()
        
        logger.info(
            f"Broadcast completed: {broadcast_id}, "
            f"sent: {sent_count}, failed: {failed_count}"
        )
        
        # TODO: ذخیره در Database
        
        return {
            'success': True,
            'sent_count': sent_count,
            'failed_count': failed_count
        }
    
    def get_broadcast(self, broadcast_id: str) -> Optional[BroadcastMessage]:
        """دریافت یک Broadcast"""
        return self._broadcasts.get(broadcast_id)
    
    def get_all_broadcasts(self) -> List[BroadcastMessage]:
        """دریافت تمام Broadcasts"""
        broadcasts = list(self._broadcasts.values())
        # مرتب‌سازی بر اساس زمان (جدیدترین اول)
        broadcasts.sort(
            key=lambda x: x.created_at,
            reverse=True
        )
        return broadcasts
    
    async def cancel_broadcast(self, broadcast_id: str) -> bool:
        """
        لغو Broadcast
        
        Args:
            broadcast_id: شناسه Broadcast
            
        Returns:
            True اگر موفق بود
        """
        broadcast = self._broadcasts.get(broadcast_id)
        if not broadcast:
            return False
        
        if broadcast.status in [
            BroadcastStatus.COMPLETED,
            BroadcastStatus.CANCELLED
        ]:
            logger.warning(
                f"Cannot cancel broadcast {broadcast_id}: "
                f"status is {broadcast.status}"
            )
            return False
        
        broadcast.status = BroadcastStatus.CANCELLED
        logger.info(f"Broadcast cancelled: {broadcast_id}")
        # TODO: ذخیره در Database
        return True
    
    # ========== Sponsor ==========
    
    def get_sponsor_config(self) -> SponsorConfig:
        """دریافت تنظیمات Sponsor"""
        return self._sponsor_config
    
    async def update_sponsor_config(
        self,
        enabled: Optional[bool] = None,
        text: Optional[str] = None,
        url: Optional[str] = None,
        button_text: Optional[str] = None
    ) -> bool:
        """
        به‌روزرسانی تنظیمات Sponsor
        
        Args:
            enabled: فعال/غیرفعال
            text: متن Sponsor
            url: لینک Sponsor
            button_text: متن دکمه
            
        Returns:
            True اگر موفق بود
        """
        try:
            if enabled is not None:
                self._sponsor_config.enabled = enabled
            if text is not None:
                self._sponsor_config.text = text
            if url is not None:
                self._sponsor_config.url = url
            if button_text is not None:
                self._sponsor_config.button_text = button_text
            
            logger.info("Sponsor config updated")
            # TODO: ذخیره در Database
            return True
        except Exception as e:
            logger.error(f"Error updating sponsor config: {e}")
            return False
    
    # ========== Ads ==========
    
    def get_ad_config(self) -> AdConfig:
        """دریافت تنظیمات تبلیغات"""
        return self._ad_config
    
    async def update_ad_config(
        self,
        enabled: Optional[bool] = None,
        text: Optional[str] = None,
        url: Optional[str] = None,
        button_text: Optional[str] = None,
        show_frequency: Optional[int] = None
    ) -> bool:
        """
        به‌روزرسانی تنظیمات تبلیغات
        
        Args:
            enabled: فعال/غیرفعال
            text: متن تبلیغ
            url: لینک تبلیغ
            button_text: متن دکمه
            show_frequency: فرکانس نمایش
            
        Returns:
            True اگر موفق بود
        """
        try:
            if enabled is not None:
                self._ad_config.enabled = enabled
            if text is not None:
                self._ad_config.text = text
            if url is not None:
                self._ad_config.url = url
            if button_text is not None:
                self._ad_config.button_text = button_text
            if show_frequency is not None and show_frequency > 0:
                self._ad_config.show_frequency = show_frequency
            
            logger.info("Ad config updated")
            # TODO: ذخیره در Database
            return True
        except Exception as e:
            logger.error(f"Error updating ad config: {e}")
            return False
    
    def should_show_ad(self) -> bool:
        """
        بررسی اینکه باید تبلیغ نمایش داده شود یا خیر
        
        Returns:
            True اگر باید نمایش داده شود
        """
        if not self._ad_config.enabled:
            return False
        
        self._ad_config.show_count += 1
        
        if self._ad_config.show_count % self._ad_config.show_frequency == 0:
            return True
        
        return False
    
    # ========== User List Management ==========
    
    async def get_all_user_ids(self) -> List[int]:
        """
        دریافت لیست تمام user_id ها
        
        ⚠️ این تابع باید از Database بخواند
        فعلاً لیست خالی برمی‌گرداند
        
        Returns:
            لیست user_id ها
        """
        # TODO: Query از Database
        logger.warning("get_all_user_ids not implemented, returning empty list")
        return []
    
    async def get_active_user_ids(self, days: int = 7) -> List[int]:
        """
        دریافت لیست کاربران فعال
        
        Args:
            days: تعداد روز گذشته
            
        Returns:
            لیست user_id های فعال
        """
        # TODO: Query از Database
        logger.warning("get_active_user_ids not implemented, returning empty list")
        return []
