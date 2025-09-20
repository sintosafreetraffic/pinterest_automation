#!/usr/bin/env python3
"""
Test script to verify deployment configuration
"""

import os
import sys
from dotenv import load_dotenv

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("🧪 Testing Environment Variables")
    print("=" * 50)
    
    load_dotenv()
    
    required_vars = [
        'SHOPIFY_API_KEY',
        'SHOPIFY_STORE_URL', 
        'SHOPIFY_COLLECTION_ID',
        'PINTEREST_ACCESS_TOKEN',
        'PINTEREST_APP_ID',
        'PINTEREST_APP_SECRET',
        'OPENAI_API_KEY',
        'SHEET_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 10}...{value[-4:] if len(value) > 4 else '***'}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing {len(missing_vars)} required environment variables")
        return False
    else:
        print(f"\n✅ All {len(required_vars)} required environment variables are set")
        return True

def test_imports():
    """Test if all required modules can be imported"""
    print("\n🧪 Testing Module Imports")
    print("=" * 50)
    
    modules_to_test = [
        'requests',
        'flask',
        'gspread',
        'openai',
        'pandas',
        'numpy'
    ]
    
    failed_imports = []
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}: Import successful")
        except ImportError as e:
            print(f"❌ {module}: Import failed - {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import {len(failed_imports)} modules")
        return False
    else:
        print(f"\n✅ All {len(modules_to_test)} modules imported successfully")
        return True

def test_automation_functions():
    """Test if automation functions can be imported"""
    print("\n🧪 Testing Automation Functions")
    print("=" * 50)
    
    try:
        # Test collection move function
        from a import move_processed_products_to_generated_collection
        print("✅ Collection move function: Import successful")
        
        # Test scheduler
        from scheduler import run_automation_workflow
        print("✅ Automation workflow function: Import successful")
        
        # Test main web service
        from main import app
        print("✅ Flask app: Import successful")
        
        print("\n✅ All automation functions imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import automation functions: {e}")
        return False

def test_web_service():
    """Test if web service can start"""
    print("\n🧪 Testing Web Service")
    print("=" * 50)
    
    try:
        from main import app
        
        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint: Working")
            else:
                print(f"❌ Health endpoint: Failed with status {response.status_code}")
                return False
            
            # Test status endpoint
            response = client.get('/status')
            if response.status_code == 200:
                print("✅ Status endpoint: Working")
            else:
                print(f"❌ Status endpoint: Failed with status {response.status_code}")
                return False
        
        print("\n✅ Web service tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Web service test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Shopify-Pinterest Automation - Deployment Test")
    print("=" * 60)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Module Imports", test_imports),
        ("Automation Functions", test_automation_functions),
        ("Web Service", test_web_service)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for deployment to Render.")
        return True
    else:
        print("❌ Some tests failed. Please fix the issues before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
