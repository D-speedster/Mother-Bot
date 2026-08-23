"""
Models و Enums برای AI Image Service
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


# ========== Enums ==========

class GenerationStatus(str, Enum):
    """وضعیت تولید تصویر"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageStyle(str, Enum):
    """سبک‌های تصویر"""
    REALISTIC = "realistic"
    CINEMATIC = "cinematic"
    ANIME = "anime"
    DIGITAL_ART = "digital_art"
    PHOTOGRAPHY = "photography"
    NONE = "none"
    
    def get_display_name(self) -> str:
        """نام نمایشی فارسی"""
        names = {
            "realistic": "🎨 واقع‌گرایانه",
            "cinematic": "🎬 سینمایی",
            "anime": "🎨 انیمه",
            "digital_art": "🖌️ هنر دیجیتال",
            "photography": "📷 عکاسی",
            "none": "✨ بدون سبک خاص"
        }
        return names.get(self.value, self.value)


class AspectRatio(str, Enum):
    """نسبت‌های تصویر"""
    SQUARE = "1:1"
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"
    STANDARD = "4:3"
    
    def get_display_name(self) -> str:
        """نام نمایشی"""
        names = {
            "1:1": "1:1 (مربع)",
            "16:9": "16:9 (افقی)",
            "9:16": "9:16 (عمودی)",
            "4:3": "4:3 (استاندارد)"
        }
        return names.get(self.value, self.value)


class Quality(str, Enum):
    """کیفیت تصویر"""
    STANDARD = "standard"
    HIGH = "high"
    
    def get_display_name(self) -> str:
        """نام نمایشی"""
        names = {
            "standard": "⚡ استاندارد",
            "high": "✨ بالا"
        }
        return names.get(self.value, self.value)


# ========== Data Models ==========

@dataclass
class GenerationRequest:
    """درخواست تولید تصویر"""
    user_id: int
    prompt: str
    style: ImageStyle = ImageStyle.NONE
    aspect_ratio: AspectRatio = AspectRatio.SQUARE
    quality: Quality = Quality.STANDARD
    count: int = 1
    generation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: GenerationStatus = GenerationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """تبدیل به dictionary"""
        return {
            'generation_id': self.generation_id,
            'user_id': self.user_id,
            'prompt': self.prompt,
            'style': self.style.value,
            'aspect_ratio': self.aspect_ratio.value,
            'quality': self.quality.value,
            'count': self.count,
            'status': self.status.value,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class GenerationResult:
    """نتیجه تولید تصویر"""
    generation_id: str
    user_id: int
    prompt: str
    style: ImageStyle
    aspect_ratio: AspectRatio
    quality: Quality
    count: int
    status: GenerationStatus
    mock_result: str  # برای Prototype
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """تبدیل به dictionary"""
        return {
            'generation_id': self.generation_id,
            'user_id': self.user_id,
            'prompt': self.prompt,
            'style': self.style.value,
            'aspect_ratio': self.aspect_ratio.value,
            'quality': self.quality.value,
            'count': self.count,
            'status': self.status.value,
            'mock_result': self.mock_result,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }
