"""
FTP Storage Provider

مسئولیت: پیاده‌سازی storage با استفاده از FTP

Features:
- Passive FTP mode
- Binary transfer mode
- Streaming upload (مناسب برای فایل‌های بزرگ)
- Auto-create directories
- Safe connection handling
- Progress reporting

Security:
- هیچ log برای password
- هیچ credential در exceptions
- اعتبارسنجی paths
"""
import os
import json
import ftplib
import logging
import asyncio
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime, timedelta

from .base import StorageProvider, StoredFile
from .config import storage_config
from .exceptions import (
    StorageConnectionError,
    StorageUploadError,
    StorageDeleteError,
    StorageFileTooLargeError
)
from .filename_utils import FilenameGenerator

logger = logging.getLogger(__name__)


class FTPStorageProvider(StorageProvider):
    """
    FTP Storage Provider
    
    پیاده‌سازی storage با FTP برای hostهای ایرانی
    
    Features:
    - Passive mode (برای firewall)
    - Binary mode (برای فایل‌های binary)
    - Streaming upload (بدون load کامل در RAM)
    - Metadata tracking (برای TTL)
    """
    
    def __init__(self):
        """مقداردهی اولیه FTP provider"""
        self.config = storage_config
        
        if not self.config.is_configured:
            logger.warning("⚠️ FTP Storage Provider: Not configured")
            return
        
        self.filename_generator = FilenameGenerator()
        
        logger.info("✅ FTP Storage Provider initialized")
    
    def _connect(self) -> ftplib.FTP:
        """
        ایجاد اتصال به FTP server
        
        Returns:
            FTP connection object
            
        Raises:
            StorageConnectionError: خطا در اتصال
        """
        try:
            # ساخت اتصال
            ftp = ftplib.FTP()
            
            # اتصال به server
            logger.debug(f"Connecting to FTP: {self.config.ftp_host}:{self.config.ftp_port}")
            ftp.connect(
                host=self.config.ftp_host,
                port=self.config.ftp_port,
                timeout=30
            )
            
            # Login (بدون log کردن password)
            logger.debug(f"FTP Login as: {self.config.ftp_username}")
            ftp.login(
                user=self.config.ftp_username,
                passwd=self.config.ftp_password
            )
            
            # Passive mode
            ftp.set_pasv(True)
            
            # Binary mode
            ftp.voidcmd('TYPE I')
            
            logger.debug("✅ FTP connected")
            
            return ftp
        
        except ftplib.error_perm as e:
            logger.error(f"❌ FTP Permission Error: {e}")
            raise StorageConnectionError(
                f"FTP authentication failed. Check credentials."
            )
        
        except (OSError, ftplib.Error) as e:
            logger.error(f"❌ FTP Connection Error: {type(e).__name__}")
            raise StorageConnectionError(
                f"Failed to connect to FTP server: {type(e).__name__}"
            )
    
    def _ensure_directory(self, ftp: ftplib.FTP, remote_path: str):
        """
        اطمینان از وجود directory در FTP
        
        Args:
            ftp: FTP connection
            remote_path: مسیر remote
        """
        if not remote_path or remote_path == '/':
            return
        
        # تبدیل به parts
        parts = remote_path.strip('/').split('/')
        current = ''
        
        for part in parts:
            current = f"{current}/{part}"
            
            try:
                # تلاش برای تغییر به directory
                ftp.cwd(current)
            except ftplib.error_perm:
                # directory وجود ندارد، ساخت آن
                try:
                    logger.debug(f"Creating FTP directory: {current}")
                    ftp.mkd(current)
                    ftp.cwd(current)
                except ftplib.error_perm as e:
                    logger.warning(f"⚠️ Cannot create directory {current}: {e}")
    
    async def upload_file(
        self,
        local_path: str,
        original_filename: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> StoredFile:
        """
        آپلود فایل به FTP storage
        
        Args:
            local_path: مسیر فایل محلی
            original_filename: نام اصلی فایل
            progress_callback: Callback برای Progress
            
        Returns:
            StoredFile
            
        Raises:
            StorageUploadError: خطا در آپلود
            StorageFileTooLargeError: فایل بزرگتر از حد مجاز
        """
        # بررسی وجود فایل
        if not os.path.exists(local_path):
            raise StorageUploadError(f"Local file not found: {local_path}")
        
        # بررسی حجم فایل
        file_size = os.path.getsize(local_path)
        if file_size > self.config.max_file_size_bytes:
            raise StorageFileTooLargeError(
                file_size,
                self.config.max_file_size_bytes
            )
        
        # ساخت نام فایل امن
        safe_filename = self.filename_generator.generate_safe_filename(
            original_filename
        )
        
        logger.info(f"📤 Uploading: {original_filename} → {safe_filename}")
        logger.info(f"📊 Size: {file_size / (1024*1024):.2f} MB")
        
        ftp = None
        uploaded_bytes = 0
        
        try:
            # اتصال به FTP
            ftp = await asyncio.to_thread(self._connect)
            
            # اطمینان از وجود directory
            if self.config.ftp_base_path:
                await asyncio.to_thread(
                    self._ensure_directory,
                    ftp,
                    self.config.ftp_base_path
                )
                await asyncio.to_thread(ftp.cwd, self.config.ftp_base_path)
            
            # Callback برای Progress
            def upload_callback(chunk: bytes):
                nonlocal uploaded_bytes
                uploaded_bytes += len(chunk)
                
                if progress_callback:
                    try:
                        progress_callback(uploaded_bytes, file_size)
                    except Exception as e:
                        logger.warning(f"⚠️ Progress callback error: {e}")
            
            # آپلود فایل (streaming)
            with open(local_path, 'rb') as f:
                await asyncio.to_thread(
                    ftp.storbinary,
                    f'STOR {safe_filename}',
                    f,
                    callback=upload_callback,
                    blocksize=8192
                )
            
            logger.info(f"✅ Upload complete: {safe_filename}")
            
            # ذخیره metadata
            await self._save_metadata(
                ftp,
                safe_filename,
                original_filename,
                file_size
            )
            
            # ساخت StoredFile
            uploaded_at = datetime.utcnow()
            expires_at = uploaded_at + timedelta(seconds=self.config.ttl_seconds)
            
            stored_file = StoredFile(
                filename=safe_filename,
                original_filename=original_filename,
                public_url=self.generate_public_url(safe_filename),
                size=file_size,
                uploaded_at=uploaded_at,
                expires_at=expires_at
            )
            
            return stored_file
        
        except StorageFileTooLargeError:
            raise
        
        except ftplib.Error as e:
            logger.error(f"❌ FTP Upload Error: {type(e).__name__}")
            raise StorageUploadError(
                f"FTP upload failed: {type(e).__name__}"
            )
        
        except Exception as e:
            logger.error(f"❌ Upload Error: {type(e).__name__}", exc_info=True)
            raise StorageUploadError(
                f"Upload failed: {type(e).__name__}"
            )
        
        finally:
            if ftp:
                try:
                    await asyncio.to_thread(ftp.quit)
                except Exception:
                    pass
    
    async def _save_metadata(
        self,
        ftp: ftplib.FTP,
        filename: str,
        original_filename: str,
        size: int
    ):
        """
        ذخیره metadata فایل
        
        Args:
            ftp: FTP connection
            filename: نام فایل در storage
            original_filename: نام اصلی
            size: حجم فایل
        """
        try:
            metadata = {
                'filename': filename,
                'original_filename': original_filename,
                'size': size,
                'uploaded_at': datetime.utcnow().isoformat(),
                'expires_at': (
                    datetime.utcnow() +
                    timedelta(seconds=self.config.ttl_seconds)
                ).isoformat()
            }
            
            metadata_filename = self.filename_generator.get_metadata_filename(
                filename
            )
            
            # آپلود metadata
            metadata_json = json.dumps(metadata, indent=2)
            metadata_bytes = metadata_json.encode('utf-8')
            
            from io import BytesIO
            metadata_file = BytesIO(metadata_bytes)
            
            await asyncio.to_thread(
                ftp.storbinary,
                f'STOR {metadata_filename}',
                metadata_file
            )
            
            logger.debug(f"✅ Metadata saved: {metadata_filename}")
        
        except Exception as e:
            # metadata failure نباید upload را fail کند
            logger.warning(f"⚠️ Failed to save metadata: {e}")
    
    async def delete_file(self, filename: str) -> bool:
        """
        حذف فایل از FTP
        
        Args:
            filename: نام فایل
            
        Returns:
            True اگر حذف شد
        """
        # اعتبارسنجی نام فایل
        if not self.filename_generator.validate_filename(filename):
            logger.warning(f"⚠️ Invalid filename: {filename}")
            return False
        
        ftp = None
        
        try:
            ftp = await asyncio.to_thread(self._connect)
            
            if self.config.ftp_base_path:
                await asyncio.to_thread(ftp.cwd, self.config.ftp_base_path)
            
            # حذف فایل اصلی
            try:
                await asyncio.to_thread(ftp.delete, filename)
                logger.info(f"🗑 Deleted: {filename}")
            except ftplib.error_perm:
                logger.debug(f"File not found: {filename}")
                return False
            
            # حذف metadata
            metadata_filename = self.filename_generator.get_metadata_filename(
                filename
            )
            try:
                await asyncio.to_thread(ftp.delete, metadata_filename)
            except ftplib.error_perm:
                pass  # metadata نبود
            
            return True
        
        except ftplib.Error as e:
            logger.error(f"❌ FTP Delete Error: {type(e).__name__}")
            raise StorageDeleteError(
                f"FTP delete failed: {type(e).__name__}"
            )
        
        finally:
            if ftp:
                try:
                    await asyncio.to_thread(ftp.quit)
                except Exception:
                    pass
    
    async def file_exists(self, filename: str) -> bool:
        """بررسی وجود فایل"""
        if not self.filename_generator.validate_filename(filename):
            return False
        
        ftp = None
        
        try:
            ftp = await asyncio.to_thread(self._connect)
            
            if self.config.ftp_base_path:
                await asyncio.to_thread(ftp.cwd, self.config.ftp_base_path)
            
            # تلاش برای دریافت size
            await asyncio.to_thread(ftp.size, filename)
            return True
        
        except ftplib.error_perm:
            return False
        
        finally:
            if ftp:
                try:
                    await asyncio.to_thread(ftp.quit)
                except Exception:
                    pass
    
    def generate_public_url(self, filename: str) -> str:
        """ساخت URL عمومی"""
        base_url = self.config.public_base_url.rstrip('/')
        return f"{base_url}/{filename}"
    
    async def cleanup_expired_files(self) -> int:
        """حذف فایل‌های منقضی شده"""
        logger.info("🧹 Starting cleanup of expired files...")
        
        deleted_count = 0
        ftp = None
        
        try:
            ftp = await asyncio.to_thread(self._connect)
            
            if self.config.ftp_base_path:
                await asyncio.to_thread(ftp.cwd, self.config.ftp_base_path)
            
            # دریافت لیست فایل‌ها
            files = await asyncio.to_thread(ftp.nlst)
            
            # فیلتر metadata files
            data_files = [f for f in files if not f.endswith('.meta')]
            
            logger.info(f"Found {len(data_files)} files to check")
            
            # بررسی هر فایل
            for filename in data_files:
                try:
                    # خواندن metadata
                    metadata = await self._read_metadata(ftp, filename)
                    
                    if metadata:
                        expires_at = datetime.fromisoformat(
                            metadata['expires_at']
                        )
                        
                        if datetime.utcnow() > expires_at:
                            # فایل منقضی شده
                            logger.info(f"🗑 Deleting expired: {filename}")
                            await asyncio.to_thread(ftp.delete, filename)
                            
                            # حذف metadata
                            meta_file = self.filename_generator.get_metadata_filename(
                                filename
                            )
                            try:
                                await asyncio.to_thread(ftp.delete, meta_file)
                            except Exception:
                                pass
                            
                            deleted_count += 1
                
                except Exception as e:
                    logger.warning(
                        f"⚠️ Error processing {filename}: {type(e).__name__}"
                    )
                    # ادامه با فایل بعدی
            
            logger.info(f"✅ Cleanup complete: {deleted_count} files deleted")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"❌ Cleanup error: {type(e).__name__}", exc_info=True)
            return deleted_count
        
        finally:
            if ftp:
                try:
                    await asyncio.to_thread(ftp.quit)
                except Exception:
                    pass
    
    async def _read_metadata(
        self,
        ftp: ftplib.FTP,
        filename: str
    ) -> Optional[dict]:
        """خواندن metadata فایل"""
        try:
            metadata_filename = self.filename_generator.get_metadata_filename(
                filename
            )
            
            from io import BytesIO
            metadata_file = BytesIO()
            
            await asyncio.to_thread(
                ftp.retrbinary,
                f'RETR {metadata_filename}',
                metadata_file.write
            )
            
            metadata_file.seek(0)
            metadata_json = metadata_file.read().decode('utf-8')
            
            return json.loads(metadata_json)
        
        except Exception:
            return None
    
    async def list_files(self) -> list[StoredFile]:
        """لیست تمام فایل‌ها"""
        files = []
        ftp = None
        
        try:
            ftp = await asyncio.to_thread(self._connect)
            
            if self.config.ftp_base_path:
                await asyncio.to_thread(ftp.cwd, self.config.ftp_base_path)
            
            file_list = await asyncio.to_thread(ftp.nlst)
            data_files = [f for f in file_list if not f.endswith('.meta')]
            
            for filename in data_files:
                metadata = await self._read_metadata(ftp, filename)
                
                if metadata:
                    files.append(StoredFile(
                        filename=filename,
                        original_filename=metadata['original_filename'],
                        public_url=self.generate_public_url(filename),
                        size=metadata['size'],
                        uploaded_at=datetime.fromisoformat(
                            metadata['uploaded_at']
                        ),
                        expires_at=datetime.fromisoformat(
                            metadata['expires_at']
                        )
                    ))
        
        finally:
            if ftp:
                try:
                    await asyncio.to_thread(ftp.quit)
                except Exception:
                    pass
        
        return files
