"""
سرویس مدیریت کیف پول و تراکنش‌ها
"""
import logging
import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class WalletService:
    """
    سرویس مدیریت کیف پول کاربران
    
    Features:
    - مدیریت موجودی کاربران
    - ثبت تراکنش‌ها (واریز/برداشت)
    - دریافت تاریخچه تراکنش‌ها
    - Transaction-safe operations برای جلوگیری از خطای همگام‌سازی
    """
    
    def __init__(self, connection: aiosqlite.Connection):
        """
        Args:
            connection: اتصال aiosqlite
        """
        self._conn = connection
    
    async def _ensure_user_exists(self, user_id: int) -> None:
        """
        اطمینان از وجود کاربر در جدول users
        
        Args:
            user_id: ID کاربر تلگرام
        """
        now = datetime.utcnow().isoformat()
        
        await self._conn.execute(
            """
            INSERT OR IGNORE INTO users (user_id, balance, created_at, updated_at)
            VALUES (?, 0, ?, ?)
            """,
            (user_id, now, now)
        )
        await self._conn.commit()
    
    async def get_balance(self, user_id: int) -> int:
        """
        دریافت موجودی کاربر
        
        Args:
            user_id: ID کاربر تلگرام
            
        Returns:
            موجودی کاربر (به تومان)
        """
        try:
            # اطمینان از وجود کاربر
            await self._ensure_user_exists(user_id)
            
            cursor = await self._conn.execute(
                "SELECT balance FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            row = await cursor.fetchone()
            balance = row[0] if row else 0
            
            logger.info(f"✅ موجودی کاربر {user_id}: {balance:,} تومان")
            return balance
        
        except Exception as e:
            logger.error(f"❌ خطا در دریافت موجودی کاربر {user_id}: {e}", exc_info=True)
            raise
    
    async def add_credit(
        self,
        user_id: int,
        amount: int,
        description: str
    ) -> bool:
        """
        افزایش موجودی و ثبت تراکنش واریز
        
        Args:
            user_id: ID کاربر تلگرام
            amount: مبلغ واریزی (تومان)
            description: توضیحات تراکنش
            
        Returns:
            True در صورت موفقیت
            
        Raises:
            ValueError: اگر مبلغ منفی یا صفر باشد
        """
        if amount <= 0:
            raise ValueError("مبلغ باید بزرگتر از صفر باشد")
        
        try:
            # شروع Transaction برای Transaction Safety
            await self._conn.execute("BEGIN IMMEDIATE")
            
            try:
                # اطمینان از وجود کاربر
                await self._ensure_user_exists(user_id)
                
                now = datetime.utcnow().isoformat()
                
                # افزایش موجودی
                await self._conn.execute(
                    """
                    UPDATE users
                    SET balance = balance + ?, updated_at = ?
                    WHERE user_id = ?
                    """,
                    (amount, now, user_id)
                )
                
                # ثبت تراکنش
                await self._conn.execute(
                    """
                    INSERT INTO transactions (user_id, amount, type, description, created_at)
                    VALUES (?, ?, 'credit', ?, ?)
                    """,
                    (user_id, amount, description, now)
                )
                
                # Commit transaction
                await self._conn.commit()
                
                logger.info(
                    f"✅ واریز موفق: کاربر {user_id}, مبلغ {amount:,} تومان, "
                    f"توضیحات: {description}"
                )
                
                return True
            
            except Exception as e:
                # Rollback در صورت خطا
                await self._conn.rollback()
                raise e
        
        except Exception as e:
            logger.error(
                f"❌ خطا در واریز به کیف پول کاربر {user_id}: {e}",
                exc_info=True
            )
            raise
    
    async def deduct_credit(
        self,
        user_id: int,
        amount: int,
        description: str
    ) -> bool:
        """
        کسر موجودی و ثبت تراکنش برداشت (در صورت کافی بودن موجودی)
        
        ⚠️ CRITICAL: این متد به صورت اتمیک موجودی را چک و کسر می‌کند
        برای جلوگیری از Double Spending در شرایط همزمانی (Concurrency)
        
        Args:
            user_id: ID کاربر تلگرام
            amount: مبلغ برداشتی (تومان)
            description: توضیحات تراکنش
            
        Returns:
            True در صورت موفقیت
            
        Raises:
            ValueError: اگر مبلغ منفی، صفر، یا بیشتر از موجودی باشد
        """
        if amount <= 0:
            raise ValueError("مبلغ باید بزرگتر از صفر باشد")
        
        try:
            # ⚠️ CRITICAL: BEGIN IMMEDIATE برای قفل کردن دیتابیس
            # جلوگیری از Race Condition در چک و کسر موجودی
            await self._conn.execute("BEGIN IMMEDIATE")
            
            try:
                # اطمینان از وجود کاربر
                await self._ensure_user_exists(user_id)
                
                # ⚠️ CRITICAL: استفاده از UPDATE با WHERE balance >= amount
                # فقط اگر موجودی کافی باشد، کسر می‌شود
                now = datetime.utcnow().isoformat()
                
                cursor = await self._conn.execute(
                    """
                    UPDATE users
                    SET balance = balance - ?, updated_at = ?
                    WHERE user_id = ? AND balance >= ?
                    """,
                    (amount, now, user_id, amount)
                )
                
                # بررسی تعداد ردیف‌های تغییر یافته
                if cursor.rowcount == 0:
                    # موجودی کافی نبود
                    await self._conn.rollback()
                    
                    # دریافت موجودی فعلی برای نمایش
                    cursor = await self._conn.execute(
                        "SELECT balance FROM users WHERE user_id = ?",
                        (user_id,)
                    )
                    row = await cursor.fetchone()
                    current_balance = row[0] if row else 0
                    
                    logger.warning(
                        f"⚠️ موجودی ناکافی برای کاربر {user_id}: "
                        f"موجودی فعلی {current_balance:,} تومان, "
                        f"مبلغ درخواستی {amount:,} تومان"
                    )
                    raise ValueError(
                        f"موجودی شما کافی نیست. موجودی فعلی: {current_balance:,} تومان"
                    )
                
                # ثبت تراکنش
                await self._conn.execute(
                    """
                    INSERT INTO transactions (user_id, amount, type, description, created_at)
                    VALUES (?, ?, 'debit', ?, ?)
                    """,
                    (user_id, amount, description, now)
                )
                
                # Commit transaction
                await self._conn.commit()
                
                logger.info(
                    f"✅ برداشت موفق: کاربر {user_id}, مبلغ {amount:,} تومان, "
                    f"موضوع: {description}"
                )
                
                return True
            
            except Exception as e:
                # Rollback در صورت خطا
                await self._conn.rollback()
                raise e
        
        except Exception as e:
            if not isinstance(e, ValueError):
                logger.error(
                    f"❌ خطا در برداشت از کیف پول کاربر {user_id}: {e}",
                    exc_info=True
                )
            raise
    
    async def get_user_transactions(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        دریافت تاریخچه تراکنش‌های کاربر
        
        Args:
            user_id: ID کاربر تلگرام
            limit: تعداد تراکنش‌های برگشتی (پیش‌فرض: 10)
            
        Returns:
            لیست تراکنش‌ها به ترتیب زمانی نزولی
        """
        try:
            cursor = await self._conn.execute(
                """
                SELECT id, amount, type, description, created_at
                FROM transactions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit)
            )
            
            rows = await cursor.fetchall()
            
            transactions = [
                {
                    'id': row[0],
                    'amount': row[1],
                    'type': row[2],
                    'description': row[3],
                    'created_at': row[4]
                }
                for row in rows
            ]
            
            logger.info(
                f"✅ تاریخچه تراکنش‌های کاربر {user_id} دریافت شد: "
                f"{len(transactions)} تراکنش"
            )
            
            return transactions
        
        except Exception as e:
            logger.error(
                f"❌ خطا در دریافت تراکنش‌های کاربر {user_id}: {e}",
                exc_info=True
            )
            raise
