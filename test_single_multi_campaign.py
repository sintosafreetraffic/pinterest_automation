#!/usr/bin/env python3
"""
Test script to create only ONE multi-product campaign with 10 products
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

def test_single_multi_campaign():
    """Test creating only ONE multi-product campaign with 10 products"""
    print("🧪 Testing ONE multi-product campaign creation...")
    
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
        print("   - LIMIT: Only 1 campaign will be created")
        
        # First, let's check how many eligible pins we have
        from a import load_pins_from_sheet
        pins_by_product = load_pins_from_sheet()
        
        if not pins_by_product:
            print("❌ No eligible pins found for advertising")
            return False
        
        total_products = len(pins_by_product)
        total_pins = sum(len(v) for v in pins_by_product.values())
        
        print(f"\n📊 Available for campaigns:")
        print(f"   - Total products: {total_products}")
        print(f"   - Total pins: {total_pins}")
        print(f"   - Products per campaign: 10")
        print(f"   - Possible campaigns: {total_products // 10}")
        
        if total_products < 10:
            print("❌ Not enough products for a 10-product campaign!")
            print(f"   Need: 10 products, Have: {total_products}")
            return False
        
        print(f"\n✅ Can create {total_products // 10} campaigns")
        print("⚠️ WARNING: This will create Pinterest campaigns that cost money!")
        print("⚠️ Only the first campaign will be created for testing")
        
        # Run the actual campaign creation with multi-product parameters
        print("\n🚀 Running multi-product campaign creation (LIMITED TO 1 CAMPAIGN)...")
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
            print("ℹ️ Check Pinterest Ads Manager to see the created campaign")
        else:
            print("⚠️ Campaign creation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Testing ONE Multi-Product Campaign Creation")
    print("=" * 50)
    
    success = test_single_multi_campaign()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test completed successfully!")
        print("ℹ️ Check Pinterest Ads Manager to verify the campaign was created")
    else:
        print("❌ Test failed!")
