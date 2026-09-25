"""
Basic Import and Smoke Tests for File Transfer

تست‌های اولیه برای اطمینان از صحت import و basic functionality
"""
import pytest


def test_import_file_transfer_service():
    """تست: import سرویس"""
    from services.file_transfer_service import FileTransferService
    assert FileTransferService is not None


def test_import_progress_tracker():
    """تست: import ProgressTracker"""
    from services.progress_tracker import ProgressTracker
    assert ProgressTracker is not None


def test_import_filename_detector():
    """تست: import FilenameDetector"""
    from utils.filename_detector import FilenameDetector
    assert FilenameDetector is not None


def test_import_file_transfer_handler():
    """تست: import Handler"""
    from handlers.child_bots.file_transfer import get_router
    assert get_router is not None


def test_import_exceptions():
    """تست: import Exceptions"""
    from services.file_transfer_service import (
        FileTransferError,
        HostNotConfiguredError,
        InvalidURLError,
        FileTooLargeError,
        DownloadError
    )
    assert FileTransferError is not None
    assert HostNotConfiguredError is not None
    assert InvalidURLError is not None
    assert FileTooLargeError is not None
    assert DownloadError is not None


def test_file_transfer_service_instantiation():
    """تست: ساخت instance از service"""
    from services.file_transfer_service import FileTransferService
    service = FileTransferService(timeout=10)
    assert service is not None
    assert service.timeout.total == 10


def test_progress_tracker_instantiation():
    """تست: ساخت instance از ProgressTracker"""
    from unittest.mock import Mock
    from services.progress_tracker import ProgressTracker
    
    mock_message = Mock()
    tracker = ProgressTracker(mock_message, operation="download")
    assert tracker is not None
    assert tracker.operation == "download"


def test_filename_detector_static_method():
    """تست: متد static FilenameDetector"""
    from utils.filename_detector import FilenameDetector
    
    url = "https://example.com/file.pdf"
    filename = FilenameDetector.detect_filename(url)
    assert filename == "file.pdf"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
