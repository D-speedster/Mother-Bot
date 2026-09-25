"""
Storage Cleanup Script

این script فایل‌های منقضی شده را از FTP storage حذف می‌کند.

Usage:
    python cleanup_storage.py

Cron Job (هر 1 ساعت):
    0 * * * * cd /path/to/mother-bot && python cleanup_storage.py >> cleanup.log 2>&1
"""
import asyncio
import logging
import sys
from services.storage import StorageService, StorageDisabledError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main cleanup function"""
    logger.info("🧹 Starting storage cleanup...")
    
    try:
        storage = StorageService()
        
        if not storage.is_enabled:
            logger.warning("⚠️ Storage is disabled - nothing to clean")
            return
        
        # Cleanup expired files
        deleted_count = await storage.cleanup_expired()
        
        logger.info(f"✅ Cleanup complete: {deleted_count} files deleted")
        
    except StorageDisabledError:
        logger.warning("⚠️ Storage is disabled")
    
    except Exception as e:
        logger.error(f"❌ Cleanup error: {type(e).__name__}: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
