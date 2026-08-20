"""
لایه پایگاه داده - مدیریت اتصال و Schema
"""
import logging
import aiosqlite
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Database:
    """
    مدیریت اتصال به پایگاه داده SQLite با پشتیبانی از آسنکرون
    
    Features:
    - Write-Ahead Logging (WAL) برای بهبود عملکرد
    - Foreign Keys برای یکپارچگی داده
    - مدیریت Schema و Migration
    """
    
    def __init__(self, db_path: str = "mother_bot.db"):
        """
        Args:
            db_path: مسیر فایل پایگاه داده
        """
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        
    async def connect(self) -> None:
        """
        برقراری اتصال به پایگاه داده و تنظیم PRAGMA
        """
        if self._connection is not None:
            logger.warning("اتصال از قبل برقرار است")
            return
            
        try:
            # ساخت دایرکتوری در صورت عدم وجود
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            # اتصال به پایگاه داده
            self._connection = await aiosqlite.connect(self.db_path)
            
            # فعال‌سازی WAL mode برای بهبود عملکرد concurrent
            await self._connection.execute("PRAGMA journal_mode = WAL")
            
            # فعال‌سازی Foreign Keys برای یکپارچگی داده
            await self._connection.execute("PRAGMA foreign_keys = ON")
            
            logger.info(f"✅ اتصال به پایگاه داده برقرار شد: {self.db_path}")
            
            # ساخت جداول
            await self._create_tables()
            
        except Exception as e:
            logger.error(f"❌ خطا در اتصال به پایگاه داده: {e}", exc_info=True)
            raise
            
    async def disconnect(self) -> None:
        """
        قطع اتصال از پایگاه داده
        """
        if self._connection is not None:
            await self._connection.close()
            self._connection = None
            logger.info("✅ اتصال به پایگاه داده قطع شد")
            
    async def _create_tables(self) -> None:
        """
        ساخت جداول پایگاه داده
        """
        # جدول ربات‌ها
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                bot_telegram_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                first_name TEXT,
                bot_type TEXT NOT NULL,
                token_encrypted TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'inactive',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ایجاد Index برای بهبود کارایی جستجو
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_bots_owner_id 
            ON bots(owner_id)
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_bots_status 
            ON bots(status)
        """)
        
        await self._connection.commit()
        logger.info("✅ Schema پایگاه داده آماده است")
        
    @property
    def connection(self) -> aiosqlite.Connection:
        """
        دسترسی به Connection برای Repository
        
        Returns:
            Connection object
            
        Raises:
            RuntimeError: اگر اتصال برقرار نباشد
        """
        if self._connection is None:
            raise RuntimeError("اتصال به پایگاه داده برقرار نیست. ابتدا connect() را فراخوانی کنید")
        return self._connection
        
    async def __aenter__(self):
        """Context manager support"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        await self.disconnect()
