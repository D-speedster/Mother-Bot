"""
Mother Bot Gateway - اتصال AI Image Bot به Mother Bot

⚠️ CRITICAL: این یک Abstraction Layer است
فعلاً Mock Implementation دارد
در آینده به Mother Bot API/Service متصل خواهد شد

هدف:
AI Image Bot ↔ Mother Bot Gateway ↔ Mother Bot Services
"""
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UserInfo:
    """اطلاعات کاربر از Mother Bot"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    wallet_balance: int = 0  # موجودی کیف پول (تومان)
    is_premium: bool = False
    created_at: Optional[str] = None


@dataclass
class WalletTransaction:
    """تراکنش کیف پول"""
    transaction_id: str
    user_id: int
    amount: int  # مقدار (مثبت: شارژ، منفی: کسر)
    description: str
    balance_after: int


class MotherBotGateway:
    """
    Gateway برای ارتباط با Mother Bot
    
    ⚠️ این یک Abstraction است
    Implementation فعلی Mock است
    
    در آینده می‌تواند به صورت:
    - Direct Service Call
    - Internal API
    - Message Queue
    - Shared Database
    پیاده‌سازی شود
    """
    
    def __init__(self, mock_mode: bool = True):
        """
        مقداردهی اولیه
        
        Args:
            mock_mode: اگر True باشد، از Mock Data استفاده می‌شود
        """
        self.mock_mode = mock_mode
        logger.info(
            f"MotherBotGateway initialized (mock_mode={mock_mode})"
        )
    
    # ========== User Management ==========
    
    async def get_user_info(self, user_id: int) -> Optional[UserInfo]:
        """
        دریافت اطلاعات کاربر از Mother Bot
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            UserInfo یا None
        """
        if self.mock_mode:
            # Mock Implementation
            logger.debug(f"Mock: Getting user info for {user_id}")
            return UserInfo(
                user_id=user_id,
                username=None,
                first_name="Test User",
                wallet_balance=0,
                is_premium=False
            )
        
        # TODO: Real Implementation
        # return await mother_bot_service.get_user(user_id)
        logger.warning("Real implementation not available")
        return None
    
    async def user_exists(self, user_id: int) -> bool:
        """
        بررسی وجود کاربر در Mother Bot
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            True اگر کاربر وجود داشته باشد
        """
        if self.mock_mode:
            # همه کاربران موجودند در Mock Mode
            return True
        
        # TODO: Real Implementation
        # return await mother_bot_service.user_exists(user_id)
        logger.warning("Real implementation not available")
        return False
    
    # ========== Wallet Management ==========
    
    async def get_user_balance(self, user_id: int) -> int:
        """
        دریافت موجودی کیف پول کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            موجودی (تومان)
        """
        if self.mock_mode:
            logger.debug(f"Mock: Getting balance for user {user_id}")
            return 0
        
        # TODO: Real Implementation
        # return await wallet_service.get_balance(user_id)
        logger.warning("Real implementation not available")
        return 0
    
    async def charge_user(
        self,
        user_id: int,
        amount: int,
        description: str
    ) -> Optional[WalletTransaction]:
        """
        کسر هزینه از کیف پول کاربر
        
        Args:
            user_id: شناسه کاربر
            amount: مقدار (تومان)
            description: توضیحات تراکنش
            
        Returns:
            WalletTransaction یا None (در صورت عدم موفقیت)
        """
        if self.mock_mode:
            logger.info(
                f"Mock: Charging user {user_id} "
                f"amount={amount}, desc={description}"
            )
            import uuid
            return WalletTransaction(
                transaction_id=str(uuid.uuid4()),
                user_id=user_id,
                amount=-amount,
                description=description,
                balance_after=0
            )
        
        # TODO: Real Implementation
        # return await wallet_service.charge(user_id, amount, description)
        logger.warning("Real implementation not available")
        return None
    
    async def has_sufficient_balance(
        self,
        user_id: int,
        required_amount: int
    ) -> bool:
        """
        بررسی کفایت موجودی
        
        Args:
            user_id: شناسه کاربر
            required_amount: مقدار موردنیاز
            
        Returns:
            True اگر موجودی کافی باشد
        """
        balance = await self.get_user_balance(user_id)
        return balance >= required_amount
    
    # ========== Bot Management ==========
    
    async def get_bot_info(self, bot_type: str = "ai_image") -> Dict[str, Any]:
        """
        دریافت اطلاعات Bot از Mother Bot
        
        Args:
            bot_type: نوع Bot
            
        Returns:
            اطلاعات Bot
        """
        if self.mock_mode:
            return {
                'bot_type': bot_type,
                'status': 'active',
                'total_users': 0,
                'created_at': None
            }
        
        # TODO: Real Implementation
        # return await bot_service.get_bot_info(bot_type)
        logger.warning("Real implementation not available")
        return {}
    
    # ========== Statistics ==========
    
    async def report_usage(
        self,
        user_id: int,
        action: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        گزارش استفاده به Mother Bot (برای آمار)
        
        Args:
            user_id: شناسه کاربر
            action: نوع عملیات
            metadata: داده‌های اضافی
        """
        if self.mock_mode:
            logger.debug(
                f"Mock: Reporting usage for user {user_id}, "
                f"action={action}"
            )
            return
        
        # TODO: Real Implementation
        # await analytics_service.report(user_id, action, metadata)
        logger.warning("Real implementation not available")
    
    # ========== Subscription Management ==========
    
    async def is_user_subscribed(self, user_id: int) -> bool:
        """
        بررسی اشتراک کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            True اگر کاربر اشتراک فعال داشته باشد
        """
        if self.mock_mode:
            # در Mock Mode همه کاربران غیر اشتراک هستند
            return False
        
        # TODO: Real Implementation
        # return await subscription_service.is_active(user_id)
        logger.warning("Real implementation not available")
        return False
    
    async def get_user_plan(self, user_id: int) -> str:
        """
        دریافت پلن کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            نام پلن (free, basic, premium, etc.)
        """
        if self.mock_mode:
            return "free"
        
        # TODO: Real Implementation
        # return await subscription_service.get_plan(user_id)
        logger.warning("Real implementation not available")
        return "free"


# ========== Singleton Instance ==========
# این instance در تمام AI Image Bot استفاده می‌شود
_gateway_instance: Optional[MotherBotGateway] = None


def get_mother_bot_gateway(mock_mode: bool = True) -> MotherBotGateway:
    """
    دریافت Gateway Instance (Singleton)
    
    Args:
        mock_mode: اگر True باشد، از Mock استفاده می‌شود
        
    Returns:
        MotherBotGateway instance
    """
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = MotherBotGateway(mock_mode=mock_mode)
    return _gateway_instance
