"""
سرویس مدیریت ادمین‌ها و آمار سیستم
"""
import logging
from typing import List, Dict, Optional
import aiosqlite

logger = logging.getLogger(__name__)


class AdminService:
    """
    سرویس مدیریت ادمین‌ها و نمایش آمار کلی سیستم
    """
    
    def __init__(self, connection: aiosqlite.Connection, admin_user_id: int):
        """
        Args:
            connection: اتصال به پایگاه داده
            admin_user_id: آیدی ادمین اصلی که غیرقابل حذف است
        """
        self._conn = connection
        self._admin_user_id = admin_user_id
    
    async def is_admin(self, user_id: int) -> bool:
        """
        بررسی اینکه آیا user_id در جدول admins وجود دارد یا خیر
        
        Args:
            user_id: شناسه کاربر تلگرام
            
        Returns:
            True اگر ادمین باشد، در غیر این صورت False
        """
        try:
            cursor = await self._conn.execute(
                "SELECT user_id FROM admins WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"❌ خطا در بررسی ادمین بودن: {e}", exc_info=True)
            return False
    
    async def get_stats(self) -> Dict[str, int]:
        """
        دریافت آمار کلی سیستم
        
        Returns:
            dict با کلیدهای:
            - total_users: تعداد کل کاربران
            - total_bots: تعداد کل ربات‌ها
            - active_bots: تعداد ربات‌های فعال
            - total_revenue: مجموع درآمد (تراکنش‌های debit)
            - pending_receipts: تعداد فیش‌های در انتظار
        """
        try:
            stats = {
                'total_users': 0,
                'total_bots': 0,
                'active_bots': 0,
                'total_revenue': 0,
                'pending_receipts': 0
            }
            
            # تعداد کاربران
            cursor = await self._conn.execute("SELECT COUNT(*) FROM users")
            result = await cursor.fetchone()
            stats['total_users'] = result[0] if result else 0
            
            # تعداد کل ربات‌ها
            cursor = await self._conn.execute("SELECT COUNT(*) FROM bots")
            result = await cursor.fetchone()
            stats['total_bots'] = result[0] if result else 0
            
            # تعداد ربات‌های فعال
            cursor = await self._conn.execute(
                "SELECT COUNT(*) FROM bots WHERE status = 'active'"
            )
            result = await cursor.fetchone()
            stats['active_bots'] = result[0] if result else 0
            
            # مجموع درآمد (تراکنش‌های debit)
            cursor = await self._conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'debit'"
            )
            result = await cursor.fetchone()
            stats['total_revenue'] = result[0] if result else 0
            
            # تعداد فیش‌های در انتظار
            cursor = await self._conn.execute(
                "SELECT COUNT(*) FROM deposit_requests WHERE status = 'pending'"
            )
            result = await cursor.fetchone()
            stats['pending_receipts'] = result[0] if result else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت آمار سیستم: {e}", exc_info=True)
            return {
                'total_users': 0,
                'total_bots': 0,
                'active_bots': 0,
                'total_revenue': 0,
                'pending_receipts': 0
            }
    
    async def get_all_admins(self) -> List[Dict[str, any]]:
        """
        دریافت لیست تمام ادمین‌ها
        
        Returns:
            لیستی از dict‌ها با اطلاعات ادمین‌ها
        """
        try:
            cursor = await self._conn.execute(
                "SELECT user_id, added_by, created_at FROM admins ORDER BY created_at ASC"
            )
            rows = await cursor.fetchall()
            
            admins = []
            for row in rows:
                admins.append({
                    'user_id': row[0],
                    'added_by': row[1],
                    'created_at': row[2]
                })
            
            return admins
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت لیست ادمین‌ها: {e}", exc_info=True)
            return []
    
    async def add_admin(self, user_id: int, added_by: int) -> bool:
        """
        افزودن ادمین جدید
        
        ⚠️ BUSINESS RULE: این متد خود را محافظت می‌کند و به handler وابسته نیست
        
        Args:
            user_id: شناسه کاربر جدید
            added_by: شناسه کاربری که ادمین را اضافه می‌کند
            
        Returns:
            True در صورت موفقیت، False اگر قبلاً وجود داشت یا خطا رخ داد
        """
        try:
            # ⚠️ SECURITY: فقط ادمین‌ها می‌توانند ادمین اضافه کنند
            if not await self.is_admin(added_by):
                logger.warning(
                    f"⚠️ تلاش غیرمجاز برای افزودن ادمین توسط {added_by}"
                )
                return False
            
            # بررسی اینکه قبلاً وجود نداشته باشد
            if await self.is_admin(user_id):
                return False
            
            # افزودن ادمین جدید
            await self._conn.execute(
                """
                INSERT INTO admins (user_id, added_by, created_at)
                VALUES (?, ?, datetime('now'))
                """,
                (user_id, added_by)
            )
            await self._conn.commit()
            
            logger.info(f"✅ ادمین جدید اضافه شد: {user_id} توسط {added_by}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در افزودن ادمین: {e}", exc_info=True)
            return False
    
    async def remove_admin(self, user_id: int, requester_id: int) -> bool:
        """
        حذف ادمین
        
        ⚠️ BUSINESS RULE: این متد خود را محافظت می‌کند و به handler وابسته نیست
        
        Args:
            user_id: شناسه کاربر
            requester_id: شناسه کسی که درخواست حذف می‌دهد
            
        Returns:
            True در صورت موفقیت، False اگر ادمین اصلی بود یا خطا رخ داد
        """
        try:
            # ⚠️ SECURITY: فقط ادمین‌ها می‌توانند ادمین حذف کنند
            if not await self.is_admin(requester_id):
                logger.warning(
                    f"⚠️ تلاش غیرمجاز برای حذف ادمین توسط {requester_id}"
                )
                return False
            
            # ⚠️ CRITICAL: ادمین اصلی غیرقابل حذف است
            if user_id == self._admin_user_id:
                logger.warning(f"⚠️ تلاش برای حذف ادمین اصلی: {user_id}")
                return False
            
            # ⚠️ BUSINESS RULE: کاربر نمی‌تواند خودش را حذف کند
            if user_id == requester_id:
                logger.warning(f"⚠️ تلاش برای حذف خود توسط {user_id}")
                return False
            
            # حذف ادمین
            cursor = await self._conn.execute(
                "DELETE FROM admins WHERE user_id = ?",
                (user_id,)
            )
            await self._conn.commit()
            
            # بررسی اینکه واقعاً حذف شده باشد
            if cursor.rowcount > 0:
                logger.info(f"✅ ادمین حذف شد: {user_id} توسط {requester_id}")
                return True
            else:
                logger.warning(f"⚠️ ادمین برای حذف یافت نشد: {user_id}")
                return False
            
        except Exception as e:
            logger.error(f"❌ خطا در حذف ادمین: {e}", exc_info=True)
            return False
    
    async def ensure_main_admin_exists(self) -> None:
        """
        اطمینان از وجود ادمین اصلی در جدول admins
        این متد در startup صدا زده می‌شود
        """
        try:
            await self._conn.execute(
                """
                INSERT OR IGNORE INTO admins (user_id, added_by, created_at)
                VALUES (?, ?, datetime('now'))
                """,
                (self._admin_user_id, self._admin_user_id)
            )
            await self._conn.commit()
            logger.info(f"✅ ادمین اصلی تضمین شد: {self._admin_user_id}")
            
        except Exception as e:
            logger.error(f"❌ خطا در تضمین ادمین اصلی: {e}", exc_info=True)
