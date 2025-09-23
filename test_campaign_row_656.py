#!/usr/bin/env python3
"""
Test script to test campaign creation for row 656
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

def test_campaign_creation_row_656():
    """Test campaign creation specifically for row 656"""
    print("🧪 Testing campaign creation for row 656...")
    
    try:
        # Import the campaign creation function
        from a import run
        
        # Test with single product mode for row 656
        print("📊 Running campaign creation in single_product mode...")
        result = run(
            campaign_mode="single_product",
            products_per_campaign=1,
            daily_budget=1000,  # 10 euro in cents
            campaign_type="WEB_CONVERSION",
            target_language="de",
            enable_second_sheet=False,
            second_sheet_id="",
            campaign_start_date="next_tuesday",
            custom_start_date=""
        )
        
        if result == "NO_ELIGIBLE_PINS":
            print("✅ Test completed: No eligible pins found (expected if no pins ready)")
        else:
            print(f"✅ Test completed: Campaign creation result: {result}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_campaign_creation_row_656()
