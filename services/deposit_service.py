"""
سرویس مدیریت درخواست‌های شارژ کیف پول (فیش‌های واریزی)
"""
import logging
import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class DepositService:
    """
    سرویس مدیریت درخواست‌های شارژ کیف پول
    
    Features:
    - ثبت درخواست شارژ جدید
    - دریافت درخواست‌های pending
    - تأیید/رد درخواست
    - مدیریت فیش‌های واریزی
    """
    
    def __init__(self, connection: aiosqlite.Connection):
        """
        Args:
            connection: اتصال aiosqlite
        """
        self._conn = connection
    
    async def create_deposit_request(
        self,
        user_id: int,
        amount: int,
        receipt_photo_id: Optional[str] = None,
        tracking_code: Optional[str] = None
    ) -> int:
        """
        ثبت درخواست شارژ جدید
        
        Args:
            user_id: ID کاربر تلگرام
            amount: مبلغ درخواستی (تومان)
            receipt_photo_id: شناسه عکس فیش در تلگرام
            tracking_code: شماره پیگیری (اختیاری)
            
        Returns:
            ID درخواست ایجادشده
            
        Raises:
            ValueError: اگر مبلغ منفی یا صفر باشد
        """
        if amount <= 0:
            raise ValueError("مبلغ باید بزرگتر از صفر باشد")
        
        if not receipt_photo_id and not tracking_code:
            raise ValueError("حداقل یکی از فیش یا کد پیگیری باید ارسال شود")
        
        try:
            now = datetime.utcnow().isoformat()
            
            cursor = await self._conn.execute(
                """
                INSERT INTO deposit_requests 
                (user_id, amount, receipt_photo_id, tracking_code, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
                """,
                (user_id, amount, receipt_photo_id, tracking_code, now, now)
            )
            
            await self._conn.commit()
            request_id = cursor.lastrowid
            
            logger.info(
                f"✅ درخواست شارژ جدید ثبت شد: ID={request_id}, "
                f"کاربر={user_id}, مبلغ={amount:,} تومان"
            )
            
            return request_id
        
        except Exception as e:
            logger.error(
                f"❌ خطا در ثبت درخواست شارژ: {e}",
                exc_info=True
            )
            raise
    
    async def get_pending_requests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        دریافت درخواست‌های در انتظار تأیید
        
        Args:
            limit: تعداد درخواست‌های برگشتی
            
        Returns:
            لیست درخواست‌های pending
        """
        try:
            cursor = await self._conn.execute(
                """
                SELECT id, user_id, amount, receipt_photo_id, tracking_code, 
                       status, created_at, updated_at
                FROM deposit_requests
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (limit,)
            )
            
            rows = await cursor.fetchall()
            
            requests = [
                {
                    'id': row[0],
                    'user_id': row[1],
                    'amount': row[2],
                    'receipt_photo_id': row[3],
                    'tracking_code': row[4],
                    'status': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                }
                for row in rows
            ]
            
            logger.info(f"✅ دریافت {len(requests)} درخواست pending")
            
            return requests
        
        except Exception as e:
            logger.error(
                f"❌ خطا در دریافت درخواست‌های pending: {e}",
                exc_info=True
            )
            raise
    
    async def get_request_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات یک درخواست خاص
        
        Args:
            request_id: ID درخواست
            
        Returns:
            اطلاعات درخواست یا None
        """
        try:
            cursor = await self._conn.execute(
                """
                SELECT id, user_id, amount, receipt_photo_id, tracking_code, 
                       status, admin_note, created_at, updated_at
                FROM deposit_requests
                WHERE id = ?
                """,
                (request_id,)
            )
            
            row = await cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'amount': row[2],
                    'receipt_photo_id': row[3],
                    'tracking_code': row[4],
                    'status': row[5],
                    'admin_note': row[6],
                    'created_at': row[7],
                    'updated_at': row[8]
                }
            
            return None
        
        except Exception as e:
            logger.error(
                f"❌ خطا در دریافت درخواست {request_id}: {e}",
                exc_info=True
            )
            raise
    
    async def approve_request_atomic(
        self,
        request_id: int,
        admin_note: Optional[str] = None
    ) -> Dict[str, any]:
        """
        تأیید درخواست شارژ به صورت اتمیک
        
        این متد تغییر وضعیت را انجام می‌دهد و اطلاعات لازم برای شارژ کیف پول را برمی‌گرداند.
        فقط یک ادمین می‌تواند این درخواست را تأیید کند (با شرط WHERE status = 'pending')
        
        Args:
            request_id: ID درخواست
            admin_note: یادداشت ادمین (اختیاری)
            
        Returns:
            dict با کلیدهای:
            - success: True/False
            - user_id: شناسه کاربر (در صورت موفقیت)
            - amount: مبلغ (در صورت موفقیت)
            - message: پیام توضیحی
        """
        try:
            now = datetime.utcnow().isoformat()
            
            # ⚠️ CRITICAL: استفاده از UPDATE با WHERE status = 'pending'
            # فقط اگر وضعیت pending باشد تغییر می‌کند
            cursor = await self._conn.execute(
                """
                UPDATE deposit_requests
                SET status = 'approved', admin_note = ?, updated_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (admin_note, now, request_id)
            )
            
            await self._conn.commit()
            
            # بررسی تعداد ردیف‌های تغییر یافته
            if cursor.rowcount == 0:
                logger.warning(
                    f"⚠️ درخواست {request_id} قبلاً پردازش شده یا یافت نشد"
                )
                return {
                    'success': False,
                    'message': 'این درخواست قبلاً پردازش شده است'
                }
            
            # دریافت اطلاعات درخواست
            cursor = await self._conn.execute(
                """
                SELECT user_id, amount
                FROM deposit_requests
                WHERE id = ?
                """,
                (request_id,)
            )
            
            row = await cursor.fetchone()
            
            if not row:
                logger.error(f"❌ خطا: درخواست {request_id} پس از تأیید یافت نشد!")
                return {
                    'success': False,
                    'message': 'خطا در دریافت اطلاعات درخواست'
                }
            
            user_id = row[0]
            amount = row[1]
            
            logger.info(
                f"✅ درخواست {request_id} تأیید شد - "
                f"کاربر={user_id}, مبلغ={amount:,}"
            )
            
            return {
                'success': True,
                'user_id': user_id,
                'amount': amount,
                'message': 'درخواست با موفقیت تأیید شد'
            }
        
        except Exception as e:
            logger.error(
                f"❌ خطا در تأیید درخواست {request_id}: {e}",
                exc_info=True
            )
            raise
    
    async def reject_request_atomic(
        self,
        request_id: int,
        admin_note: Optional[str] = None
    ) -> Dict[str, any]:
        """
        رد درخواست شارژ به صورت اتمیک
        
        Args:
            request_id: ID درخواست
            admin_note: دلیل رد (اختیاری)
            
        Returns:
            dict با کلیدهای:
            - success: True/False
            - user_id: شناسه کاربر (در صورت موفقیت)
            - amount: مبلغ (در صورت موفقیت)
            - message: پیام توضیحی
        """
        try:
            now = datetime.utcnow().isoformat()
            
            # ⚠️ CRITICAL: استفاده از UPDATE با WHERE status = 'pending'
            cursor = await self._conn.execute(
                """
                UPDATE deposit_requests
                SET status = 'rejected', admin_note = ?, updated_at = ?
                WHERE id = ? AND status = 'pending'
                """,
                (admin_note, now, request_id)
            )
            
            await self._conn.commit()
            
            # بررسی تعداد ردیف‌های تغییر یافته
            if cursor.rowcount == 0:
                logger.warning(
                    f"⚠️ درخواست {request_id} قبلاً پردازش شده یا یافت نشد"
                )
                return {
                    'success': False,
                    'message': 'این درخواست قبلاً پردازش شده است'
                }
            
            # دریافت اطلاعات درخواست
            cursor = await self._conn.execute(
                """
                SELECT user_id, amount
                FROM deposit_requests
                WHERE id = ?
                """,
                (request_id,)
            )
            
            row = await cursor.fetchone()
            
            if not row:
                logger.error(f"❌ خطا: درخواست {request_id} پس از رد یافت نشد!")
                return {
                    'success': False,
                    'message': 'خطا در دریافت اطلاعات درخواست'
                }
            
            user_id = row[0]
            amount = row[1]
            
            logger.info(
                f"✅ درخواست {request_id} رد شد - "
                f"کاربر={user_id}, مبلغ={amount:,}"
            )
            
            return {
                'success': True,
                'user_id': user_id,
                'amount': amount,
                'message': 'درخواست با موفقیت رد شد'
            }
        
        except Exception as e:
            logger.error(
                f"❌ خطا در رد درخواست {request_id}: {e}",
                exc_info=True
            )
            raise
    
    async def get_user_requests(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        دریافت درخواست‌های یک کاربر
        
        Args:
            user_id: ID کاربر تلگرام
            limit: تعداد درخواست‌های برگشتی
            
        Returns:
            لیست درخواست‌های کاربر
        """
        try:
            cursor = await self._conn.execute(
                """
                SELECT id, amount, receipt_photo_id, tracking_code, 
                       status, admin_note, created_at, updated_at
                FROM deposit_requests
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit)
            )
            
            rows = await cursor.fetchall()
            
            requests = [
                {
                    'id': row[0],
                    'amount': row[1],
                    'receipt_photo_id': row[2],
                    'tracking_code': row[3],
                    'status': row[4],
                    'admin_note': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                }
                for row in rows
            ]
            
            return requests
        
        except Exception as e:
            logger.error(
                f"❌ خطا در دریافت درخواست‌های کاربر {user_id}: {e}",
                exc_info=True
            )
            raise
