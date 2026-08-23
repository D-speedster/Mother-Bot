"""
تست Owner-Based Authorization برای AI Image Admin Panel

این تست‌ها بررسی می‌کنند که:
1. فقط Owner می‌تواند به Admin Panel دسترسی داشته باشد
2. Non-Owner دسترسی Silent است (هیچ پاسخی ارسال نمی‌شود)
3. هر Bot Instance authorization مستقل خودش را دارد
4. Owner یک Bot نمی‌تواند به Admin Panel Bot دیگری دسترسی داشته باشد
"""

import asyncio
from unittest.mock import AsyncMock, Mock, MagicMock
from aiogram import Bot
from aiogram.types import Message, User, Chat, CallbackQuery


# Import handlers
from handlers.child_bots.ai_image_admin import (
    get_bot_context,
    is_owner,
    check_owner_access,
    cmd_admin
)


def create_mock_bot(bot_id: int, owner_id: int, bot_type: str = "ai_image") -> Bot:
    """ساخت Mock Bot با bot_context"""
    mock_bot = Mock(spec=Bot)
    mock_bot.bot_context = {
        "bot_id": bot_id,
        "owner_id": owner_id,
        "bot_type": bot_type
    }
    return mock_bot


def create_mock_message(user_id: int, bot: Bot) -> Message:
    """ساخت Mock Message"""
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.first_name = f"User{user_id}"
    
    mock_chat = Mock(spec=Chat)
    mock_chat.id = user_id
    
    mock_message = Mock(spec=Message)
    mock_message.from_user = mock_user
    mock_message.chat = mock_chat
    mock_message.bot = bot
    mock_message.answer = AsyncMock()
    
    return mock_message


def create_mock_callback(user_id: int, bot: Bot) -> CallbackQuery:
    """ساخت Mock CallbackQuery"""
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    
    mock_callback = Mock(spec=CallbackQuery)
    mock_callback.from_user = mock_user
    mock_callback.bot = bot
    mock_callback.answer = AsyncMock()
    mock_callback.message = Mock()
    mock_callback.message.edit_text = AsyncMock()
    
    return mock_callback


# ========== تست Context Functions ==========

def test_get_bot_context():
    """Test: دریافت bot_context از Bot instance"""
    print("\n🧪 Test 1: get_bot_context()")
    
    # Setup: Bot با context
    bot = create_mock_bot(bot_id=17, owner_id=79049016)
    message = create_mock_message(user_id=79049016, bot=bot)
    
    # Execute
    context = get_bot_context(message)
    
    # Assert
    assert context is not None, "❌ context نباید None باشد"
    assert context['bot_id'] == 17, f"❌ bot_id: expected 17, got {context.get('bot_id')}"
    assert context['owner_id'] == 79049016, f"❌ owner_id: expected 79049016, got {context.get('owner_id')}"
    assert context['bot_type'] == "ai_image", f"❌ bot_type: expected ai_image, got {context.get('bot_type')}"
    
    print("✅ Test 1 PASSED: bot_context به درستی دریافت شد")


def test_is_owner_positive():
    """Test: Owner بودن کاربر - Positive Case"""
    print("\n🧪 Test 2: is_owner() - Owner Access")
    
    # Setup
    bot_context = {
        "bot_id": 17,
        "owner_id": 79049016,
        "bot_type": "ai_image"
    }
    
    # Execute
    result = is_owner(user_id=79049016, bot_context=bot_context)
    
    # Assert
    assert result is True, "❌ Owner باید True برگرداند"
    
    print("✅ Test 2 PASSED: Owner به درستی تشخیص داده شد")


def test_is_owner_negative():
    """Test: Owner نبودن کاربر - Negative Case"""
    print("\n🧪 Test 3: is_owner() - Non-Owner Access")
    
    # Setup
    bot_context = {
        "bot_id": 17,
        "owner_id": 79049016,
        "bot_type": "ai_image"
    }
    
    # Execute
    result = is_owner(user_id=12345678, bot_context=bot_context)
    
    # Assert
    assert result is False, "❌ Non-Owner باید False برگرداند"
    
    print("✅ Test 3 PASSED: Non-Owner به درستی رد شد")


# ========== تست Authorization ==========

async def test_owner_access_message():
    """Test A: Owner → /admin در Bot خودش → Panel نمایش داده شود"""
    print("\n🧪 Test A: Owner Access via Message (/admin)")
    
    # Setup: User A ساخته Bot #17
    bot = create_mock_bot(bot_id=17, owner_id=79049016)
    message = create_mock_message(user_id=79049016, bot=bot)
    
    # Execute
    result = await check_owner_access(message)
    
    # Assert
    assert result is True, "❌ Owner باید دسترسی داشته باشد"
    assert message.answer.call_count == 0, "❌ check_owner_access نباید پاسخی ارسال کند"
    
    print("✅ Test A PASSED: Owner دسترسی دارد")


async def test_non_owner_access_message():
    """Test B: Non-Owner → /admin در Bot غیرخودش → Silent"""
    print("\n🧪 Test B: Non-Owner Access via Message (Silent)")
    
    # Setup: User B تلاش برای دسترسی به Bot #17 که Owner آن User A است
    bot = create_mock_bot(bot_id=17, owner_id=79049016)
    message = create_mock_message(user_id=12345678, bot=bot)
    
    # Execute
    result = await check_owner_access(message)
    
    # Assert
    assert result is False, "❌ Non-Owner نباید دسترسی داشته باشد"
    assert message.answer.call_count == 0, "❌ برای Non-Owner نباید هیچ پاسخی ارسال شود (Silent)"
    
    print("✅ Test B PASSED: Non-Owner Silent شد")


async def test_owner_access_callback():
    """Test E: Owner → Callback در Bot خودش → Works"""
    print("\n🧪 Test E: Owner Access via Callback")
    
    # Setup
    bot = create_mock_bot(bot_id=17, owner_id=79049016)
    callback = create_mock_callback(user_id=79049016, bot=bot)
    
    # Execute
    result = await check_owner_access(callback)
    
    # Assert
    assert result is True, "❌ Owner باید دسترسی داشته باشد"
    
    print("✅ Test E PASSED: Owner Callback دارد")


async def test_non_owner_access_callback():
    """Test F: Non-Owner → Callback در Bot غیرخودش → Silent"""
    print("\n🧪 Test F: Non-Owner Access via Callback (Silent)")
    
    # Setup
    bot = create_mock_bot(bot_id=17, owner_id=79049016)
    callback = create_mock_callback(user_id=12345678, bot=bot)
    
    # Execute
    result = await check_owner_access(callback)
    
    # Assert
    assert result is False, "❌ Non-Owner نباید دسترسی داشته باشد"
    assert callback.answer.call_count == 1, "❌ Callback باید dismiss شود"
    
    print("✅ Test F PASSED: Non-Owner Callback Silent شد")


# ========== تست Isolation ==========

async def test_multiple_bots_isolation():
    """Test G: دو Bot همزمان با Ownerهای مختلف - Isolation کامل"""
    print("\n🧪 Test G: Multiple Bots Isolation")
    
    # Setup: دو Bot با Ownerهای مختلف
    bot_17 = create_mock_bot(bot_id=17, owner_id=79049016)  # User A's bot
    bot_18 = create_mock_bot(bot_id=18, owner_id=12345678)  # User B's bot
    
    # Test 1: User A → Bot #17 → Access ✅
    message_a_to_17 = create_mock_message(user_id=79049016, bot=bot_17)
    result_a_to_17 = await check_owner_access(message_a_to_17)
    assert result_a_to_17 is True, "❌ User A باید به Bot #17 خودش دسترسی داشته باشد"
    
    # Test 2: User B → Bot #17 → No Access ❌
    message_b_to_17 = create_mock_message(user_id=12345678, bot=bot_17)
    result_b_to_17 = await check_owner_access(message_b_to_17)
    assert result_b_to_17 is False, "❌ User B نباید به Bot #17 دسترسی داشته باشد"
    
    # Test 3: User A → Bot #18 → No Access ❌
    message_a_to_18 = create_mock_message(user_id=79049016, bot=bot_18)
    result_a_to_18 = await check_owner_access(message_a_to_18)
    assert result_a_to_18 is False, "❌ User A نباید به Bot #18 دسترسی داشته باشد"
    
    # Test 4: User B → Bot #18 → Access ✅
    message_b_to_18 = create_mock_message(user_id=12345678, bot=bot_18)
    result_b_to_18 = await check_owner_access(message_b_to_18)
    assert result_b_to_18 is True, "❌ User B باید به Bot #18 خودش دسترسی داشته باشد"
    
    print("✅ Test G PASSED: Bot Isolation کامل است")
    print("   ✓ User A → Bot #17 ✅")
    print("   ✓ User B → Bot #17 ❌")
    print("   ✓ User A → Bot #18 ❌")
    print("   ✓ User B → Bot #18 ✅")


# ========== Main Test Runner ==========

async def run_async_tests():
    """اجرای تست‌های async"""
    print("\n" + "="*60)
    print("🚀 Running Owner-Based Authorization Tests")
    print("="*60)
    
    # Sync tests
    test_get_bot_context()
    test_is_owner_positive()
    test_is_owner_negative()
    
    # Async tests
    await test_owner_access_message()
    await test_non_owner_access_message()
    await test_owner_access_callback()
    await test_non_owner_access_callback()
    await test_multiple_bots_isolation()
    
    print("\n" + "="*60)
    print("✅ همه تست‌ها با موفقیت انجام شد!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_async_tests())
