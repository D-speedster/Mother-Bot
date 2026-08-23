"""
Generation Service - لایه Business Logic برای تولید تصویر

این Service بین Handler و Provider واسط است
"""
import logging
from typing import Optional, Dict, Any

from .models import (
    GenerationRequest,
    GenerationResult,
    GenerationStatus,
    ImageStyle,
    AspectRatio,
    Quality
)
from .mock_provider import MockProvider

logger = logging.getLogger(__name__)


class GenerationService:
    """
    سرویس تولید تصویر
    
    مسئولیت‌ها:
    - مدیریت درخواست‌های تولید
    - ارتباط با Provider
    - Validation
    - Error Handling
    """
    
    def __init__(self):
        """
        مقداردهی اولیه سرویس
        
        در آینده Provider از config خوانده می‌شود:
        - MockProvider (development)
        - OpenAIProvider (production)
        - StabilityProvider (production)
        """
        self.provider = MockProvider()
        self._active_requests: Dict[str, GenerationRequest] = {}
        # برای Session-based history (بدون Database)
        self._user_history: Dict[int, list] = {}
    
    async def create_generation(
        self,
        user_id: int,
        prompt: str,
        style: ImageStyle = ImageStyle.NONE,
        aspect_ratio: AspectRatio = AspectRatio.SQUARE,
        quality: Quality = Quality.STANDARD,
        count: int = 1
    ) -> GenerationRequest:
        """
        ایجاد درخواست جدید
        
        Args:
            user_id: شناسه کاربر
            prompt: توضیحات تصویر
            style: سبک تصویر
            aspect_ratio: نسبت تصویر
            quality: کیفیت
            count: تعداد تصاویر
            
        Returns:
            GenerationRequest
            
        Raises:
            ValueError: اگر Prompt نامعتبر باشد
        """
        # اعتبارسنجی Prompt
        is_valid, error = await self.provider.validate_prompt(prompt)
        if not is_valid:
            logger.warning(
                f"Invalid prompt from user {user_id}: {error}"
            )
            raise ValueError(error)
        
        # ساخت Request
        request = GenerationRequest(
            user_id=user_id,
            prompt=prompt.strip(),
            style=style,
            aspect_ratio=aspect_ratio,
            quality=quality,
            count=count,
            status=GenerationStatus.PENDING
        )
        
        # ذخیره در active requests
        self._active_requests[request.generation_id] = request
        
        logger.info(
            f"Generation request created: "
            f"id={request.generation_id}, "
            f"user={user_id}"
        )
        
        return request
    
    async def execute_generation(
        self,
        request: GenerationRequest
    ) -> GenerationResult:
        """
        اجرای تولید تصویر
        
        Args:
            request: درخواست تولید
            
        Returns:
            GenerationResult
        """
        # تغییر وضعیت به PROCESSING
        request.status = GenerationStatus.PROCESSING
        
        logger.info(
            f"Starting generation: id={request.generation_id}"
        )
        
        try:
            # صدا زدن Provider
            result = await self.provider.generate(request)
            
            # ذخیره در History (Session-based)
            self._add_to_history(request.user_id, result)
            
            # حذف از active requests
            self._active_requests.pop(request.generation_id, None)
            
            return result
        
        except Exception as e:
            logger.error(
                f"Generation failed: "
                f"id={request.generation_id}, "
                f"error={type(e).__name__}",
                exc_info=True
            )
            
            # ساخت نتیجه با وضعیت FAILED
            result = GenerationResult(
                generation_id=request.generation_id,
                user_id=request.user_id,
                prompt=request.prompt,
                style=request.style,
                aspect_ratio=request.aspect_ratio,
                quality=request.quality,
                count=request.count,
                status=GenerationStatus.FAILED,
                mock_result="",
                created_at=request.created_at,
                error_message="خطایی در تولید تصویر رخ داد"
            )
            
            # حذف از active requests
            self._active_requests.pop(request.generation_id, None)
            
            return result
    
    def _add_to_history(self, user_id: int, result: GenerationResult):
        """
        افزودن به History کاربر (Session-based)
        
        در نسخه واقعی این به Database ذخیره می‌شود
        """
        if user_id not in self._user_history:
            self._user_history[user_id] = []
        
        self._user_history[user_id].append(result)
        
        # محدود کردن تعداد History (حافظه)
        if len(self._user_history[user_id]) > 20:
            self._user_history[user_id] = self._user_history[user_id][-20:]
    
    def get_user_history(
        self,
        user_id: int,
        limit: int = 10
    ) -> list[GenerationResult]:
        """
        دریافت History کاربر
        
        Args:
            user_id: شناسه کاربر
            limit: حداکثر تعداد
            
        Returns:
            لیست GenerationResult (جدیدترین‌ها اول)
        """
        history = self._user_history.get(user_id, [])
        return list(reversed(history[-limit:]))
    
    def get_user_stats(self, user_id: int) -> Dict[str, int]:
        """
        دریافت آمار کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            Dictionary شامل آمار
        """
        history = self._user_history.get(user_id, [])
        
        completed_count = sum(
            1 for r in history 
            if r.status == GenerationStatus.COMPLETED
        )
        
        total_images = sum(
            r.count for r in history 
            if r.status == GenerationStatus.COMPLETED
        )
        
        return {
            'total_requests': len(history),
            'completed_requests': completed_count,
            'total_images': total_images
        }
    
    def get_generation_by_id(
        self,
        generation_id: str,
        user_id: int
    ) -> Optional[GenerationResult]:
        """
        دریافت یک Generation با ID
        
        Args:
            generation_id: شناسه Generation
            user_id: شناسه کاربر (برای امنیت)
            
        Returns:
            GenerationResult یا None
        """
        history = self._user_history.get(user_id, [])
        
        for result in history:
            if result.generation_id == generation_id:
                return result
        
        return None
    
    def clear_user_history(self, user_id: int):
        """
        پاک کردن History کاربر
        
        Args:
            user_id: شناسه کاربر
        """
        self._user_history.pop(user_id, None)
        logger.info(f"History cleared for user {user_id}")
