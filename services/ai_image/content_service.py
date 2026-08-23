"""
Content Service برای AI Image Bot

مدیریت محتوا شامل:
- راهنما (Guide)
- سوالات متداول (FAQ)
- پیام‌های سیستم
"""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FAQ:
    """مدل FAQ"""
    id: str
    question: str
    answer: str
    enabled: bool = True
    order: int = 0
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return asdict(self)


class SystemMessages:
    """پیام‌های سیستم قابل تنظیم"""
    
    def __init__(self):
        """مقداردهی اولیه با پیام‌های پیش‌فرض"""
        self.messages = {
            'welcome': (
                "🖼️ **به ربات تولید تصویر خوش آمدید!**\n\n"
                "✨ استودیو تولید تصویر با هوش مصنوعی\n\n"
                "از منوی زیر یک گزینه را انتخاب کنید:"
            ),
            'generation_started': (
                "🎨 **در حال آماده‌سازی تصویر...**\n\n"
                "⏳ لطفاً چند لحظه صبر کنید..."
            ),
            'generation_completed': (
                "✅ **تولید تصویر انجام شد!**\n\n"
                "💡 تصویر شما آماده است."
            ),
            'generation_failed': (
                "❌ **خطایی در تولید تصویر رخ داد!**\n\n"
                "لطفاً دوباره تلاش کنید."
            ),
            'limit_reached': (
                "⚠️ **محدودیت روزانه**\n\n"
                "شما به حداکثر تعداد تولید تصویر در روز رسیده‌اید.\n"
                "لطفاً فردا دوباره امتحان کنید."
            ),
            'maintenance': (
                "🔧 **سیستم در حال تعمیر و نگهداری است**\n\n"
                "لطفاً بعداً مراجعه کنید."
            ),
            'invalid_prompt': (
                "⚠️ **Prompt نامعتبر است**\n\n"
                "لطفاً توضیحات معتبرتری وارد کنید."
            ),
            'help': (
                "📖 **راهنمای استفاده**\n\n"
                "**مراحل تولید تصویر:**\n\n"
                "1️⃣ روی «🖼️ ساخت تصویر» کلیک کنید\n"
                "2️⃣ Prompt خود را بنویسید\n"
                "3️⃣ سبک تصویر را انتخاب کنید\n"
                "4️⃣ نسبت و کیفیت را مشخص کنید\n"
                "5️⃣ تعداد تصاویر را انتخاب کنید\n"
                "6️⃣ درخواست را تأیید کنید\n\n"
                "💡 Prompt را به انگلیسی بنویسید تا نتیجه بهتری دریافت کنید."
            )
        }
    
    def get(self, key: str) -> str:
        """دریافت یک پیام"""
        return self.messages.get(key, "")
    
    def set(self, key: str, message: str) -> bool:
        """تنظیم یک پیام"""
        if key in self.messages:
            self.messages[key] = message
            return True
        return False
    
    def get_all(self) -> Dict[str, str]:
        """دریافت تمام پیام‌ها"""
        return self.messages.copy()


class ContentService:
    """
    سرویس مدیریت محتوا برای AI Image Bot
    
    ⚠️ فعلاً محتوا در حافظه نگهداری می‌شود
    در آینده به Database متصل خواهد شد
    """
    
    def __init__(self):
        """مقداردهی اولیه"""
        self._guide_content = self._init_default_guide()
        self._faqs: Dict[str, FAQ] = {}
        self._system_messages = SystemMessages()
        self._offline_messages: List[Dict[str, Any]] = []
    
    def _init_default_guide(self) -> str:
        """مقداردهی راهنمای پیش‌فرض"""
        return """📖 **راهنمای کامل AI Image Bot**

## 🎨 معرفی

این ربات به شما امکان می‌دهد با استفاده از هوش مصنوعی، تصاویر خلاقانه و منحصربه‌فرد بسازید.

## 🚀 مراحل تولید تصویر

### مرحله 1: شروع
روی دکمه «🖼️ ساخت تصویر» کلیک کنید.

### مرحله 2: نوشتن Prompt
توضیحات تصویر موردنظر خود را وارد کنید.

**نکات مهم:**
• Prompt را به انگلیسی بنویسید
• هرچه جزئیات بیشتر، کنترل بیشتر
• از کلمات کلیدی دقیق استفاده کنید

**مثال Prompt خوب:**
`a futuristic city at night, neon lights, cyberpunk style, highly detailed`

### مرحله 3: انتخاب سبک
سبک تصویر را انتخاب کنید:
• 🎨 واقع‌گرایانه
• 🎬 سینمایی
• 🎨 انیمه
• 🖌️ هنر دیجیتال
• 📷 عکاسی

### مرحله 4: تنظیمات
نسبت و کیفیت تصویر را مشخص کنید.

### مرحله 5: تأیید
Preview را بررسی و تولید را تأیید کنید.

## 💡 نکات پیشرفته

### چگونه Prompt خوب بنویسیم؟
1. موضوع اصلی را مشخص کنید
2. جزئیات را اضافه کنید
3. سبک هنری را ذکر کنید
4. نورپردازی را توصیف کنید
5. کیفیت مورد نیاز را بیان کنید

### مثال‌های Prompt

**پرتره:**
`portrait of a young woman, professional photography, natural lighting, bokeh background`

**منظره:**
`mountain landscape at sunset, dramatic clouds, golden hour, highly detailed`

**مفهومی:**
`futuristic robot, sci-fi concept art, artstation trending, 4k, detailed`

## ❓ سوالات متداول

**Q: چرا باید Prompt به انگلیسی باشد؟**
A: مدل‌های AI عموماً با داده‌های انگلیسی آموزش دیده‌اند و نتایج بهتری می‌دهند.

**Q: چند تصویر می‌توانم در روز تولید کنم؟**
A: محدودیت روزانه توسط مدیر تنظیم می‌شود.

**Q: چطور می‌توانم کیفیت تصاویر را بهبود دهم؟**
A: از کیفیت «بالا» استفاده کنید و Prompt دقیق‌تری بنویسید.

## 📞 پشتیبانی

در صورت بروز مشکل، با پشتیبانی تماس بگیرید.
"""
    
    # ========== Guide ==========
    
    def get_guide(self) -> str:
        """دریافت راهنما"""
        return self._guide_content
    
    async def update_guide(self, content: str) -> bool:
        """
        به‌روزرسانی راهنما
        
        Args:
            content: محتوای جدید
            
        Returns:
            True اگر موفق بود
        """
        try:
            self._guide_content = content
            logger.info("Guide content updated")
            # TODO: ذخیره در Database
            return True
        except Exception as e:
            logger.error(f"Error updating guide: {e}")
            return False
    
    # ========== FAQ ==========
    
    def get_all_faqs(self, only_enabled: bool = False) -> List[FAQ]:
        """
        دریافت تمام FAQها
        
        Args:
            only_enabled: فقط FAQهای فعال
            
        Returns:
            لیست FAQ
        """
        faqs = list(self._faqs.values())
        if only_enabled:
            faqs = [f for f in faqs if f.enabled]
        # مرتب‌سازی بر اساس order
        faqs.sort(key=lambda x: x.order)
        return faqs
    
    def get_faq(self, faq_id: str) -> Optional[FAQ]:
        """دریافت یک FAQ"""
        return self._faqs.get(faq_id)
    
    async def create_faq(
        self,
        question: str,
        answer: str,
        enabled: bool = True,
        order: int = 0
    ) -> FAQ:
        """
        ایجاد FAQ جدید
        
        Args:
            question: سوال
            answer: جواب
            enabled: فعال/غیرفعال
            order: ترتیب نمایش
            
        Returns:
            FAQ ساخته‌شده
        """
        import uuid
        faq_id = str(uuid.uuid4())
        faq = FAQ(
            id=faq_id,
            question=question,
            answer=answer,
            enabled=enabled,
            order=order
        )
        self._faqs[faq_id] = faq
        logger.info(f"FAQ created: {faq_id}")
        # TODO: ذخیره در Database
        return faq
    
    async def update_faq(
        self,
        faq_id: str,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        enabled: Optional[bool] = None,
        order: Optional[int] = None
    ) -> bool:
        """
        به‌روزرسانی FAQ
        
        Args:
            faq_id: شناسه FAQ
            question: سوال جدید
            answer: جواب جدید
            enabled: فعال/غیرفعال
            order: ترتیب جدید
            
        Returns:
            True اگر موفق بود
        """
        faq = self._faqs.get(faq_id)
        if not faq:
            logger.warning(f"FAQ not found: {faq_id}")
            return False
        
        try:
            if question is not None:
                faq.question = question
            if answer is not None:
                faq.answer = answer
            if enabled is not None:
                faq.enabled = enabled
            if order is not None:
                faq.order = order
            
            logger.info(f"FAQ updated: {faq_id}")
            # TODO: ذخیره در Database
            return True
        except Exception as e:
            logger.error(f"Error updating FAQ {faq_id}: {e}")
            return False
    
    async def delete_faq(self, faq_id: str) -> bool:
        """
        حذف FAQ
        
        Args:
            faq_id: شناسه FAQ
            
        Returns:
            True اگر موفق بود
        """
        if faq_id in self._faqs:
            del self._faqs[faq_id]
            logger.info(f"FAQ deleted: {faq_id}")
            # TODO: حذف از Database
            return True
        return False
    
    # ========== System Messages ==========
    
    def get_system_message(self, key: str) -> str:
        """دریافت یک پیام سیستم"""
        return self._system_messages.get(key)
    
    def get_all_system_messages(self) -> Dict[str, str]:
        """دریافت تمام پیام‌های سیستم"""
        return self._system_messages.get_all()
    
    async def update_system_message(self, key: str, message: str) -> bool:
        """
        به‌روزرسانی پیام سیستم
        
        Args:
            key: کلید پیام
            message: پیام جدید
            
        Returns:
            True اگر موفق بود
        """
        success = self._system_messages.set(key, message)
        if success:
            logger.info(f"System message updated: {key}")
            # TODO: ذخیره در Database
        return success
    
    # ========== Offline Messages ==========
    
    async def save_offline_message(
        self,
        user_id: int,
        message_text: str,
        message_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        ذخیره پیام آفلاین
        
        Args:
            user_id: شناسه کاربر
            message_text: متن پیام
            message_data: داده‌های اضافی
            
        Returns:
            شناسه پیام ذخیره‌شده
        """
        import uuid
        message_id = str(uuid.uuid4())
        offline_msg = {
            'id': message_id,
            'user_id': user_id,
            'message_text': message_text,
            'message_data': message_data or {},
            'timestamp': datetime.utcnow().isoformat(),
            'handled': False
        }
        self._offline_messages.append(offline_msg)
        logger.info(f"Offline message saved: {message_id}")
        # TODO: ذخیره در Database
        return message_id
    
    def get_offline_messages(
        self,
        only_unhandled: bool = False
    ) -> List[Dict[str, Any]]:
        """
        دریافت پیام‌های آفلاین
        
        Args:
            only_unhandled: فقط پیام‌های بررسی‌نشده
            
        Returns:
            لیست پیام‌های آفلاین
        """
        messages = self._offline_messages
        if only_unhandled:
            messages = [m for m in messages if not m['handled']]
        return list(reversed(messages))  # جدیدترین‌ها اول
    
    async def mark_offline_message_handled(self, message_id: str) -> bool:
        """
        علامت‌گذاری پیام آفلاین به عنوان بررسی‌شده
        
        Args:
            message_id: شناسه پیام
            
        Returns:
            True اگر موفق بود
        """
        for msg in self._offline_messages:
            if msg['id'] == message_id:
                msg['handled'] = True
                logger.info(f"Offline message marked as handled: {message_id}")
                # TODO: به‌روزرسانی در Database
                return True
        return False
