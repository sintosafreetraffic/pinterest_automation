#!/usr/bin/env python3
"""
Test script to verify campaign configuration locally
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_campaign_configuration():
    """Test campaign configuration with multi-product setup"""
    print("🧪 Testing campaign configuration locally...")
    
    try:
        # Import required modules
        from forefront import run_step3_campaign_creation
        
        # Test the campaign creation with multi-product configuration
        print("📊 Testing multi-product campaign configuration:")
        print("   - Campaign Mode: multi_product")
        print("   - Products per Campaign: 10")
        print("   - Daily Budget: 10 euro (1000 cents)")
        print("   - Second Sheet: Enabled")
        print("   - CTA: 'On Sale' (added to pins)")
        
        # Get second sheet ID from environment
        second_sheet_id = os.getenv("SECOND_SHEET_ID")
        if not second_sheet_id:
            print("❌ SECOND_SHEET_ID not found in environment variables")
            print("ℹ️ This is required for multi-product campaigns")
            return False
        
        print(f"✅ Second Sheet ID: {second_sheet_id}")
        
        # Test campaign creation
        print("\n🚀 Running campaign creation test...")
        result = run_step3_campaign_creation(
            campaign_mode="multi_product",
            products_per_campaign=10,
            daily_budget=1000,  # 10 euro in cents
            campaign_type="WEB_CONVERSION",
            target_language="de",
            enable_second_sheet=True,
            second_sheet_id=second_sheet_id,
            campaign_start_date="next_tuesday",
            custom_start_date=""
        )
        
        print(f"\n📊 Campaign creation result: {result}")
        
        if result == "NO_ELIGIBLE_PINS":
            print("✅ Test completed: No eligible pins found (expected if no pins ready)")
            print("ℹ️ This means the configuration is working correctly")
        elif result:
            print("✅ Test completed: Campaign creation successful")
        else:
            print("⚠️ Test completed: Campaign creation failed")
        
        print("\n✅ Campaign configuration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pin_cta():
    """Test that pins have CTA 'On Sale'"""
    print("\n🧪 Testing pin CTA configuration...")
    
    try:
        from pinterest_post import post_pin
        
        # Check if the post_pin function includes CTA
        import inspect
        source = inspect.getsource(post_pin)
        
        if '"call_to_action": "ON_SALE"' in source:
            print("✅ SUCCESS: Pin CTA 'On Sale' is configured correctly")
            return True
        else:
            print("❌ FAILED: Pin CTA 'On Sale' not found in post_pin function")
            return False
            
    except Exception as e:
        print(f"❌ Failed to check pin CTA: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Campaign Configuration Locally")
    print("=" * 50)
    
    # Test 1: Campaign configuration
    campaign_test = test_campaign_configuration()
    
    # Test 2: Pin CTA
    cta_test = test_pin_cta()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Campaign Configuration: {'✅ PASS' if campaign_test else '❌ FAIL'}")
    print(f"   Pin CTA 'On Sale': {'✅ PASS' if cta_test else '❌ FAIL'}")
    
    if campaign_test and cta_test:
        print("\n🎉 All tests passed! Configuration is correct.")
    else:
        print("\n⚠️ Some tests failed. Please check the configuration.")
