"""
پکیج handlers - شامل تمام handler های ربات
"""
from .start import router as start_router
from .bot_maker import router as bot_maker_router
from .wallet import router as wallet_router

# لیست تمام routerها برای ثبت در dispatcher
__all__ = ['start_router', 'bot_maker_router', 'wallet_router']
