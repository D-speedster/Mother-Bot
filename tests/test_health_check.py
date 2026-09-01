"""
Tests for Health Check Service

تست‌های سرویس Health Check برای Local Bot API
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.telegram import LocalBotAPIConfig, HealthCheckService
from services.telegram.health_check import HealthCheckResult
from services.exceptions import (
    TelegramAPIError,
    InvalidTokenError,
    NetworkTimeoutError
)


@pytest.fixture
def enabled_config():
    """Config با Local API فعال"""
    return LocalBotAPIConfig(
        enabled=True,
        base_url='http://localhost',
        port=8081
    )


@pytest.fixture
def disabled_config():
    """Config با Local API غیرفعال"""
    return LocalBotAPIConfig(
        enabled=False,
        base_url='http://localhost',
        port=8081
    )


@pytest.fixture
def health_service(enabled_config):
    """Health Check Service با config فعال"""
    return HealthCheckService(enabled_config)


@pytest.fixture
def mock_client(monkeypatch):
    """Mock LocalBotAPIClient"""
    mock = MagicMock()
    
    # Mock __init__ برای جلوگیری از ValueError
    def mock_init(self, config, timeout=15):
        self.config = config
        self.timeout = timeout
    
    mock.__init__ = mock_init
    
    return mock


class TestHealthCheckDisabled:
    """تست‌های Health Check برای حالت غیرفعال"""
    
    @pytest.mark.asyncio
    async def test_health_check_disabled_config(self, disabled_config):
        """
        تست: Health Check با config غیرفعال
        """
        service = HealthCheckService(disabled_config)
        result = await service.check_health('test_token')
        
        assert result.success is False
        assert result.server_reachable is False
        assert result.api_response_valid is False
        assert result.get_me_works is False
        assert result.error_type == 'disabled'
        assert 'غیرفعال' in result.message
    
    @pytest.mark.asyncio
    async def test_quick_check_disabled_config(self, disabled_config):
        """
        تست: Quick Check با config غیرفعال
        """
        service = HealthCheckService(disabled_config)
        result = await service.quick_check('test_token')
        
        assert result is False


class TestHealthCheckInvalidToken:
    """تست‌های Health Check برای توکن نامعتبر"""
    
    @pytest.mark.asyncio
    async def test_health_check_empty_token(self, health_service):
        """
        تست: Health Check با توکن خالی
        """
        result = await health_service.check_health('')
        
        assert result.success is False
        assert result.error_type == 'invalid_test_token'
        assert 'خالی' in result.message or 'نامعتبر' in result.message
    
    @pytest.mark.asyncio
    async def test_health_check_none_token(self, health_service):
        """
        تست: Health Check با None token
        """
        result = await health_service.check_health(None)
        
        assert result.success is False
        assert result.error_type == 'invalid_test_token'


class TestHealthCheckResult:
    """تست‌های HealthCheckResult dataclass"""
    
    def test_result_to_dict(self):
        """
        تست: تبدیل result به dictionary
        """
        result = HealthCheckResult(
            success=True,
            message='Success',
            server_reachable=True,
            api_response_valid=True,
            get_me_works=True,
            error_type=None,
            api_url='http://localhost:8081'
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['success'] is True
        assert result_dict['message'] == 'Success'
        assert result_dict['server_reachable'] is True
        assert result_dict['api_response_valid'] is True
        assert result_dict['get_me_works'] is True
        assert result_dict['error_type'] is None
        assert result_dict['api_url'] == 'http://localhost:8081'
    
    def test_result_to_dict_with_error(self):
        """
        تست: تبدیل result با error به dictionary
        """
        result = HealthCheckResult(
            success=False,
            message='Error',
            server_reachable=False,
            api_response_valid=False,
            get_me_works=False,
            error_type='timeout',
            api_url='http://localhost:8081'
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['success'] is False
        assert result_dict['error_type'] == 'timeout'


class TestHealthCheckErrorHandling:
    """تست‌های مدیریت خطا در Health Check"""
    
    @pytest.mark.asyncio
    async def test_health_check_handles_invalid_token_error(
        self,
        health_service,
        monkeypatch
    ):
        """
        تست: مدیریت InvalidTokenError
        """
        # Mock LocalBotAPIClient.get_me برای raise InvalidTokenError
        async def mock_get_me(token):
            raise InvalidTokenError("Invalid token")
        
        # Patch LocalBotAPIClient
        from services.telegram import local_api_client
        
        class MockClient:
            def __init__(self, config, timeout=15):
                self.config = config
            
            async def get_me(self, token):
                raise InvalidTokenError("Invalid token")
        
        monkeypatch.setattr(
            local_api_client,
            'LocalBotAPIClient',
            MockClient
        )
        
        result = await health_service.check_health('invalid_token')
        
        assert result.success is False
        assert result.error_type == 'invalid_token'
        assert result.server_reachable is True  # سرور در دسترس بود ولی token نامعتبر بود
        assert result.api_response_valid is True
        assert result.get_me_works is False
    
    @pytest.mark.asyncio
    async def test_health_check_handles_network_timeout(
        self,
        health_service,
        monkeypatch
    ):
        """
        تست: مدیریت NetworkTimeoutError
        """
        from services.telegram import local_api_client
        
        class MockClient:
            def __init__(self, config, timeout=15):
                self.config = config
            
            async def get_me(self, token):
                raise NetworkTimeoutError("Timeout")
        
        monkeypatch.setattr(
            local_api_client,
            'LocalBotAPIClient',
            MockClient
        )
        
        result = await health_service.check_health('test_token')
        
        assert result.success is False
        assert result.error_type == 'timeout'
        assert result.server_reachable is False
        assert result.get_me_works is False
    
    @pytest.mark.asyncio
    async def test_health_check_handles_api_error(
        self,
        health_service,
        monkeypatch
    ):
        """
        تست: مدیریت TelegramAPIError
        """
        from services.telegram import local_api_client
        
        class MockClient:
            def __init__(self, config, timeout=15):
                self.config = config
            
            async def get_me(self, token):
                raise TelegramAPIError("API Error", status_code=500)
        
        monkeypatch.setattr(
            local_api_client,
            'LocalBotAPIClient',
            MockClient
        )
        
        result = await health_service.check_health('test_token')
        
        assert result.success is False
        assert result.error_type == 'api_error'
        assert result.get_me_works is False
    
    @pytest.mark.asyncio
    async def test_health_check_handles_connection_error(
        self,
        health_service,
        monkeypatch
    ):
        """
        تست: مدیریت خطای اتصال (شامل "connection" در پیام)
        """
        from services.telegram import local_api_client
        
        class MockClient:
            def __init__(self, config, timeout=15):
                self.config = config
            
            async def get_me(self, token):
                raise TelegramAPIError(
                    "خطا در اتصال به Local API Server",
                    status_code=None
                )
        
        monkeypatch.setattr(
            local_api_client,
            'LocalBotAPIClient',
            MockClient
        )
        
        result = await health_service.check_health('test_token')
        
        assert result.success is False
        assert result.error_type == 'api_error'
        # باید server_reachable=False باشد چون "connection" در پیام است
        assert result.server_reachable is False
    
    @pytest.mark.asyncio
    async def test_health_check_handles_unexpected_error(
        self,
        health_service,
        monkeypatch
    ):
        """
        تست: مدیریت خطای غیرمنتظره
        """
        from services.telegram import local_api_client
        
        class MockClient:
            def __init__(self, config, timeout=15):
                self.config = config
            
            async def get_me(self, token):
                raise RuntimeError("Unexpected error")
        
        monkeypatch.setattr(
            local_api_client,
            'LocalBotAPIClient',
            MockClient
        )
        
        result = await health_service.check_health('test_token')
        
        assert result.success is False
        assert result.error_type == 'unexpected_error'


class TestHealthCheckSuccess:
    """تست‌های Health Check موفق"""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, health_service, monkeypatch):
        """
        تست: Health Check موفق با پاسخ معتبر
        """
        from services.telegram import local_api_client
        
        class MockClient:
            def __init__(self, config, timeout=15):
                self.config = config
            
            async def get_me(self, token):
                return {
                    'id': 123456789,
                    'username': 'test_bot',
                    'first_name': 'Test Bot',
                    'is_bot': True
                }
        
        monkeypatch.setattr(
            local_api_client,
            'LocalBotAPIClient',
            MockClient
        )
        
        result = await health_service.check_health('valid_token')
        
        assert result.success is True
        assert result.server_reachable is True
        assert result.api_response_valid is True
        assert result.get_me_works is True
        assert result.error_type is None
        assert 'test_bot' in result.message
    
    @pytest.mark.asyncio
    async def test_health_check_invalid_response_no_id(
        self,
        health_service,
        monkeypatch
    ):
        """
        تست: پاسخ بدون id (نامعتبر)
        """
        from services.telegram import local_api_client
        
        class MockClient:
            def __init__(self, config, timeout=15):
                self.config = config
            
            async def get_me(self, token):
                return {
                    'username': 'test_bot',
                    # 'id' وجود ندارد
                }
        
        monkeypatch.setattr(
            local_api_client,
            'LocalBotAPIClient',
            MockClient
        )
        
        result = await health_service.check_health('valid_token')
        
        assert result.success is False
        assert result.server_reachable is True
        assert result.api_response_valid is False
        assert result.get_me_works is False
        assert result.error_type == 'invalid_response'
    
    @pytest.mark.asyncio
    async def test_health_check_not_a_bot(self, health_service, monkeypatch):
        """
        تست: پاسخ با is_bot=False (حساب کاربری است، نه ربات)
        """
        from services.telegram import local_api_client
        
        class MockClient:
            def __init__(self, config, timeout=15):
                self.config = config
            
            async def get_me(self, token):
                return {
                    'id': 123456789,
                    'username': 'test_user',
                    'is_bot': False  # این یک user است
                }
        
        monkeypatch.setattr(
            local_api_client,
            'LocalBotAPIClient',
            MockClient
        )
        
        result = await health_service.check_health('user_token')
        
        assert result.success is False
        assert result.server_reachable is True
        assert result.api_response_valid is True
        assert result.get_me_works is False
        assert result.error_type == 'not_a_bot'
    
    @pytest.mark.asyncio
    async def test_quick_check_success(self, health_service, monkeypatch):
        """
        تست: Quick Check موفق
        """
        from services.telegram import local_api_client
        
        class MockClient:
            def __init__(self, config, timeout=15):
                self.config = config
            
            async def get_me(self, token):
                return {
                    'id': 123456789,
                    'username': 'test_bot',
                    'is_bot': True
                }
        
        monkeypatch.setattr(
            local_api_client,
            'LocalBotAPIClient',
            MockClient
        )
        
        result = await health_service.quick_check('valid_token')
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_quick_check_failure(self, health_service, monkeypatch):
        """
        تست: Quick Check ناموفق
        """
        from services.telegram import local_api_client
        
        class MockClient:
            def __init__(self, config, timeout=15):
                self.config = config
            
            async def get_me(self, token):
                raise NetworkTimeoutError("Timeout")
        
        monkeypatch.setattr(
            local_api_client,
            'LocalBotAPIClient',
            MockClient
        )
        
        result = await health_service.quick_check('test_token')
        
        assert result is False
