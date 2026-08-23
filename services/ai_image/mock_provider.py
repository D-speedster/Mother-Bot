"""
Mock Provider برای AI Image Generation

⚠️ این Provider هیچ API واقعی صدا نمی‌زند
فقط نتیجه Mock برمی‌گرداند
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from .models import (
    GenerationRequest,
    GenerationResult,
    GenerationStatus
)

logger = logging.getLogger(__name__)


class MockProvider:
    """
    Mock Provider برای شبیه‌سازی تولید تصویر
    
    در آینده این کلاس با:
    - OpenAIProvider
    - StabilityProvider
    - MidjourneyProvider
    جایگزین خواهد شد
    """
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        شبیه‌سازی تولید تصویر
        
        Args:
            request: درخواست تولید تصویر
            
        Returns:
            GenerationResult با وضعیت COMPLETED
        """
        logger.info(
            f"Mock Generation started: "
            f"user={request.user_id}, "
            f"prompt={request.prompt[:30]}..."
        )
        
        # شبیه‌سازی تأخیر پردازش (1-2 ثانیه)
        await asyncio.sleep(1.5)
        
        # ساخت نتیجه Mock
        mock_result = self._create_mock_result(request)
        
        result = GenerationResult(
            generation_id=request.generation_id,
            user_id=request.user_id,
            prompt=request.prompt,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            quality=request.quality,
            count=request.count,
            status=GenerationStatus.COMPLETED,
            mock_result=mock_result,
            created_at=request.created_at,
            completed_at=datetime.utcnow()
        )
        
        logger.info(
            f"Mock Generation completed: "
            f"generation_id={request.generation_id}"
        )
        
        return result
    
    def _create_mock_result(self, request: GenerationRequest) -> str:
        """
        ساخت متن نتیجه Mock
        
        در نسخه واقعی این بخش URL تصویر یا File ID برمی‌گرداند
        """
        return (
            f"🎨 تصویر Mock تولید شد\n\n"
            f"📝 Prompt: {request.prompt}\n"
            f"🎨 Style: {request.style.get_display_name()}\n"
            f"📐 Ratio: {request.aspect_ratio.get_display_name()}\n"
            f"⚡ Quality: {request.quality.get_display_name()}\n"
            f"🖼️ Count: {request.count}\n\n"
            f"⚠️ در نسخه واقعی اینجا تصویر نمایش داده می‌شود"
        )
    
    async def validate_prompt(self, prompt: str) -> tuple[bool, Optional[str]]:
        """
        اعتبارسنجی Prompt
        
        در نسخه واقعی می‌تواند شامل:
        - Content Moderation
        - NSFW Detection
        - Length Check
        باشد
        
        Args:
            prompt: متن Prompt
            
        Returns:
            (is_valid, error_message)
        """
        # بررسی خالی بودن
        if not prompt or not prompt.strip():
            return False, "Prompt نمی‌تواند خالی باشد"
        
        # بررسی طول
        if len(prompt) < 3:
            return False, "Prompt باید حداقل 3 کاراکتر باشد"
        
        if len(prompt) > 500:
            return False, "Prompt نباید بیش از 500 کاراکتر باشد"
        
        # همه چیز OK
        return True, None
