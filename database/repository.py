"""
Repository - لایه دسترسی به داده برای عملیات CRUD ربات‌ها
"""
import logging
import sqlite3
import aiosqlite
from datetime import datetime
from typing import Optional, Dict, Any, List

from services.exceptions import TokenAlreadyRegisteredError

logger = logging.getLogger(__name__)


class BotRepository:
    """
    Repository برای مدیریت عملیات دیتابیس ربات‌ها
    
    معماری لایه‌بندی: Handler -> Service -> Repository -> aiosqlite -> SQLite
    
    Features:
    - مدیریت Race Condition با IntegrityError
    - عملیات CRUD کامل
    - Timestamp خودکار
    """
    
    def __init__(self, connection: aiosqlite.Connection):
        """
        Args:
            connection: اتصال aiosqlite
        """
        self._conn = connection
    
    async def create_bot(
        self,
        owner_id: int,
        bot_telegram_id: int,
        username: Optional[str],
        first_name: Optional[str],
        bot_type: str,
        token_encrypted: str,
        status: str = 'inactive'
    ) -> int:
        """
        ثبت ربات جدید در دیتابیس
        
        Args:
            owner_id: ID کاربر تلگرام (صاحب ربات)
            bot_telegram_id: ID تلگرام ربات
            username: نام کاربری ربات (بدون @)
            first_name: نام ربات
            bot_type: نوع ربات (shop, downloader, ...)
            token_encrypted: توکن رمزنگاری‌شده
            status: وضعیت ربات (پیش‌فرض: inactive)
            
        Returns:
            ID رکورد ایجادشده در دیتابیس
            
        Raises:
            TokenAlreadyRegisteredError: اگر ربات قبلاً ثبت شده باشد (Race Condition)
            ValueError: اگر پارامترهای اجباری خالی باشند
        """
        # اعتبارسنجی ورودی‌ها
        if not owner_id or not bot_telegram_id or not bot_type or not token_encrypted:
            raise ValueError("پارامترهای اجباری نمی‌توانند خالی باشند")
        
        try:
            now = datetime.utcnow().isoformat()
            
            cursor = await self._conn.execute(
                """
                INSERT INTO bots (
                    owner_id, bot_telegram_id, username, first_name,
                    bot_type, token_encrypted, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    owner_id,
                    bot_telegram_id,
                    username,
                    first_name,
                    bot_type,
                    token_encrypted,
                    status,
                    now,
                    now
                )
            )
            
            await self._conn.commit()
            bot_id = cursor.lastrowid
            
            logger.info(
                f"✅ ربات ثبت شد: ID={bot_id}, bot_telegram_id={bot_telegram_id}, "
                f"username=@{username}, owner={owner_id}"
            )
            
            return bot_id
        
        except (aiosqlite.IntegrityError, sqlite3.IntegrityError) as e:
            # مدیریت خطای UNIQUE constraint (Race Condition)
            # این خطا زمانی رخ می‌دهد که bot_telegram_id تکراری باشد
            logger.warning(
                f"⚠️ تلاش برای ثبت مجدد ربات: bot_telegram_id={bot_telegram_id}, "
                f"owner={owner_id}"
            )
            
            # پرتاب خطای اختصاصی برای مدیریت در لایه بالاتر
            raise TokenAlreadyRegisteredError(
                bot_id=bot_telegram_id,
                username=username
            )
        
        except Exception as e:
            logger.error(f"❌ خطا در ثبت ربات: {e}", exc_info=True)
            raise
    
    async def get_bot_by_telegram_id(self, bot_telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات ربات با استفاده از Telegram ID
        
        Args:
            bot_telegram_id: ID تلگرام ربات
            
        Returns:
            Dict شامل اطلاعات ربات یا None اگر یافت نشود
        """
        try:
            cursor = await self._conn.execute(
                """
                SELECT 
                    id, owner_id, bot_telegram_id, username, first_name,
                    bot_type, token_encrypted, status, created_at, updated_at
                FROM bots
                WHERE bot_telegram_id = ?
                """,
                (bot_telegram_id,)
            )
            
            row = await cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'owner_id': row[1],
                    'bot_telegram_id': row[2],
                    'username': row[3],
                    'first_name': row[4],
                    'bot_type': row[5],
                    'token_encrypted': row[6],
                    'status': row[7],
                    'created_at': row[8],
                    'updated_at': row[9]
                }
            
            return None
        
        except Exception as e:
            logger.error(f"❌ خطا در جستجوی ربات: {e}", exc_info=True)
            raise
    
    async def get_bots_by_owner(self, owner_id: int) -> List[Dict[str, Any]]:
        """
        دریافت لیست ربات‌های یک کاربر
        
        Args:
            owner_id: ID کاربر تلگرام
            
        Returns:
            لیست Dict‌های حاوی اطلاعات ربات‌ها
        """
        try:
            cursor = await self._conn.execute(
                """
                SELECT 
                    id, owner_id, bot_telegram_id, username, first_name,
                    bot_type, token_encrypted, status, created_at, updated_at
                FROM bots
                WHERE owner_id = ?
                ORDER BY created_at DESC
                """,
                (owner_id,)
            )
            
            rows = await cursor.fetchall()
            
            return [
                {
                    'id': row[0],
                    'owner_id': row[1],
                    'bot_telegram_id': row[2],
                    'username': row[3],
                    'first_name': row[4],
                    'bot_type': row[5],
                    'token_encrypted': row[6],
                    'status': row[7],
                    'created_at': row[8],
                    'updated_at': row[9]
                }
                for row in rows
            ]
        
        except Exception as e:
            logger.error(f"❌ خطا در دریافت لیست ربات‌ها: {e}", exc_info=True)
            raise
    
    async def update_bot_status(self, bot_id: int, status: str) -> bool:
        """
        به‌روزرسانی وضعیت ربات
        
        Args:
            bot_id: ID رکورد در دیتابیس
            status: وضعیت جدید
            
        Returns:
            True اگر به‌روزرسانی موفق باشد، False اگر رکورد یافت نشود
        """
        try:
            now = datetime.utcnow().isoformat()
            
            cursor = await self._conn.execute(
                """
                UPDATE bots
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, now, bot_id)
            )
            
            await self._conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"✅ وضعیت ربات به‌روز شد: ID={bot_id}, status={status}")
                return True
            else:
                logger.warning(f"⚠️ ربات با ID={bot_id} یافت نشد")
                return False
        
        except Exception as e:
            logger.error(f"❌ خطا در به‌روزرسانی وضعیت ربات: {e}", exc_info=True)
            raise
    
    async def delete_bot(self, bot_id: int) -> bool:
        """
        حذف ربات از دیتابیس
        
        Args:
            bot_id: ID رکورد در دیتابیس
            
        Returns:
            True اگر حذف موفق باشد، False اگر رکورد یافت نشود
        """
        try:
            cursor = await self._conn.execute(
                "DELETE FROM bots WHERE id = ?",
                (bot_id,)
            )
            
            await self._conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"✅ ربات حذف شد: ID={bot_id}")
                return True
            else:
                logger.warning(f"⚠️ ربات با ID={bot_id} یافت نشد")
                return False
        
        except Exception as e:
            logger.error(f"❌ خطا در حذف ربات: {e}", exc_info=True)
            raise
    
    async def count_bots_by_owner(self, owner_id: int) -> int:
        """
        شمارش تعداد ربات‌های یک کاربر
        
        Args:
            owner_id: ID کاربر تلگرام
            
        Returns:
            تعداد ربات‌های کاربر
        """
        try:
            cursor = await self._conn.execute(
                "SELECT COUNT(*) FROM bots WHERE owner_id = ?",
                (owner_id,)
            )
            
            row = await cursor.fetchone()
            return row[0] if row else 0
        
        except Exception as e:
            logger.error(f"❌ خطا در شمارش ربات‌ها: {e}", exc_info=True)
            raise
