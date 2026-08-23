"""
Test Script for AI Image Admin Panel

این script Import و ساختار کلی Admin Panel را تست می‌کند
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_service_imports():
    """Test importing services"""
    print("\n📦 Testing Service Imports...")
    
    try:
        from services.ai_image import (
            AdminService,
            ConfigService,
            ContentService,
            BroadcastService,
            MotherBotGateway,
            get_mother_bot_gateway
        )
        print("✅ All services imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Service import failed: {e}")
        return False


def test_keyboard_imports():
    """Test importing keyboards"""
    print("\n⌨️ Testing Keyboard Imports...")
    
    try:
        from keyboards.ai_image_admin_keyboards import (
            get_admin_main_keyboard,
            get_management_keyboard,
            get_communication_keyboard,
            get_ai_settings_keyboard,
            get_content_keyboard,
            get_system_keyboard
        )
        print("✅ All keyboards imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Keyboard import failed: {e}")
        return False


def test_handler_imports():
    """Test importing admin handler"""
    print("\n🎛️ Testing Handler Imports...")
    
    try:
        from handlers.child_bots.ai_image_admin import (
            get_admin_router,
            is_admin
        )
        print("✅ Admin handler imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Handler import failed: {e}")
        return False


def test_service_instantiation():
    """Test creating service instances"""
    print("\n🏗️ Testing Service Instantiation...")
    
    try:
        from services.ai_image import (
            AdminService,
            ConfigService,
            ContentService,
            BroadcastService,
            get_mother_bot_gateway
        )
        
        admin_service = AdminService()
        config_service = ConfigService()
        content_service = ContentService()
        broadcast_service = BroadcastService()
        gateway = get_mother_bot_gateway(mock_mode=True)
        
        print("✅ All services instantiated successfully")
        return True
    except Exception as e:
        print(f"❌ Service instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_operations():
    """Test basic config operations"""
    print("\n⚙️ Testing Config Operations...")
    
    try:
        from services.ai_image import ConfigService
        
        config_service = ConfigService()
        
        # Test getting AI config
        ai_config = config_service.get_ai_config()
        print(f"  - AI Config provider: {ai_config.provider}")
        
        # Test getting styles
        styles = config_service.get_all_styles()
        print(f"  - Styles count: {len(styles)}")
        
        # Test maintenance config
        maintenance = config_service.get_maintenance_config()
        print(f"  - Maintenance mode: {maintenance.mode.value}")
        
        print("✅ Config operations successful")
        return True
    except Exception as e:
        print(f"❌ Config operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_content_operations():
    """Test basic content operations"""
    print("\n📝 Testing Content Operations...")
    
    try:
        from services.ai_image import ContentService
        
        content_service = ContentService()
        
        # Test getting guide
        guide = content_service.get_guide()
        print(f"  - Guide length: {len(guide)} chars")
        
        # Test getting FAQs
        faqs = content_service.get_all_faqs()
        print(f"  - FAQs count: {len(faqs)}")
        
        # Test system messages
        messages = content_service.get_all_system_messages()
        print(f"  - System messages count: {len(messages)}")
        
        print("✅ Content operations successful")
        return True
    except Exception as e:
        print(f"❌ Content operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gateway_operations():
    """Test Mother Bot Gateway"""
    print("\n🌉 Testing Mother Bot Gateway...")
    
    try:
        from services.ai_image import get_mother_bot_gateway
        
        gateway = get_mother_bot_gateway(mock_mode=True)
        
        # Test mock operations (async functions need event loop)
        print(f"  - Gateway mode: {'Mock' if gateway.mock_mode else 'Real'}")
        
        print("✅ Gateway operations successful")
        return True
    except Exception as e:
        print(f"❌ Gateway operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_existing_ai_image_handler():
    """Test that existing AI Image handler still works"""
    print("\n🖼️ Testing Existing AI Image Handler...")
    
    try:
        from handlers.child_bots.ai_image import get_router
        
        router = get_router()
        print(f"  - Router name: {router.name}")
        
        print("✅ Existing AI Image handler works")
        return True
    except Exception as e:
        print(f"❌ Existing handler failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("AI Image Admin Panel - Import & Structure Test")
    print("="*60)
    
    results = []
    
    results.append(("Service Imports", test_service_imports()))
    results.append(("Keyboard Imports", test_keyboard_imports()))
    results.append(("Handler Imports", test_handler_imports()))
    results.append(("Service Instantiation", test_service_instantiation()))
    results.append(("Config Operations", test_config_operations()))
    results.append(("Content Operations", test_content_operations()))
    results.append(("Gateway Operations", test_gateway_operations()))
    results.append(("Existing Handler", test_existing_ai_image_handler()))
    
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n📈 Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
