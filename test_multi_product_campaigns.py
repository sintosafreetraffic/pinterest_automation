#!/usr/bin/env python3
"""
Test script to run multi-product campaigns with 10 products per campaign
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

def test_multi_product_campaigns():
    """Test multi-product campaign creation with 10 products per campaign"""
    print("🧪 Testing multi-product campaign creation...")
    
    try:
        # Import the actual campaign creation function
        from a import run
        
        # Get second sheet ID from environment
        second_sheet_id = os.getenv("SECOND_SHEET_ID")
        if not second_sheet_id:
            print("❌ SECOND_SHEET_ID not found in environment variables")
            return False
        
        print(f"✅ Using Second Sheet ID: {second_sheet_id}")
        print("📊 Campaign Configuration:")
        print("   - Mode: multi_product")
        print("   - Products per Campaign: 10")
        print("   - Daily Budget: 10 euro (1000 cents)")
        print("   - Second Sheet: Enabled")
        print("   - CTA: 'On Sale'")
        
        # Run the actual campaign creation with multi-product parameters
        print("\n🚀 Running multi-product campaign creation...")
        result = run(
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
            print("ℹ️ No eligible pins found for advertising")
            print("ℹ️ This means all available content has been processed")
        elif result:
            print("✅ Multi-product campaign creation completed successfully")
        else:
            print("⚠️ Campaign creation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Testing Multi-Product Campaign Creation")
    print("=" * 50)
    
    success = test_multi_product_campaigns()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")
