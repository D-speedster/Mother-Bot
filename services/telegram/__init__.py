"""
Telegram Services - Local Bot API Support

این ماژول لایه انتزاعی برای ارتباط با Telegram Bot API است.
از هر دو حالت Standard API و Local Bot API پشتیبانی می‌کند.

Exports:
    - LocalBotAPIClient: کلاینت برای Local Bot API Server
    - LocalBotAPIConfig: کلاس تنظیمات Local API
    - HealthCheckService: سرویس health check برای Local API
"""

from .local_api_client import LocalBotAPIClient
from .local_api_config import LocalBotAPIConfig
from .health_check import HealthCheckService

__all__ = [
    'LocalBotAPIClient',
    'LocalBotAPIConfig',
    'HealthCheckService',
]
